# rapp-kernel/1.0

**The kernel, the frozen agent ABI, and the "never break userspace" release contract.**

- **spec_id:** `rapp-kernel/1.0`
- **status:** canonical, stable
- **home:** `kody-w/rapp-installer` → `rapp_brainstem/KERNEL.md`
- **kernel artifact:** `rapp_brainstem/brainstem.py` (the grail)
- **inventory:** see `KERNEL_TREE.md` for the file-level kernel manifest
- **depends on:** `rapp-installer` (the grail repo), the GitHub substrate (raw CDN, tags, Pages)
- **referenced by:** `rapp-distro/1.0` (a distro PINS a kernel tag), `rapp-god` (drift detection), `rappid eternity` (content-address of the kernel artifact)

> **One-line definition.** The *kernel* is a single file — `brainstem.py` — that serves exactly one wire (`POST /chat`) and auto-discovers exactly one extension point (drop-in agents). Every release of the kernel is an **immutable, annotated git tag** `brainstem-vX.Y.Z`. The ABI those agents are written against is **frozen**: any agent written for any prior `vX` MUST run unmodified on every later kernel of the same MAJOR. This is the RAPP rendering of "never break userspace."

---

## 0. Why this spec exists

The kernel is the *atom* of the whole estate. Neighborhoods, the estate, and the metropolis are all just brainstems talking to brainstems over `/chat`. If the kernel's shape drifts — if `/chat` changes meaning, if the agent class contract moves, if a tag is force-pushed — every downstream brainstem in the estate silently breaks, and there is no central server to roll back.

This document writes down the contract that has been true *in practice* but never formalized:

1. **What is kernel vs. userspace.**
2. **The frozen agent ABI** (the syscall surface drop-ins are compiled against).
3. **The "never break userspace" SemVer rule.**
4. **The release & tag process** (immutable `brainstem-vX.Y.Z`).
5. **Rollback** (pin any tag at install time).
6. **Anti-drift** (the grail is the single source; mirrors are downstream).
7. **Conformance** (what makes a server a `rapp-kernel/1.0`).

---

## 1. The kernel is one file

### 1.1 Definition

The **kernel** is `rapp_brainstem/brainstem.py`: a single-file Flask server (~1,100 lines) that owns, indivisibly:

- **auth** — the GitHub-Copilot token exchange chain (`GITHUB_TOKEN` env → `.copilot_token` → `gh auth token`), short-lived Copilot tokens with auto-refresh;
- **the wire** — `POST /chat` (plus its health/UI/login support routes);
- **agent orchestration** — discover → build tool schemas → call the model with tools → execute `perform()` → loop (≤3 rounds) → return;
- **the import shims** — `sys.modules` injection so cloud-authored agents run locally unmodified.

The kernel is the **grail**: it is sacred and changes only through the grail repo (`rapp-installer`). It is the *engine, not the experience* (see `CONSTITUTION.md`). The kernel ships with a small set of supporting engine files; the authoritative list is `KERNEL_TREE.md`. As of this spec the kernel surface is:

| File | Role | Layer |
|------|------|-------|
| `brainstem.py` | the kernel proper — all routes, auth, orchestration | **kernel** |
| `basic_agent.py` (and `agents/basic_agent.py`) | the ABI base class | **kernel (ABI)** |
| `local_storage.py` | the Azure-File-Storage shim target | **kernel (ABI)** |
| `soul.md` | default system prompt, user-replaceable | seed |
| `index.html` | built-in web UI served at `/` | seed |
| `VERSION` | the SemVer string this checkout claims | **kernel (release)** |
| `requirements.txt`, `start.sh`, `start.ps1` | bootstrap | bootstrap |
| `CONSTITUTION.md` | governance | governance |

### 1.2 Kernel vs. userspace

There is a hard line:

- **Userspace** is **`agents/`** — the user's entire workspace. Everything a user creates, installs from RAR, or drags in lives here. The kernel treats it as opaque, reloadable-from-disk state.
- **Everything else** in the checkout is **kernel/engine surface** and is not the user's to edit. Runtime scratch state lives in `.brainstem_data/` (also not kernel).

The kernel never breaks userspace. That promise is the entire point of §2–§3.

---

## 2. The frozen agent ABI

The ABI (Application Binary Interface) is the *syscall surface* that drop-in agents are written against. It is **frozen across the whole `1.x` line** and may only change under the §3 MAJOR rule. There are exactly four guarantees.

### 2.1 ABI-1 — The agent class contract

An agent is a Python class that extends `BasicAgent` and provides:

```python
from basic_agent import BasicAgent   # resolvable both as `basic_agent` and `agents.basic_agent`

class MyAgent(BasicAgent):
    def __init__(self):
        self.name = "MyAgent"
        self.metadata = {
            "name": "MyAgent",
            "description": "Tells the model exactly when to invoke this agent.",
            "parameters": {                      # OpenAI function-calling JSON schema
                "type": "object",
                "properties": {
                    "topic": {"type": "string", "description": "self-sufficient; the caller sees only this"}
                },
                "required": ["topic"]
            }
        }
        super().__init__()

    def perform(self, **kwargs) -> str:          # MUST return a string
        return "result the model will read back"
```

Frozen surface of `BasicAgent`:

| Member | Contract | Frozen |
|--------|----------|--------|
| `self.name` | string; the tool name surfaced to the model | yes |
| `self.metadata` | dict with `name`, `description`, `parameters` (OpenAI function schema) | yes |
| `perform(self, **kwargs) -> str` | called with the model-supplied args as kwargs; returns a string | yes |
| `system_context(self) -> str | None` | optional; text injected into the system prompt each turn | yes |
| `to_tool(self) -> dict` | derives the OpenAI tool definition from `metadata`; kernel-provided | yes |

**The kernel calls `perform(**kwargs)` and reads back a string.** It may pass kwargs the agent did not declare (and reserved kwargs like `user_guid` may be injected/stripped by the kernel for memory agents); a conforming agent therefore accepts `**kwargs` and never assumes a closed argument set. Because the model only ever sees `metadata.description` and the `parameters` schema, **every parameter description must be self-sufficient** — nothing load-bearing may be hardcoded outside the schema.

### 2.2 ABI-2 — `POST /chat` is the only wire

`POST /chat` is the **single public capability surface**. All agent capability flows through it; the kernel exposes no per-feature REST routes. The frozen request/response shape — **as the grail `brainstem.py` actually serves it** (`brainstem-v0.6.1`). [`PARITY.md`](./PARITY.md) is the single **normative owner** of this wire; this section restates it for context only:

```jsonc
// Request
POST /chat
{
  "user_input": "user turn (string)",
  "conversation_history": [ {"role": "user|assistant", "content": "..."} ],  // optional prior turns
  "session_id": "opaque id (string)"                                          // optional; echoed back
}

// Response
{
  "response": "final assistant text (string)",
  "session_id": "the conversation id (string)",
  "agent_logs": "agent activity, NEWLINE-JOINED STRING (not an array)",
  "voice_mode": false,
  "model": "the model used (string)",
  "requested_model": "the model asked for (string)"
}
```

Guarantees: `/chat` accepts `user_input` + optional `conversation_history`/`session_id`, runs the discover→tools→`perform`→loop cycle (bounded at 3 tool rounds), and returns `response` (+ `session_id`, `agent_logs` as a newline-joined string, `voice_mode`, `model`, `requested_model`). There is **no** `assistant_response` key. New capability is added by **dropping an agent**, never by adding a route. (Fleet/estate messaging rides on top of `/chat` as signed twin-chat events — see [`rapp-fleet-chat/1.0`](https://github.com/kody-w/leviathan/blob/main/FLEET_CHAT.md) / `rapp-commons-event/1.0` — not on a side channel.)

### 2.3 ABI-3 — Auto-discovery

The kernel discovers agents from the **`agents/` tree** by the filename pattern **`*_agent.py`**. Discovery is fresh on every `/chat` request — edit a file and the next request picks it up, no restart. Reserved subdirectories `experimental_agents/` and `disabled_agents/` are **excluded** from discovery and are reserved names a conforming kernel will never auto-load. Everything else under `agents/` is the user's to organize (subdirectories for swarms/stacks are allowed). The pattern `*_agent.py`, the reserved-dir exclusions, and the reload-per-request semantics are frozen.

### 2.4 ABI-4 — The import shims

So that agents authored for the cloud tier (CommunityRAPP / Azure Functions) run locally unmodified, the kernel injects `sys.modules` at import time. The frozen shim:

```python
from utils.azure_file_storage import AzureFileStorageManager
# → transparently resolved to local_storage.py, JSON files under .brainstem_data/
```

Missing pip dependencies referenced by an agent are auto-installed at import time. The shim target (`utils.azure_file_storage` → local storage manager with the same method surface) is frozen; this is what makes drop-ins **portable across tiers** without edits.

### 2.5 What the ABI deliberately does NOT promise

- The model provider, model id, or token-exchange internals (Tier-1 is Copilot-only by design; this is an implementation detail behind `/chat`, not ABI).
- Line counts, private function names, or internal globals inside `brainstem.py`.
- The contents of `soul.md` / `index.html` (seed files, user-replaceable).

Agents that reach past the ABesI into kernel internals are **non-conforming** and carry no compatibility guarantee.

---

## 3. "Never break userspace" — the SemVer rule

The kernel version in `VERSION` is `MAJOR.MINOR.PATCH`. The rule binds the meaning of those numbers to the ABI:

| Bump | Trigger | Promise to userspace |
|------|---------|----------------------|
| **PATCH** (`x.y.Z`) | bug fix, no surface change | every drop-in keeps working |
| **MINOR** (`x.Y.0`) | additive — new optional ABI surface, new routes-behind-`/chat`, new model support | every drop-in keeps working; new agents may use new surface |
| **MAJOR** (`X.0.0`) | an **ABI break** (§2.1–§2.4 changes incompatibly) | **avoid.** A drop-in MAY require changes |

**The prime directive:** a drop-in agent written against **any** prior `vX` MUST run **unmodified** on **every** later kernel sharing that MAJOR. Concretely, within `1.x`:

- `BasicAgent` + `metadata` + `perform(**kwargs) -> str` keep working;
- `POST /chat` keeps its request/response shape;
- `*_agent.py` auto-discovery + reserved-dir exclusions keep working;
- the `utils.azure_file_storage` shim keeps resolving.

**An ABI break is a last resort, not a feature.** A MAJOR bump is a governance event (a Constitution-level decision), not a routine release. The bias is overwhelmingly toward *additive* MINOR changes. If a capability can be delivered as a new optional kwarg, a new agent, or new behavior behind `/chat`, it MUST be — never as a breaking change to ABI-1..4.

---

## 4. Release & tag process

`main` is production. The install one-liner pulls `main`. Therefore `main` is **always** a working kernel, and every release is a frozen point you can return to.

### 4.1 Canonical tag form

A kernel release is an **immutable annotated git tag**:

```
brainstem-vX.Y.Z
```

- `brainstem-v0.6.1`, `brainstem-v1.0.0`, …
- **Annotated** (`git tag -a`), carrying release notes as the tag message.
- **Immutable**: a tag, once pushed, **never moves**. No force-push, no re-point, ever. To fix a bad release you cut a *new* higher tag — you never rewrite an old one. This is what makes a tag a trustworthy rollback point and a stable content-address (see §6 / rappid eternity).

> **Legacy form (compatibility contract).** Earlier releases were tagged `vX.Y.Z` (e.g. `v0.5.0`, `v1.0.0`). Per the RAPP compatibility contract, tooling MUST **read** both `brainstem-vX.Y.Z` and the legacy `vX.Y.Z` forms forever, and MUST **emit** only the canonical `brainstem-vX.Y.Z` form going forward. The two forms are reconciled by the `X.Y.Z` core; never rewrite an existing tag to migrate it.

### 4.2 Cutting a release

1. **Bump `VERSION`** in `rapp_brainstem/VERSION` to `X.Y.Z` (per the §3 rule).
2. Land the change on `main` with a `release: vX.Y.Z` commit (development happens on feature/fix branches; `main` is reached only by a release merge — never push features directly to `main`).
3. **Cut the tag** on that commit:
   ```bash
   git tag -a brainstem-vX.Y.Z -m "release notes: what changed, ABI impact (none expected)"
   git push origin brainstem-vX.Y.Z
   ```
4. **Ship release notes** in the annotated tag message and the repo release. Notes MUST state the ABI impact explicitly — for a conforming MINOR/PATCH that line is literally **"ABI: unchanged (drop-ins from all prior 1.x run unmodified)."**

`VERSION` on `main` and the latest `brainstem-v*` tag MUST agree. The installer reads `VERSION` over the raw CDN to decide upgrades, so the two drifting apart is itself a drift bug (§6).

### 4.3 What a tag freezes

A `brainstem-vX.Y.Z` tag freezes the *entire kernel tree* at that commit: `brainstem.py`, the ABI files, `VERSION`, the bootstrap scripts. Because the tag is immutable, the SHA-256 content-address of the kernel artifact at that tag is stable forever — the kernel itself is a `rappid`-addressable artifact (PKI-free; keypair binding optional, never required).

---

## 5. Rollback — tags are the rollback points

Any tagged kernel can be pinned at install time. There is no separate "downgrade" mechanism; you simply install a different immutable tag.

```bash
# Pin a specific kernel by env var:
BRAINSTEM_VERSION=0.6.0 curl -fsSL https://rapp.tools/install.sh | bash

# …or by flag, accepting canonical or legacy tag forms:
curl -fsSL https://rapp.tools/install.sh | bash -s -- --version brainstem-v0.6.0
curl -fsSL https://rapp.tools/install.sh | bash -s -- --version v0.6.0   # legacy form still resolves
```

The installer resolves the pin to the matching git tag and `git checkout`s it; if the tag does not exist it lists the available tags and stops. Because every tag is immutable and `main` is always working, **rollback is risk-free**: pinning `brainstem-vX.Y.Z` yields byte-identical the kernel that shipped as that release. Omitting the pin tracks `main` (latest production).

---

## 6. Anti-drift — the grail is the single source

There is exactly **one** authoritative kernel: `brainstem.py` in `rapp-installer` (the grail). Everything else is downstream:

- **Distros** (`rapp-distro/1.0`) do not fork the kernel; they **pin a `brainstem-vX.Y.Z` tag** and add agents/soul/config on top.
- **Mirrors** (e.g. a kernel copy embedded in `RAPP` or `rapp-mcp`) are **downstream replicas** and MUST be byte-identical to a tagged grail kernel. A mirror that diverges from its claimed tag is drift.
- **`function_app.py` parity** (the Azure tier) is sacred: the cloud entrypoint MUST behave identically to `brainstem.py` for the ABI surface. Stem/function_app parity is part of "never break userspace" across tiers.

**Enforcement leg:** `rapp-god` drift detection treats the grail kernel at its latest tag as ground truth and flags any mirror, distro pin, or `function_app.py` whose ABI surface or kernel bytes drift from it. Drift is filed as a traceable issue, not silently tolerated. The neuron mesh (`rapp-map`) carries per-file cards so a single changed kernel line can be swept across every dependent surface.

---

## 7. Conformance

A server is a conforming **`rapp-kernel/1.0`** if and only if **all** hold:

1. **One wire.** It serves `POST /chat` with the §2.2 request/response shape, and exposes no per-capability REST routes in place of agents.
2. **The frozen ABI.** It auto-discovers `agents/**/*_agent.py` (excluding `experimental_agents/` and `disabled_agents/`), instantiates classes extending `BasicAgent`, builds tools from `metadata`, calls `perform(**kwargs)`, reads back a string, and honors the `utils.azure_file_storage` shim — i.e. a drop-in written for any `1.x` kernel runs unmodified.
3. **A matching tag.** Its `VERSION` equals `X.Y.Z` and it was shipped at an immutable annotated tag `brainstem-vX.Y.Z` (legacy `vX.Y.Z` accepted on read) traceable to the grail.

A server that adds capability only through drop-in agents, never moves a tag, and never breaks a prior drop-in **remains conformant forever**. That permanence is the foundation the neighborhoods → estate → metropolis mesh is built on.

---

## 8. Worked example — cutting `brainstem-v1.1.0` (additive, no break)

**Goal:** add an optional `system_context()`-driven memory injection improvement and support a new model id. Both are *additive* → MINOR.

1. **Branch.** `git checkout -b feat/context-injection` off `main`; implement entirely behind `/chat` and `BasicAgent` — no change to the four ABI guarantees.
2. **Prove no break.** Run the drop-in suite: a `hello_agent.py` written against `brainstem-v0.4.0` still loads, the model still calls it, `perform()` still returns a string. `POST /chat` shape unchanged.
3. **Bump.** `VERSION`: `1.0.0` → `1.1.0`.
4. **Release commit.** Merge to `main` as `release: v1.1.0`.
5. **Tag, immutably:**
   ```bash
   git tag -a brainstem-v1.1.0 -m "v1.1.0 — additive: per-turn context injection, model X support.
   ABI: unchanged (drop-ins from all prior 1.x run unmodified)."
   git push origin brainstem-v1.1.0
   ```
6. **Downstream.** `rapp-god` re-checks: grail latest tag = `brainstem-v1.1.0`; the `RAPP` kernel mirror and `function_app.py` are swept for parity; any distro may now choose to re-pin from `brainstem-v1.0.0` → `brainstem-v1.1.0`, or stay pinned — both keep working.
7. **Rollback proof.** A user who dislikes the new injection runs `BRAINSTEM_VERSION=1.0.0 curl … | bash` and is byte-identically back on `brainstem-v1.0.0`. No data migration, because `agents/` (userspace) never changed.

**Contrast — what a MAJOR would have required.** Had the change instead altered `perform`'s signature or `/chat`'s response shape, it would break prior drop-ins → it MUST be a `2.0.0` MAJOR, gated as a governance decision, with release notes stating the exact break and a migration path. The default answer to "should we break the ABI?" is **no** — find the additive path.

---

## Appendix A — ABI quick card (paste into any agent author's notes)

```
extends BasicAgent · name + metadata{name,description,parameters(OpenAI schema)} · perform(**kwargs)->str
optional: system_context()->str|None
file: agents/**/<name>_agent.py   (NOT under experimental_agents/ or disabled_agents/)
wire:  POST /chat {user_input, conversation_history?, session_id?} -> {response, session_id, agent_logs(newline-string), voice_mode, model, requested_model}
shim:  from utils.azure_file_storage import AzureFileStorageManager   (→ local)
guarantee: works on every 1.x kernel, unmodified, forever.
```

## Appendix B — Relationship to the estate

| Spec | Relationship |
|------|--------------|
| `rapp-distro/1.0` | a distro **pins** a `brainstem-vX.Y.Z`; this spec defines what it's pinning |
| `rappid eternity` | the kernel artifact at a tag is sha256 content-addressed; PKI-free, keypair optional |
| `rapp-god` | drift enforcement: grail-latest-tag is ground truth for all mirrors/distros |
| `rapp-commons-event/1.0` / `rapp-leviathan` | fleet/estate messaging rides **on** `/chat` (ABI-2), not a side route |
| `function_app.py` (Tier 2) | MUST hold ABI parity with `brainstem.py` ("never break userspace" across tiers) |

---

*The kernel is the atom. Freeze its shape, immutably tag its releases, never break the agents written against it — and an estate of brainstems can be built on it that no single failure can take down.*
