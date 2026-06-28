# The Cubby Shelf & the Super-RAR

> **Schemas:** `rapp-cubby/1.0` · `rapp-super-rar/1.0` · **Version:** `1.0.0` · **Canonical source:** `kody-w/RAPP` (`specs/CUBBY.md`)
>
> **Status:** shipping today. Both artifacts are emitted on disk by the batcave edition of `rapp_agent.py` (the `cubby_*` / `super_rar` / `load` actions). This document locks the formats that already exist; it does not invent new ones.
>
> **Authority order** (when docs disagree, the higher wins): `MASTER_PLAN.md` → `CONSTITUTION.md` → spec-docs (this file) → vault → code. This is a spec-doc; it does not outrank the plan or the law.
>
> **Ground truth this spec is bound to:** the kernel is the brainstem (the grail, `rapp-installer`); a RAPP is a distro pinning it; **agents are the only extension**; **`/chat` is the only wire**; trust = **gh-collaborator + sha256** (rappid identity is PKI-free sha256, keypair **OPTIONAL, never required**); **GitHub is the substrate** (raw CDN + Issues-mailbox + PR-consent + Pages-edge); north star = *use everyone else's hardware → neighborhoods → estate → metropolis*.

---

## 1 — Scope

This document defines **two coupled artifacts** that together form the *local distribution layer* beneath neighborhoods and stores — the layer that lets an operator stockpile and stream work between brainstems **without ever committing to a git repo**:

| Artifact | Schema | What it is |
|---|---|---|
| **Cubby** | `rapp-cubby/1.0` | A private, **git-invisible** shelf — one named corner of an operator's local estate (agents, organs, senses, rapplications, neighborhoods, eggs, show-and-tell) described by a `cubby.json` manifest. |
| **Super-RAR** | `rapp-super-rar/1.0` | The **federated index** that aggregates cubbies — and the three public stores — into one ranked, sha256-pinned result set, queryable by `where=local | neighborhood | stores`. |

A standard **RAR** (the RAPP Agent Registry, `kody-w/RAR`) stocks *agents only*. The **super-RAR** carries the **whole RAPP stack** across **every cubby** — one private registry over the full ecosystem anatomy. The relationship is: *cubby* is the shelf, *super-RAR* is the catalog over all the shelves.

### 1.1 The kernel is never touched

Per [[feedback_brainstem_repo_is_sacred]] and [[feedback_minimal_root_brainstem_data]], this entire layer lives **outside** the grail engine surface:

- Cubbies live under `~/.brainstem/cubbies/<slug>/` — adjacent to `.brainstem_data/`, never inside the grail repo `rapp_brainstem/`.
- Eggs live under `~/.brainstem/eggs/`. Loadout state lives at the brainstem's `loadout_path` (`rapp-loadout/1.0`).
- When a cubby's agents are **streamed** into a running brainstem, the streamed files are registered in **`.git/info/exclude`** so the grail's `git status` stays **byte-identical** before and after (§3, the *zero grail-commit-risk invariant*).

The cubby/super-RAR layer adds **no new brainstem symbol and no new wire**. It is delivered entirely by drop-in agents speaking `/chat` (per [[feedback_chat_endpoint_sacred]], [[feedback_swarm_agents_drop_in_compatible]]). Nothing here is a REST route.

---

## 2 — `rapp-cubby/1.0` — the cubby manifest

A **cubby** is a directory `~/.brainstem/cubbies/<slug>/` containing a `cubby.json` at its root and zero or more **anatomy sub-directories**. The seven anatomy kinds (the *estate anatomy*) are:

```
agents/  organs/  senses/  rapplications/  neighborhoods/  eggs/  show-and-tell/
```

### 2.1 `cubby.json` schema

```jsonc
{
  "schema": "rapp-cubby/1.0",          // REQUIRED — exact string, the format gate
  "github_login": "kody-w",            // REQUIRED — operator's gh login, or "local" if unattributed
  "slug": "rapp-installer",            // REQUIRED — dir name; ^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$
  "display_name": "RAPP Installer",    // REQUIRED — human label
  "what_im_cooking": "…",              // REQUIRED — one-line intent (the shelf's purpose, free text)
  "created_at": "2026-06-27T02:06:04Z",// REQUIRED — UTC, RFC-3339, Zulu ("UTC-first frames")
  "estate": {                          // REQUIRED — declared anatomy of this cubby
    "anatomy": ["agents","organs","senses","rapplications","neighborhoods","eggs","show-and-tell"]
  },
  "streamable": { "agents": true },    // REQUIRED — per-kind stream permission (see §2.3)

  // ── OPTIONAL ──
  "parent_cubby": null,                // slug of the cubby this was forked from, or null
  "is_sub_cubby": false,               // true if nested under another cubby
  "collected_from": {                  // present iff the cubby was assembled by `cubby_collect`
    "query": "bookfactory",            //   the search term used
    "source": "all",                   //   local | neighborhood | stores | all
    "at": "2026-06-10T13:19:05Z"       //   UTC timestamp of the collect
  }
}
```

**Required:** `schema`, `github_login`, `slug`, `display_name`, `what_im_cooking`, `created_at`, `estate.anatomy`, `streamable`.
**Optional:** `parent_cubby`, `is_sub_cubby`, `collected_from`.

A reader **MUST** reject any manifest whose `schema` is not exactly `rapp-cubby/1.0`. A reader **MUST** ignore unknown keys (forward-compatibility — new facts are added as fields, never by versioning a value, per [[feedback_rapp_compatibility_contract]]).

### 2.2 Identity & rappid binding

A cubby's local identity is the pair `(github_login, slug)`. It resolves into the eternity namespace under its **operator's estate rappid** — canonical form `rappid:@<owner>/<slug>:<64-hex>` (256-bit sha256 content-address, **PKI-free**; keypair binding is OPTIONAL opt-in sovereignty and is **never required** to own, name, or stream a cubby). A cubby itself carries no key material. When a cubby is published into a **neighborhood**, the neighborhood's `super-rar/index.json` records the binding via its `neighborhood_rappid` (§4.1), and the public **commons** member-profile variant (`rapp-commons-cubby/1.0`, a sibling profile, not this schema) adds explicit `from` / `owner` rappid fields. The two are interoperable: `rapp-cubby/1.0` is the private local shelf; `rapp-commons-cubby/1.0` is its public neighborhood-member face.

### 2.3 `streamable` — per-kind permission

`streamable` is a map from anatomy-kind to boolean. It is an **assertion of intent**, gating which kinds the super-RAR marks streamable. In practice **only `agents` are streamable** (`streamable: true`), because agents are the only kind the kernel hot-loads (the frozen ABI). All other kinds (organs, senses, rapplications, neighborhoods, eggs) are **catalog-only** — discoverable and packable as eggs, but not directly streamed into the running agent loop. A cubby MAY omit a kind from `streamable`; an absent kind defaults to **not streamable**.

---

## 3 — The git-invisible streaming contract

Streaming is how a cubby's `agents/*_agent.py` enter a **running** brainstem and start serving **without a commit**. It is performed by the agent's `load` action (`_load`) and is governed by five hard rules.

### 3.1 The procedure (`load cubby=<whose-agents>`)

1. **Source resolve.** `src = <cubbies-root>/<cubby>/agents/`. The cubby handle MUST match `^[A-Za-z0-9][A-Za-z0-9-]{0,38}$`; an unsafe handle is refused.
2. **sha256 verification (default `verify=true`).** Each candidate file's sha256 is compared against the neighborhood RAR manifest's pin (`rar/index.json` → `agents[].sha256`). A file whose hash does **not** match its pin is **refused as drift** (tampered cubby file) and skipped with a reason — never loaded.
3. **Kernel protection.** Any filename in `KERNEL_AGENTS` is **never overwritten** (CONSTITUTION Art. XXXIII — [[project_kernel_agents_and_rapp]]). Current set: `basic_agent.py`, `context_memory_agent.py`, `manage_memory_agent.py`, `learn_new_agent.py`, `swarm_factory_agent.py`, `hacker_news_agent.py`.
4. **Operator-file protection.** If a destination file already exists, was **not** previously streamed (not in the loadout), and differs by sha256 from the source, it is **your own file** and is **never overwritten**.
5. **Copy + exclude + record.** Surviving files are copied into `<brainstem>/agents/`, each registered in **`.git/info/exclude`**, and recorded in the loadout (`rapp-loadout/1.0`) with `{file, sha256, from_cubby, loaded_at, target}`. Auto-discovery hot-loads them on the next `/chat` request — **no restart** (per the frozen ABI: `agents/*_agent.py` are reloaded from disk every request).

### 3.2 `.git/info/exclude` mechanics

`_register_excludes` resolves each streamed file's path **relative to the git top-level** and appends it (under a `# streamed in (rapp load) — git-invisible by design` banner) to `<git-top>/.git/info/exclude`, de-duplicating against existing lines. `.git/info/exclude` is a **local, uncommitted** ignore list — it is itself never tracked. Unloading (`unload`) removes the file and its exclude line.

### 3.3 The zero grail-commit-risk invariant

> **INVARIANT.** For any sequence of `load` / `unload` operations against the grail brainstem, `git status --porcelain` of the grail repo is **byte-identical** before and after. Streamed agents run but are **invisible** to git; the operator can never accidentally commit a neighbor's agent into the sacred grail.

This is the property that makes the cubby layer safe to run **directly on top of the grail** (per [[feedback_grail_agents_untracked_wiped]]: live drops are ephemeral; the durable home is the registry, not the grail tree).

### 3.4 Secret boundary

The secret-name filter (`_SECRET_NAME_RE`: `.env`, `*token*`, `*secret*`, `*credential*`, `*password*`, `*apikey*`, `*.pem/.key/.p12/.pfx`, `id_rsa`/`id_ed25519`, `.copilot*`, `.netrc`, `private-estate-secret`, …) **refuses** any matching file from crossing during pack/stream. Secrets are *substance*; cubbies carry only *bones* (warehouse, agents). State that is keys/PII/`.env` never travels.

---

## 4 — `rapp-super-rar/1.0` — the federated index

### 4.1 Index schema

`super-rar/index.json` is rebuilt by the agent's `super_rar rebuild=true` action (the builder `_build_super_rar`):

```jsonc
{
  "schema": "rapp-super-rar/1.0",          // REQUIRED
  "neighborhood_rappid": "rappid:@kody-w/rapp-batcave:72c739…eb100",  // REQUIRED for where=neighborhood
  "built_at": "2026-06-27T02:55:36Z",      // REQUIRED — UTC Zulu
  "note": "…",                             // OPTIONAL — human description of this super-store
  "count": 25,                             // REQUIRED — len(entries)
  "by_kind": { "agent": 18, "egg": 6, "rapplication": 1 },  // REQUIRED — histogram
  "entries": [
    {
      "kind": "agent",                     // REQUIRED — one of SUPER_RAR_KINDS (§4.2)
      "name": "neuron_swarm_agent.py",     // REQUIRED — basename
      "cubby": "kody-w",                   // REQUIRED — owning cubby/handle
      "path": "cubbies/kody-w/agents/neuron_swarm_agent.py",  // REQUIRED — rel to cubby_root
      "streamable": true,                  // REQUIRED — true iff kind == "agent"
      "sha256": "88da16f3…aa74e18",        // REQUIRED for files — content pin (the join key)
      "purpose": "…"                       // OPTIONAL — first docstring line, ≤140 chars
    }
    // …
  ]
}
```

A reader MUST reject `schema != rapp-super-rar/1.0` and MUST treat `sha256` as the **content-address join key** — the same agent appearing in two cubbies is the *same artifact* iff its sha256 matches (never compare by name or path).

### 4.2 The six anatomy kinds (`SUPER_RAR_KINDS`)

| kind | sub-dir | glob | streamable |
|---|---|---|---|
| `agent` | `agents/` | `*_agent.py` | **true** |
| `organ` | `organs/` | `*_organ.py` | false |
| `sense` | `senses/` | `*.py` | false |
| `rapplication` | `rapplications/` | `*` | false |
| `neighborhood` | `neighborhoods/` | `*` | false |
| `egg` | `eggs/` | `*.egg` | false |

The builder walks `<cubby_root>/<handle>/<sub>/<glob>` for every handle (skipping `.`/`_`-prefixed), sha256-pins each file, and lifts the first docstring line as `purpose`. **Only `agent` is streamable** (§2.3).

### 4.3 The federated query model — `where`

`super_rar query=… where=local | neighborhood | stores` composes results from three sources:

- **`where=local`** — index of the operator's **own whole estate**: `_build_super_rar(~/.brainstem/cubbies)`. Searches *everything you have built*, across every local cubby. This is the default when no neighborhood is mounted.
- **`where=neighborhood`** — the **super-store**: `_build_super_rar(<mounted-neighborhood>/cubbies)`. One private registry over **every neighbor's** full stack. Default when a neighborhood is mounted. Find what a neighbor already built and `load` it in.
- **`where=stores`** — the three **public catalogs** over the raw CDN substrate, merged into one result set:
  - **RAR** — agents — `https://raw.githubusercontent.com/kody-w/RAR/main/agents` (`RAPP_RAR_RAW`)
  - **RAPP_Store** — rapplications — `…/kody-w/RAPP_Store/main/index.json` (`RAPPSTORE_URL`)
  - **RAPP_Sense_Store** — senses — `…/kody-w/RAPP_Sense_Store/main/index.json` (`RAPP_SENSE_URL`)

**Ranking & composition.** Results from all in-scope sources are unioned, de-duplicated **by sha256** (a local cubby copy and a store copy of the same bytes collapse to one row, annotated with every source it appears in), and ranked by: (1) substring/keyword match of `query` against `name` + `purpose`, then (2) source proximity — **local > neighborhood > stores** (you prefer what is already on your disk, then your neighbors', then the public commons), then (3) `kind` priority `agent > rapplication > sense > organ > neighborhood > egg`. `where` is a **filter on which sources participate**, not a different schema — every source yields `rapp-super-rar/1.0` entries.

### 4.4 Rebuild & CI gate

The index is a **materialized view**; it MUST be rebuilt after any cubby mutation. Rebuild is idempotent (`super_rar rebuild=true`, a.k.a. the `build_super_rar` procedure). A conformant publisher SHOULD gate CI with a **`--check`** mode that re-runs the build and fails if the committed `super-rar/index.json` differs from the freshly-built one (stale-index drift = a failing build). Because every entry is sha256-pinned and the index is byte-deterministic, `--check` is a pure equality test.

---

## 5 — Cubby-as-egg (offline travel)

A cubby is portable. The agent's `cubby_egg` / `cubby_import` actions pack and hatch a cubby as a single self-contained file using the egg family (`brainstem-egg/2.3`, profile **`brainstem-egg/2.3-cubby`** — specified separately; referenced here as the carrier).

- **`cubby_egg cubby=<slug>`** → `_pack_cubby_egg` serializes the cubby directory (manifest + anatomy, minus any secret-matching file per §3.4) into `~/.brainstem/eggs/cubby-<slug>.egg`. Eggs are catalog entries with `streamable: false`.
- **`cubby_import path=<egg>`** → hatches the egg back into `~/.brainstem/cubbies/<slug>/`, reconstructing the same structure.

**Round-trip guarantee.** `cubby_import(cubby_egg(C)) ≡ C` for all non-secret files: same paths, same bytes, same sha256. This is how a cubby travels offline — `cubby_egg` on the source machine, sneakernet/Issues-mailbox the `.egg`, `cubby_import` on the target — with **no network and no git** (the *offline-degrade* path of the metropolis substrate). Local↔neighborhood is symmetric: `cubby_egg` then land in a neighborhood, or `cubby_import` from a neighborhood egg — same structure both ways.

---

## 6 — Trust model & the public/private boundary

### 6.1 Trust primitives

Exactly two, no more (per ground truth and [[project_rappid_eternity_standard]]):

1. **gh-collaborator** — *who may publish into this neighborhood/cave*. A cubby crossing into a shared space is authorized by being committed by a GitHub collaborator on the host repo (PR-consent is the gate). No keys, no signatures required. Keypair binding is **OPTIONAL** opt-in sovereignty (survives takedown/death) and is **never required** by any cubby or super-RAR operation.
2. **sha256** — *what exactly is this artifact*. Every entry is content-addressed. `load` refuses any file that drifts from its pinned hash (§3.1). sha256 is the **join key** across all sources (§4.3).

### 6.2 Two deployments

| Deployment | Reach | Auth |
|---|---|---|
| **Batcave** (private) — `kody-w/rapp-batcave` | private neighborhood super-store | **gh-auth** (collaborators only) |
| **Cave** (public) — `kody-w/RAPP` `/cave` (curl one-liner) | public on-ramp | **anonymous curl** over raw CDN |

Both expose the same `rapp-super-rar/1.0` index over their `cubbies/`. The difference is who can *publish* (gh-collaborator on a private repo vs. PR-consent on a public one) — never the schema.

### 6.3 The PUBLIC_BOUNDARY exclusion rule

> **RULE (PUBLIC_BOUNDARY).** Only **committed-public** artifacts cross into a public super-RAR. An operator's local, uncommitted cubbies under `~/.brainstem/cubbies/` are **git-invisible** and therefore **can never appear** in any public `super-rar/index.json` — there is nothing for the public builder to see. Private/operator agents never leak.

This is enforced structurally, in three layers, with **no trust assumption**:

1. **Git-invisibility** — local cubbies are not in any repo; `where=neighborhood`/`stores` only ever indexes files **committed** to the host repo's `cubbies/`. A file that was never committed simply does not exist to the public builder.
2. **Secret filter** (§3.4) — even within a committed cubby, secret-matching files are refused from pack/stream, so a key cannot ride along.
3. **Operator-file protection** (§3.1 rule 4) — streaming into a brainstem never overwrites the operator's own divergent files, so an inbound public cubby cannot silently replace private work.

The net effect: *public composition is opt-in by commit*. To share, you commit to a public cubby (PR-consent); everything else stays on your disk, invisible.

### 6.4 How it composes with the rest of the estate

The cubby layer is the **floor** of the composition stack the north star climbs:

```
agent → cubby (private shelf, git-invisible)
      → super-RAR (federated index over all local cubbies)         [where=local]
      → neighborhood (cubbies committed to a shared repo)           [where=neighborhood]
      → estate → metropolis (neighborhoods composed over the substrate)
                 stores (the public commons: RAR / RAPP_Store / Sense) [where=stores]
```

A neighborhood (`rapp-neighborhood` / `NEIGHBORHOOD_PROTOCOL`) is *a repo whose `cubbies/` are published*; its `super-rar/index.json` is the neighborhood's super-store. Estate→metropolis mesh-composition (Issues-mailbox / PR-consent / Pages-edge / offline-degrade / UTC-first frames — specified separately) federates *neighborhood super-RARs*, which federate *cubbies*. The cubby is the atom of distribution; the super-RAR is how atoms become a catalog at every tier, addressed by the same sha256 the whole estate uses as its join key.

---

## 7 — Worked example

Kody builds a `neuron_swarm_agent.py` and wants a neighbor in the batcave to use it — without either party committing to the grail.

**1 — Shelve it (private, git-invisible).** A local cubby already exists or is created:

```jsonc
// ~/.brainstem/cubbies/kody-w/cubby.json
{ "schema": "rapp-cubby/1.0", "github_login": "kody-w", "slug": "kody-w",
  "display_name": "kody-w", "what_im_cooking": "the operator twin — agents, games, the voxel world",
  "created_at": "2026-06-27T02:06:04Z",
  "estate": { "anatomy": ["agents","organs","senses","rapplications","neighborhoods","eggs","show-and-tell"] },
  "streamable": { "agents": true } }
```

The file `~/.brainstem/cubbies/kody-w/agents/neuron_swarm_agent.py` is on disk only — `git status` of the grail shows **nothing**.

**2 — Publish into the neighborhood (PR-consent).** The cubby is committed to `kody-w/rapp-batcave` `cubbies/kody-w/` (a gh-collaborator action). CI runs `super_rar rebuild=true --check`; the rebuilt index now contains:

```jsonc
{ "kind": "agent", "name": "neuron_swarm_agent.py", "cubby": "kody-w",
  "path": "cubbies/kody-w/agents/neuron_swarm_agent.py",
  "streamable": true, "sha256": "88da16f3…aa74e18",
  "purpose": "Summon a neuron swarm from chat — planner→lenses→reconciler." }
```

**3 — The neighbor finds it.** On their machine: `super_rar where=neighborhood query=swarm`. The federated index returns the entry above, ranked above any public-store match of the same name (neighborhood > stores).

**4 — Stream it in (zero-commit, hot-load).** `load cubby=kody-w`:
- sha256 of the source is checked against `rar/index.json` pin `88da16f3…` → **match**, accepted.
- not in `KERNEL_AGENTS`, not an existing divergent operator file → copied to `<brainstem>/agents/neuron_swarm_agent.py`.
- `agents/neuron_swarm_agent.py` appended to `.git/info/exclude`; recorded in the loadout.
- next `/chat` auto-discovers it. The neighbor can now say *"summon a neuron swarm"*.
- **`git status` of their grail: still byte-identical.** Invariant held.

**5 — Carry it offline (optional).** `cubby_egg cubby=kody-w` → `~/.brainstem/eggs/cubby-kody-w.egg`. Hand the egg to a third operator with no network; `cubby_import path=cubby-kody-w.egg` reconstructs the cubby, sha256-identical, ready to `load`.

At no point did anyone commit to the grail, exchange a key, or hit a non-`/chat` route. Trust was gh-collaborator (who could publish) + sha256 (what the bytes were). Nothing private left Kody's disk.

---

## 8 — Conformance

### 8.1 A conformant host MUST

1. **Emit & accept** `cubby.json` exactly as §2.1 (all required fields; reject `schema != rapp-cubby/1.0`; ignore unknown keys).
2. **Place** cubbies under `~/.brainstem/cubbies/`, eggs under `~/.brainstem/eggs/`, **never** inside the grail repo.
3. **On `load`:** sha256-verify against the neighborhood RAR pin and **refuse drift**; **never overwrite** a `KERNEL_AGENTS` file or a divergent operator file; register every streamed file in `.git/info/exclude`; record it in the `rapp-loadout/1.0` loadout.
4. **Preserve the zero grail-commit-risk invariant** (§3.3): grail `git status` byte-identical across any `load`/`unload`.
5. **Refuse secret-matching files** (§3.4) from any pack or stream.
6. **Build** `super-rar/index.json` exactly as §4.1 over `SUPER_RAR_KINDS` (§4.2); mark `streamable` true **iff** `kind == "agent"`; pin every file by sha256.
7. **Support** `where=local | neighborhood | stores`, de-duplicating by sha256 and ranking local > neighborhood > stores (§4.3).
8. **Enforce PUBLIC_BOUNDARY** (§6.3): only committed-public artifacts ever appear in a public index.
9. **Guarantee** the egg round-trip `cubby_import(cubby_egg(C)) ≡ C` for non-secret files (§5).
10. Require **no keypair** for any of the above (PKI-free; keypair OPTIONAL).

### 8.2 Test vectors

- **TV-1 (manifest gate).** `{"schema":"rapp-cubby/2.0", …}` → reader rejects. Removing any required field → reject. Adding `"future_field": 1` → accepted, ignored.
- **TV-2 (invisibility).** Snapshot grail `git status --porcelain`; `load cubby=X`; re-snapshot → strings equal. `unload` → still equal.
- **TV-3 (drift refusal).** Flip one byte of a cubby agent whose pin is in `rar/index.json`; `load` → that file `skipped` with `why` containing `sha256 drift … refused`; it is **not** copied.
- **TV-4 (kernel guard).** A cubby containing `manage_memory_agent.py`; `load` → skipped `kernel — never overwritten`.
- **TV-5 (operator guard).** Pre-place a *different* `foo_agent.py` in `agents/`; `load` a cubby with its own `foo_agent.py` → skipped `your own file — won't overwrite`.
- **TV-6 (secret refusal).** Place `.env` and `id_ed25519` in a cubby; `cubby_egg` → neither appears in the egg; `load` → neither crosses.
- **TV-7 (super-RAR shape).** Build over a fixture with 2 agents + 1 egg + 1 rapplication → `count==4`, `by_kind=={"agent":2,"egg":1,"rapplication":1}`, agents `streamable:true`, others `false`, every file has `sha256`.
- **TV-8 (dedup join).** Same agent bytes in a local cubby and in RAR; `super_rar where=stores` then `where=local` of the union → one row, sha256 collapsed, local-source ranked first.
- **TV-9 (CI gate).** Mutate a cubby without rebuilding; `super_rar rebuild=true --check` → non-zero exit (stale-index drift).
- **TV-10 (egg round-trip).** `cubby_egg` then `cubby_import` into a clean root → recursive sha256 of every non-secret file matches the original.

### 8.3 Registration in the drift observatory

`rapp-cubby/1.0` and `rapp-super-rar/1.0` MUST be registered as **parts** in `kody-w/rapp-god` (`registry.json` / `ecosystem-spec.json`, mirrored to `kody-w/rapp-map`) so the drift observatory tracks their schema versions across the four legs (agent / rapp-god / rapp-map / RAPP-Bible). Home of record for both specs is this file, `kody-w/RAPP/specs/CUBBY.md`. Divergence between the two `ecosystem-spec.json` mirrors **is** drift and MUST fail `verify`.

---

*This document is part of the RAPP species canon (`kody-w/RAPP`). It locks formats already emitted in practice; it does not outrank `MASTER_PLAN.md` or `CONSTITUTION.md`. Excludes — specified separately: `rapp-distro/1.0`, `rapp-frame/2.0`, `brainstem-egg/2.3`, and the estate→metropolis mesh-composition tier.*
