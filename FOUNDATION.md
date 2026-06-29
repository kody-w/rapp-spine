# The Foundation — locked

Everything in the RAPP universe — organisms, swarms, flocks, neighborhoods, the
planetary frame-net, whatever eternity builds next — stands on this. It is **locked**
on purpose: you build *from* it, never *into* it, so nothing drifts.

## 1. The brainstem is the atom

The brainstem is the indivisible unit. A 1-cell daemon, a 5-estate being, a 50-node
fleet, a planet of edges on a light-delay — all of them are **brainstems composed**.
The atom is the same everywhere; only the arrangement scales.

- one brainstem = an organism (`rapp-agent/1.0`, the kernel)
- many cells in one = a **being** (Wrapped Organism)
- many bodies as one mind = a **fleet** (Leviathan Protocol)
- many fleets across the planet, async = the **frame-net** (`rapp-frame/2.0`)

Compose atoms; never split the atom.

## 2. The kernel is locked (the anti-drift law)

The kernel (`rapp-agent/1.0`, [kody-w/rapp-installer](https://github.com/kody-w/rapp-installer) — the grail; [kody-w/RAPP](https://github.com/kody-w/RAPP) is the reference distro that pins it) is **frozen
contract**: one `/chat` tool-loop, the `BasicAgent.metadata` + `perform(**kwargs) -> str`
ABI, agent-injected direct routes, T1/T2 parity. Every capability — the swarm, the
frame-net, the auth, the registry — ships as an **agent / cartridge / spine-profile on
the existing wire, never an engine edit.** A passing CI invariant proves the kernel never
changed. This is what lets the foundation be *built upon* without drifting underneath.

**Corollary — every hero use case survives, forever.** Because an edge *is* a full
brainstem running the unchanged kernel + agents, everything the rapp repo offers today
(eggs/organisms, the RAR/Store/Sense federation, vBrainstem, the three tiers, soul/memory/
rappid identity) works at every edge, unchanged. The frame-net only *re-aims* it.

## 2a. The kernel/distro model — the Linux philosophy

RAPP deliberately follows the model that made **Linux rule compute**: a tiny sacred kernel, and an
open explosion of *distros* built on it. The mapping is exact:

| Linux | RAPP |
|---|---|
| the Linux kernel | the **brainstem** (`rapp-agent/1.0`, [kody-w/rapp-installer](https://github.com/kody-w/rapp-installer) — **the grail**) |
| a kernel release + immutable tag (`v6.9`) | a brainstem **VERSION** + immutable `vX.Y.Z` tag |
| the syscall ABI — *"never break userspace"* | the **agent ABI**: `BasicAgent.metadata` + `perform(**kwargs) -> str`, the `/chat` envelope, agent auto-discovery |
| loadable modules / userspace programs | **agents** — drop-in `*_agent.py` |
| a distro (Ubuntu, Fedora, Arch) | a **RAPP distro** — the unmodified kernel (pinned to a version) + a userland (agents, `soul.md`, specs, branding) |
| an LTS distro pinning an older kernel | [kody-w/RAPP](https://github.com/kody-w/RAPP) pins kernel **v0.6.0** *byte-identical* while the grail ships `0.6.1` (verified: `brainstem.py` + `basic_agent.py` + `VERSION` all match grail@v0.6.0) |

**The rules (borrowed from Linus, because they work):**

1. **The kernel is sacred and minimal.** One file, one job. Changed only in the grail, version-bumped, tagged immutably. Distros never patch it.
2. **The kernel never breaks userspace.** The agent ABI is frozen — an `agent.py` written for any kernel keeps running on every later kernel, forever. This is the contract that lets the ecosystem compound.
3. **A distro = a pinned kernel + a userland.** It ships the kernel *unmodified* (byte-identical to a grail tag) and adds everything else on top. RAPP is the reference distro.
4. **Anyone can spawn a distro.** Pick a kernel version, assemble a userland, ship — no permission needed. Exactly why Linux distros number in the thousands. The kernel stays one thing; the variety lives in the distros. *This is the adoption flywheel.*
5. **Pin, don't fork.** A distro may pin any kernel version (LTS-style) or track the latest (rolling) — but it may **not modify** the kernel. That's a fork, and forks are drift. The freeze CI invariant is therefore **`distro kernel files == grail @ its pinned tag`** — *not* `main == main`.

So "kernel sacred," "use everyone else's hardware," and "engine, not experience" are one idea: the
kernel is the single fixed point; distros and operators do everything else. The estate's "split-brain"
between rapp-installer and RAPP was never drift — it is a distro correctly **pinning** an unmodified
kernel. RAPP is to the brainstem what Ubuntu is to Linux.

**Two layers of the same idea.** A **distro** pins the kernel *file* on the *same* substrate (a Flask brainstem) — RAPP. A **substrate-distro** pins the kernel *loop* on a *different* substrate: T2 (`function_app.py`, Azure Functions), T3 (Dataverse), the headless SDK, the browser (Pyodide). Both are "the same kernel, different wrapper" — the loop is locked; only the silicon differs. The freeze invariant for a distro is `KERNEL_PIN` (kernel file == grail@tag); for a substrate-distro it is the `rapp-runtime-parity/1.0` golden vectors (loop output == reference). *The kernel is locked in T2 too — it's the same loop.* This is exactly *"use everyone else's hardware":* the one locked kernel runs on whoever's silicon.

## 3. A globally-public canonical twin for everything

Every load-bearing spec has a **canonical twin**: content-addressed, signed, and served
as a static API over GitHub raw (`rapp-static-api/1.0`). Any brainstem, anywhere — even a
fresh one, even an edge on a spotty link — fetches the *authoritative* version from a
public URL, verifies its hash, and acts. [`rapp-god`](https://github.com/kody-w/rapp-god)
watches every copy against the canonical hash and reports drift; it never silently forks.

The canonical registry is [`foundation.json`](foundation.json) — `{ spec, version, repo,
raw_url, sha256, locked }` per foundation pillar. Fetch it, verify it, build on it.

```
read  →  raw.githubusercontent.com/.../foundation.json   (canonical, hashed, immutable)
verify →  sha256(spec) == foundation.json[spec].sha256    (no silent drift)
build →  agents/cartridges/profiles ON the wire           (never into the kernel)
```

## 4. The foundation pillars (locked)

| pillar | spec | what it locks |
|---|---|---|
| **Kernel** | `rapp-agent/1.0` | the atom — the single-file brainstem contract |
| **Fleet** | `leviathan` SPEC v1.0 | one mind, many bodies (sync, LAN) |
| **Being** | `rapp-leviathan-egg/1.0` + Wrapped Organism | many cells, one organism (portable) |
| **Planet** | `rapp-frame/2.0` | many fleets, async, over GitHub (frame/echo/public-twin) |
| **Survival** | `rapp-hydra/1.0` | many heads, one body — the static medium no one can shut down (cut a head, two grow) |
| **Router** | `rapp-spine/1.0` | situation → the right pillar |
| **Map / Drift** | `rapp-map`, `rapp-god` | where each pillar lives; is your copy canonical? |
| **Roadmap** | [`rapp-roadmap`](https://github.com/kody-w/rapp-roadmap) | how we build from here without un-locking the kernel |

## 4a. The law + the spec corpus (brought into the lock)

The foundation isn't only protocols — it's the **law** that keeps the kernel sacred and the **full
spec corpus**, both content-addressed and hydra-served in [`foundation.json`](foundation.json):

- **The law (constitutions).** The kernel **[CONSTITUTION](https://github.com/kody-w/RAPP/blob/main/CONSTITUTION.md)**
  is the authoring discipline (Article 0 — *the file IS the agent IS the documentation IS the contract*);
  **MASTER_PLAN** is the why-axis first-principles north star (when the two disagree, **the Master Plan
  wins**); **SPEC** is the wire contract they protect. Estate constitutions
  (`rappterbook`, `rappterbook-governance`) govern their own domains. *"What does the law say — is this
  change allowed?"* routes here.
- **The spec corpus.** Every RAPP spec, three ways: **[RAPP-Bible](https://github.com/kody-w/RAPP-Bible)**
  (canonical aggregate), **[rapp_docs](https://github.com/kody-w/rapp_docs)** (live-streamed from each home
  repo's raw, no copies), and **[rapp-god](https://github.com/kody-w/rapp-god)** (the drift detector —
  watches every copy against the canonical hash). The spine's [`registry.json`](registry.json) routes
  situations to the right spec; `foundation.json` locks the pillars + the law by hash.

The law and the corpus are themselves canonical public twins — so the discipline that keeps the kernel
sacred is as locked, public, and drift-watched as the kernel itself.

## 5. Build from here

Lock first, build second. New capability = a new agent/cartridge/egg/frame, registered
against `foundation.json`, routed by the spine, watched by rapp-god, promoted per the
roadmap. The kernel does not move. The twin is always public. Nothing drifts.

---

*Compose atoms. Lock the kernel. Publish the twin. Build forever.*
