# PROPOSAL — The RAPP body's own frames: a public, signed biography of the whole organism

> Companion to PROPOSAL-twin-stack-coherence.md. Kody's directive 2026-07-08: "think of this RAPP
> BODY as its OWN global frame … its own repo … so we can literally see the body change over time
> through these frames that are published globally publicly."

## The idea, placed in the ontology

A twin already has this: `frames/` in kody-w/twin is a SHA-signed, chained, public biography of a
BEING. The move is to recognize that **the RAPP ecosystem is itself a being** — the organism — and
give it the exact same organ. Not a new primitive: the twin frame pattern applied at body scale
(CRAWL rule 6 — compose, don't invent). The body gets bones (the canonical spec — it has this),
an immune system (PLAN-drift-immunity — proposed today), and now a **biography**: frames.

One sentence: **kody-w/twin/frames is the biography of Kody's twin; the body-frames repo is the
biography of RAPP itself.** Same format, same chain discipline, same public-by-construction rule.

## The repo

`kody-w/rapp-body` (working name; the organism's own estate). Contents:

```
rapp-body/
├── frames/                     # the biography — append-only, chained, signed
│   └── 2026/07/08-<seq>.frame.json
├── body.html                   # single-file timeline viewer — watch the body change
├── vitals.json                 # latest-frame pointer + current health rollup (static API)
├── tools/pulse.mjs             # the frame-taker (zero-dep, same class as build-atlas.mjs)
└── .github/workflows/pulse.yml # daily + event-triggered
```

## What a body-frame captures (the organism's vital signs at an instant)

Conform to the twin frame schema (kody-w/twin/frames is the format authority; extend with a
`body` payload, never fork the envelope):

- **chain**: `prev` = sha256 of the previous frame (append-only, unforgeable ordering);
  identity per rapp-eternity/1.0 — content-address first, keypair signature OPTIONAL.
- **skeleton**: ecosystem-spec version + sha256 (all three homes: RAPP root, rapp-god, rapp-map —
  equality is itself a vital sign); spine registry.json + foundation.json shas.
- **census**: every cataloged repo → default-branch head sha, pushed_at, reachable? (new repos
  since last frame and vanished repos are FIRST-CLASS events — today's "repo outran the catalog"
  drift class becomes visible the day it happens).
- **vitals**: latest ecosystem-sync verdict + drift counts by severity; open `drift()` issue
  census (count + age); estate-Atlas badge state (once Tier 2 lands); rapp-god status.
- **events since last frame**: canon ratifications, spec version bumps, drift issues opened/closed,
  postings planted (new doormen/front doors), agents published to RAR.

Each frame is small, diffable JSON. `body.html` renders the chain as a timeline — the body growing
repos, shedding drift, bumping canon — literally watchable, globally public, zero servers
(rapp-static-api/1.0: the repo IS the API).

## Why this closes the loop (frames × immunity × coherence)

- **Drift becomes history, not just alerts.** The immune system (sweeps) detects; the frames
  REMEMBER. "When did rapp-eternity appear and how long until the catalog registered it?" is a
  frame diff, not an archaeology dig.
- **The organism gets the same integrity guarantee as a twin.** Nobody — including us — can
  quietly rewrite what the body looked like last month. Same reason twin frames exist: an
  unforgeable biography is what makes the being trustworthy.
- **It's the demo of the whole thesis.** RAPP's story is "beings made of data with public bones
  and signed biographies." The ecosystem practicing this on ITSELF is the most credible telling:
  the body is its own first citizen.
- **DOG/GOD applies cleanly:** the body-frames repo is the organism's DOG — its public reflection.
  Any private operational state (tokens, unpublished work) stays off-frame by construction, same
  law as every twin.

## The snake through time (the framing that locks the design)

Kody's directive: think of the ecosystem as **a snake slithering through time** — each frame a
cross-sectional SLICE of its existence, the full chain its worldline, cradle to grave, public on
GitHub as raw-loadable data. Three design consequences fall straight out:

1. **Identity is the worldline, not any slice.** No single frame IS the body — the chained
   sequence is. This is rapp-eternity applied at body scale: the content-addressed chain is the
   identity; a slice is just where you cut it. (Same reason a twin is its frames, not its latest
   state.)
2. **Witnessed vs reconstructed frames — the cradle is reachable.** Frames taken from today
   forward are `witnessed` (the pulse observed the body live). But git already remembers: every
   repo's history lets us RECONSTRUCT approximate slices backwards — spec versions, repo births,
   canon ratifications — as `reconstructed` frames, marked as such, chained before the genesis
   witness. The flip book then genuinely opens at the cradle: the actual birth of RAPP, not the
   day we started filming. (Honesty rule: reconstructed frames carry their evidence — the commit
   shas they were derived from — and never claim witness.)
3. **The player is the product.** `player.html` — single-file, zero-server, loads the whole chain
   from raw.githubusercontent (CORS-open, per rapp-static-api/1.0):
   - Walks the chain (latest ← `prev` links, or a `frames/index.json` manifest for one-fetch load).
   - Renders each slice as a **visual body**, not a table: repos as organs/cells (sized by
     activity, clustered by spine layer), drift as inflammation coloring, spec version as age
     rings, new organs appearing, deprecated ones fading — so playback literally shows a body
     being born, growing, getting older, transforming.
   - **Flip-book controls:** play/pause/scrub/speed, frame-diff highlighting (what changed since
     the previous slice), jump-to-event (ratifications, births, drift storms).
   - Same artifact discipline as atlas.html/the OS generator: self-contained, light/dark, works
     from file:// and Pages.

Cradle to grave includes the grave: the twin ESTATE.md heirloom ceremony applies at body scale —
the biography is the part of the organism built to outlive its operator. Succession of the body's
frames repo (who may append after) is an ESTATE.md profile, not a new invention.

## Build notes (small, after the drift fixes land)

1. Frame-taker `pulse.mjs`: reads spec homes + repo census via GitHub API + latest sweep/issue
   state; emits + chains the frame; ~the same zero-dep discipline as build-atlas.mjs. Much of the
   harvest logic IS Atlas — reuse, don't duplicate (an Atlas `assets.json` can be an input).
2. Cadence: daily cron pulse + workflow_dispatch + triggered on canon events (same triggers as the
   immunity plan's mandatory sweeps — one event model for both).
3. First frame = genesis frame: today's post-fix state, referencing the 13-finding sweep and the
   reconciliation — the biography opens with the day the body got its immune system.
4. Register in the catalog at birth (per today's lesson) and in the spine map layer:
   rapp-god = proprioception, Atlas = skeleton check, mesh = immune system, **rapp-body = memory**.
