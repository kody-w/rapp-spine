#!/usr/bin/env python3
"""Verify the rapp-spine/1.1 graph, sources, coverage, and completion semantics."""

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import sys
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

import crawl
import generate_crawl


RAW = "https://raw.githubusercontent.com"
SPINE = f"{RAW}/kody-w/rapp-spine/main"
SPINE_REPO_RAW = f"{RAW}/kody-w/rapp-spine"
SPINE_COMMIT_API = "https://api.github.com/repos/kody-w/rapp-spine/commits/main"
ESTATE = f"{RAW}/kody-w/rapp-map/main/estate-map.json"
ROOT = Path(__file__).resolve().parent
LOCAL_ESTATE = Path(
    os.environ.get("RAPP_ESTATE_MAP_PATH", ROOT.parent / "rapp-map" / "estate-map.json")
).expanduser()
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")


def get(url, timeout=20):
    try:
        request = urllib.request.Request(url, headers={"User-Agent": "rapp-spine/1.1 verifier"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.read()
    except Exception:
        return None


def load_json_source(
    url,
    local_path,
    prefer_local=False,
    allow_remote_fallback=True,
):
    path = Path(local_path).expanduser()
    if prefer_local:
        if path.exists():
            try:
                body = path.read_bytes()
                return (
                    json.loads(body),
                    {"kind": "local", "target": str(path)},
                    body,
                )
            except Exception:
                return (
                    None,
                    {"kind": "local", "target": str(path), "invalid": True},
                    None,
                )
        if not allow_remote_fallback:
            return (
                None,
                {"kind": "local", "target": str(path), "missing": True},
                None,
            )
    body = get(url)
    try:
        value = json.loads(body) if body else None
    except Exception:
        value = None
    return value, {"kind": "remote", "target": url}, body


def load_text_source(
    url,
    local_path,
    prefer_local=False,
    allow_remote_fallback=True,
):
    path = Path(local_path).expanduser()
    if prefer_local:
        if path.exists():
            try:
                body = path.read_bytes()
                return (
                    body.decode("utf-8"),
                    {"kind": "local", "target": str(path)},
                    body,
                )
            except Exception:
                return (
                    None,
                    {"kind": "local", "target": str(path), "invalid": True},
                    None,
                )
        if not allow_remote_fallback:
            return (
                None,
                {"kind": "local", "target": str(path), "missing": True},
                None,
            )
    body = get(url)
    try:
        value = body.decode("utf-8") if body else None
    except UnicodeDecodeError:
        value = None
    return value, {"kind": "remote", "target": url}, body


def decode_text(body):
    try:
        return body.decode("utf-8") if body is not None else None
    except UnicodeDecodeError:
        return None


def resolve_remote_commit():
    body = get(SPINE_COMMIT_API)
    try:
        sha = json.loads(body).get("sha") if body else None
    except Exception:
        sha = None
    return sha if isinstance(sha, str) and COMMIT_RE.fullmatch(sha) else None


def pin_spine_url(url, commit):
    repo_prefix = f"{SPINE_REPO_RAW}/"
    if isinstance(url, str) and isinstance(commit, str) and url.startswith(repo_prefix):
        ref_and_path = url.removeprefix(repo_prefix)
        _ref, separator, relative = ref_and_path.partition("/")
        if separator and relative:
            return f"{SPINE_REPO_RAW}/{commit}/{relative}"
    return url


def get_source(url, prefer_local=False):
    if not isinstance(url, str):
        return None
    if "://" not in url:
        candidate = (ROOT / url).resolve()
        try:
            candidate.relative_to(ROOT)
            return candidate.read_bytes()
        except (OSError, ValueError):
            return None
    if prefer_local and url.startswith(f"{SPINE}/"):
        path = ROOT / url.removeprefix(f"{SPINE}/")
        try:
            return path.read_bytes()
        except OSError:
            return None
    return get(url)


def _iter(value):
    """Yield every dict in a nested JSON structure."""
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _iter(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter(child)


def valid_sha256(value):
    return isinstance(value, str) and SHA256_RE.fullmatch(value) is not None


def add_drift(report, invariant, issue, **details):
    report["drift"].append({"invariant": invariant, "issue": issue, **details})


def fetch_targets(
    targets,
    prefer_local,
    spine_commit=None,
    preloaded=None,
):
    original_targets = sorted(set(targets))
    resolved_by_original = {
        target: pin_spine_url(target, spine_commit) for target in original_targets
    }
    content = dict(preloaded or {})
    unresolved_targets = sorted(
        {
            resolved
            for resolved in resolved_by_original.values()
            if resolved not in content
        }
    )
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as executor:
        for target, body in zip(
            unresolved_targets,
            executor.map(
                lambda value: get_source(value, prefer_local=prefer_local),
                unresolved_targets,
            ),
        ):
            content[target] = body
    return {
        original: content.get(resolved)
        for original, resolved in resolved_by_original.items()
    }


def validate_material_profiles(crawl_document):
    errors = []
    profiles = crawl_document.get("material_profiles", {})
    issues_by_node = defaultdict(list)
    for issue in crawl_document.get("issues", []):
        for node_id in issue.get("related_node_ids", []):
            issues_by_node[node_id].append(issue)

    for node in crawl_document.get("graph", {}).get("nodes", []):
        profile = profiles.get(node.get("material_profile"))
        if not isinstance(profile, dict):
            errors.append(f"{node.get('id')} has no declared material profile")
            continue
        required_roles = profile.get("required_source_roles", [])
        if node.get("required_source_roles") != required_roles:
            errors.append(f"{node['id']} required_source_roles drift from its profile")
        by_role = defaultdict(list)
        for source in node.get("sources", []):
            by_role[source.get("role")].append(source)
            target = source.get("target")
            if source.get("required") and target and not target.startswith(
                ("https://", "http://")
            ):
                errors.append(
                    f"{node['id']} required source {source.get('role')} is not an absolute URL"
                )
        for role in required_roles:
            required_matches = [
                source for source in by_role[role] if source.get("required") is True
            ]
            if not required_matches:
                errors.append(f"{node['id']} lacks required=true source role {role}")
                continue
            for source in required_matches:
                if source.get("availability") == "unresolved":
                    structured = [
                        issue
                        for issue in issues_by_node[node["id"]]
                        if issue.get("source_role") == role
                        and issue.get("source") == "generated.required_material"
                    ]
                    if not structured:
                        errors.append(
                            f"{node['id']} silently leaves required role {role} unresolved"
                        )
        for entry_point in node.get("entry_points", []):
            if entry_point.get("safe_for_crawl"):
                if not entry_point.get("read_only"):
                    errors.append(f"{node['id']} marks a writable entry point safe")
                if entry_point.get("method") not in {"GET", "HEAD"}:
                    errors.append(f"{node['id']} marks a non-read method safe")
                if not entry_point.get("target"):
                    errors.append(f"{node['id']} has a safe entry point without a target")
            elif entry_point.get("kind") == "display_only":
                if entry_point.get("policy") != "never_execute":
                    errors.append(f"{node['id']} display entry point lacks never_execute policy")
    return errors


def validate_route_integrity(crawl_document, registry):
    errors = []
    nodes = {
        node["id"]: node for node in crawl_document.get("graph", {}).get("nodes", [])
    }
    route_nodes = [node for node in nodes.values() if node["type"] == "route"]
    if len(route_nodes) != len(registry.get("router", [])):
        errors.append("route node count does not match registry.router")
    if crawl_document.get("router") != registry.get("router"):
        errors.append("crawl.router does not retain registry.router display fields")
    edges = defaultdict(list)
    for item in crawl_document.get("graph", {}).get("relations", []):
        if item.get("type") == "routes_to":
            edges[item["from"]].append((item.get("order"), item.get("to")))
    for route in route_nodes:
        target_ids = route.get("target_ids", [])
        display_targets = route.get("display", {}).get("use", [])
        if len(target_ids) != len(display_targets):
            errors.append(f"{route['id']} does not resolve every display target")
        for target_id in target_ids:
            if target_id not in nodes:
                errors.append(f"{route['id']} references missing node {target_id}")
        exact_edges = [
            target for _, target in sorted(edges[route["id"]], key=lambda item: item[0])
        ]
        if exact_edges != target_ids:
            errors.append(f"{route['id']} route relation order/targets drift")
    return errors


def input_hash_errors(crawl_document, registry_bytes, foundation_bytes):
    errors = []
    selected_inputs = {
        "registry": registry_bytes,
        "foundation": foundation_bytes,
    }
    for key, body in selected_inputs.items():
        if body is None:
            errors.append(f"{key} source bytes are unavailable")
            continue
        expected = hashlib.sha256(body).hexdigest()
        actual = crawl_document.get("inputs", {}).get(key, {}).get("sha256")
        if actual != expected:
            errors.append(f"crawl input hash for {key} is stale")
    return errors


def deterministic_artifact_errors(
    registry,
    foundation,
    registry_bytes,
    foundation_bytes,
    actual_artifacts,
):
    errors = []
    try:
        expected = generate_crawl.build_artifacts(
            registry=registry,
            foundation=foundation,
            registry_bytes=registry_bytes,
            foundation_bytes=foundation_bytes,
        )
    except Exception as error:
        return [f"generator failed: {error}"]
    for name, content in expected.items():
        actual = actual_artifacts.get(name)
        if actual is None:
            errors.append(f"{name} is unavailable")
        elif actual != content:
            errors.append(f"{name} is stale")
    return errors


def receipt_source_results(crawl_document, plan, fetched):
    results = crawl.unprobed_sources(plan)
    for source in plan["read_targets"]:
        target = source.get("target")
        if not target or target not in fetched:
            continue
        body = fetched[target]
        if body is None:
            results[source["key"]] = {
                "status": "unreadable",
                "target": target,
                "integrity": "not_checkable",
            }
            continue
        actual = hashlib.sha256(body).hexdigest()
        expected = source.get("sha256")
        results[source["key"]] = {
            "status": "read",
            "target": target,
            "bytes": len(body),
            "sha256": actual,
            "integrity": "verified"
            if expected == actual
            else "mismatch"
            if expected
            else "not_pinned",
        }
    return results


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true", help="prefer checked-in spine sources")
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    report = {"spec": "rapp-spine-verification/1.1", "invariants": {}, "drift": []}
    remote_commit = None if args.local else resolve_remote_commit()
    spine_base = (
        SPINE
        if args.local
        else f"{SPINE_REPO_RAW}/{remote_commit or 'UNRESOLVED_COMMIT'}"
    )
    estate, estate_origin, _estate_bytes = load_json_source(
        ESTATE, LOCAL_ESTATE, args.local
    )
    registry, registry_origin, registry_bytes = load_json_source(
        f"{spine_base}/registry.json",
        ROOT / "registry.json",
        args.local,
        allow_remote_fallback=False,
    )
    foundation, foundation_origin, foundation_bytes = load_json_source(
        f"{spine_base}/foundation.json",
        ROOT / "foundation.json",
        args.local,
        allow_remote_fallback=False,
    )
    crawl_document, crawl_origin, crawl_bytes = load_json_source(
        f"{spine_base}/crawl.json",
        ROOT / "crawl.json",
        args.local,
        allow_remote_fallback=False,
    )
    coverage, coverage_origin, coverage_bytes = load_json_source(
        f"{spine_base}/coverage.json",
        ROOT / "coverage.json",
        args.local,
        allow_remote_fallback=False,
    )
    llms_full, llms_origin, _llms_bytes = load_text_source(
        f"{spine_base}/llms-full.txt",
        ROOT / "llms-full.txt",
        args.local,
        allow_remote_fallback=False,
    )
    crawl_graph, crawl_graph_origin, _crawl_graph_bytes = load_text_source(
        f"{spine_base}/CRAWL_GRAPH.md",
        ROOT / "CRAWL_GRAPH.md",
        args.local,
        allow_remote_fallback=False,
    )

    inputs = {
        "estate_map": isinstance(estate, dict) and isinstance(estate.get("repos"), list),
        "registry": isinstance(registry, dict) and isinstance(registry.get("registry"), list),
        "foundation": isinstance(foundation, dict)
        and isinstance(foundation.get("pillars"), list),
        "crawl": isinstance(crawl_document, dict)
        and crawl_document.get("spec") == generate_crawl.SPEC,
        "coverage": isinstance(coverage, dict)
        and coverage.get("spec") == "rapp-spine-coverage/1.0",
        "llms_full": isinstance(llms_full, str),
        "crawl_graph": isinstance(crawl_graph, str),
        "remote_commit": args.local or remote_commit is not None,
    }
    expected_spine_origin = "local" if args.local else "remote"
    spine_origins = {
        "registry": registry_origin,
        "foundation": foundation_origin,
        "crawl": crawl_origin,
        "coverage": coverage_origin,
        "llms_full": llms_origin,
        "crawl_graph": crawl_graph_origin,
    }
    inputs["spine_origin_consistency"] = all(
        origin.get("kind") == expected_spine_origin
        for origin in spine_origins.values()
    )
    report["invariants"]["I0_input_availability"] = {
        "sources": inputs,
        "expected_spine_origin": expected_spine_origin,
        "resolved_remote_commit": remote_commit,
        "origins": {
            "estate_map": estate_origin,
            **spine_origins,
        },
        "pass": all(inputs.values()),
    }
    for source, loaded in inputs.items():
        if not loaded:
            add_drift(report, "I0", f"{source} unavailable or invalid", source=source)

    estate = estate or {}
    registry = registry or {"registry": [], "router": []}
    foundation = foundation or {"pillars": []}
    crawl_document = crawl_document or {"graph": {"nodes": [], "relations": []}}
    coverage = coverage or {}
    actual_artifacts = {
        "crawl.json": decode_text(crawl_bytes),
        "coverage.json": decode_text(coverage_bytes),
        "llms-full.txt": llms_full,
        "CRAWL_GRAPH.md": crawl_graph,
    }
    selected_surface_bytes = {
        "registry.json": (registry_origin, registry_bytes),
        "foundation.json": (foundation_origin, foundation_bytes),
        "crawl.json": (crawl_origin, crawl_bytes),
        "coverage.json": (coverage_origin, coverage_bytes),
        "llms-full.txt": (llms_origin, _llms_bytes),
        "CRAWL_GRAPH.md": (crawl_graph_origin, _crawl_graph_bytes),
    }
    preloaded_sources = {}
    for name, (origin, body) in selected_surface_bytes.items():
        if body is None:
            continue
        if origin.get("kind") == "remote":
            preloaded_sources[origin["target"]] = body
        else:
            preloaded_sources[f"{SPINE}/{name}"] = body
    node_by_id = {
        node.get("id"): node
        for node in crawl_document.get("graph", {}).get("nodes", [])
        if isinstance(node, dict) and isinstance(node.get("id"), str)
    }

    # I1 — estate inventory coverage must be represented by exact repository nodes.
    repository_nodes = {
        node.get("repo", "").lower(): node["id"]
        for node in node_by_id.values()
        if node.get("type") == "repository" and isinstance(node.get("repo"), str)
    }
    load_bearing = [
        record for record in estate.get("repos", []) if record.get("load_bearing")
    ]
    missing_repos = sorted(
        {
            record["repo"]
            for record in load_bearing
            if record.get("repo", "").lower() not in repository_nodes
        }
    )
    report["invariants"]["I1_spine_completeness"] = {
        "load_bearing": len(load_bearing),
        "represented": len(load_bearing) - len(missing_repos),
        "referenced": len(load_bearing) - len(missing_repos),
        "missing": missing_repos,
        "repository_nodes": len(repository_nodes),
        "pass": not missing_repos,
    }
    for repo in missing_repos:
        add_drift(
            report,
            "I1",
            "load-bearing repo has no exact repository graph node",
            repo=repo,
        )

    # Build the authoritative full plan from graph.traversal_order, then fetch every
    # required source target once. Unresolved sources remain explicit receipt failures.
    full_plan = None
    required_plan_sources = []
    if crawl_document.get("spec") == generate_crawl.SPEC:
        try:
            full_plan = crawl.build_plan(
                crawl_document,
                mode="full",
                batch_size=max(1, len(node_by_id)),
            )
            required_plan_sources = [
                source for source in full_plan["read_targets"] if source["required"]
            ]
        except Exception as error:
            report["invariants"]["I0_input_availability"]["sources"]["full_plan"] = False
            report["invariants"]["I0_input_availability"]["pass"] = False
            add_drift(report, "I0", f"full crawl plan unavailable: {error}", source="crawl")

    protocol_nodes = [
        node for node in node_by_id.values() if node.get("type") == "protocol"
    ]
    protocol_sources = []
    for node in protocol_nodes:
        for source in node.get("sources", []):
            if source.get("role") == "canonical_material" and source.get("required"):
                protocol_sources.append((node, source))
    locked_records = [
        record for record in _iter(foundation) if record.get("locked")
    ]
    exact_targets = [
        source["target"]
        for source in required_plan_sources
        if isinstance(source.get("target"), str)
    ]
    fetched = fetch_targets(
        exact_targets,
        args.local,
        spine_commit=remote_commit,
        preloaded=preloaded_sources,
    )

    # I2 — no routing-only entry may disappear; unresolved material must be structured.
    resolved = unreadable = declared_unresolved = silent_unresolved = 0
    issue_by_node = defaultdict(list)
    for issue in crawl_document.get("issues", []):
        for target_id in issue.get("related_node_ids", []):
            issue_by_node[target_id].append(issue)
    for node, source in protocol_sources:
        target = source.get("target")
        if not target:
            structured = any(
                issue.get("source") == "generated.required_material"
                and issue.get("source_role") == "canonical_material"
                for issue in issue_by_node[node["id"]]
            )
            if structured:
                declared_unresolved += 1
            else:
                silent_unresolved += 1
                add_drift(
                    report,
                    "I2",
                    "required canonical material is silently unresolved",
                    spec_id=node["display"]["spec_id"],
                    node_id=node["id"],
                )
        elif fetched.get(target) is None:
            unreadable += 1
            add_drift(
                report,
                "I2",
                f"canonical material unreadable: {target}",
                spec_id=node["display"]["spec_id"],
                node_id=node["id"],
            )
        else:
            resolved += 1
    source_complete = unreadable == 0 and declared_unresolved == 0 and silent_unresolved == 0
    report["invariants"]["I2_spec_resolvability"] = {
        "required": len(protocol_sources),
        "resolved": resolved,
        "unreadable": unreadable,
        "unresolved": declared_unresolved + silent_unresolved,
        "declared_unresolved": declared_unresolved,
        "silent_unresolved": silent_unresolved,
        "routing_only": declared_unresolved + silent_unresolved,
        "complete": source_complete,
        "pass": unreadable == 0 and silent_unresolved == 0,
    }

    # I3 — immutable foundation evidence retains valid, reachable hashes.
    hash_ok = hash_stale = hash_invalid = hash_unreachable = 0
    for record in locked_records:
        target = record.get("raw_url")
        expected = record.get("sha256")
        subject = record.get("spec") or record.get("doc")
        if not isinstance(target, str) or not valid_sha256(expected):
            hash_invalid += 1
            add_drift(
                report,
                "I3",
                "locked foundation record lacks raw_url or valid sha256",
                spec=subject,
            )
            continue
        body = fetched.get(target)
        if body is None:
            hash_unreachable += 1
            add_drift(
                report,
                "I3",
                f"foundation source unreadable: {target}",
                spec=subject,
            )
        elif hashlib.sha256(body).hexdigest() == expected:
            hash_ok += 1
        else:
            hash_stale += 1
            add_drift(
                report,
                "I3",
                f"foundation sha256 stale for {target}",
                spec=subject,
            )
    report["invariants"]["I3_hash_integrity"] = {
        "ok": hash_ok,
        "stale": hash_stale,
        "invalid": hash_invalid,
        "unreachable": hash_unreachable,
        "pass": hash_stale == 0 and hash_invalid == 0 and hash_unreachable == 0,
    }

    # I4 — compatibility invariant: an exact registry spec_id has one owner.
    by_spec_id = defaultdict(set)
    for entry in registry.get("registry", []):
        if entry.get("spec_id") and entry.get("repo"):
            by_spec_id[entry["spec_id"]].add(entry["repo"])
    collisions = {
        spec_id: sorted(repos)
        for spec_id, repos in by_spec_id.items()
        if len(repos) > 1
    }
    report["invariants"]["I4_no_collision"] = {
        "collisions": collisions,
        "pass": not collisions,
    }
    for spec_id, repos in collisions.items():
        add_drift(
            report,
            "I4",
            f"declared by multiple repos: {repos}",
            spec_id=spec_id,
        )

    # I5 — readable exact protocol material must declare the registry spec_id.
    honest = dishonest = 0
    for node, source in protocol_sources:
        target = source.get("target")
        body = fetched.get(target) if target else None
        if body is None:
            continue
        spec_id = node["display"]["spec_id"]
        if spec_id in body.decode("utf-8", "replace"):
            honest += 1
        else:
            dishonest += 1
            add_drift(
                report,
                "I5",
                f"canonical material does not declare {spec_id}",
                spec_id=spec_id,
                node_id=node["id"],
            )
    report["invariants"]["I5_spec_id_honesty"] = {
        "honest": honest,
        "dishonest": dishonest,
        "pass": dishonest == 0,
    }

    # I6 — graph schema/shape and retained display compatibility.
    schema_errors = []
    try:
        generate_crawl.validate_crawl(crawl_document)
    except Exception as error:
        schema_errors.extend(str(error).splitlines())
    if crawl_document.get("registry") != registry.get("registry"):
        schema_errors.append("crawl.registry does not retain registry display entries")
    if crawl_document.get("layers") != registry.get("layers"):
        schema_errors.append("crawl.layers does not retain registry display layers")
    schema_errors.extend(
        input_hash_errors(crawl_document, registry_bytes, foundation_bytes)
    )
    report["invariants"]["I6_schema_shape"] = {
        "errors": schema_errors,
        "pass": not schema_errors,
    }
    for error in schema_errors:
        add_drift(report, "I6", error)

    # I7 — fuzzy labels are display-only; exact graph targets and relations are authoritative.
    route_errors = validate_route_integrity(crawl_document, registry)
    report["invariants"]["I7_route_referential_integrity"] = {
        "routes": len(registry.get("router", [])),
        "exact_target_references": sum(
            len(node.get("target_ids", []))
            for node in node_by_id.values()
            if node.get("type") == "route"
        ),
        "errors": route_errors,
        "pass": not route_errors,
    }
    for error in route_errors:
        add_drift(report, "I7", error)

    # I8 — every relation closes and every node is reachable from the root.
    graph_health = crawl.graph_health(crawl_document)
    graph_pass = (
        not graph_health["root_missing"]
        and not graph_health["dangling_relations"]
        and not graph_health["orphan_node_ids"]
    )
    report["invariants"]["I8_graph_closure"] = {
        **graph_health,
        "nodes": len(node_by_id),
        "relations": len(crawl_document.get("graph", {}).get("relations", [])),
        "pass": graph_pass,
    }
    for item in graph_health["dangling_relations"]:
        add_drift(report, "I8", f"dangling relation: {item}")
    if graph_health["root_missing"]:
        add_drift(report, "I8", "graph root is missing")
    for node_id in graph_health["orphan_node_ids"]:
        add_drift(report, "I8", "orphan graph node", node_id=node_id)

    # I9 — required material profiles, structured gaps, and safe entry points.
    material_errors = validate_material_profiles(crawl_document)
    report["invariants"]["I9_required_material_profiles"] = {
        "profiles": len(crawl_document.get("material_profiles", {})),
        "structured_issues": len(crawl_document.get("issues", [])),
        "errors": material_errors,
        "pass": not material_errors,
    }
    for error in material_errors:
        add_drift(report, "I9", error)

    # I10 — all generated AI/human surfaces must be byte-for-byte fresh.
    deterministic_errors = deterministic_artifact_errors(
        registry,
        foundation,
        registry_bytes,
        foundation_bytes,
        actual_artifacts,
    )
    report["invariants"]["I10_deterministic_generation"] = {
        "artifacts": sorted(generate_crawl.OUTPUTS),
        "errors": deterministic_errors,
        "pass": not deterministic_errors,
    }
    for error in deterministic_errors:
        add_drift(report, "I10", error)

    # I11 — coverage.json must be a deterministic accounting of the graph.
    coverage_errors = []
    if crawl_document.get("spec") == generate_crawl.SPEC:
        expected_coverage = generate_crawl.build_coverage(crawl_document)
        if coverage != expected_coverage:
            coverage_errors.append("coverage.json does not match crawl.json")
    else:
        coverage_errors.append("coverage cannot be checked without rapp-spine/1.1 graph")
    report["invariants"]["I11_coverage_accounting"] = {
        "errors": coverage_errors,
        "pass": not coverage_errors,
    }
    for error in coverage_errors:
        add_drift(report, "I11", error)

    # I12 — a receipt must stay incomplete whenever required material is unread/unavailable.
    receipt_errors = []
    receipt = None
    receipt_results = {}
    required_role_counts = Counter(source["role"] for source in required_plan_sources)
    read_role_counts = Counter()
    if full_plan is not None:
        try:
            receipt_results = receipt_source_results(crawl_document, full_plan, fetched)
            for source in required_plan_sources:
                if receipt_results[source["key"]]["status"] == "read":
                    read_role_counts[source["role"]] += 1
            receipt = crawl.build_receipt(crawl_document, full_plan, receipt_results)
            dimensions = receipt.get("completion", {})
            required_dimensions = {
                "inventory_graph_coverage",
                "graph_integrity",
                "source_integrity_availability",
                "known_gaps",
                "operational_conformance",
            }
            if not required_dimensions.issubset(dimensions):
                receipt_errors.append("receipt omits required completion dimensions")
            source_dimension = dimensions.get("source_integrity_availability", {})
            source_counts = source_dimension.get("counts", {})
            if source_counts.get("not_read", 0):
                receipt_errors.append("receipt leaves required source targets unread")
            if not receipt.get("passed"):
                receipt_errors.append(
                    "receipt contains unreadable or integrity-mismatched required sources"
                )
            if declared_unresolved and receipt.get("complete"):
                receipt_errors.append("receipt claims complete with unresolved required material")
            receipt_failures = source_dimension.get("failures", [])
            unresolved_nodes = {
                source["node_id"]
                for source in required_plan_sources
                if not source.get("target")
            }
            receipted_unresolved = {
                failure["node_id"]
                for failure in receipt_failures
                if failure.get("status") == "unresolved"
            }
            if not unresolved_nodes.issubset(receipted_unresolved):
                receipt_errors.append("receipt silently omits unresolved required material")
        except Exception as error:
            receipt_errors.append(f"receipt generation failed: {error}")
    else:
        receipt_errors.append("receipt cannot be built without rapp-spine/1.1 graph")
    report["invariants"]["I12_completion_receipt"] = {
        "complete": receipt.get("complete") if receipt else False,
        "required_sources": len(required_plan_sources),
        "required_by_role": dict(sorted(required_role_counts.items())),
        "read_by_role": dict(sorted(read_role_counts.items())),
        "source_counts": (
            receipt.get("completion", {})
            .get("source_integrity_availability", {})
            .get("counts", {})
            if receipt
            else {}
        ),
        "errors": receipt_errors,
        "pass": not receipt_errors,
    }
    for error in receipt_errors:
        add_drift(report, "I12", error)

    receipt_completion = receipt.get("completion", {}) if receipt else {}
    receipt_inventory = receipt_completion.get("inventory_graph_coverage", {})
    receipt_graph = receipt_completion.get("graph_integrity", {})
    receipt_sources = receipt_completion.get("source_integrity_availability", {})
    receipt_gaps = receipt_completion.get("known_gaps", {})
    receipt_operational = receipt_completion.get("operational_conformance", {})

    inventory_complete = (
        report["invariants"]["I1_spine_completeness"]["pass"]
        and report["invariants"]["I6_schema_shape"]["pass"]
        and report["invariants"]["I7_route_referential_integrity"]["pass"]
        and report["invariants"]["I8_graph_closure"]["pass"]
        and bool(receipt_inventory.get("complete"))
        and bool(receipt_graph.get("complete"))
    )
    source_integrity_complete = (
        bool(receipt_sources.get("complete"))
        and report["invariants"]["I2_spec_resolvability"]["complete"]
        and report["invariants"]["I3_hash_integrity"]["pass"]
        and report["invariants"]["I5_spec_id_honesty"]["pass"]
    )
    blocking_issues = [
        issue for issue in crawl_document.get("issues", []) if issue.get("blocking")
    ]
    report["completion"] = {
        "inventory_graph_coverage": {
            "receipt_inventory": receipt_inventory,
            "receipt_graph": receipt_graph,
            "complete": inventory_complete,
            "load_bearing_repos": len(load_bearing),
            "represented": len(load_bearing) - len(missing_repos),
        },
        "source_integrity_availability": {
            **receipt_sources,
            "complete": source_integrity_complete,
            "protocol_material": {
                "resolved": resolved,
                "unreadable": unreadable,
                "declared_unresolved": declared_unresolved,
            },
        },
        "known_gaps": {
            **receipt_gaps,
            "complete": bool(receipt_gaps.get("complete")),
        },
        "operational_conformance": {
            **receipt_operational,
            "complete": bool(receipt_operational.get("healthy")),
        },
    }
    report["passed"] = all(
        invariant["pass"] for invariant in report["invariants"].values()
    )
    report["completion"]["complete"] = report["passed"] and all(
        dimension["complete"] for dimension in report["completion"].values()
    )
    report["complete"] = report["completion"]["complete"]
    report["status"] = (
        "complete"
        if report["passed"] and report["complete"]
        else "conformant_with_known_gaps"
        if report["passed"]
        else "invalid"
    )
    report["drift_count"] = len(report["drift"])
    report["known_gap_count"] = len(blocking_issues)

    if args.as_json:
        print(json.dumps(report, indent=2))
    else:
        for name, invariant in report["invariants"].items():
            print(f"  {'PASS' if invariant['pass'] else 'FAIL'}  {name}")
        if report["passed"] and report["complete"]:
            verdict = "✅ COMPLETE — inventory, sources, gaps, and operations are healthy"
        elif report["passed"]:
            verdict = (
                "⚠️  CONFORMANT GRAPH — crawl remains incomplete with "
                f"{report['known_gap_count']} blocking declared gap(s)"
            )
        else:
            verdict = f"❌ INVALID — {report['drift_count']} conformance drift item(s)"
        print(f"\n{verdict}")
        for item in report["drift"][:40]:
            subject = (
                item.get("repo")
                or item.get("spec_id")
                or item.get("spec")
                or item.get("node_id")
                or item.get("source")
                or "spine"
            )
            print(f"   · [{item['invariant']}] {subject}: {item['issue']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
