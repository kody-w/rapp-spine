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
