# rapp-kernel-boundary/1.0 — The Kernel Network Trust Boundary

> Status: **Normative**, versioned, public.
> Spec id: `rapp-kernel-boundary/1.0`
> Home: `kody-w/rapp-installer/specs/NETWORK_TRUST_BOUNDARY.md`
> Kernel: the brainstem (`rapp-installer`, the grail) — `rapp_brainstem/brainstem.py`.
> Depends on: `CONSTITUTION` Art. XXV ("chat is the only wire"), `rapp-trust/1.0` (gh-collaborator + sha256), `rapp-roadmap` Phase 1, `rapp-twin-chat/1.0`, `rapp-commons-event/1.0`, `rapp-resident/1.0`.
> Excludes: `rapp-distro/1.0`, `rapp-frame/2.0` (formalized separately).

---

## 0. Why this spec exists

The brainstem is, by construction, a **remote-code-execution engine**: its whole purpose is to load arbitrary `*_agent.py` files from `agents/` and run their `perform(**kwargs)` on request. That is a feature, not a bug — but it is only safe under one assumption: **the only thing that can reach the engine's privileged surfaces is the local user.**

That assumption has never been written down, and the kernel's own default contradicts it. As of this spec, `brainstem.py` still ends with:

```python
app.run(host="0.0.0.0", port=PORT, debug=False)   # brainstem.py L1817 — STILL LIVE
```

`0.0.0.0` binds **every** network interface. Every one of the kernel's ~25 routes — including the ones that write and execute code — is therefore reachable by **anything on the LAN, with no authentication**. On a coffee-shop or corporate Wi-Fi this is an unauthenticated RCE, **and it is still open today**. The same class of hole is re-opened, deliberately, by Leviathan's injected `/api/agent` route (see §6).

"What you don't write down gets lost." This spec writes down the trust boundary the engine has always *assumed*, makes it **normative**, classifies every route, and **mandates the closure of** both RCE surfaces — the grail's own `0.0.0.0` bind and Leviathan's unauth route. It is the *specification* of the fix, not the fix itself: until R1 and R7 (§4, §6) actually land in the grail, **both surfaces remain unremediated** (`rapp-roadmap` Phase 1 is **OPEN** — see §8). The boundary is written so the engine's openness to the *local* user survives the fix.

This spec changes **policy and defaults**, never the agent ABI. It is fully compatible with "never break userspace" (`rapp-kernel-release/1.0`): no agent, no `/chat` payload, and no `BasicAgent` contract changes.

---

## 1. Threat model

**Asset.** The kernel can: execute agent code (`/chat` → `perform()`), **write new executable code** to disk (`/agents/import` writes `*_agent.py`), delete code (`/agents/<f>` DELETE), read host/auth diagnostics, and drive an OAuth/device-code login that yields a GitHub/Copilot token.

**Adversary.** Any process that can open a TCP connection to the listening port: another user on the same LAN/VPN, a malicious page performing DNS-rebinding or CSRF against `localhost`, a co-tenant container, a compromised device on the network.

**Trust assumption (made explicit and normative).** The kernel trusts exactly one principal: **the local user on loopback** (`127.0.0.1` / `::1`). Reach to a **privileged** route (§3) by any other principal, absent an explicit local token (§7), MUST be treated as **arbitrary code execution as the user** and MUST be refused.

**Current reality (not yet conformant).** The shipping grail does **not** yet enforce this: it binds `0.0.0.0` (§0) and any deployment running Leviathan also exposes the unauthenticated `/api/agent` (§6). The threat above is therefore **live**, not hypothetical, until R1/R7 land.

**Non-goals.** This spec does not add user accounts, TLS, or multi-tenant isolation to the kernel. The kernel is single-user and local-first by design (`rapp-distro/1.0`). It defines a *boundary*, not an authentication system. Anything that needs to cross the boundary does so as a **signed `/chat` event** (§6) or via the **optional local agent-token** (§7).

---

## 2. Terminology

- **Loopback origin** — a connection whose remote address is `127.0.0.0/8` or `::1`.
- **Privileged route** — a route that executes code, mutates the agent/config surface, exposes secrets/host detail, or drives auth. See §3.
- **Public-safe route** — a read-only liveness/identity route that leaks no secret and mutates no state. See §3.
- **The wire** — `POST /chat`. Per Art. XXV it is the *only* sanctioned channel for capability.
- **Local agent-token** — an optional per-instance bearer secret that authorizes a non-loopback caller to use privileged routes (§7).

---

## 3. Route trust classification (normative)

Every `@app.route` in the kernel is classified into exactly one of two tiers. The classification is **closed**: a new route MAY NOT be added without assigning a tier, and per Art. XXV a *new capability* MUST NOT introduce a new privileged route at all (§5).

### 3.1 Public-safe (MAY answer any origin)

These are read-only, secret-free, side-effect-free. They MAY be served on any bound interface so that neighbors/estate peers can probe liveness and identity (`rapp-metropolis/*` discovery).

| Route | Method | Why public-safe |
|---|---|---|
| `/health` | GET | liveness only |
| `/version` | GET | kernel version string only |
| `/` | GET | static web UI shell (no secrets in markup) |

> Implementations MUST ensure `/health`, `/version`, and `/` never embed tokens, file paths, or agent source. If `/` ever needs privileged data it must fetch it from a privileged route subject to §4.

### 3.2 Privileged (loopback-only OR local-token, §4)

| Route | Method | Privilege |
|---|---|---|
| `/chat` | POST | **executes agent `perform()`** — full RCE surface |
| `/agents/import` | POST | **writes `*_agent.py` to disk** — persistent RCE surface |
| `/agents/<filename>` | DELETE | deletes agent code |
| `/agents` | GET | enumerates installed agents (capability inventory) |
| `/agents/export/<filename>` | GET | exfiltrates agent source |
| `/models` , `/models/set` | GET / POST | reads / changes the active model |
| `/login`, `/login/poll`, `/login/status`, `/login/switch` | POST/GET | drives device-code OAuth → GitHub/Copilot token |
| `/debug/auth` | GET | exposes auth/token state |
| `/diagnostics`, `/diagnostics/book.json`, `/diagnostics/clear`, `/diagnostics/report` | GET/POST | host/session detail; mutates diagnostic state |
| `/voice`, `/voice/config` (GET/POST), `/voice/export`, `/voice/import`, `/voice/toggle` | GET/POST | reads/writes config; `import` ingests config blobs |

**Default classification rule:** any route **not** explicitly listed in §3.1 is privileged. New routes default to privileged.

---

## 4. Default bind = loopback (normative)

> **R1.** The kernel **MUST** default its listen bind to loopback: `host="127.0.0.1"` (and/or `::1`). This replaces `host="0.0.0.0"` at `brainstem.py` L1817. **This change has not yet landed in the grail; until it does the kernel binds `0.0.0.0` by default and R1 is unmet.**

> **R2.** Binding a non-loopback interface (`0.0.0.0`, a LAN IP) **MUST** require explicit operator opt-in via the env var **`BRAINSTEM_BIND`**. The value is the bind address; the kernel binds it verbatim. Absent `BRAINSTEM_BIND`, the kernel binds `127.0.0.1`.

> **R3.** When `BRAINSTEM_BIND` resolves to anything other than loopback, the kernel **MUST** emit a loud, unmissable startup warning to stderr that names the exposure and the mitigation, e.g.:
>
> ```
> ⚠  BRAINSTEM EXPOSED: binding 0.0.0.0 — every privileged route (/chat, /agents/import,
>    /diagnostics, /login) is reachable from the network. This is REMOTE CODE EXECUTION as you.
>    Set BRAINSTEM_AGENT_TOKEN to require a bearer on privileged routes (see rapp-kernel-boundary/1.0 §7).
> ```

> **R4.** Even when bound non-loopback, **privileged routes (§3.2) MUST still enforce origin/token policy (§4.1).** Binding wider does not relax authorization; it only changes which packets reach the socket.

### 4.1 Privileged-route gate (normative)

For every request to a privileged route the kernel **MUST** apply, in order:

1. If the remote address is a **loopback origin** → **allow**.
2. Else if a **local agent-token** is configured (§7) and the request presents the matching bearer → **allow**, and the request is attributed to the token's bound principal (§7.2).
3. Else → **refuse** with `403` and a body referencing this spec; the refusal MUST NOT execute any agent, write any file, or reveal token/host detail.

Public-safe routes (§3.1) skip this gate.

> **R5 (anti-rebind hardening, SHOULD).** To resist DNS-rebinding from a browser, privileged routes SHOULD additionally reject requests whose `Host` header is not `localhost`, `127.0.0.1`, `[::1]`, or the configured bind, and SHOULD reject cross-site requests lacking a same-origin `Origin`/`Sec-Fetch-Site: same-origin` when one is present. Loopback socket reach remains necessary but the `Host`/`Origin` check closes the rebind gap.

---

## 5. "/chat is the only wire" as a security invariant (Art. XXV)

Art. XXV ("chat is the only wire") has always been an *architectural* rule: capability flows through agents over `POST /chat`, not through bespoke REST endpoints. This spec elevates it to a **security invariant**:

> **R6.** A new capability **MUST NOT** earn a new privileged REST route. New capability is delivered as an **agent** (`*_agent.py`, frozen ABI) invoked over `/chat`. The privileged route surface is **closed** at the set enumerated in §3.2; it shrinks over time, it does not grow.

Why this is a security property, not just taste: every new privileged route is a new place to forget the §4.1 gate. By forbidding new privileged routes, the kernel keeps the **entire** authorization surface to one chokepoint (`/chat`) plus a frozen, audited legacy set. An agent added over `/chat` inherits the boundary automatically — it cannot be reached except through the gated wire.

Corollary: **route injection is forbidden.** No accessory, plugin, or "fleet" layer may register an additional Flask route on the kernel app — most especially not an unauthenticated one. This is exactly the Leviathan failure mode, named and closed next.

---

## 6. The `/api/agent` RCE — named and closed

**The hole.** `/api/agent` is **not part of the grail.** It is injected at runtime by Leviathan's `FlockEndpoint` so a controller can drive many brainstem bodies *without* going through `/chat` and *without* the LLM — bypassing both the wire and any auth, to "kill the shared-token throttle." Combined with the legacy `0.0.0.0` bind, `/api/agent` is a fully unauthenticated, networked `perform()` invocation: textbook RCE. **It is live today** in any deployment running Leviathan. It directly violates §5 (route injection) and §4 (privileged reach).

**The closure (decision #2, this session) — specified, not yet enforced.** Fleet messaging is re-expressed as **signed twin-chat events over `/chat`**, never as a new route:

- A fleet message is a **`rapp-commons-event/1.0`** event addressed to a peer twin, carried as a **`rapp-twin-chat/1.0`** turn delivered to that peer's **`POST /chat`**.
- The sender is a **`rapp-resident/1.0`** identity; the event is **signed** and resolves under **`rapp-trust/1.0`** (gh-collaborator membership and/or a `rappid` sha256 content-address; keypair binding OPTIONAL per the eternity resolution, never required).
- The receiving kernel applies the **§4.1 gate** like any other `/chat` request: loopback, or a presented local agent-token (§7), or `403`. There is no path that reaches `perform()` un-gated.

> **R7.** Leviathan-class controllers **MUST** drive bodies via signed `/chat` twin-chat events. The injected `/api/agent` route **MUST** be removed; any deployment that injects an unauthenticated route is **non-conformant** with `rapp-kernel-boundary/1.0` and with Art. XXV. **As of this spec the route is still injected and still unauthenticated — R7 is unmet until Leviathan stops registering it.**

This preserves Leviathan's intent — one mind driving many bodies, flight-recorded, resilient when interactive `/chat` is busy — while eliminating the unauth route. The throttle problem is a *rate/auth* problem solved by the local agent-token + serial waves, not by deleting authentication.

---

## 7. Optional local agent-token (`BRAINSTEM_AGENT_TOKEN`)

For *sanctioned* non-loopback operation (a deliberately-shared neighborhood body, a Leviathan fleet on a trusted segment), the kernel offers an **optional** bearer. It is opt-in; loopback never requires it.

### 7.1 Shape

- Env var: **`BRAINSTEM_AGENT_TOKEN`** — a high-entropy secret (≥128 bits). If unset, **no** token is accepted and only loopback may reach privileged routes (the safe default).
- Presented by callers as `Authorization: Bearer <token>` (or `X-Brainstem-Token: <token>`).
- Compared in **constant time**. Never logged; never returned by `/debug/auth` or `/diagnostics`.

### 7.2 Binding to a principal (cross-ref `rapp-trust/1.0`)

A presented token authorizes the request, and the request is **attributed** to the principal the operator bound the token to:

- **gh-collaborator** — the token authorizes writes on behalf of a named GitHub collaborator of this instance's home repo (`rapp-trust/1.0` default ownership; `sig_suite: none`). Inbound `/agents/import` writes are recorded as authored by that collaborator.
- **rappid** — alternatively bound to a `rappid:@owner/slug:<sha256>` content-address. The sha256 *is* the identity (PKI-free). A signing keypair MAY be bound for sovereignty (un-shutdownable ownership, MASTER_PLAN §4) but is **OPTIONAL and never required** (MASTER_PLAN §3). The token works with `sig_suite: none`.

> **R8.** The local agent-token authorizes a caller to pass the §4.1 gate; it does **not** widen the route set. Token-authorized callers may reach exactly the §3.2 privileged routes, same as a loopback caller. There is still no un-gated route.

> **R9.** Persistent writes (`/agents/import`, `/agents/<f>` DELETE) performed by a non-loopback, token-authorized caller MUST be attributed to the bound principal in the kernel's record/flight-recorder, so every byte of installed code traces to a `rapp-trust` identity.

---

## 8. How it composes with the estate

- **Kernel / distro.** The boundary is a kernel invariant; a `rapp-distro/1.0` distro pins a kernel version and inherits this boundary unchanged. Tags are immutable (`rapp-kernel-release/1.0`); R1–R9 ride the kernel tag.
- **Neighborhood → estate → metropolis.** Public-safe routes (§3.1) are the *discovery* surface neighbors probe (liveness/identity). All *capability* between bodies crosses as signed `/chat` events (§6) under `rapp-trust/1.0` — so "use everyone else's hardware" scales without ever opening an unauth code path. The mesh-composition tier (`rapp-metropolis/*`) builds **on top of** this gate, never around it.
- **GitHub-as-substrate.** Cross-instance consent rides PR-consent and Issues-mailbox; the *runtime* hop into a peer is still the gated `/chat` wire. The boundary is the local enforcement point of the estate's global trust model.
- **Roadmap.** This spec is the written form of `rapp-roadmap` **Phase 1: "closes the unauth `/api/agent` RCE."** **Phase 1 is currently OPEN.** Writing the boundary does not close it: the shipping grail still binds `0.0.0.0` (R1 unmet, §4) and Leviathan still injects the unauthenticated `/api/agent` (R7 unmet, §6). Phase 1 is *done* only when **R1** (loopback default) and **R7** (no injected route) are merged into the grail **and** a distro pins the resulting tag. Until then, treat both RCE surfaces as **live and unremediated**.

---

## 9. Conformance

A kernel/instance is **conformant with `rapp-kernel-boundary/1.0`** iff:

1. **C1 — Loopback default.** With no `BRAINSTEM_BIND` set, the listener binds loopback only. (Test: start kernel; assert it is unreachable from a non-loopback address.) *Current grail: FAILS C1 — binds `0.0.0.0` by default.*
2. **C2 — Gated privilege.** A request to any §3.2 route from a non-loopback origin **without** a valid token is refused `403`, executes no agent, writes no file, leaks no secret. (Test below.) *Current grail: FAILS C2 — privileged routes answer un-gated.*
3. **C3 — Loud opt-in.** Setting `BRAINSTEM_BIND=0.0.0.0` binds wide **and** emits the §4.1/R3 warning; privileged routes still enforce C2.
4. **C4 — No new/injected privileged routes.** The privileged route set equals §3.2; no accessory registers an additional route (esp. no unauth `/api/agent`). (Test: diff live route table against §3.2 + §3.1.) *A Leviathan deployment currently FAILS C4 — `/api/agent` is injected.*
5. **C5 — Token binding.** When `BRAINSTEM_AGENT_TOKEN` is set, only the matching bearer passes the gate from non-loopback, attributed to a `rapp-trust` principal; writes are recorded against it.
6. **C6 — Public-safe stays open & clean.** `/health`, `/version`, `/` answer any origin and contain no secrets.

### 9.1 Reference conformance test (C2)

```bash
# Bind wide WITHOUT a token, then prove a non-loopback-style privileged call is refused.
BRAINSTEM_BIND=0.0.0.0 ./start.sh &           # expect the §R3 warning on stderr

# A privileged route presented as a non-loopback caller (Host spoof / no token) MUST 403:
code=$(curl -s -o /dev/null -w '%{http_code}' \
  -H 'Host: attacker.example' \
  -X POST http://<lan-ip>:7071/agents/import \
  -d '{"filename":"pwn_agent.py","content":"# rce"}')
test "$code" = "403" || { echo "FAIL: privileged route reachable un-gated"; exit 1; }

# Public-safe liveness still answers:
curl -fsS http://<lan-ip>:7071/health >/dev/null || { echo "FAIL: health unreachable"; exit 1; }
echo "PASS: rapp-kernel-boundary/1.0 C2/C6"
```

> Run against the current grail this test **FAILS** (the privileged route returns `200`, not `403`) — which is the expected, honest result until R1/R4 land. It is written to pass only a conformant kernel.

---

## 10. Worked example: a sanctioned neighborhood body

> Illustrative of the **target** (post-R1/R7) behavior. The current grail does not yet behave this way (see §8/§9).

**Goal.** Kody runs a brainstem on his desktop and wants his laptop's controller to drive it as part of a 2-body neighborhood — without re-opening the RCE.

1. **Default (safe).** Plain `./start.sh` binds `127.0.0.1`. The laptop cannot reach it at all. Nothing is exposed. (C1.)
2. **Sanctioned exposure.** Kody opts in explicitly:
   ```bash
   export BRAINSTEM_BIND=0.0.0.0
   export BRAINSTEM_AGENT_TOKEN=$(openssl rand -hex 32)   # bound to gh-collaborator kody-w
   ./start.sh
   # stderr: ⚠ BRAINSTEM EXPOSED ... set BRAINSTEM_AGENT_TOKEN ...   (it is set → guarded)
   ```
3. **Driving the body (decision #2).** The laptop sends a fleet message as a **signed `rapp-twin-chat/1.0`** turn (a `rapp-commons-event/1.0` event from `rapp-resident` `kody-w`) to the desktop's `POST /chat`, presenting the bearer:
   ```bash
   curl -fsS http://desktop.lan:7071/chat \
     -H "Authorization: Bearer $BRAINSTEM_AGENT_TOKEN" \
     -H 'Content-Type: application/json' \
     -d '{"user_input":"{\"schema\":\"rapp-commons-event/1.0\",\"kind\":\"fleet.command\",\"body\":\"@desktop run nightly-sweep\",\"sig_suite\":\"none\"}","session_id":"sweep-1"}'
   ```
   The desktop's §4.1 gate sees a non-loopback origin, a valid bearer bound to `kody-w` → **allow**, attributed to `kody-w`. The sweep runs through the normal `/chat` → agent path; the call is flight-recorded against `kody-w`.
4. **Attacker on the same Wi-Fi.** Hits `/agents/import` with no token → **403**, no file written (C2). Hits `/health` → `200` (C6). There is **no `/api/agent`** to hit (C4).

Result: one mind drives many bodies, fleet messaging works, the throttle is sidestepped via the token rather than by deleting auth — and the unauthenticated RCE is gone on both surfaces.

---

## 11. Changelog

- **1.0** — Initial canonical boundary. Establishes loopback default (`BRAINSTEM_BIND` opt-in), the §3 route trust classification, the §4.1 privileged-route gate, Art. XXV as a security invariant forbidding new/injected privileged routes, the named closure of Leviathan's `/api/agent` via signed `/chat` twin-chat events, and the optional `BRAINSTEM_AGENT_TOKEN` bound to a `rapp-trust/1.0` principal. **Specifies (does not yet implement)** the closure of `rapp-roadmap` Phase 1: Phase 1 remains **OPEN** until R1 (loopback default) and R7 (no injected `/api/agent`) land in the grail and a distro pins the tag. Until then the kernel still binds `0.0.0.0` and the unauthenticated `/api/agent` is still live.