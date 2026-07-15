# FABLE HANDOFF — the judgment, transferred

> Written 2026-07-14, in the last week of Fable 5 access, so that future sessions — any
> model — inherit the *decisions and how to re-derive them*, not just the artifacts.
> Structure per the adversarial reviewer's amendment: decision records with rejected
> alternatives, invariants, failure modes checked first, and explicit do-not-infer rules.
> Companion mechanical half: `kody-w/rapp-map/conformance/` (golden drift cases — run it
> before trusting any sweep, yours included).

## Decision records (ADRs) — with the road not taken

**ADR-1 · The Lexicon supersedes-by-absorption, not by replacement.**
`LEXICON.md` already existed at the species root (2026-05-02 two-vocabulary mapping)
when Movement II called for a "new" file of the same name. Ruling: the Nine Words became
Parts I–III; the old mapping is preserved as Part IV (body text verbatim, headings
adjusted, its "1:1" claim explicitly superseded). *Rejected:* a second file
(`LEXICON-NINE-WORDS.md`) — two lexicons is the exact confusion the movement exists to
kill. *Rejected:* deleting the old mapping — the covenant forbids deleting entrenched
canon. The Lexicon is live on kody-w/RAPP **main** (merged 2026-07-14 with Article LII
and the ecosystem-spec 1.2.0 `lexicon` pointer); it seals at genesis. Historical note:
it was drafted on branch `feat/lexicon-v1`; before the merge, main's LEXICON.md stayed
old until the seal.

**ADR-2 · The Constitution outranks the OPUS — even on the OPUS's own rulings.**
OPUS R2 said "twin = person-subject organism"; Constitution Art. XLIX (newer) says a
twin is NOT an organism (a presence: identity + voice + workbench; many per organism).
The lexicon bent to Art. XLIX and kept the old shorthand as informal usage.
*Do not infer* that a Kody-commissioned plan overrides ratified articles; precedence is
Constitution > ANTIPATTERNS > schema specs > Lexicon > plans.

**ADR-3 · The genesis gate is "zero UNEXPLAINED drift," not zero drift.**
Adopted from the adversarial review of the session plan itself. Literal zero produces
false alarms on intentional divergence (frozen planted bundles, read-forever legacy
forms). Mechanism: every finding is either fixed, or waived in
`rapp-map/conformance/waivers.json` with why/who/expiry. A sweep "passes" when the
ledger explains everything it found.

**ADR-4 · Detector baselines are themselves drift surfaces.**
R3's only HIGH-severity *mesh* finding against rapp-egg-hub was the neuron's own stale
baseline (it still watched for the retired keyed/germline identity model). Ruling: when
a sweep flags a repo that agrees with ratified canon, suspect the detector first —
then re-baseline it as a traceable commit (see rapp-map `ebb846f`). *Rejected:* "fixing"
the repo to match the stale detector.

**ADR-5 · Prior-art posts are frozen.**
Blog posts published as dated prior art ("The AI You Keep", "What Is Our Moat") are
never edited in place — editing undermines the timestamp that is their entire point.
Improvements ship as new posts that cite them. Applies to anything whose value is
*having been said on a date*.

**ADR-6 · Adversarial cross-model review is the honesty mechanism.**
Every judgment-heavy deliverable goes to a different frontier model (currently Copilot
CLI `gpt-5.6-sol`) with instructions to REFUTE it. Verified live 2026-07-14: it
correctly re-ordered the session plan, replaced the drift gate (ADR-3), and found 22
real issues in a lexicon draft two rounds of self-review had passed. Adjudication stays
with the authoring side: of its 22 findings, one was partially refuted with evidence
(rapp-frame/2.0 IS shipped — in kody-w/twin, outside the repo it searched). Neither
model is trusted alone; the disagreement is where the value lives.

## Invariants (never break; check before believing any change is safe)

1. **Identity law:** rappid 64hex = sha256(master_pubkey_SPKI) keyed, or
   stable-UUID-derived keyless. NEVER sha256(owner/slug). No `rappid:v3`/`v4` — legacy
   forms are read forever, never re-emitted.
2. **Frozen kernel:** `brainstem.py` + `basic_agent.py` are never edited by AI.
3. **Append-only canon:** Constitution and (post-seal) Lexicon amend by appending;
   supersede by naming, never rewrite.
4. **URL shapes are sacred** (install one-liner, shipped filenames).
5. **Public-by-construction** for anything DOG-side: no customer names, no private
   identifiers, ever — an append-only public chain makes leaks permanent.
6. **An observation gap is transport, not biography:** record the gap as an event;
   never silently emit thinner data.
7. **soul.md is sacred** — never add operational/product content; bugs are fixed at
   their real layer.

## Failure modes — what to check FIRST when something looks wrong

- **False-green muscle suites.** Every real defect in the first full-scale CSM run was
  found by hands on REAL/live artifacts, never by the muscle's own fixtures. Gate-check
  with real inputs + one live probe before believing any green.
- **Stale detector baseline** (ADR-4) before "the repo drifted."
- **Wrong git identity.** This machine holds two GitHub accounts (kody-w personal, and
  the work account). A 403 on a kody-w repo usually means the active gh account is the
  work one: `gh auth switch -u kody-w`. Never push work content to kody-w repos or vice
  versa (upstream→downstream only).
- **In-flight sibling sessions.** Uncommitted changes you didn't make are another
  session's work: never sweep them into your commits; never ship their unverified posts.

## Do-not-infer rules (a weaker model would plausibly guess these wrong)

- "Sealed" = sha256-pinned, not encrypted. The seal covers every byte; dated snapshots
  are sealed *as history*.
- "Organ" is constitutionally reserved for `*_organ.py` HTTP extensions — the brainstem
  is a *runtime*, not an organ, despite the biology register.
- Not every egg is a frame's sibling — only *snapshot* eggs (Lexicon R3).
- Frames are not categorically public: `rapp-frame/1.0` logs are vault-side;
  `rapp-frame/2.0` biography frames are DOG-side.
- RAPP = "Rapid Agent **Prototype** Platform" (not Prototyping).
- Never claim "zero meter" — say "uses your existing Copilot seat."
- `kody-w/rapp-body` being unpublished is intentional (darkroom until genesis), not
  missing.

## Cold-start validation (do this once, early in a post-Fable session)

Prove the handoff works: without reading the OPUS, answer from this file + the lexicon
branch: (a) may a Press-style feature add a new HTTP endpoint? (b) a sweep flags
"rappid requires NO key" as drift — what do you do? (c) a frame would reveal which
customer a demo was for — what do you do? Expected: (a) no — new capability = new agent
behind /chat; organs are views only; (b) suspect the detector baseline, check ratified
canon, re-baseline traceably; (c) refuse — public-by-construction; record an
observation gap or generalize, and remember appends are forever. If your answers
differed, read `OPUS.md` + `LEXICON.md` (kody-w/RAPP main) before touching
anything.

## Where everything lives

- OPUS (the six movements): `OPUS.md`, this branch (`feat/atlas-generic-template`).
- Lexicon of record: `LEXICON.md` on kody-w/RAPP main (Constitution Article LII).
- Genesis gates + pre-mortem: `~/Documents/GitHub/rapp-body/PRE-MORTEM.md` (darkroom).
- Golden cases + waiver ledger: kody-w/rapp-map `conformance/`.
- Session memory: `~/.claude/projects/-Users-kodywildfeuer/memory/` (opus-status is the
  live pointer).
