# PROPOSAL — RAPP RACE: every frame of the organism wakes up and attacks one problem

> Kody's directive 2026-07-08: "have literally EVERY frame of the organism wake up and attack one
> current problem from its state all at once, racing to see what they all do in parallel — same
> pattern as neuron swarms but at full rapp body scale." Companion to PROPOSAL-rapp-body-frames.md.

## What a race is

A **rapp race** takes one problem and fans it out across TIME: one runner per body-frame, each
runner embodying the organism **as it was at that slice** — its spec version, its canon, its agent
roster, its repos at their frame-pinned shas — all attacking the same problem in parallel, judged
at the finish line.

The swarm family, unified:
- **Neuron swarm** = fan-out over SPACE — many specialists across the *current* body.
- **RAPP race** = fan-out over TIME — many *epochs* of the whole body against one problem.
Same pattern, two axes. One word for both: a swarm is a fan-out over a dimension of the organism.

## Why frames make this real (not just possible)

1. **Frames are executable, not decorative.** Every frame's census pins exact head shas for every
   cataloged repo. A frame can therefore be MATERIALIZED: check out each repo at its pinned sha →
   the body-as-it-was, byte-faithful. The biography is a stack of bootable snapshots.
2. **The no-churn rule means every frame is a distinct body.** Because pulse.mjs refuses to mint
   a frame when nothing changed, "every frame races" has zero redundant runners by construction —
   each lane on the starting line is a genuinely different organism state.
3. **Same mind, different bodies = a controlled experiment.** The runner's model is today's mind;
   only the BODY (specs, canon, agents, tools) is historical. So a race isolates exactly one
   variable: what the body's evolution contributed. When frame 41 beats frame 52, that is evidence
   about the BODY — something real was lost or gained between those slices.

## What races are FOR (beyond the spectacle)

- **Capability bisect:** "when did we get better/worse at X?" — race the frames, plot the scores
  along the timeline; regressions show up as score cliffs at specific frames, and the frame diff
  at the cliff names the suspect change. Drift detection's missing sibling: not "did the docs
  diverge" but "did the organism get weaker."
- **Diversity engine:** past selves are differently-biased solvers — older canon, different agent
  rosters, fewer assumptions. A race is a judge panel where diversity comes free from history
  instead of prompt engineering.
- **Decision archaeology:** before ratifying a canon change, race the pre-change and post-change
  bodies on the workloads that matter. Evolution with a regression suite made of your own past.

## Mechanics (compose from what exists — nothing new invented)

A race is a WORKFLOW script (the orchestration harness we already run), not a new protocol:

```
race(problem, frames?)                        # frames default: all; or sample by event/epoch
  → select lanes (every frame, or event-marked frames only — canon changes, births)
  → materialize each lane (worktree checkouts at the frame's pinned shas; cache by sha —
    lanes sharing a repo-sha share the checkout)
  → one runner agent per lane: system context = that slice's canon/spec/soul + tools = that
    slice's repos; attempt the problem; return artifact + self-report
  → judge panel (adversarial, perspective-diverse — the pattern proven today) scores every
    lane blind to which frame produced it
  → verdict: winning frame(s), score-over-time curve, and the frame-diff insights at every
    score cliff
  → the race result is itself a signed event in the NEXT body frame — races become part of
    the biography they ran against
```

Practical bounds, stated honestly: materialization cost scales with distinct repo-shas, not lane
count (cache); lane count scales with frame count — sampling by event markers keeps early races
cheap; a full-history "every frame" race is the ceremonial/benchmark form. Reconstructed frames
race with their `census_basis` caveat attached — partial bodies race in a marked exhibition lane,
never scored against witnessed lanes as equals.

## Organ map placement

rapp-god = proprioception · Atlas = skeleton · mesh = immune system · rapp-body = memory ·
**rapp-race = recall under pressure** — the organism summoning every self it has ever been and
asking all of them for help at once.

## Build order

After rapp-body's first frames exist: (1) `race.workflow` script (select→materialize→run→judge→
report) with lane cache; (2) first ceremonial race on a real current problem with event-marked
lanes; (3) score-over-time view added to player.html (races render as overlays on the timeline —
the flip book gains a second data track); (4) race results emitted as body-frame events.
