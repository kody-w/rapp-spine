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
- many fleets across the planet, async = the **frame-net** (`rapp-frame/1.0`)

Compose atoms; never split the atom.

## 2. The kernel is locked (the anti-drift law)

The kernel (`rapp-agent/1.0`, [kody-w/RAPP](https://github.com/kody-w/RAPP)) is **frozen
contract**: one `/chat` tool-loop, the `BasicAgent.metadata` + `perform(**kwargs) -> str`
ABI, agent-injected direct routes, T1/T2 parity. Every capability — the swarm, the
frame-net, the auth, the registry — ships as an **agent / cartridge / spine-profile on
the existing wire, never an engine edit.** A passing CI invariant proves the kernel never
changed. This is what lets the foundation be *built upon* without drifting underneath.

**Corollary — every hero use case survives, forever.** Because an edge *is* a full
brainstem running the unchanged kernel + agents, everything the rapp repo offers today
(eggs/organisms, the RAR/Store/Sense federation, vBrainstem, the three tiers, soul/memory/
rappid identity) works at every edge, unchanged. The frame-net only *re-aims* it.

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
| **Planet** | `rapp-frame/1.0` | many fleets, async, over GitHub (frame/echo/public-twin) |
| **Survival** | `rapp-hydra/1.0` | many heads, one body — the static medium no one can shut down (cut a head, two grow) |
| **Router** | `rapp-spine/1.0` | situation → the right pillar |
| **Map / Drift** | `rapp-map`, `rapp-god` | where each pillar lives; is your copy canonical? |
| **Roadmap** | [`rapp-roadmap`](https://github.com/kody-w/rapp-roadmap) | how we build from here without un-locking the kernel |

## 5. Build from here

Lock first, build second. New capability = a new agent/cartridge/egg/frame, registered
against `foundation.json`, routed by the spine, watched by rapp-god, promoted per the
roadmap. The kernel does not move. The twin is always public. Nothing drifts.

---

*Compose atoms. Lock the kernel. Publish the twin. Build forever.*
