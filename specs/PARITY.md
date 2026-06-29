# rapp-runtime-parity/1.0

> **Status:** Canonical · **Version:** 1.0 · **Home:** `kody-w/rapp-spine/specs/PARITY.md`
> **Companion:** `rapp-kernel/1.0` (the ABI half) · **Authority on drift:** `rapp-god`
> **Estate map:** https://raw.githubusercontent.com/kody-w/rapp-map/main/estate-map.json

## 0. Why this spec exists

> *"`brainstem.py` and `function_app.py` must function identically across the stack."* — **Stem/function_app parity is sacred.**

RAPP is not "a server." RAPP is a **runtime contract** that can be implemented on many
substrates: a local Flask process (Tier 1 / brainstem), an Azure Function (Tier 2 / spinal
cord), a static Dataverse-backed handler (Tier 3 / nervous system), a headless SDK, or a
browser. The **north star** — "use everyone else's hardware → neighborhoods → estate →
metropolis" — only works if a request that a neighbor's brainstem can answer is answered
**the same way** by *any* RAPP runtime, regardless of who owns the silicon.

If two runtimes claiming to be RAPP diverge on the wire, then the estate is not one
medium — it is N incompatible products wearing the same name. **Parity is the wire half of
the "one runtime, many substrates" contract.** `rapp-kernel/1.0` freezes the *agent ABI*
(what an agent author writes). This spec freezes the *observable behavior of `/chat`* (what
a caller sees) and provides the **golden conformance vectors** that *prove* a
substrate-swapped runtime is the same runtime.

The governing principle of this corpus: **what you don't write down gets lost.** Parity has
been true *in practice* (brainstem.py is the kernel; kody-w/CommunityRAPP/function_app.py (Tier 2) emits the kernel envelope (response/session_id/agent_logs/voice_mode/model/requested_model) — aligned 2026-06-28; legacy assistant_response/voice_response/user_guid kept additively for back-compat; the canonical 400 body now matches. (One residual: T2 uses a per-request agent cache; observable output is identical.))
but never written as a spec an LLM can learn from or a harness can enforce. This closes
that gap.

---

## 1. Definitions

| Term | Meaning |
|------|---------|
| **Runtime** | Any executable that serves the RAPP `/chat` contract on some substrate. |
| **Reference runtime** | `kody-w/rapp-installer/rapp_brainstem/brainstem.py` at the pinned kernel tag. **The reference is normative**: where any wording here is ambiguous, the reference runtime's observable behavior wins. |
| **Parity** | The property that a runtime reproduces the reference runtime's **observable `/chat` behavior** byte-behaviorally, for all inputs, modulo the **out-of-scope axes** (§3). |
| **Observable behavior** | The `/chat` request envelope it accepts, the response envelope it emits, the tool-call discovery+execution **loop semantics**, the `agent_logs` shape, and the **agent ABI** it honors. Nothing else. |
| **Golden conformance vector** | A frozen `(system_prompt + history + agents + user_input → expected tool-call sequence + expected envelope)` case any conformant runtime MUST reproduce. |
| **Parity tier** | A declared conformance level (§4) a runtime asserts and the harness verifies. |
| **Deviation / drift** | Any observable difference from the reference that is not an out-of-scope axis. A deviation is **drift, not a feature** (§7). |

Parity is **behavioral**, not implementational. A runtime written in Rust, in TypeScript,
or as a pile of Azure bindings is conformant iff it passes the vectors. We never compare
source; we compare the wire.

---

## 2. What parity covers (the IN-SCOPE surface)

A conformant runtime MUST be identical to the reference on **all four** of the following.
These are the *only* things parity asserts, and it asserts them **completely**.

### 2.1 The `/chat` request envelope

`POST /chat` accepts a JSON body:

```json
{
  "user_input": "string (required, non-empty after trim)",
  "conversation_history": [ { "role": "user|assistant|tool", "...": "..." } ],
  "session_id": "string (optional; server mints a UUIDv4 if absent)"
}
```

Rules (all normative, all observable in the reference):
- `user_input` is **required**. Missing/empty-after-trim → `400` with body `{"error": "user_input is required"}`.
- `conversation_history` defaults to `[]`. The runtime MUST **filter** history to roles
  `user`, `assistant`, `tool` and drop everything else **before** sending to the model.
- `session_id` is echoed back; if absent the runtime mints a UUIDv4 and returns it.
- The body is parsed permissively (`force=True` semantics): a non-JSON or empty body is
  treated as `{}` (and therefore fails the `user_input` check with `400`).

### 2.2 The tool-call discovery + execution loop semantics

This is the heart of parity. Per `/chat` call, in order:

1. **Load soul** (the system prompt) fresh.
2. **Discover agents** fresh from the agent source (`rapp-kernel/1.0` auto-discovery:
   recursive `*_agent.py`, excluding `experimental_agents/` and `disabled_agents/`). Agents
   are reloaded **every request** — no warm cache that survives an edit.
3. **Build tools** = `[agent.to_tool() for agent in agents]`, or `null`/absent if there are
   no agents. Each tool is the OpenAI function schema `{"type":"function","function":
   {"name","description","parameters"}}` derived from the agent's `metadata`.
4. **Assemble messages**: `[{"role":"system","content": soul + Σ system_context()}]` +
   filtered history + `{"role":"user","content": user_input}`. Every agent's optional
   `system_context()` string is concatenated onto the system prompt (in agent-discovery
   order); failures in one agent's `system_context()` MUST NOT abort the turn.
5. **Loop up to 3 rounds** (`MAX_ROUNDS = 3`, frozen):
   - Call the model with `messages` + `tools`.
   - Append the assistant message to `messages`.
   - If the assistant message has `tool_calls`: execute each (§2.3), append each tool
     result message, continue the loop. The trigger is the **presence of `tool_calls` on
     the message**, regardless of whether `finish_reason == "tool_calls"` — some providers
     set the finish reason, some only populate the array; both MUST be honored.
   - If there are no `tool_calls`: **break**.
   - On the 3rd round the loop ends whether or not tools were requested; the last assistant
     `content` is the reply.

The round cap, the "presence-not-finish_reason" trigger, the fresh-per-request reload, and
the system-context concatenation are **all parity-load-bearing**. A runtime that caches
agents across requests, that loops 5 times, or that only triggers on `finish_reason` is
**non-conformant** even if it "works."

### 2.3 Tool execution + `agent_logs` shape

For each `tool_call` the runtime:
- Resolves the agent by `function.name`.
- Parses `function.arguments` as JSON; **on parse failure, falls back to `{}`** (never
  throws out of the loop).
- Calls `agent.perform(**args)` and coerces the return to `str`.
- Appends a tool result message exactly shaped:
  ```json
  { "tool_call_id": "<tc.id>", "role": "tool", "name": "<fn_name>", "content": "<str(result)>" }
  ```
- Records a log line:
  - success → `"[<fn_name>] <result>"`
  - the agent raised → result becomes `"Error: <e>"` and log `"[<fn_name>] ERROR: <e>"`
  - agent not found → result and log both `"Agent '<fn_name>' not found."`

`agent_logs` in the response is these lines **joined by `"\n"`** across all rounds, in
execution order. The shape is part of the contract: tooling (e.g. Flight Recorder,
rapp-god) reads it.

### 2.4 The `/chat` response envelope

On success (`200`):

```json
{
  "response": "string — final assistant content (\"\" if none)",
  "session_id": "string",
  "agent_logs": "string — newline-joined log lines (\"\" if no tools ran)",
  "voice_mode": false,
  "model": "string — the model that actually answered",
  "requested_model": "string — the configured/requested model id"
}
```

- `model` MAY differ from `requested_model` when the runtime's own fallback logic switched
  models; clients rely on this to attribute answers honestly. A runtime with no fallback
  sets them equal.
- If `voice_mode` is on **and** the reply contains the `|||VOICE|||` sentinel, the runtime
  splits it: `response` = text before, `voice_response` = text after. `voice_mode` is an
  out-of-scope *capability* (§3) — but **if present, its envelope behavior MUST match.**

On error:
- `400` → `{"error": "user_input is required"}` for the empty-input case.
- Upstream model HTTP error → `502` with `{"error": <human msg>, "model": <id>, "detail": <≤300 chars>}`;
  quota/`429` produces the "usage limit reached" message.
- Any other exception → `500` with `{"error": "<message>"}`.

The **key names, the status codes, and the error-vs-success discrimination** are in scope.
The exact human-readable English of an error *message* is NOT (a runtime MAY localize), but
the **machine-readable keys and status codes are**.

### 2.5 The agent ABI (by reference)

Parity requires that the runtime honor the **frozen agent ABI** defined in
`rapp-kernel/1.0`:

```python
class BasicAgent:
    metadata: dict            # OpenAI function schema: name, description, parameters
    def perform(self, **kwargs) -> str: ...
    def system_context(self) -> str | None: ...   # optional
    def to_tool(self) -> dict: ...                  # {"type":"function","function":{...}}
```

A runtime is conformant only if an **unmodified** agent that runs on the reference runtime
runs identically on it. "Never break userspace." Substrate-specific glue (e.g. the
`utils.azure_file_storage → local_storage.py` import shim) is allowed *because it preserves
the ABI* (§3).

---

## 3. What MAY differ (explicitly OUT of scope)

Parity is about the *wire and the loop*, not about *how the runtime is powered*. The
following axes are deliberately free. A divergence on any of these is **NOT drift** and MUST
NOT be reported as a parity failure:

| Axis | Free to vary |
|------|--------------|
| **Auth chain** | Copilot token exchange (T1) vs Azure OpenAI key (T2) vs managed identity / Entra (T2 cloud) vs Dataverse connector auth (T3). |
| **Storage backend** | `local_storage.py` JSON files vs Azure Files vs Dataverse tables vs in-memory. The `utils.azure_file_storage` shim exists *to make this axis invisible to agents.* |
| **Model provider / id** | GitHub Copilot models, Azure OpenAI deployments, or anything else. `model`/`requested_model` simply report whatever was used. |
| **Transport host / port / URL** | `localhost:7071`, an Azure Functions host, a Pages-edge worker, a browser `fetch` handler — all fine. |
| **Model-selection / fallback policy** | Whether and how a runtime falls back across models. (Its *reporting* via `model` is in scope; its *policy* is not.) |
| **Optional capabilities** | `voice_mode`, diagnostics routes, login UI, model picker. *If implemented*, their envelopes match (§2.4); a runtime MAY omit them entirely. |
| **Non-`/chat` routes** | `/health`, `/agents`, `/voice/*`, `/diagnostics/*`, etc. are runtime conveniences, **not** part of the parity contract. Per *"/chat is the sacred endpoint,"* all capability flows through `/chat`; auxiliary routes are out of scope by construction. |

The discipline: **the only thing a RAPP caller is entitled to is `/chat` behaving like the
reference.** Everything about *how the box is wired* is the substrate's business.

---

## 4. The in-scope runtimes registry + parity tiers

Each runtime in the estate declares a **parity tier**. The registry is a small JSON
manifest. The canonical copy **SHOULD** ship alongside this spec as `parity-runtimes.json`
and be mirrored into `rapp-map` — this file is **PLANNED** and is not yet committed; the
manifest below is its normative shape:

```json
{
  "spec": "rapp-runtime-parity/1.0",
  "reference": "brainstem.py",
  "runtimes": [
    { "id": "brainstem.py",          "repo": "kody-w/rapp-installer",     "path": "rapp_brainstem/brainstem.py",       "substrate": "flask-local",   "tier": "reference" },
    { "id": "function_app.py",       "repo": "kody-w/CommunityRAPP",      "path": "function_app.py",                   "substrate": "azure-functions","tier": "full" },
    { "id": "rapp-dataverse",        "repo": "kody-w/rapp-dataverse",     "path": "handler",                           "substrate": "dataverse-static","tier": "core" },
    { "id": "rapp-brainstem-sdk",    "repo": "kody-w/rapp-brainstem-sdk", "path": "sdk",                               "substrate": "headless",      "tier": "full" },
    { "id": "vBrainstem",            "repo": "kody-w/vBrainstem",         "path": "browser",                           "substrate": "browser",       "tier": "core" }
  ]
}
```

### Parity tiers

| Tier | Asserts | MUST pass |
|------|---------|-----------|
| **reference** | This *is* the definition. | (defines the vectors) |
| **full** | Identical observable `/chat` behavior including the optional-capability envelopes it implements, the loop semantics, error envelopes, and the full agent ABI. | **All** golden vectors. |
| **core** | The request/response envelope, the tool-call loop semantics, `agent_logs` shape, and agent ABI — but MAY omit optional capabilities and MAY have narrower error surfacing. | All vectors tagged `core: true`. |
| **edge** | A reduced runtime (e.g. offline-degrade / static-only) that serves a deterministic subset (e.g. no-LLM agents) with identical envelopes for what it *does* answer. | All vectors tagged `edge: true`. |

A runtime's declared tier is a claim; the **harness verifies it**. A runtime that fails its
declared tier's vectors is in **drift** and is reported to rapp-god (§7). `tier` for any
runtime is **monotonic in releases**: a runtime MUST NOT silently lower its tier between
versions without a recorded reconciliation.

> Note: `vBrainstem` is "core" because a browser runtime cannot run arbitrary Python
> `perform()` agents on the reference's ABI; it serves the envelope + loop semantics over a
> JS agent shim. This is a *legitimate, declared* reduction, not drift.

---

## 5. Golden conformance vectors

The vectors are a **frozen corpus** that **SHOULD** ship alongside this spec at
`rapp_brainstem/parity_vectors/` (mirrored into `rapp-map` for estate-wide harness runs).
This corpus is **PLANNED** — it is not yet committed; what follows is its normative schema
and required cases. Each vector is a single JSON file. **Vectors are content-addressed by
sha256** of their canonical JSON (consistent with rappid eternity identity, §8) so a runtime
can attest *exactly which* corpus it passed.

### 5.1 Vector schema

```json
{
  "id": "rapp-parity-vector",
  "name": "single-tool-then-answer",
  "spec": "rapp-runtime-parity/1.0",
  "tags": { "core": true, "edge": false },
  "fixture": {
    "soul": "You are a calculator. Use tools for arithmetic.",
    "agents": [
      {
        "name": "AddNumbers",
        "metadata": {
          "name": "AddNumbers",
          "description": "Add two integers a and b.",
          "parameters": {
            "type": "object",
            "properties": { "a": {"type":"integer"}, "b": {"type":"integer"} },
            "required": ["a","b"]
          }
        },
        "perform": { "kind": "deterministic", "returns": "{a}+{b}={sum}" }
      }
    ],
    "model": { "kind": "scripted" }
  },
  "request": {
    "user_input": "what is 2 plus 3?",
    "conversation_history": [],
    "session_id": "fixed-session-0001"
  },
  "model_script": [
    { "round": 1, "emit": { "tool_calls": [
        { "id": "tc_1", "function": { "name": "AddNumbers", "arguments": "{\"a\":2,\"b\":3}" } } ] } },
    { "round": 2, "emit": { "content": "2 plus 3 is 5." } }
  ],
  "expect": {
    "status": 200,
    "tool_call_sequence": ["AddNumbers"],
    "envelope": {
      "response": "2 plus 3 is 5.",
      "session_id": "fixed-session-0001",
      "agent_logs": "[AddNumbers] 2+3=5",
      "voice_mode": false
    },
    "envelope_required_keys": ["response","session_id","agent_logs","voice_mode","model","requested_model"]
  }
}
```

### 5.2 Why vectors carry a `model_script`

The LLM is **non-deterministic and is an out-of-scope axis** (§3). Parity is therefore
tested by **mocking the model with a scripted responder** (`model.kind = "scripted"`,
`model_script` per round). This isolates the thing parity actually governs — the runtime's
*loop, envelope, and ABI handling* — from the thing it doesn't — *which model and whether it
chose to call a tool.* The harness injects the script at the runtime's model-call seam.

This mirrors *"prototypes solve with mocked data"*: the runtime executes its **real**
end-to-end loop; only the model *data* is scripted. Flip the script for a live model and the
loop behaves identically.

### 5.3 The frozen corpus (minimum required cases)

Every conformant corpus MUST include at least these classes (each a vector, `core` unless
noted):

1. **`empty-input-400`** — missing/blank `user_input` → `400 {"error":"user_input is required"}`.
2. **`no-agents-passthrough`** — agents empty → `tools` null, single round, plain reply, `agent_logs=""`.
3. **`single-tool-then-answer`** — one tool call round, then a reply (the §5.1 example).
4. **`parallel-tool-calls`** — two `tool_calls` in one assistant message → both executed in
   order, two tool messages appended, `agent_logs` has both lines joined by `\n`.
5. **`multi-round-tools`** — tool call in round 1 *and* round 2, answer in round 3.
6. **`round-cap-3`** — model requests a tool on every round → loop stops after exactly 3
   rounds; the 3rd assistant `content` is returned even though a tool was still requested.
7. **`bad-arguments-fallback`** — `function.arguments` is invalid JSON → args default to
   `{}`, `perform()` still runs, no 500.
8. **`agent-not-found`** — model names a tool that doesn't exist → result/log
   `"Agent 'X' not found."`, loop continues, `200`.
9. **`agent-raises`** — `perform()` throws → result `"Error: ..."`, log `"[X] ERROR: ..."`, `200`.
10. **`history-role-filter`** — history containing a `system` / junk-role message → it is
    dropped before the model call; only `user/assistant/tool` survive.
11. **`system-context-injection`** — an agent with `system_context()` → its string is
    concatenated onto the system prompt (verified via the captured outbound `messages[0]`).
12. **`finish-reason-agnostic-trigger`** (`core`) — a `tool_calls` array present **without**
    `finish_reason=="tool_calls"` still triggers execution.
13. **`session-id-minted`** — request with no `session_id` → response carries a valid UUIDv4
    and the same id is used for the whole turn.
14. **`voice-sentinel-split`** (full only) — `voice_mode` on + `|||VOICE|||` in reply →
    `response`/`voice_response` split.

Adding a vector to the corpus is a **versioned act**: it bumps the corpus sha256 and is
announced via the Issues-mailbox to every registered runtime so they can re-attest. Vectors
are **append-only and immutable** once tagged (consistent with rappid eternity, §8); a
"fixed" vector is a *new* vector with a new id, never a mutation.

---

## 6. The parity harness

`parity_harness.py` **SHOULD** ship alongside this spec; it is **PLANNED** and not yet
committed. It runs the corpus against a live runtime and emits a pass/fail report.

### 6.1 Contract

```
parity_harness.py --runtime <url-or-module> \
                  --vectors rapp_brainstem/parity_vectors/ \
                  --tier full|core|edge \
                  [--report report.json]
```

For each vector the harness:
1. Stands the fixture into the runtime (writes the `soul`, drops the deterministic agents
   into the runtime's agent source, injects the scripted model at the model-call seam).
2. Issues the `request` to the runtime's `/chat`.
3. Compares the actual `(status, tool_call_sequence, envelope, required-keys, agent_logs)`
   against `expect`, **modulo out-of-scope keys** (`model`, `requested_model`, and any
   value the vector marks `ignore`). Comparison is **exact** on in-scope keys.
4. Records `pass` / `fail` with a structured diff.

### 6.2 Report shape

```json
{
  "spec": "rapp-runtime-parity/1.0",
  "runtime": "function_app.py",
  "declared_tier": "full",
  "corpus_sha256": "…",
  "utc": "2026-06-28T00:00:00Z",
  "summary": { "total": 14, "passed": 14, "failed": 0, "tier_satisfied": true },
  "results": [ { "vector": "single-tool-then-answer", "pass": true, "diff": null } ]
}
```

The report timestamp is **UTC-first** (consistent with the metropolis frame discipline) so
reports from runtimes across the estate are directly comparable.

### 6.3 Reference cross-walk

The reference implementation of the harness **SHOULD** ship a **cross-walk**: it runs the
corpus against both `brainstem.py` and `CommunityRAPP/function_app.py` and asserts
**identical** in-scope results. This cross-walk is the executable embodiment of *"stem/function_app parity
is sacred"* and SHOULD run in CI on any change to either file.

---

## 7. Deviation policy: drift, not features

A deviation from the reference on an **in-scope** surface is **drift**. It is never a
"feature" of a downstream runtime.

1. **Detection.** The harness (run by a runtime's own CI, by the estate-sync sweep, or
   ad-hoc) produces a failing report.
2. **Reporting.** The failing report is filed to **rapp-god** (the registry/drift authority)
   as a drift record — `{ runtime, vector, declared_tier, corpus_sha256, diff, utc }` — over
   the **Issues-mailbox** of the runtime's home repo, cross-linked to rapp-god. This reuses
   the estate's existing drift-remediation channel; no new transport.
3. **Reconciliation — direction is fixed.** Reconciliation is **always toward the
   reference.** The non-reference runtime changes to match `brainstem.py`. The reference
   only changes via a deliberate `rapp-kernel`/this-spec version bump (a new contract), never
   to accommodate a downstream divergence.
   - *Exception:* if the divergence reveals a **bug in the reference**, that is fixed in the
     reference under the kernel release process (`rapp-kernel/1.0`) and a **new vector** is
     added to the corpus so the bug can never silently return.
4. **No silent tier drops.** A runtime that can no longer meet its declared tier MUST either
   be fixed or have its registry `tier` lowered *with* a recorded reconciliation note. A
   silently-lowered tier is itself drift.

Governance: parity drift is a first-class entry in the same board as
`project_ecosystem_drift_remediation` — the file-by-file estate scan — so a runtime that
falls out of parity shows up next to every other cross-repo drift.

---

## 8. Trust model

Parity inherits the estate trust model wholesale; it introduces **no new trust primitive.**

- **Vector & corpus integrity = sha256 content-address.** Each vector and the corpus as a
  whole are identified by sha256 (rappid eternity identity — **PKI-free**). A runtime
  attests "I pass corpus `<sha256>`"; anyone can recompute the hash and re-run. Keypair
  signing of a parity report is **OPTIONAL** sovereignty (a runtime owner MAY sign their
  attestation) and is **NEVER required** to participate. The hash is the join key.
- **Authorship / ownership = gh-collaborator (default).** Who may *amend* the corpus or the
  runtimes registry is governed by GitHub collaborator status on `kody-w/rapp-spine`
  (and the mirror in `rapp-map`) — `sig_suite: none` by default. No PKI gate.
- **Consent = PR.** Adding a runtime to the registry, adding/retiring a vector, or bumping
  the corpus is a **pull request** — PR-consent is the change-control wire.
- **Distribution = GitHub-as-substrate.** The spec, the corpus, the harness, and the reports
  ride the raw-CDN + Issues-mailbox + Pages-edge substrate like everything else. A runtime's
  attestation report can be served from its own Pages edge and aggregated by rapp-god.
- **No authority beyond the reference.** There is exactly one source of behavioral truth —
  `brainstem.py` at the pinned kernel tag — and one hash-addressed corpus derived from it.
  Trust is "recompute the hash, re-run the harness," not "trust a signer."

---

## 9. How parity composes with the rest of the estate

```
                        rapp-kernel/1.0  ── the AGENT ABI (what an author writes)
                              │  "never break userspace"
                              ▼
   one runtime, many substrates
                              │
        rapp-runtime-parity/1.0  ── the /chat WIRE (what a caller sees)   ◄── this spec
                              │  golden vectors + harness
        ┌─────────────┬───────┴────────┬──────────────┬─────────────┐
   brainstem.py   function_app.py   rapp-dataverse  brainstem-sdk  vBrainstem
   (T1 reference)  (T2 full)        (T3 core)        (full)        (core)
        │              │                │               │             │
        └── every runtime serves the SAME /chat → neighbors can call neighbors
                              │
            neighborhoods → estate → metropolis (use everyone else's hardware)
```

- **With `rapp-kernel/1.0`:** two halves of one contract. The kernel freezes the *agent ABI*
  (author-facing); parity freezes the */chat wire + loop* (caller-facing). A runtime is "a
  RAPP runtime" iff it satisfies **both**. Neither alone is sufficient: a correct ABI with a
  divergent loop, or a correct envelope that won't run a standard agent, both fail.
- **With the metropolis mesh:** parity is the *precondition* for "use everyone else's
  hardware." Mesh composition (Issues-mailbox routing, PR-consent, Pages-edge, offline-
  degrade, UTC-first frames) only makes sense if a request routed to *any* neighbor's
  runtime is answered the same way. Parity is what makes a neighbor's brainstem a
  **fungible** unit of estate compute. The `edge` tier is exactly the offline-degrade /
  static head case: it answers a deterministic subset with identical envelopes.
- **With Leviathan/fleet messaging:** fleet chat is **signed twin-chat over `/chat`** (the
  sacred wire), not the unauth `/api/agent` route. Parity guarantees every fleet body
  exposes that wire identically, which is *why* one mind can drive many bodies — they are,
  by this spec, the same runtime.
- **With rapp-god / estate-sync:** parity reports are drift records on the same board as
  every other cross-repo drift, filed over the Issues-mailbox, reconciled toward the
  reference.
- **With rapp-map:** the runtimes registry and the corpus are mirrored into `rapp-map` so an
  estate-wide harness run can attest the *whole* estate at a known corpus sha256.

---

## 10. Worked example: proving T2 is the same runtime as T1

**Goal:** show that `CommunityRAPP/function_app.py` (Azure Functions, Azure OpenAI auth, Azure
Files storage) is the **same runtime** as `brainstem.py` (Flask, Copilot auth, local JSON).

Their **out-of-scope axes are entirely different** — different transport, host, auth,
storage, model provider. Parity does not care.

**Step 1 — pick the vector** `single-tool-then-answer` (§5.1), corpus sha256
`a1b2…` (abbreviated).

**Step 2 — run the harness against T1 (reference):**

```
$ parity_harness.py --runtime http://localhost:7071 --vectors ./parity_vectors --tier reference
```
T1 response (in-scope keys):
```json
{ "response": "2 plus 3 is 5.",
  "session_id": "fixed-session-0001",
  "agent_logs": "[AddNumbers] 2+3=5",
  "voice_mode": false }
```

**Step 3 — run the same harness against T2:**

```
$ parity_harness.py --runtime https://communityrapp.azurewebsites.net --vectors ./parity_vectors --tier full
```
T2 response (in-scope keys):
```json
{ "response": "2 plus 3 is 5.",
  "session_id": "fixed-session-0001",
  "agent_logs": "[AddNumbers] 2+3=5",
  "voice_mode": false }
```
The out-of-scope keys differ and are ignored: T1 reports `"model":"claude-sonnet-…"` via
Copilot; T2 reports `"model":"gpt-4o"` via an Azure OpenAI deployment. **Both pass.**

**Step 4 — the cross-walk asserts equality:**

```json
{ "spec": "rapp-runtime-parity/1.0",
  "corpus_sha256": "a1b2…",
  "utc": "2026-06-28T00:00:00Z",
  "crosswalk": { "brainstem.py": "pass(14/14)", "function_app.py": "pass(14/14)",
                 "in_scope_identical": true } }
```

**Step 5 — a deviation appears (drift, not a feature).** Suppose a later T2 change makes it
loop **5** rounds instead of 3. Vector `round-cap-3` now fails on T2: it returns a 4th-round
tool result where T1 returned the 3rd-round content. The harness files a drift record to
`kody-w/CommunityRAPP` Issues, cross-linked to rapp-god:
```json
{ "runtime": "function_app.py", "vector": "round-cap-3", "declared_tier": "full",
  "corpus_sha256": "a1b2…",
  "diff": { "expected_rounds": 3, "actual_rounds": 5 },
  "utc": "2026-06-28T00:00:00Z" }
```
Reconciliation direction is fixed: **T2 is changed back to `MAX_ROUNDS = 3`** to match the
reference. T1 is not touched. After the fix the cross-walk is green again, and T2 may
re-attest the corpus. The estate remains **one runtime, many substrates.**

---

## 11. Conformance checklist (normative summary)

A runtime is **conformant at tier T** iff:

- [ ] It accepts the §2.1 request envelope, including the `400` empty-input rule and
      permissive body parsing.
- [ ] It runs the §2.2 loop: fresh per-request agent discovery, system-context
      concatenation, ≤3 rounds, presence-of-`tool_calls` trigger.
- [ ] It executes tools and emits the §2.3 tool-message + `agent_logs` shapes, including the
      bad-args, not-found, and raised-exception behaviors.
- [ ] It emits the §2.4 success and error envelopes with the exact in-scope keys + status
      codes.
- [ ] It honors the `rapp-kernel/1.0` agent ABI unmodified (§2.5).
- [ ] It varies *only* on the §3 out-of-scope axes.
- [ ] It passes every golden vector tagged for tier **T** at the corpus sha256 it attests.
- [ ] Its registry entry's declared `tier` equals the tier the harness verifies.

If all boxes are checked, it is — by definition — **the same runtime**, no matter whose
hardware it runs on. That is the whole point.

---

*rapp-runtime-parity/1.0 — canonical. Reference: `brainstem.py`. Companion: `rapp-kernel/1.0`.
Drift authority: `rapp-god`. PKI-free identity via sha256; keypair attestation optional,
never required. /chat is the only wire.*