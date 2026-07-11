#!/usr/bin/env python3
"""Crawl the RAPP spine through a deterministic, read-only graph."""

import argparse
import concurrent.futures
import hashlib
import json
import re
import sys
import urllib.request
from collections import Counter, defaultdict, deque
from pathlib import Path


ROOT = Path(__file__).resolve().parent
REMOTE = "https://raw.githubusercontent.com/kody-w/rapp-spine/main/registry.json"
REMOTE_CRAWL = "https://raw.githubusercontent.com/kody-w/rapp-spine/main/crawl.json"
REMOTE_BASE = "https://raw.githubusercontent.com/kody-w/rapp-spine/main/"
LOCAL = str(ROOT / "registry.json")
LOCAL_CRAWL = ROOT / "crawl.json"
CRAWL_SPEC = "rapp-spine/1.1"
GRAPH_SPEC = "rapp-crawl-graph/1.0"
PLAN_SPEC = "rapp-crawl-plan/1.0"
PLAN_TEMPLATE_SPEC = "rapp-crawl-plan-template/1.0"
RECEIPT_SPEC = "rapp-crawl-receipt/1.0"
_STOP = set("a an the i to my of for and or is are with no on in it this that you your me we so".split())
_TRAVERSAL_RELATIONS = {
    "routes_to",
    "uses_artifact",
    "owned_by",
    "in_layer",
    "supported_by",
    "has_issue",
    "canonical_wire",
}
_CANONICAL_WIRE_REQUIREMENTS = [
    ("kody-w/leviathan", "leviathan/1.0", "rapp-fleet-chat/1.0")
]


def _load_url(url):
    request = urllib.request.Request(url, headers={"User-Agent": "rapp-spine/1.1"})
    with urllib.request.urlopen(request, timeout=20) as response:
        return json.loads(response.read())


def load(remote=False):
    """Load the backward-compatible registry/router document."""
    if remote:
        return _load_url(REMOTE)
    with open(LOCAL, encoding="utf-8") as handle:
        return json.load(handle)


def load_crawl(remote=False):
    """Load the rapp-spine/1.1 exact crawl graph."""
    if remote:
        document = _load_url(REMOTE_CRAWL)
    else:
        with LOCAL_CRAWL.open(encoding="utf-8") as handle:
            document = json.load(handle)
    validate_crawl_document(document)
    return document


def validate_crawl_document(crawl_document):
    """Fail closed unless the document is the supported crawl and graph schema."""
    if not isinstance(crawl_document, dict):
        raise ValueError("crawl document must be an object")
    if crawl_document.get("spec") != CRAWL_SPEC:
        raise ValueError(
            f"unsupported crawl spec: {crawl_document.get('spec')!r}; expected {CRAWL_SPEC}"
        )
    graph = crawl_document.get("graph")
    if not isinstance(graph, dict) or graph.get("spec") != GRAPH_SPEC:
        raise ValueError(f"unsupported graph schema; expected {GRAPH_SPEC}")
    nodes = graph.get("nodes")
    relations = graph.get("relations")
    order = graph.get("traversal_order")
    root_id = graph.get("root_id")
    if not isinstance(nodes, list) or not isinstance(relations, list):
        raise ValueError("graph nodes and relations must be arrays")
    if not isinstance(order, list) or not isinstance(root_id, str):
        raise ValueError("graph traversal_order/root_id shape is invalid")
    node_ids = []
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get("id"), str):
            raise ValueError("every graph node must have a string id")
        if not isinstance(node.get("type"), str):
            raise ValueError(f"{node['id']} must have a string type")
        node_ids.append(node["id"])
    node_id_set = set(node_ids)
    if len(node_ids) != len(node_id_set):
        raise ValueError("graph node IDs must be unique")
    if len(order) != len(set(order)) or set(order) != node_id_set:
        raise ValueError("graph.traversal_order must contain every graph node exactly once")
    if root_id not in node_id_set:
        raise ValueError("graph root_id does not reference a node")
    relation_keys = set()
    for item in relations:
        if (
            not isinstance(item, dict)
            or not isinstance(item.get("type"), str)
            or item.get("from") not in node_id_set
            or item.get("to") not in node_id_set
        ):
            raise ValueError(f"invalid or dangling graph relation: {item!r}")
        relation_keys.add((item["from"], item["type"], item["to"]))
    for node in nodes:
        if node.get("type") == "evidence" and (
            node["id"],
            "uses_artifact",
            "artifact:foundation.json",
        ) not in relation_keys:
            raise ValueError(
                f"{node['id']} lacks its foundation artifact dependency"
            )
    protocols_by_identity = {
        (node.get("repo", "").lower(), node.get("canonical_protocol_identity")): node
        for node in nodes
        if node.get("type") == "protocol"
    }
    for repo, legacy_identity, canonical_identity in _CANONICAL_WIRE_REQUIREMENTS:
        legacy = protocols_by_identity.get((repo.lower(), legacy_identity))
        canonical = protocols_by_identity.get((repo.lower(), canonical_identity))
        if (
            legacy is None
            or canonical is None
            or (
                legacy["id"],
                "canonical_wire",
                canonical["id"],
            )
            not in relation_keys
        ):
            raise ValueError(
                f"missing canonical wire relation: {repo} "
                f"{legacy_identity} -> {canonical_identity}"
            )

    full_plan = crawl_document.get("plans", {}).get("full")
    if not isinstance(full_plan, dict):
        raise ValueError("plans.full is required")
    if full_plan.get("spec") != PLAN_TEMPLATE_SPEC:
        raise ValueError(
            f"unsupported full-plan template schema; expected {PLAN_TEMPLATE_SPEC}"
        )
    if full_plan.get("produces") != PLAN_SPEC:
        raise ValueError("plans.full does not produce the supported plan schema")
    if full_plan.get("graph_spec") != CRAWL_SPEC:
        raise ValueError("plans.full.graph_spec does not match the crawl spec")
    if full_plan.get("mode") != "full" or full_plan.get("read_only") is not True:
        raise ValueError("plans.full must declare a read-only full crawl")
    if full_plan.get("node_ids") != order:
        raise ValueError("plans.full.node_ids must exactly equal graph.traversal_order")
    if not isinstance(crawl_document.get("router"), list) or not isinstance(
        crawl_document.get("registry"), list
    ):
        raise ValueError("crawl router and registry display fields must be arrays")
    if crawl_document.get("safety", {}).get("mode") != "read_only":
        raise ValueError("crawl safety.mode must be read_only")
    return crawl_document


def validate_plan(plan, crawl_document=None):
    """Validate a generated plan before source probing or receipt creation."""
    if not isinstance(plan, dict) or plan.get("spec") != PLAN_SPEC:
        raise ValueError(f"unsupported plan schema; expected {PLAN_SPEC}")
    if plan.get("graph_spec") != CRAWL_SPEC:
        raise ValueError("plan.graph_spec does not match the supported crawl spec")
    if plan.get("mode") not in {"full", "scoped"} or plan.get("read_only") is not True:
        raise ValueError("plan must declare a read-only full or scoped crawl")
    expected = plan.get("expected_node_ids")
    visited = plan.get("node_ids")
    if not isinstance(expected, list) or not isinstance(visited, list):
        raise ValueError("plan node inventories must be arrays")
    if len(expected) != len(set(expected)) or len(visited) != len(set(visited)):
        raise ValueError("plan node inventories must not contain duplicates")
    if not set(visited).issubset(expected):
        raise ValueError("plan visited nodes must be a subset of expected nodes")
    batches = plan.get("batches")
    read_targets = plan.get("read_targets")
    if not isinstance(batches, list) or not isinstance(read_targets, list):
        raise ValueError("plan batches and read_targets must be arrays")
    if plan.get("batch_count") != len(batches):
        raise ValueError("plan batch_count does not match batches")
    flattened = []
    for index, batch in enumerate(batches, 1):
        if (
            not isinstance(batch, dict)
            or batch.get("index") != index
            or not isinstance(batch.get("node_ids"), list)
        ):
            raise ValueError("plan batch shape/order is invalid")
        flattened.extend(batch["node_ids"])
    if flattened != expected:
        raise ValueError("plan batches must exactly partition expected_node_ids")
    for source in read_targets:
        if (
            not isinstance(source, dict)
            or not isinstance(source.get("key"), str)
            or not isinstance(source.get("node_id"), str)
            or not isinstance(source.get("role"), str)
            or source.get("required") not in {True, False}
        ):
            raise ValueError("plan read target shape is invalid")
        if source["node_id"] not in visited:
            raise ValueError("plan read target belongs to an unvisited node")
    if crawl_document is not None:
        validate_crawl_document(crawl_document)
        graph_ids = set(graph_index(crawl_document))
        if not set(expected).issubset(graph_ids):
            raise ValueError("plan references nodes outside the crawl graph")
        if plan["mode"] == "full" and expected != crawl_document["graph"]["traversal_order"]:
            raise ValueError("full plan does not exactly cover graph.traversal_order")
    return plan


def _toks(value):
    return {
        word
        for word in re.findall(r"[a-z0-9]+", value.lower())
        if word not in _STOP and len(word) > 2
    }


def match(spine, situation, n=3):
    """Preserve the rapp-spine/1.0 fuzzy router selection behavior."""
    query = _toks(situation)
    scored = []
    for route in spine["router"]:
        haystack = _toks(
            route["situation"] + " " + route["why"] + " " + " ".join(route["use"])
        )
        scored.append((len(query & haystack), route))
    scored.sort(key=lambda item: -item[0])
    return [route for score, route in scored[:n] if score > 0]


def print_spine(spine):
    print(f"\n  THE RAPP SPINE ({spine['spec']})  ·  situation -> layer -> protocol\n")
    print("  COLUMN:", " -> ".join(spine["layers_order"]))
    print("\n  ROUTER:")
    for route in spine["router"]:
        print(f"   • {route['situation']}")
        print(f"       -> {', '.join(route['use'])}")
    print(
        f"\n  ({len(spine['registry'])} protocols, {len(spine['router'])} routes. "
        '`crawl.py "<situation>"` to route.)\n'
    )


def graph_index(crawl_document):
    nodes = crawl_document["graph"]["nodes"]
    return {node["id"]: node for node in nodes}


def route_nodes_for_hits(crawl_document, hits):
    by_situation = {
        node["display"]["situation"]: node
        for node in crawl_document["graph"]["nodes"]
        if node["type"] == "route"
    }
    missing = [hit["situation"] for hit in hits if hit["situation"] not in by_situation]
    if missing:
        raise ValueError("fuzzy route has no exact graph node: " + ", ".join(missing))
    return [by_situation[hit["situation"]] for hit in hits]


def _closure(crawl_document, start_ids):
    adjacency = defaultdict(list)
    for item in crawl_document["graph"]["relations"]:
        if item["type"] in _TRAVERSAL_RELATIONS:
            adjacency[item["from"]].append(item["to"])
    seen = set()
    queue = deque(start_ids)
    while queue:
        node_id = queue.popleft()
        if node_id in seen:
            continue
        seen.add(node_id)
        queue.extend(adjacency[node_id])
    return seen


def _source_key(node_id, source):
    return f"{node_id}|{source['role']}|{source.get('target') or '<unresolved>'}"


def plan_sources(crawl_document, node_ids):
    nodes = graph_index(crawl_document)
    records = []
    for node_id in node_ids:
        node = nodes[node_id]
        for source in node["sources"]:
            records.append(
                {
                    "key": _source_key(node_id, source),
                    "node_id": node_id,
                    "node_type": node["type"],
                    **source,
                }
            )
    return records


def build_plan(
    crawl_document,
    mode="full",
    route_ids=None,
    situation=None,
    batch_size=25,
    batch=None,
):
    """Build a deterministic full or exact-route-closure plan."""
    validate_crawl_document(crawl_document)
    if batch_size < 1:
        raise ValueError("batch_size must be at least 1")
    graph = crawl_document["graph"]
    order = list(graph["traversal_order"])
    node_ids = set(graph_index(crawl_document))
    if len(order) != len(set(order)) or set(order) != node_ids:
        raise ValueError("graph.traversal_order must contain every graph node exactly once")
    if mode == "full":
        expected = order
        selected_routes = []
    elif mode == "scoped":
        selected_routes = list(route_ids or [])
        if not selected_routes:
            raise ValueError("scoped crawl requires at least one exact route ID")
        closure = _closure(crawl_document, selected_routes)
        closure.add(graph["root_id"])
        for issue in crawl_document.get("issues", []):
            if closure.intersection(issue.get("related_node_ids", [])):
                closure.add(issue["id"])
        expected = [graph["root_id"]]
        expected.extend(node_id for node_id in selected_routes if node_id not in expected)
        expected.extend(
            node_id for node_id in order if node_id in closure and node_id not in expected
        )
    else:
        raise ValueError(f"unknown crawl mode: {mode}")

    batches = []
    for offset in range(0, len(expected), batch_size):
        batches.append(
            {
                "index": len(batches) + 1,
                "node_ids": expected[offset : offset + batch_size],
            }
        )
    if batch is not None:
        if batch < 1 or batch > len(batches):
            raise ValueError(f"batch must be between 1 and {len(batches)}")
        visited = list(batches[batch - 1]["node_ids"])
    else:
        visited = list(expected)

    return {
        "spec": PLAN_SPEC,
        "graph_spec": crawl_document["spec"],
        "mode": mode,
        "read_only": True,
        "situation": situation,
        "route_ids": selected_routes,
        "batch_size": batch_size,
        "batch_count": len(batches),
        "selected_batch": batch,
        "expected_node_ids": expected,
        "node_ids": visited,
        "batches": batches,
        "read_targets": plan_sources(crawl_document, visited),
        "forbidden_actions": list(crawl_document["safety"]["forbidden_actions"]),
    }


def _local_target(target, remote):
    if remote:
        return None
    if target.startswith(REMOTE_BASE):
        candidate = (ROOT / target.removeprefix(REMOTE_BASE)).resolve()
    elif "://" not in target:
        candidate = (ROOT / target).resolve()
    else:
        return None
    try:
        candidate.relative_to(ROOT)
    except ValueError:
        return None
    return candidate


def read_target(target, remote=False, timeout=20):
    """Read an exact target with GET semantics; never execute its contents."""
    local = _local_target(target, remote)
    if local is not None:
        try:
            return local.read_bytes()
        except OSError:
            return None
    if not target.startswith(("https://", "http://")):
        return None
    try:
        request = urllib.request.Request(
            target,
            method="GET",
            headers={"User-Agent": "rapp-spine/1.1 read-only crawler"},
        )
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except Exception:
        return None


def probe_sources(plan, remote=False, workers=12):
    """Read every exact source target in a plan, deduplicating network reads."""
    validate_plan(plan)
    targets = sorted(
        {
            source["target"]
            for source in plan["read_targets"]
            if source.get("target")
        }
    )
    content = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        for target, body in zip(
            targets,
            executor.map(lambda value: read_target(value, remote=remote), targets),
        ):
            content[target] = body

    results = {}
    for source in plan["read_targets"]:
        key = source["key"]
        target = source.get("target")
        if not target:
            results[key] = {
                "status": "unresolved",
                "target": None,
                "integrity": "not_checkable",
            }
            continue
        body = content.get(target)
        if body is None:
            results[key] = {
                "status": "unreadable",
                "target": target,
                "integrity": "not_checkable",
            }
            continue
        actual = hashlib.sha256(body).hexdigest()
        expected = source.get("sha256")
        integrity = "verified" if expected == actual else "mismatch" if expected else "not_pinned"
        results[key] = {
            "status": "read",
            "target": target,
            "bytes": len(body),
            "sha256": actual,
            "integrity": integrity,
        }
    return results


def unprobed_sources(plan):
    validate_plan(plan)
    results = {}
    for source in plan["read_targets"]:
        results[source["key"]] = {
            "status": "unresolved" if not source.get("target") else "not_read",
            "target": source.get("target"),
            "integrity": "not_checkable",
        }
    return results


def graph_health(crawl_document):
    graph = crawl_document["graph"]
    nodes = graph_index(crawl_document)
    dangling = [
        item
        for item in graph["relations"]
        if item["from"] not in nodes or item["to"] not in nodes
    ]
    adjacency = defaultdict(list)
    for item in graph["relations"]:
        adjacency[item["from"]].append(item["to"])
    root_id = graph.get("root_id")
    seen = set()
    queue = deque([root_id] if root_id in nodes else [])
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        queue.extend(adjacency[current])
    return {
        "root_missing": root_id not in nodes,
        "dangling_relations": dangling,
        "orphan_node_ids": sorted(set(nodes) - seen),
    }


def build_receipt(crawl_document, plan, source_results):
    """Build a machine-readable completion proof with independent dimensions."""
    validate_crawl_document(crawl_document)
    validate_plan(plan, crawl_document)
    nodes = graph_index(crawl_document)
    expected = plan["expected_node_ids"]
    visited = plan["node_ids"]
    missing = [node_id for node_id in expected if node_id not in set(visited)]
    expected_types = Counter(nodes[node_id]["type"] for node_id in expected)
    visited_types = Counter(nodes[node_id]["type"] for node_id in visited)
    inventory_complete = not missing

    health = graph_health(crawl_document)
    graph_complete = (
        not health["root_missing"]
        and not health["dangling_relations"]
        and not health["orphan_node_ids"]
    )

    source_counts = Counter()
    source_failures = []
    integrity_counts = Counter()
    expected_required_sources = [
        source
        for source in plan_sources(crawl_document, expected)
        if source["required"]
    ]
    visited_required_keys = {
        source["key"] for source in plan["read_targets"] if source["required"]
    }
    for source in expected_required_sources:
        if source["key"] in visited_required_keys:
            result = source_results.get(
                source["key"],
                {"status": "not_read", "integrity": "not_checkable"},
            )
        else:
            result = {"status": "not_read", "integrity": "not_checkable"}
        source_counts[result["status"]] += 1
        integrity_counts[result.get("integrity", "not_checkable")] += 1
        if result["status"] != "read" or result.get("integrity") == "mismatch":
            source_failures.append(
                {
                    "node_id": source["node_id"],
                    "role": source["role"],
                    "target": source.get("target"),
                    "status": result["status"],
                    "integrity": result.get("integrity"),
                }
            )
    source_complete = inventory_complete and not source_failures

    issue_nodes = [
        nodes[node_id]
        for node_id in expected
        if nodes[node_id]["type"] == "issue"
    ]
    blocking_issues = [
        node["display"] for node in issue_nodes if node["display"]["blocking"]
    ]
    known_gaps_complete = not blocking_issues

    operational_nodes = [nodes[node_id] for node_id in expected]
    nonconformant = [
        node["id"]
        for node in operational_nodes
        if node["conformance"] == "nonconformant"
    ]
    unavailable = [
        node["id"]
        for node in operational_nodes
        if node["lifecycle"] == "unpublished"
    ]
    deprecated = [
        node["id"]
        for node in operational_nodes
        if node["lifecycle"] == "deprecated"
    ]
    not_assessed = sum(
        node["conformance"] == "not_assessed" for node in operational_nodes
    )
    operational_healthy = not nonconformant and not unavailable

    complete = (
        inventory_complete
        and graph_complete
        and source_complete
        and known_gaps_complete
        and operational_healthy
    )
    unexpected_source_failure = any(
        failure["status"] == "unreadable" or failure["integrity"] == "mismatch"
        for failure in source_failures
    )
    passed = graph_complete and not unexpected_source_failure
    return {
        "spec": RECEIPT_SPEC,
        "graph_spec": crawl_document["spec"],
        "mode": plan["mode"],
        "read_only": True,
        "selected_batch": plan["selected_batch"],
        "completion": {
            "inventory_graph_coverage": {
                "expected_nodes": len(expected),
                "visited_nodes": len(visited),
                "expected_by_type": dict(sorted(expected_types.items())),
                "visited_by_type": dict(sorted(visited_types.items())),
                "missing_node_ids": missing,
                "complete": inventory_complete,
            },
            "graph_integrity": {
                **health,
                "complete": graph_complete,
            },
            "source_integrity_availability": {
                "expected_required_sources": len(expected_required_sources),
                "visited_required_sources": len(visited_required_keys),
                "counts": dict(sorted(source_counts.items())),
                "integrity": dict(sorted(integrity_counts.items())),
                "failures": source_failures,
                "complete": source_complete,
            },
            "known_gaps": {
                "structured": len(issue_nodes),
                "blocking": len(blocking_issues),
                "blocking_issue_ids": [issue["id"] for issue in blocking_issues],
                "complete": known_gaps_complete,
            },
            "operational_conformance": {
                "nonconformant_node_ids": nonconformant,
                "unavailable_node_ids": unavailable,
                "deprecated_node_ids": deprecated,
                "not_assessed": not_assessed,
                "healthy": operational_healthy,
            },
            "complete": complete,
        },
        "passed": passed,
        "complete": complete,
    }


def print_plan(crawl_document, plan, receipt):
    nodes = graph_index(crawl_document)
    print(
        f"\n  RAPP SPINE {plan['mode'].upper()} CRAWL · {len(plan['node_ids'])}/"
        f"{len(plan['expected_node_ids'])} nodes · READ-ONLY\n"
    )
    for batch in plan["batches"]:
        marker = "*" if plan["selected_batch"] in (None, batch["index"]) else " "
        print(f"  {marker} batch {batch['index']}/{plan['batch_count']} ({len(batch['node_ids'])} nodes)")
        if plan["selected_batch"] is None or plan["selected_batch"] == batch["index"]:
            for node_id in batch["node_ids"]:
                node = nodes[node_id]
                print(
                    f"      {node_id}  [{node['type']} · {node['status']} · "
                    f"{node['materiality']}]"
                )
    completion = receipt["completion"]
    print("\n  COMPLETION RECEIPT:")
    print(
        "   inventory/graph:",
        "complete" if completion["inventory_graph_coverage"]["complete"] else "partial",
    )
    print(
        "   source integrity/availability:",
        "complete"
        if completion["source_integrity_availability"]["complete"]
        else "incomplete",
    )
    print("   known blocking gaps:", completion["known_gaps"]["blocking"])
    print(
        "   operational/conformance:",
        "healthy" if completion["operational_conformance"]["healthy"] else "degraded",
    )
    print(f"   overall complete: {str(receipt['complete']).lower()}\n")


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("situation", nargs="*")
    parser.add_argument("--remote", action="store_true")
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--layer")
    parser.add_argument("--collisions", action="store_true")
    parser.add_argument("--full", action="store_true", help="explicit exhaustive crawl")
    parser.add_argument("--plan", action="store_true", help="build exact scoped crawl plan")
    parser.add_argument(
        "--receipt",
        action="store_true",
        help="emit the machine-readable completion receipt",
    )
    parser.add_argument("--batch-size", type=int, default=25)
    parser.add_argument("--batch", type=int)
    parser.add_argument(
        "--no-probe",
        action="store_true",
        help="plan only; do not read exact source targets",
    )
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    situation = " ".join(args.situation).strip()

    if args.layer or args.collisions:
        spine = load(args.remote)
        if args.layer:
            matches = [
                layer
                for layer in spine["layers"]
                if args.layer.lower() in layer["layer"].lower()
            ]
            if args.as_json:
                print(json.dumps(matches, indent=2))
            else:
                for layer in matches:
                    print(
                        f"\n  {layer['layer']}\n  {layer['summary']}\n  protocols: "
                        f"{', '.join(layer['protocols'])}\n"
                    )
            return 0
        if args.as_json:
            print(json.dumps(spine["collisions_and_gaps"], indent=2))
        else:
            print("\n  COLLISIONS & GAPS the spine resolves:\n")
            for collision in spine["collisions_and_gaps"]:
                print(f"   - {collision}\n")
        return 0

    if args.full and args.plan:
        raise SystemExit("--full and --plan are mutually exclusive")
    if args.full and situation:
        raise SystemExit("--full does not accept a scoped situation")
    if not situation and not args.full:
        if args.plan or args.receipt or args.batch is not None or args.no_probe:
            raise SystemExit("use --full for an exhaustive plan or provide a scoped situation")
        print_spine(load(args.remote))
        return 0

    planning = args.full or args.plan or args.receipt
    if not planning and (
        args.batch is not None or args.no_probe or args.batch_size != 25
    ):
        raise SystemExit("--batch, --batch-size, and --no-probe require --full or --plan")
    if not planning:
        spine = load(args.remote)
        hits = match(spine, situation)
        if args.as_json:
            print(json.dumps(hits, indent=2))
            return 0
        if not hits:
            print(
                f"\n  No direct route for: {situation!r}\n"
                "  Crawl the whole spine: `python crawl.py --full`\n"
            )
            return 0
        print(f"\n  CRAWLING THE SPINE for: {situation!r}\n")
        for route in hits:
            print(f"   → USE: {', '.join(route['use'])}")
            print(f"     situation: {route['situation']}")
            print(f"     why: {route['why']}\n")
        return 0

    crawl_document = load_crawl(args.remote)
    if args.full:
        mode = "full"
        route_ids = None
    else:
        hits = match(crawl_document, situation, n=1)
        if not hits:
            raise SystemExit(f"no route matched scoped situation: {situation!r}")
        mode = "scoped"
        route_ids = [node["id"] for node in route_nodes_for_hits(crawl_document, hits)]
    plan = build_plan(
        crawl_document,
        mode=mode,
        route_ids=route_ids,
        situation=situation or None,
        batch_size=args.batch_size,
        batch=args.batch,
    )
    results = unprobed_sources(plan) if args.no_probe else probe_sources(plan, args.remote)
    receipt = build_receipt(crawl_document, plan, results)

    if args.receipt:
        print(json.dumps(receipt, indent=2))
    elif args.as_json:
        print(json.dumps({"plan": plan, "receipt": receipt}, indent=2))
    else:
        print_plan(crawl_document, plan, receipt)
    return 0 if receipt["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
