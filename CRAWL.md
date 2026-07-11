# How an AI crawls the spine

**“Crawl the spine” with no situation means an exhaustive, read-only traversal.** It does not mean “print the router” or “pick a few likely protocols.”

## Exhaustive crawl

1. Fetch `https://raw.githubusercontent.com/kody-w/rapp-spine/main/crawl.json`.
2. Confirm `spec == "rapp-spine/1.1"` and verify the recorded `registry.json` and `foundation.json` hashes.
3. Traverse every ID in `graph.traversal_order`. Graph node IDs and typed relations are authoritative.
4. Read every required `sources[]` target using GET only. Never execute an `entry_points[]` record unless `safe_for_crawl == true`; generated safe entries are read-only.
5. Include every registry protocol and repository node. A missing target is not permission to skip a node: record its structured issue as unresolved.
6. Emit a `rapp-crawl-receipt/1.0` separating:
   - inventory/graph coverage,
   - source integrity/availability,
   - known gaps,
   - operational/conformance health.
7. Call the crawl complete only when all four dimensions are complete.

Deterministic helper:

```bash
python3 crawl.py --full
python3 crawl.py --full --json
python3 crawl.py --full --batch-size 25 --batch 1
python3 crawl.py --full --receipt
```

Use `--no-probe` to emit the full deterministic plan without reading network sources. Its receipt is intentionally incomplete because sources were not read.

For backward compatibility, bare `python3 crawl.py` prints the whole spine summary. The exhaustive
AI phrase contract does not silently change that established CLI behavior.

## Scoped situation

Scoped routing remains supported:

1. Fuzzy-match the situation against the retained `router` display fields.
2. Select the matching typed `route:*` node.
3. Ignore fuzzy text after selection; follow that node's fixed `target_ids` and typed graph closure.
4. Apply the same read-only and receipt rules to the scoped plan.

```bash
python3 crawl.py "drive my LAN brainstems as one fleet"       # compatible display result
python3 crawl.py --json "drive my LAN brainstems as one fleet"
python3 crawl.py --plan "drive my LAN brainstems as one fleet"
python3 crawl.py --plan --json --no-probe "drive my LAN brainstems as one fleet"
```

`--layer`, `--collisions`, and `--remote` retain their compatible roles.

## JSON output shape

`--json` in full or scoped plan mode emits one wrapper object:

```json
{
  "plan": {"spec": "rapp-crawl-plan/1.0", "node_ids": [], "read_targets": []},
  "receipt": {
    "spec": "rapp-crawl-receipt/1.0",
    "completion": {
      "inventory_graph_coverage": {},
      "graph_integrity": {},
      "source_integrity_availability": {},
      "known_gaps": {},
      "operational_conformance": {},
      "complete": false
    }
  }
}
```

`crawl.json.plans.full` is a `rapp-crawl-plan-template/1.0` inventory template whose
`produces` field names `rapp-crawl-plan/1.0`; it is not itself a runtime plan. Actual
`rapp-crawl-plan/1.0` objects are emitted by `crawl.py` and include batching, expected/visited
node inventories, read targets, and safety fields.

`--receipt` emits the receipt object directly, without the outer `plan` / `receipt` wrapper.
Legacy `--json "<situation>"` still emits the compatible array of router display matches.

Stable `jq` paths:

```bash
python3 crawl.py --full --json --no-probe \
  | jq '.plan.node_ids | length'
python3 crawl.py --full --json --no-probe \
  | jq '.receipt.completion.source_integrity_availability.counts'
python3 crawl.py --plan --json --no-probe "governing law" \
  | jq '.receipt.completion.known_gaps.blocking'
python3 crawl.py --full --receipt --no-probe \
  | jq '.completion.known_gaps.blocking'
```

## Safety rule

The registry's historical `entry_point` strings include install, run, and deploy instructions. They remain present for compatibility but are `display_only` with `policy: "never_execute"` in the graph. Crawling reads evidence; it never installs, runs, deploys, mutates, or writes to an estate repository.
