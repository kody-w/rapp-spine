# rapp-auth/1.0 — The Brainstem Auth Chain

> **Status:** Canonical · **Version:** 1.0 · **Home:** `kody-w/rapp-spine/specs/AUTH_CHAIN.md`
> **Layer:** Tier-1 (Brainstem / the grail kernel) · **Reference implementation:** `rapp_brainstem/brainstem.py`
> **Normative keywords:** MUST / MUST NOT / SHOULD / MAY per RFC 2119.

---

## 0. One-line definition

**The auth chain is the kernel's single outbound trust anchor: the operator's GitHub
account *is* the identity, and the brainstem holds zero API keys.** A GitHub token is
resolved through a fixed precedence, constrained to `ghu_`-prefix tokens, and exchanged
for a short-lived GitHub Copilot API token that is cached and auto-refreshed. This is the
only credential the Tier-1 kernel ever handles.

This realizes the ground-truth principle **"GitHub IS the substrate"** at the credential
layer: no key vault, no service principal, no API-key prompt — just `gh`-shaped identity.

---

## 1. Scope & non-goals

### 1.1 In scope (normative)
`rapp-auth/1.0` governs **only** the Tier-1 outbound path:

```
brainstem  ──(GitHub token)──▶  GitHub Copilot token-exchange API  ──(Copilot token)──▶  /chat/completions
```

It specifies: token precedence, the `ghu_`/`gho_` acceptance rule, the device-code OAuth
flow and its single-poller invariant, the Copilot token exchange & refresh lifecycle,
on-disk token storage, and log/telemetry scrubbing.

### 1.2 Out of scope (cross-referenced, NOT governed here)
- **Tier-2 (Spinal Cord / Azure):** Azure OpenAI auth via `azuredeploy.json` / managed
  identity / `AZURE_OPENAI_KEY`. A *different* trust anchor; see `function_app.py`.
- **Tier-3 (Nervous System / M365):** Dataverse app-registration + macOS SSO brokered
  auth (`disableBrokeredAuth=false`). See the Power Platform solution + MSX tether docs.
- **Inbound auth to the brainstem itself** (who may call `localhost:7071/chat`). Tier-1 is
  local-first and binds loopback; inbound authorization is a separate concern.
- **Rappid eternity identity** (`rappid:@owner/slug:<sha256>`). That is *content-address*
  identity for artifacts. `rapp-auth` is *operator* identity for outbound LLM calls. They
  are orthogonal: eternity is PKI-free sha256; auth is GitHub-account-as-identity. Neither
  requires a keypair.

> **Tier-1 is Copilot-only by intent.** Do not propose unifying this chain with a generic
> `llm.py` multi-provider abstraction. Single auth, single provider, one training story.

---

## 2. Trust model

| Property | Statement |
|---|---|
| **Identity** | The GitHub account that owns the token. No separate username/password, no API key. |
| **Authorization** | A valid GitHub Copilot subscription on that account. Absence of a subscription is a first-class, named failure (`no_copilot_access`), never a crash. |
| **Secret custody** | The kernel custodies exactly one long-lived secret (the `ghu_` token) and one short-lived secret (the Copilot session token), both on the local disk of the operator's own machine. |
| **Blast radius** | Local. Tokens never leave the machine except in the two HTTPS calls to `github.com` / the Copilot endpoint. They MUST NOT be written to telemetry, diagnostics, or logs (see §7). |
| **Keypair** | None. Consistent with rappid-eternity, **no asymmetric keypair is required by any component of this chain.** GitHub's OAuth is the only cryptographic dependency. |

**Why GitHub.** The substrate principle: GitHub already authenticates the developer, hosts
the raw-CDN corpus, the Issues-mailbox, PR-consent, and Pages-edge. Reusing the GitHub
account as the LLM identity means the operator authenticates **once**, with an account they
already have, to unlock the engine — "use everyone else's hardware" begins with using
GitHub's identity plane instead of minting our own.

---

## 3. Token precedence (normative)

`get_github_token()` MUST resolve the GitHub token in this exact order and return the
**first** source that yields a usable token:

1. **`GITHUB_TOKEN` environment variable** — if set and non-empty, returned verbatim.
   This is the operator override and CI path. (It is trusted as-is; see §3.2 caveat.)
2. **`.copilot_token` file** — the persisted device-code OAuth result (a `ghu_` token,
   JSON `{"access_token", "refresh_token", "saved_at"}`; legacy plain-text accepted).
3. **`gh auth token` CLI** — invoked with a 5s timeout, inheriting the user `PATH`
   (Windows resolves machine+user `PATH` from the registry). **Accepted only if the
   returned token does NOT start with `gho_`.**

If all three miss, `get_github_token()` returns `None`, and the caller MUST surface the
device-code login prompt (§5), never a stack trace.

### 3.1 The `ghu_` / `gho_` rule (normative, load-bearing)

> Only **`ghu_`** tokens work with the Copilot token-exchange API. **`gho_`** tokens
> (issued by a plain OAuth App, e.g. by `gh auth token`) lack Copilot scope and return
> HTTP 404 from the exchange endpoint.

Therefore:

- The brainstem device-code flow MUST use the **GitHub App** client id that issues `ghu_`
  tokens: `COPILOT_CLIENT_ID = "Iv1.b507a08c87ecfe98"`.
  *(The OAuth-App id `Ov23ctDVkRmgkPke0Mmm` issues `gho_` tokens and MUST NOT be used.)*
- Source (3), `gh auth token`, MUST be **skipped when it returns a `gho_` token**.
- The exchange request auth scheme is prefix-derived:
  `Authorization: token <t>` when `t` starts with `ghu_`, else `Authorization: Bearer <t>`.

### 3.2 Precedence caveat
Source (1) is returned **without** the `gho_` filter (it is an explicit operator override
and may legitimately be a PAT in some setups). Sources (2) and (3) are the auto-discovery
paths and are subject to the `ghu_`/`gho_` rule. A `gho_`-only environment therefore fails
at exchange time with the explicit guidance of §8, not silently.

---

## 4. Copilot token exchange & lifecycle (normative)

`get_copilot_token()` returns `(copilot_token, endpoint)` resolving in this order:

1. **In-memory cache** `_copilot_token_cache` — returned iff
   `now < expires_at − 60` (a mandatory **60-second refresh buffer**).
2. **Disk cache** `.copilot_session` — same 60s-buffer validity check; rehydrates the
   in-memory cache. This is what lets a restarted brainstem keep serving without a new login.
3. **Fresh exchange** — `GET https://api.github.com/copilot_internal/v2/token` with the
   GitHub token from §3 and the editor-identity headers
   (`Editor-Version: vscode/1.95.0`, `Editor-Plugin-Version: copilot/1.0.0`,
   `User-Agent: GitHubCopilotChat/...`).

### 4.1 Exchange response handling
- On **HTTP 401/403/404**: attempt `refresh_github_token()` (OAuth `grant_type=refresh_token`
  against the stored `refresh_token`) and retry the exchange **once**.
- If it still fails and the error `notification_id == "no_copilot_access"`: raise the
  sentinel `NO_COPILOT_ACCESS:<username>`, delete the stale `.copilot_token` (so health
  reports unauthenticated), and surface §8 guidance.
- On any other failure: raise a human-readable `Copilot auth failed (<status>): <msg>`.
  **The token file MUST NOT be deleted on generic failures** — only on a confirmed
  `no_copilot_access`. (Transient 5xx must not destroy a working refresh token.)

### 4.2 On success
Cache `{token, endpoint, expires_at}` both in memory and to `.copilot_session`. `endpoint`
defaults to `https://api.individual.githubcopilot.com` if the response omits it. If the
response omits `expires_at`, default to `now + 600`.

```
                 ┌─────────────── 60s buffer ───────────────┐
   issued ───────┼──────────── valid window ────────────────┤ expires_at
                 ▲                                           ▲
            re-exchange                                  hard expiry
            happens here
```

---

## 5. Device-code OAuth flow (normative)

When no token is resolvable, `/login` starts the GitHub **device authorization** flow:

1. `POST https://github.com/login/device/code` with `client_id=<COPILOT_CLIENT_ID>`
   → `{device_code, user_code, verification_uri, interval, expires_in}`.
2. Present `user_code` + `verification_uri` to the operator (browser/console).
3. A background thread polls
   `POST https://github.com/login/oauth/access_token`
   (`grant_type=urn:ietf:params:oauth:grant-type:device_code`) every `interval` seconds
   until it yields an `access_token` (+ `refresh_token`), which is saved via §6.

### 5.1 Single-poller invariant (normative, race-critical)

> **The background poll thread (`_bg_poll_loop`) is the SOLE caller of
> `poll_device_code()`.** The `/login/poll` HTTP endpoint MUST read the shared
> `_login_result` written by that thread — it MUST NOT call `poll_device_code()` itself.

GitHub's device endpoint consumes the authorization on first success; **two concurrent
pollers race and one loses the token** ("double-consume"). Funnelling every poll through
one thread and exposing only its result eliminates the race. On success the thread eagerly
performs the §4 exchange so `/login/poll` can report `Authenticated with GitHub Copilot!`
in one round-trip.

### 5.2 Pending-code persistence & reuse
- The pending `{device_code, user_code, verification_uri, interval, expires_at}` MUST be
  persisted to `.copilot_pending` so a server restart mid-login resumes the same code
  rather than orphaning it.
- A still-valid pending code MUST be **reused** (not regenerated) when `/login` is hit
  again (e.g. page refresh) — regenerating would invalidate the code the user is currently
  typing ("refresh-kills-auth"). `force_new=True` (explicit account switch) bypasses reuse
  and clears stale `_login_result` + `_copilot_session`.

---

## 6. Tokens at rest (security, normative)

Three credential files live beside `brainstem.py`. All three MUST be in `.gitignore` and
SHOULD be created with owner-only permissions (`0600`) where the OS supports it.

| File | Contents | Lifetime | Sensitivity |
|---|---|---|---|
| `.copilot_token` | `{access_token (ghu_), refresh_token, saved_at}` | long-lived (refreshable) | **High** — the durable identity secret |
| `.copilot_session` | `{token, endpoint, expires_at}` | short-lived (~minutes) | Medium — auto-reissued |
| `.copilot_pending` | `{device_code, user_code, …, expires_at}` | transient (≤ `expires_in`, ~15 min) | Medium — a live grant in flight |

Required `.gitignore` coverage (the grail ships this):

```gitignore
# Token files (contain secrets)
.copilot_token
.copilot_session
.copilot_pending
```

Rules:
- These files MUST NEVER be committed, bundled into a release tag, or copied into the
  public corpus.
- A token value MUST NEVER be written to any telemetry/diagnostics surface. Where a prefix
  is logged for debugging, it MUST be truncated (`token[:4]`/`token[:8]`) — never the full
  secret.
- On `no_copilot_access`, `.copilot_token` MUST be deleted (§4.1). On generic/transient
  failure it MUST be retained.

---

## 7. Log & telemetry scrubbing (normative)

The brainstem keeps a structured event log (`_tlog` stream) exposed via diagnostics
(`/diagnostics/book.json`). Auth events are logged for debuggability, but secret-adjacent
fields MUST be redacted before exposure:

```python
_SCRUB_KEYS = {"user_code", "device_code", "session_id"}
# before serving any event: drop these keys from ev["data"]
```

Conformance:
- Any field name in `_SCRUB_KEYS` MUST be stripped from every event emitted to
  `/diagnostics/book.json` and any externally-readable log surface.
- Full token values, `refresh_token`, and the Copilot session `token` MUST NOT be logged
  at all (not merely scrubbed) — only truncated prefixes (§6) are permitted.
- A port MAY extend `_SCRUB_KEYS` but MUST NOT shrink it below this baseline set.

---

## 8. Failure modes & operator UX (normative)

| Condition | Detection | Required operator-facing behavior |
|---|---|---|
| No token anywhere | §3 returns `None` | Surface the device-code prompt (`user_code` + `verification_uri`). MUST NOT raise a stack trace to the user. |
| `gho_`-only account | exchange → 404, no `ghu_` available | Explicit message that the available token lacks Copilot scope; direct the user to `/login` for a `ghu_` device-code token. |
| No Copilot subscription | exchange → `notification_id: no_copilot_access` | Raise `NO_COPILOT_ACCESS:<username>`, delete `.copilot_token`, tell the user the named account has no Copilot access. |
| Expired GitHub token | exchange → 401/403 | Attempt refresh once (§4.1); if it fails, fall through to the device-code prompt. |
| Expired device code | poll past `expires_at` | Clear `.copilot_pending`, raise "Login code expired. Please try again." |
| Transient 5xx at exchange | non-(401/403/404) | Retain token file, surface retryable error. MUST NOT delete credentials. |

---

## 9. Conformance — parity is sacred

`function_app.py` (Tier-2) and **every** future `/chat` port MUST implement an **identical**
auth contract where they speak to the Copilot API:

- C1. Token precedence of §3, in order.
- C2. The `ghu_`/`gho_` acceptance rule of §3.1 (skip `gho_` from CLI; App-id for `ghu_`).
- C3. The 60s refresh buffer and dual (memory + disk) Copilot-token cache of §4.
- C4. The single-poller invariant of §5.1.
- C5. The `_SCRUB_KEYS` baseline of §7 and the no-full-token-in-logs rule.
- C6. Never-delete-on-transient-failure (§4.1).

This is the **"never break userspace"** guarantee applied to auth: the same account, the
same files, the same prompts, the same redactions, regardless of which body the operator is
talking to. A port that diverges from C1–C6 is non-conformant and MUST NOT ship.

### 9.1 Conformance vectors
A conforming implementation MUST pass these:

| # | Input | Expected |
|---|---|---|
| V1 | `GITHUB_TOKEN=ghu_AAA` set | exchange uses `Authorization: token ghu_AAA` |
| V2 | env empty, `.copilot_token`={access_token: ghu_BBB} | returns `ghu_BBB` |
| V3 | env empty, no file, `gh auth token`→`gho_CCC` | source (3) skipped → returns `None` → device prompt |
| V4 | valid memory cache, `now < expires_at−60` | no network call; cached token returned |
| V5 | memory cache `now` in [expires_at−60, expires_at] | re-exchange triggered (buffer enforced) |
| V6 | two concurrent `/login/poll` calls | exactly one consumes the grant; both observe the same `_login_result` |
| V7 | event `{user_code, device_code, session_id, ok:true}` via diagnostics | only `{ok:true}` is visible |
| V8 | exchange → `no_copilot_access` for `alice` | raises `NO_COPILOT_ACCESS:alice`, `.copilot_token` deleted |
| V9 | exchange → HTTP 503 | token file retained, retryable error raised |

---

## 10. How it composes with the estate

- **The grail kernel.** This chain is *part of the single-file kernel* and ships frozen
  with each immutable `vX.Y.Z` tag. Distros (`rapp-distro`) pin a kernel and inherit this
  auth contract unchanged.
- **`/chat` is the only wire.** Auth is invoked *inside* the `/chat` (and `/login`) request
  path; it adds no new REST surface beyond the login endpoints the flow requires. All
  capability still flows through `/chat`.
- **Agents never see tokens.** The frozen agent ABI (`BasicAgent.metadata` +
  `perform(**kwargs)->str`) receives no credentials. Outbound LLM identity is the kernel's
  job alone; agents extend behavior, never auth. An agent that wants the host LLM calls the
  host's `call_copilot` via `sys.modules` — it never touches `get_copilot_token()`.
- **Mesh / fleet (Leviathan over `/chat`).** Inter-twin trust (signed twin-chat events,
  gh-collaborator + sha256) is a *separate, inbound* trust plane. `rapp-auth` is the
  *outbound* anchor that lets each body reach the LLM. The two compose cleanly: a fleet
  message is authorized by the mesh trust model; the body that receives it uses its own
  local `rapp-auth` GitHub identity to do the LLM work. No keypair is introduced on either
  side — eternity stays PKI-free, auth stays GitHub-account-as-identity.
- **Substrate symmetry.** GitHub is the identity plane here, the CDN for the corpus, the
  Issues-mailbox, and the PR-consent gate elsewhere. One account, many roles — the
  metropolis runs on identity the operator already owns.

---

## 11. Worked example

**Scenario.** Operator `alice` (Copilot subscriber) starts a fresh brainstem on a laptop
with `gh` installed but logged into a personal OAuth session (`gho_` token), no
`GITHUB_TOKEN`.

1. First `/chat` → `get_copilot_token()` → `get_github_token()`:
   - env `GITHUB_TOKEN` empty,
   - no `.copilot_token`,
   - `gh auth token` → `gho_xxxx` → **skipped** (§3.1) → returns `None`.
2. Kernel surfaces device-code prompt:
   `POST .../device/code` → `user_code=ABCD-1234`, `verification_uri=github.com/login/device`.
   Pending state persisted to `.copilot_pending`. Background poller starts (sole poller).
   The `login.device_code_started` event logs `{user_code: "ABCD-1234"}` — which is
   **scrubbed** out of `/diagnostics/book.json` (§7).
3. Alice opens the URL, enters `ABCD-1234`, authorizes.
4. Background thread's `poll_device_code()` receives `ghu_zzzz` (+ refresh token) →
   `save_github_token()` writes `.copilot_token` (gitignored, prefix-only logged) →
   eagerly runs `get_copilot_token()`:
   - exchange `GET .../copilot_internal/v2/token` with `Authorization: token ghu_zzzz`
     → `{token: tid_..., endpoint, expires_at}` → cached in memory **and** `.copilot_session`.
   - `_login_result = {status: ok}`.
5. The pending browser `/login/poll` reads `_login_result` (it did **not** poll GitHub
   itself — §5.1) → shows "Authenticated with GitHub Copilot!".
6. `/chat` resumes; subsequent calls hit the in-memory cache until `expires_at − 60s`,
   then re-exchange silently. Restarting the server rehydrates from `.copilot_session` with
   no new login.

**Counter-scenario.** If `alice` had **no** Copilot subscription, step 4's exchange returns
`notification_id: no_copilot_access`; the kernel raises `NO_COPILOT_ACCESS:alice`, deletes
`.copilot_token`, and the UI explains the account lacks Copilot access (§8) — no crash, no
secret leaked.

---

## Appendix A — Reference symbols (`rapp_brainstem/brainstem.py`)

| Symbol | Role |
|---|---|
| `COPILOT_CLIENT_ID = "Iv1.b507a08c87ecfe98"` | GitHub **App** id issuing `ghu_` tokens |
| `COPILOT_TOKEN_URL` | `https://api.github.com/copilot_internal/v2/token` |
| `get_github_token()` | §3 precedence + `ghu_`/`gho_` rule |
| `_exchange_github_for_copilot()` / `get_copilot_token()` | §4 exchange + cache + refresh |
| `refresh_github_token()` | OAuth `grant_type=refresh_token` |
| `start_device_code_login()` / `_bg_poll_loop()` / `poll_device_code()` | §5 device flow + single poller |
| `_save_pending_login()` / `_load_pending_login()` | §5.2 pending persistence |
| `_save_copilot_cache()` / `_load_copilot_cache()` | §4 disk session cache |
| `_SCRUB_KEYS = {"user_code","device_code","session_id"}` | §7 scrub baseline |
| `.copilot_token` / `.copilot_session` / `.copilot_pending` | §6 at-rest files |

---

*rapp-auth/1.0 — the kernel authenticates as you, with the GitHub account you already have,
holding zero API keys. The account is the identity; sha256 is the artifact identity; no
keypair is ever required. Written down so it is never lost.*
