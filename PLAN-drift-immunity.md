# PLAN — Drift immunity: how the RAPP organism stays healthy

> Authored 2026-07-08, the day a full-mesh sweep (44 agents) found 13 drift issues — 3 of them live
> Eternity-invariant violations — while the four-leg triangle itself was byte-perfect. That split is
> the lesson: **the discipline works exactly where it's installed, and nowhere else.**

## What today proved about how drift actually happens

1. **Canon changes don't propagate themselves.** The Eternity ruling (2026-06-03) retired v2
   minting; a month later two specs still *taught* the retired form. Nobody swept downstream at
   ratification time.
2. **Twins drift when the pin ritual is skippable.** rapp-map's MD render lagged its own JSON twin
   — both still claiming v1.0.0 — because nothing *forces* the same-commit re-render.
3. **New repos outrun the catalog.** rapp-eternity was declared "the sole identity standard" by
   another spec while absent from the canonical repos list. Creation didn't include registration.
4. **Hash-watching is necessary, not sufficient.** rapp-god kept the mirrors byte-identical
   (it worked!) — but hashes can't see a spec *contradicting* canon, an MD contradicting its JSON,
   or two sections of one file naming different serving agents.
5. **Mirrors decay silently.** The Bible's eternity mirror lost one word ("OPTIONAL") and thereby
   implied mandatory PKI — a one-word semantic inversion no checksum flags.

## The immune system — four tiers, cheapest first

Organism framing: **lint = reflexes · Atlas = skeleton · rapp-god = proprioception · mesh = immune system.**

### Tier 1 — Reflexes: per-commit invariant lint (zero-LLM, free, every push)
One shared lint rule-pack (single source of truth, e.g. `rapp-spine/tools/drift-lint` or a
reusable GitHub workflow `kody-w/rapp-drift-lint`) adopted by every spec-bearing repo's CI:
- forbid minting language for `rappid:v2:` / non-@ rappid forms outside explicitly-marked
  legacy-read sections;
- forbid "Prototyping Platform" (canon: Prototype);
- pin checks: beacon schema references must be ≥ the constitutionally-mandated version;
- twin-pin rule: if `ecosystem-spec.json` changes in a commit, `ECOSYSTEM_SPEC.md` must change in
  the same commit (and versions must match) — CI fails otherwise. Same pattern for any JSON+MD twin.
Rules are regex-grade on purpose: instant, deterministic, no judgment. Every HIGH found today would
have been caught at commit time by 2–3 lines of lint.

### Tier 2 — Skeleton: Atlas on the estate (structural, 6h CI, already built)
Instantiate the Atlas engine (built today, staged at `~/Documents/GitHub/rapp-atlas`) with an
estate config — the drift-guard we shipped Bill, pointed at ourselves:
- **liveness**: every repo in the canonical repos list + every `entry_point` in the spine registry
  resolves (today: RAPP-Network's nominal neuron path 404'd — this check catches that class);
- **absorption**: every schema in `schemas_ref` has a cataloged owning repo; every spine vertebra's
  spec file exists at its declared path; every RAR-published agent's repo is reachable;
- **source-error honesty** (built today): an unreadable source is a red badge, never silence.
Output: estate `assets.json` + badge on rapp-map/rapp-god. Structural gaps become a red badge
within 6 hours instead of waiting for someone to notice.

### Tier 3 — Proprioception: rapp-god as-is (hashes, mirrors)
Already works — keep it. Today's evidence: the triangle it guards was the only part of the
ecosystem with zero drift. Its scope is byte-equality of things declared identical; don't ask more
of it, don't duplicate it in the other tiers.

### Tier 4 — Immune system: scheduled semantic mesh sweep (LLM, weekly + triggered)
The 44-agent ecosystem-sync deep sweep, run on a schedule instead of on suspicion:
- **weekly cron** (cloud routine) with `fix=true` → auto-files `drift(<id>)` issues, `drift` label
  (the convention established today);
- **triggered sweeps** — mandatory, same-session — after: any CONSTITUTION amendment, any
  ecosystem-spec version bump, any new repo registration, any invariant re-wording. The 2026-06-03
  Eternity ratification is exactly when today's three HIGHs were born; a triggered sweep that day
  would have caught all three at birth;
- **scoped sweeps** for cheap targeted checks (`scope:` arg) between full runs.

## The write-time ritual (prevention beats detection)
Small, mandatory, and checkable:
1. **Ratify → sweep → file, same session.** No canon change is "done" until the old form has been
   hunted ecosystem-wide and every hit has a `drift()` issue.
2. **Twins bump together.** JSON + MD render + version pin in one commit (Tier-1 lint enforces).
3. **Registration at birth.** A new repo/spec enters `ecosystem-spec.json` (and the spine registry,
   if load-bearing) in its first ratified commit — Tier-2 absorption makes the omission visible.
4. **Mirror headers are contracts.** A mirror is only edited by re-syncing from its declared
   upstream of record; Tier-4 checks mirror wording against upstream.
5. **Frozen bundles get a refresh cadence.** Planted/frozen seeds (specs/README.md class) are
   by-design stale — schedule the refresh ritual (quarterly or on major canon change) so "frozen"
   never silently means "wrong".

## Triage doctrine (dealing with what's found)
- **Severity ladder:** HIGH = live invariant violation → fix within a day; MEDIUM = catalog/schema/
  render lag → within a week; LOW = wording → batched.
- **Traceability chain (established today):** `drift(<id>)` issue → feature branch → merge
  referencing the issue → issue closes ONLY after a re-sweep confirms the finding is gone. "Fixed"
  is a sweep verdict, not a merge event.
- **Authority order is the tiebreaker, always:** CONSTITUTION > canonical spec (species root) >
  specs > renders > mirrors > code/pages. Mirrors never win; pages never define canon (today's H3
  = chat.html asserting canon is the anti-pattern).

## Rollout order
1. Land today's 13 fixes via the issue→branch→merge chain; re-sweep to confirm clean (in flight).
2. Tier-1 lint pack: author once in the spine, adopt in the 6 repos that drifted today first.
3. Tier-2 estate Atlas: estate config + badge (engine already built and battle-tested on MCAPS).
4. Tier-4 weekly routine + the ratify→sweep ritual written into the CONSTITUTION/spine doctrine
   so it binds future canon changes.
5. First monthly health review: sweep verdict + badge history + open-drift-issue age = the
   organism's vitals.
