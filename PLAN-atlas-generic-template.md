# PLAN — Atlas → generic registry-of-registries template (brainstem-mutable)

> **Branch:** `feat/atlas-generic-template` · **Source of intent:** Bill Whalen's approved work brief
> https://gist.github.com/billwhalenmsft/3ca0daf1a1bea6305f1bc44491afd0b2 (public, fetched 2026-07-08)
> **Status:** plan locked; build not started. **M3 UNBLOCKED 2026-07-08:** Bill re-sent the invite,
> accepted — `kody-w` now has WRITE on `billwhalenmsft/MCAPS-OS-Platform` (private; `feat/se-os` is
> the default branch). Recon verified: no `atlas/` dir exists yet; vendored packs present at
> `src/components/se-os/workshop/packs/` (both current packs absorbed — matches the brief's all-green
> state, so M3's detection DoD needs the fixture path). `billwhalenmsft/se-os-template` verified
> public; feed target `web_ui/resource-hub-data.json` verified present (46 KB).

---

## 1. Bill's intent, distilled (what he has → what he wants)

Bill runs a 3-tier flywheel (Platform product ← SE cockpit ← public SE template). Assets are authored
at the bottom, "absorbed" up into the platform, and rediscovered by future SEs through a curated
Resource Hub. His brief asks Kody for **Atlas** — the instrumentation layer on that flywheel:

1. **Job 1 — drift/absorption guard:** prove the flywheel actually turns. Flag authored-but-unabsorbed
   packs, work stranded on non-deploy branches, stale workspace entries, template divergence.
2. **Job 2 — one canonical `assets.json`:** every asset (pack, recipe, demo, solution, agent, doc,
   generator, environment) harvested into ONE uniform, *actionable* shape — each entry carrying
   `actions[]` (find → act) and `composes_into` (ingredient → solution graph).

Hard rules he locked: **additive & read-only** (own `atlas/` dir, never touch Builder code),
**static-first** (JSON + HTML + badge, CI on 6h + on-change), **observe never coerce** (drift is
reported; the only writes are reviewable PRs to the curated discovery surface).

Bill's own framing: this is a straight port of Kody's proven trio — rapp-god (drift detector),
RAR (federated single-file registry), static-JSON-as-API. **He is asking for a RAPP pattern,
instantiated for his workflow.** That is the tell that the pattern should be extracted once, generically.

## 2. Spine crawl verdict (situation → protocol)

Crawled `rapp-spine` per CRAWL.md:

| Concern | Vertebra | Layer |
|---|---|---|
| Zero-infra API/registry/catalog/status-badge | `rapp-static-api/1.0` | distribution |
| Cross-repo drift detection, observe-never-coerce | `rapp-grail-scan/1.0` (rapp-god) | map |
| Runs as a drop-in brainstem agent | `rapp-agent/1.0` (agents/ dir contract) | runtime |
| Publish/discover the template as a community agent | RAR (`rapp-registry/1.0`) | distribution |

**CRAWL.md rule 6 governs:** *"the situation may be a new agent/cartridge/§-profile on top of an
existing protocol — not a new protocol. Default to composing, not inventing."*
→ Atlas-generic is a **template + single-file agent composing existing vertebrae**. No new spec id,
no new endpoint, no registry.json edit in this branch. (If the template later proves load-bearing,
registration happens in a normal compliance round — not here.)

## 3. What we build: `rapp-atlas` — the generic template

**One sentence:** a workflow-agnostic registry-of-registries kit — feed a brainstem a description of
ANYONE's asset flywheel (where assets are authored, where they're absorbed, where they're discovered)
and it mutates the template into THEIR Atlas.

### 3.1 The split: frozen core vs mutation surface

**Frozen core (the engine — same for every user):**
- The **uniform asset model** (Bill's shape, adopted verbatim as the contract):
  `{ id, kind, title, tier, provenance{repo,path,sha,authored_by}, status{authored,absorbed,deploy_line}, actions[]{verb,handle}, composes_into[], tags[] }`
- The **pipeline:** harvest manifests → normalize to asset model → emit `assets.json` + `atlas.html`
  dashboard + shields badge → run drift checks → open reviewable PRs to feed targets.
- The **doctrine:** additive, read-only on sources, static-first, observe-never-coerce, PR-delivered
  writes only. Non-negotiable in every mutation.

**Mutation surface (`atlas.config.json` — what the brainstem rewrites per user):**
- `tiers[]` — the user's repos/branches and each one's role (authoring / product / discovery).
- `harvest[]` — glob → kind mappings ("what counts as an asset here and where does it live").
- `checks[]` — which drift guards apply (absorption, branch-strand, liveness, template-drift), each
  as source-glob vs target-glob pairs.
- `feeds[]` — discovery surfaces to auto-feed via PR, with the transform (exhaustive index → curated view).
- `actions{}` — per-kind default action handles (what use/deploy/story/compose means in THEIR world).
- `branding` — names, badge label, dashboard title.

### 3.2 Deliverable shape (RAPP idiom)

```
kody-w/rapp-atlas            (new public repo — the template)
├── atlas_agent.py           single-file brainstem agent: takes a workflow description +
│                            repo handles, interviews/infers, EMITS a filled atlas.config.json
│                            + the build script — the "mutate to WHOEVER" entry point
├── build-atlas.mjs          the frozen engine (Node, gh/fetch only, zero deps)
├── atlas.config.json        example config (self-hosting: rapp-atlas watching the RAPP estate)
├── atlas.schema.json        config + asset-model schemas (the contract, versioned)
├── atlas.html               standalone dashboard (single-file, renders any assets.json)
└── .github/workflows/atlas.yml   6h + on-change, paths-scoped
```

`atlas_agent.py` publishes to RAR like any community agent. The engine self-hosts: the example
config points at the RAPP estate itself, so the repo's own badge/dashboard is the living demo.

### 3.3 Build order — upstream → downstream (two-RAPPs ruling)

Content flows **kody-w → billwhalenmsft**, never backwards:

1. **M1 — engine, self-hosted (kody-w lane, unblocked NOW):** `rapp-atlas` repo; engine + schema +
   dashboard; example config watching 2–3 RAPP-estate repos; badge live.
   *DoD: `assets.json` regenerates in CI; dashboard renders it; a deliberately-planted drift fixture
   is flagged.*
2. **M2 — mutation agent (kody-w lane):** `atlas_agent.py` — given a plain-language workflow
   description, emits a valid filled config; publish to RAR.
   *DoD: feed it a workflow description it has never seen; the emitted config validates against
   `atlas.schema.json` and the engine runs it green end-to-end.*
3. **M3 — Bill instance (work lane, BLOCKED on collaborator invite):** run the M2 agent on Bill's
   brief → config for his 3 tiers → instantiate as the firewalled `atlas/` dir on `feat/se-os` per
   his locked decisions (branch off `feat/se-os`, touch only `atlas/**` + paths-scoped workflow,
   feed Resource-Hub-only via PR). His first-PR DoD applies: dashboard shows true absorption state
   for engagement packs, detection proven via fixture.
   *M3 proves the whole thesis: Bill's Atlas is just one mutation of the template.*
4. **M4 — harden from what M3 teaches:** fold instance learnings back into the template as config
   capabilities (never as Bill-specific code); widen asset kinds; then consider spine registration.

**Boundary law for M3:** the generic template stays clean-room — built ONLY from Bill's public gist
+ public repos. Nothing from inside MCAPS-OS-Platform (once access lands) flows back into kody-w
repos; learnings return as *generic config capabilities* only. No customer names anywhere in
`rapp-atlas` (fixtures use synthetic names).

## 4. Execution notes (CSM)

- **Muscle (Copilot CLI, `claude-opus-4.8`, unlimited):** M1 engine + dashboard + CI, M2 agent
  scaffolding, fixtures, docs. Orders per `~/Desktop/RAPP-Master-Strategy/09-COPILOT-ORDERS.md`.
- **Cortex (Fable 5):** this plan; schema/contract review; the full-E2E pass + adversarial critique
  of each milestone AFTER muscle finishes; naming; the M3 instantiation judgment call.
- **Immediate next actions in this window:**
  1. Ping Bill for the MCAPS-OS-Platform invite (M3 unblocked later; don't wait on it).
  2. Muscle order #1: scaffold `rapp-atlas` per §3.2, M1 scope only.
  3. Cortex E2E: run the engine against the self-host config, criticize, then polish.
