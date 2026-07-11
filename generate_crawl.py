#!/usr/bin/env python3
"""Generate the deterministic rapp-spine/1.1 crawl contract and surfaces."""

import argparse
import copy
import hashlib
import json
import re
from collections import Counter, defaultdict, deque
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent
REGISTRY = ROOT / "registry.json"
FOUNDATION = ROOT / "foundation.json"
OUTPUTS = {
    "crawl.json": ROOT / "crawl.json",
    "coverage.json": ROOT / "coverage.json",
    "llms-full.txt": ROOT / "llms-full.txt",
    "CRAWL_GRAPH.md": ROOT / "CRAWL_GRAPH.md",
}
SPEC = "rapp-spine/1.1"
GRAPH_SPEC = "rapp-crawl-graph/1.0"
PLAN_SPEC = "rapp-crawl-plan/1.0"
PLAN_TEMPLATE_SPEC = "rapp-crawl-plan-template/1.0"
ROOT_ID = "spine:rapp-spine%2F1.1"
REMOTE_BASE = "https://raw.githubusercontent.com/kody-w/rapp-spine/main"
SPEC_RE = re.compile(r"\b(?:brainstem-egg|rapp[-_][a-z0-9_-]+)/\d+(?:\.\d+)*\b", re.I)
REPO_RE = re.compile(r"\bkody-w/[A-Za-z0-9_.-]+\b", re.I)
URL_RE = re.compile(r"https?://[^\s]+")

MATERIAL_PROFILES = {
    "spine-root": {
        "required_source_roles": [],
        "description": "Root of the complete crawl inventory.",
    },
    "authoritative-artifact": {
        "required_source_roles": ["authoritative_input"],
        "description": "A checked-in source document from which the graph is generated.",
    },
    "layer": {
        "required_source_roles": [],
        "description": "An ordered display and ownership layer.",
    },
    "route": {
        "required_source_roles": [],
        "required_relation": "routes_to",
        "description": "A situation whose display labels resolve to exact graph node IDs.",
    },
    "registry-protocol": {
        "required_source_roles": ["canonical_material"],
        "description": "Every registry entry requires an exact readable canonical material target.",
    },
    "repository": {
        "required_source_roles": ["repository_identity"],
        "description": "A repository represented by the registry or foundation inventory.",
    },
    "foundation-locked": {
        "required_source_roles": ["integrity_evidence"],
        "description": "A foundation source pinned by sha256.",
    },
    "foundation-supporting": {
        "required_source_roles": ["supporting_evidence"],
        "description": "A supporting corpus or infrastructure reference.",
    },
    "issue": {
        "required_source_roles": [],
        "description": "A structured collision, gap, security concern, or lifecycle issue.",
    },
}

NODE_ENUMS = {
    "lifecycle": {"active", "deprecated", "unpublished", "not_applicable"},
    "status": {"resolved", "unresolved", "degraded", "represented", "informational"},
    "materiality": {"required", "supporting", "routing", "informational", "gap"},
    "conformance": {"not_assessed", "conformant", "nonconformant", "not_applicable"},
}

# This alias is declared by the estate entry but is not repeated in registry.spec_id.
EXACT_ROUTE_ALIASES = {
    "rapp-commons-event/1.0": (
        "kody-w/rapp-commons",
        "rapp-commons-protocol/2.0 (+ rapp-commons-event/1.0)",
    ),
    "rapp-network-beacon/1.1": (
        "kody-w/rapp-estate",
        "rapp-estate/1.1 (canonical def in kody-w/RAPP specs/SPEC.md)",
    ),
}

CANONICAL_WIRE_RELATIONS = [
    (
        "kody-w/leviathan",
        "leviathan/1.0",
        "rapp-fleet-chat/1.0",
    )
]


def read_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def json_text(value):
    return json.dumps(value, indent=2, ensure_ascii=False) + "\n"


def sha256_bytes(value):
    return hashlib.sha256(value).hexdigest()


def encoded(value):
    return quote(str(value), safe="/.-_~")


def repo_id(repo):
    return f"repo:{encoded(repo.lower())}"


def canonical_protocol_identity(value):
    tokens = SPEC_RE.findall(value)
    if tokens:
        return tokens[0].lower()
    self_titled = re.search(
        r"\b([a-z0-9_-]+)\s+spec\s+v?(\d+(?:\.\d+)*)\b",
        value,
        re.I,
    )
    if self_titled:
        return f"{self_titled.group(1).lower()}/{self_titled.group(2)}"
    canonical = re.search(
        r"\b([a-z][a-z0-9_-]*)/(\d+(?:\.\d+)*)\b",
        value,
        re.I,
    )
    if canonical:
        return f"{canonical.group(1).lower()}/{canonical.group(2)}"
    return None


def protocol_key(entry):
    return canonical_protocol_identity(entry["spec_id"]) or "entry"


def protocol_id(entry):
    return f"protocol:{encoded(entry['repo'].lower())}/{encoded(protocol_key(entry))}"


def route_id(situation):
    digest = hashlib.sha256(situation.encode("utf-8")).hexdigest()[:16]
    return f"route:{digest}"


def evidence_id(section, record):
    key = record.get("spec") or record.get("doc") or record.get("role") or record["repo"]
    return f"evidence:foundation/{section}/{encoded(key)}@{encoded(record['repo'].lower())}"


def issue_id(kind, text):
    digest = hashlib.sha256(f"{kind}\0{text}".encode("utf-8")).hexdigest()[:16]
    return f"issue:{kind}:{digest}"


def normalize(value):
    return re.sub(r"[^a-z0-9/_.-]+", " ", value.lower()).strip()


def first_url(value):
    if not isinstance(value, str):
        return None
    match = URL_RE.search(value)
    return match.group(0).rstrip(".,);") if match else None


def markdown_escape(value):
    return str(value).replace("|", "\\|")


def source_record(role, required, target=None, availability=None, sha256=None):
    if availability is None:
        availability = "declared" if target else "unresolved"
    record = {
        "role": role,
        "required": required,
        "target": target,
        "availability": availability,
        "read_only": True,
        "method": "GET",
    }
    if sha256:
        record["sha256"] = sha256
        record["integrity"] = "sha256"
    return record


def safe_entry_points(entry):
    points = []
    if entry.get("raw_url"):
        points.append(
            {
                "kind": "canonical_read",
                "target": entry["raw_url"],
                "method": "GET",
                "read_only": True,
                "safe_for_crawl": True,
            }
        )
    points.append(
        {
            "kind": "repository_read",
            "target": f"https://github.com/{entry['repo']}",
            "method": "GET",
            "read_only": True,
            "safe_for_crawl": True,
        }
    )
    points.append(
        {
            "kind": "display_only",
            "display": entry.get("entry_point", ""),
            "read_only": False,
            "safe_for_crawl": False,
            "policy": "never_execute",
        }
    )
    return points


def protocol_aliases(entry):
    aliases = {
        normalize(entry["spec_id"]),
        normalize(entry["spec_id"].split(" (", 1)[0]),
        normalize(entry["repo"]),
        normalize(entry["repo"].split("/", 1)[-1]),
    }
    aliases.update(normalize(value) for value in SPEC_RE.findall(entry["spec_id"]))
    return sorted(alias for alias in aliases if alias)


def evidence_aliases(record):
    aliases = {
        normalize(record["repo"]),
        normalize(record["repo"].split("/", 1)[-1]),
    }
    for key in ("spec", "doc"):
        if record.get(key):
            aliases.add(normalize(record[key]))
            aliases.add(normalize(record[key].split(" (", 1)[0]))
            aliases.update(normalize(value) for value in SPEC_RE.findall(record[key]))
    return sorted(alias for alias in aliases if alias)


def classify_protocol(entry):
    text = " ".join(
        str(entry.get(key, ""))
        for key in ("spec_id", "purpose", "role", "when_to_use", "entry_point")
    ).lower()
    if any(word in text for word in ("unpublished", "not found / 404", "repo 404", "standalone repo 404")):
        lifecycle = "unpublished"
    elif any(word in text for word in ("deprecated", "archived", "superseded", "moved ->")):
        lifecycle = "deprecated"
    else:
        lifecycle = "active"

    nonconformant = any(
        phrase in text
        for phrase in (
            "non-conformant",
            "nonconformant",
            "parity target incomplete",
            "known phase-1 rce",
            "unauthenticated",
        )
    )
    if not entry.get("raw_url"):
        status = "unresolved"
    elif nonconformant:
        status = "degraded"
    else:
        status = "resolved"
    conformance = "nonconformant" if nonconformant else "not_assessed"
    return lifecycle, status, conformance


def issue_kind(text):
    upper = text.upper()
    if re.search(r"\bSECURITY\s+GAP\b|\bRCE\b", upper):
        return "security"
    if re.search(r"\bMISSING\b|\b404S?\b|\bGAPS?\b", upper):
        return "gap"
    if re.search(r"\bDEPRECATIONS?\b|\bARCHIVED\b", upper):
        return "lifecycle"
    if re.search(r"\bCOLLISIONS?\b|\bOVERLAPS?\b|\bSEAMS?\b", upper):
        return "collision"
    return "clarification"


def relation(source, kind, target):
    return {"from": source, "type": kind, "to": target}


def _unique_candidate(candidates, label, stage):
    unique = sorted({node["id"]: node for node in candidates}.values(), key=lambda node: node["id"])
    if len(unique) == 1:
        return unique[0]["id"]
    if len(unique) > 1:
        raise ValueError(
            f"ambiguous route target {label!r} during {stage}: "
            + ", ".join(node["id"] for node in unique)
        )
    return None


def resolve_route_target(label, nodes):
    """Resolve one display route label to one exact graph node ID or fail."""
    full = normalize(label)
    head = normalize(label.split(" (", 1)[0])
    by_type = defaultdict(list)
    for node in nodes:
        by_type[node["type"]].append(node)

    alias = EXACT_ROUTE_ALIASES.get(head) or EXACT_ROUTE_ALIASES.get(full)
    if alias:
        repo, spec_id = alias
        matches = [
            node
            for node in by_type["protocol"]
            if normalize(node.get("repo", "")) == normalize(repo)
            and node.get("display", {}).get("spec_id") == spec_id
        ]
        found = _unique_candidate(matches, label, "exact override")
        if found:
            return found
        raise ValueError(f"route override for {label!r} does not identify a graph node")

    head_protocols = [
        node for node in by_type["protocol"] if head in node.get("aliases", [])
    ]
    if not head_protocols:
        for node_type in ("evidence", "artifact"):
            exact = [node for node in by_type[node_type] if head in node.get("aliases", [])]
            found = _unique_candidate(exact, label, f"exact {node_type} alias")
            if found:
                return found

    mentioned_repos = {normalize(value) for value in REPO_RE.findall(label)}
    if mentioned_repos:
        pool = [
            node
            for node in by_type["protocol"]
            if normalize(node.get("repo", "")) in mentioned_repos
        ]
        exact = [node for node in pool if head in node.get("aliases", [])]
        found = _unique_candidate(exact, label, "repository-qualified alias")
        if found:
            return found
        if len(pool) == 1:
            return pool[0]["id"]
        if pool:
            contained = [
                node
                for node in pool
                if any(alias and alias in full for alias in node.get("aliases", []))
            ]
            found = _unique_candidate(contained, label, "repository-qualified match")
            if found:
                return found
            raise ValueError(
                f"repository qualifier in route target {label!r} remains ambiguous: "
                + ", ".join(node["id"] for node in pool)
            )

    for node_type in ("protocol", "evidence", "artifact", "repository"):
        exact = [node for node in by_type[node_type] if head in node.get("aliases", [])]
        found = _unique_candidate(exact, label, f"exact {node_type} alias")
        if found:
            return found

    for node_type in ("protocol", "evidence", "artifact", "repository"):
        ranked = []
        for node in by_type[node_type]:
            matches = [
                alias
                for alias in node.get("aliases", [])
                if len(alias) >= 5 and alias in full
            ]
            if matches:
                ranked.append((max(len(alias) for alias in matches), node))
        if ranked:
            best = max(score for score, _ in ranked)
            found = _unique_candidate(
                [node for score, node in ranked if score == best],
                label,
                f"contained {node_type} alias",
            )
            if found:
                return found

    raise ValueError(f"unresolved route target {label!r}")


def _related_nodes(text, nodes):
    mentioned_repos = {value.lower() for value in REPO_RE.findall(text)}
    related = set()
    for node in nodes:
        repo = node.get("repo")
        if repo and repo.lower() in mentioned_repos:
            related.add(node["id"])
    specs = {normalize(value) for value in SPEC_RE.findall(text)}
    if specs:
        for node in nodes:
            if specs.intersection(node.get("aliases", [])):
                related.add(node["id"])
    if re.search(r"\bLeviathan\b", text, re.I) and re.search(
        r"\bPOST\s+/api/agent(?:/<name>)?", text, re.I
    ):
        for node in nodes:
            if (
                node.get("type") == "protocol"
                and node.get("repo", "").lower() == "kody-w/leviathan"
                and node.get("canonical_protocol_identity")
                in {"leviathan/1.0", "rapp-fleet-chat/1.0"}
            ):
                related.add(node["id"])
    return sorted(related)


def build_crawl(registry, foundation, registry_bytes=None, foundation_bytes=None):
    generated = registry.get("generated") or foundation.get("generated")
    registry_bytes = (
        json_text(registry).encode("utf-8")
        if registry_bytes is None
        else registry_bytes
    )
    foundation_bytes = (
        json_text(foundation).encode("utf-8")
        if foundation_bytes is None
        else foundation_bytes
    )
    registry_sha = sha256_bytes(registry_bytes)
    foundation_sha = sha256_bytes(foundation_bytes)
    nodes = []
    relations = []
    issues = []
    ordered = []

    def add_node(node):
        nodes.append(node)
        ordered.append(node["id"])
        return node

    add_node(
        {
            "id": ROOT_ID,
            "type": "spine",
            "label": "RAPP Spine exhaustive crawl",
            "lifecycle": "active",
            "status": "resolved",
            "materiality": "required",
            "material_profile": "spine-root",
            "required_source_roles": [],
            "sources": [],
            "entry_points": [],
            "conformance": "not_assessed",
            "aliases": ["rapp-spine/1.1"],
        }
    )

    artifact_nodes = [
        {
            "id": "artifact:registry.json",
            "type": "artifact",
            "label": "registry.json",
            "lifecycle": "active",
            "status": "resolved",
            "materiality": "required",
            "material_profile": "authoritative-artifact",
            "required_source_roles": ["authoritative_input"],
            "sources": [
                source_record(
                    "authoritative_input",
                    True,
                    f"{REMOTE_BASE}/registry.json",
                    availability="declared",
                    sha256=registry_sha,
                )
            ],
            "entry_points": [
                {
                    "kind": "canonical_read",
                    "target": f"{REMOTE_BASE}/registry.json",
                    "method": "GET",
                    "read_only": True,
                    "safe_for_crawl": True,
                },
            ],
            "conformance": "not_assessed",
            "aliases": ["registry.json"],
        },
        {
            "id": "artifact:foundation.json",
            "type": "artifact",
            "label": "foundation.json",
            "lifecycle": "active",
            "status": "resolved",
            "materiality": "required",
            "material_profile": "authoritative-artifact",
            "required_source_roles": ["authoritative_input"],
            "sources": [
                source_record(
                    "authoritative_input",
                    True,
                    f"{REMOTE_BASE}/foundation.json",
                    availability="declared",
                    sha256=foundation_sha,
                )
            ],
            "entry_points": [
                {
                    "kind": "canonical_read",
                    "target": f"{REMOTE_BASE}/foundation.json",
                    "method": "GET",
                    "read_only": True,
                    "safe_for_crawl": True,
                },
            ],
            "conformance": "not_assessed",
            "aliases": ["foundation.json"],
        },
    ]
    for node in artifact_nodes:
        add_node(node)
        relations.append(relation(ROOT_ID, "has_artifact", node["id"]))

    layer_nodes = {}
    for order, layer_name in enumerate(registry["layers_order"]):
        display = next(
            item for item in registry["layers"] if item["layer"].split(" ", 1)[0] == layer_name
        )
        node = add_node(
            {
                "id": f"layer:{encoded(layer_name)}",
                "type": "layer",
                "label": display["layer"],
                "order": order,
                "lifecycle": "active",
                "status": "informational",
                "materiality": "routing",
                "material_profile": "layer",
                "required_source_roles": [],
                "sources": [],
                "entry_points": [],
                "conformance": "not_applicable",
                "aliases": [normalize(layer_name), normalize(display["layer"])],
                "display": copy.deepcopy(display),
            }
        )
        layer_nodes[layer_name] = node
        relations.append(relation(ROOT_ID, "orders_layer", node["id"]))

    foundation_by_url = {}
    for section in ("pillars", "law"):
        for record in foundation.get(section, []):
            if record.get("raw_url"):
                foundation_by_url[record["raw_url"]] = record

    protocol_nodes = []
    protocol_by_id = {}
    for index, entry in enumerate(registry["registry"]):
        lifecycle, status, conformance = classify_protocol(entry)
        source = source_record(
            "canonical_material",
            True,
            entry.get("raw_url"),
            availability="declared" if entry.get("raw_url") else "unresolved",
            sha256=(foundation_by_url.get(entry.get("raw_url")) or {}).get("sha256"),
        )
        node = add_node(
            {
                "id": protocol_id(entry),
                "type": "protocol",
                "label": entry["spec_id"],
                "repo": entry["repo"],
                "canonical_protocol_identity": protocol_key(entry),
                "layer_id": layer_nodes[entry["layer"]]["id"],
                "lifecycle": lifecycle,
                "status": status,
                "materiality": "required",
                "material_profile": "registry-protocol",
                "required_source_roles": ["canonical_material"],
                "sources": [source],
                "entry_points": safe_entry_points(entry),
                "conformance": conformance,
                "aliases": protocol_aliases(entry),
                "display": {"registry_index": index, **copy.deepcopy(entry)},
            }
        )
        protocol_nodes.append(node)
        protocol_by_id[node["id"]] = node
        relations.extend(
            [
                relation("artifact:registry.json", "declares", node["id"]),
                relation(node["id"], "in_layer", node["layer_id"]),
                relation(node["id"], "owned_by", repo_id(entry["repo"])),
            ]
        )

    protocols_by_identity = {
        (node["repo"].lower(), node["canonical_protocol_identity"]): node
        for node in protocol_nodes
    }
    for repo, legacy_identity, canonical_identity in CANONICAL_WIRE_RELATIONS:
        legacy = protocols_by_identity.get((repo.lower(), legacy_identity))
        canonical = protocols_by_identity.get((repo.lower(), canonical_identity))
        if legacy is None or canonical is None:
            raise ValueError(
                f"canonical wire mapping is unresolved: {repo} "
                f"{legacy_identity} -> {canonical_identity}"
            )
        relations.append(
            {
                "from": legacy["id"],
                "type": "canonical_wire",
                "to": canonical["id"],
                "role": "replacement",
            }
        )

    repo_names = {}
    for entry in registry["registry"]:
        repo_names.setdefault(entry["repo"].lower(), entry["repo"])
    for section in ("pillars", "law", "spec_corpus", "core_infra"):
        for record in foundation.get(section, []):
            if isinstance(record.get("repo"), str):
                repo_names.setdefault(record["repo"].lower(), record["repo"])

    unavailable_repos = {
        entry["repo"].lower()
        for entry in registry["registry"]
        if entry["spec_id"].lower().startswith("(none;")
        and re.search(r"\b(?:404S?|UNPUBLISHED)\b", entry["spec_id"], re.I)
    }
    repository_nodes = []
    for repo_key in sorted(repo_names):
        repo = repo_names[repo_key]
        repository_target = None if repo_key in unavailable_repos else f"https://github.com/{repo}"
        node = add_node(
            {
                "id": repo_id(repo),
                "type": "repository",
                "label": repo,
                "repo": repo,
                "lifecycle": "unpublished" if repo_key in unavailable_repos else "active",
                "status": "unresolved" if repo_key in unavailable_repos else "represented",
                "materiality": "required",
                "material_profile": "repository",
                "required_source_roles": ["repository_identity"],
                "sources": [
                    source_record(
                        "repository_identity",
                        True,
                        repository_target,
                        availability="unresolved"
                        if repo_key in unavailable_repos
                        else "declared",
                    )
                ],
                "entry_points": (
                    [
                        {
                            "kind": "repository_read",
                            "target": repository_target,
                            "method": "GET",
                            "read_only": True,
                            "safe_for_crawl": True,
                        }
                    ]
                    if repository_target
                    else []
                ),
                "conformance": "not_assessed",
                "aliases": sorted({normalize(repo), normalize(repo.split("/", 1)[-1])}),
            }
        )
        repository_nodes.append(node)
        relations.append(relation(ROOT_ID, "inventories_repository", node["id"]))

    evidence_nodes = []
    for section in ("pillars", "law", "spec_corpus", "core_infra"):
        for index, record in enumerate(foundation.get(section, [])):
            target = record.get("raw_url") or first_url(record.get("url"))
            locked = bool(record.get("locked"))
            role = "integrity_evidence" if locked else "supporting_evidence"
            node = add_node(
                {
                    "id": evidence_id(section, record),
                    "type": "evidence",
                    "label": record.get("spec")
                    or record.get("doc")
                    or record.get("role")
                    or record["repo"],
                    "repo": record["repo"],
                    "canonical_protocol_identity": canonical_protocol_identity(
                        str(record.get("spec") or "")
                    ),
                    "foundation_section": section,
                    "lifecycle": "active",
                    "status": "resolved" if target else "unresolved",
                    "materiality": "required" if locked else "supporting",
                    "material_profile": "foundation-locked"
                    if locked
                    else "foundation-supporting",
                    "required_source_roles": [role],
                    "sources": [
                        source_record(
                            role,
                            True,
                            target,
                            availability="declared" if target else "unresolved",
                            sha256=record.get("sha256") if locked else None,
                        )
                    ],
                    "entry_points": (
                        [
                            {
                                "kind": "evidence_read",
                                "target": target,
                                "method": "GET",
                                "read_only": True,
                                "safe_for_crawl": True,
                            }
                        ]
                        if target
                        else []
                    ),
                    "conformance": "not_assessed",
                    "aliases": evidence_aliases(record),
                    "display": {
                        "foundation_section": section,
                        "foundation_index": index,
                        **copy.deepcopy(record),
                    },
                }
            )
            evidence_nodes.append(node)
            relations.extend(
                [
                    relation("artifact:foundation.json", "declares", node["id"]),
                    relation(node["id"], "uses_artifact", "artifact:foundation.json"),
                    relation(node["id"], "owned_by", repo_id(record["repo"])),
                ]
            )

    for protocol in protocol_nodes:
        protocol_source = protocol["sources"][0].get("target")
        for evidence in evidence_nodes:
            evidence_source = evidence["sources"][0].get("target")
            if protocol_source and protocol_source == evidence_source:
                relations.append(relation(protocol["id"], "supported_by", evidence["id"]))
            elif (
                protocol["canonical_protocol_identity"]
                and protocol["canonical_protocol_identity"]
                == evidence["canonical_protocol_identity"]
                and protocol["repo"].lower() == evidence["repo"].lower()
            ):
                relations.append(relation(protocol["id"], "supported_by", evidence["id"]))

    route_nodes = []
    route_relations = []
    resolver_nodes = protocol_nodes + evidence_nodes + artifact_nodes + repository_nodes
    for index, route in enumerate(registry["router"]):
        target_ids = [resolve_route_target(label, resolver_nodes) for label in route["use"]]
        node = add_node(
            {
                "id": route_id(route["situation"]),
                "type": "route",
                "label": route["situation"],
                "route_index": index,
                "target_ids": target_ids,
                "lifecycle": "active",
                "status": "resolved",
                "materiality": "routing",
                "material_profile": "route",
                "required_source_roles": [],
                "sources": [],
                "entry_points": [],
                "conformance": "not_applicable",
                "aliases": [],
                "display": copy.deepcopy(route),
            }
        )
        route_nodes.append(node)
        route_relations.append(relation(ROOT_ID, "indexes_route", node["id"]))
        route_relations.append(relation(node["id"], "uses_artifact", "artifact:registry.json"))
        for target_index, (display_target, target_id) in enumerate(zip(route["use"], target_ids)):
            route_relations.append(
                {
                    "from": node["id"],
                    "type": "routes_to",
                    "to": target_id,
                    "order": target_index,
                    "display_target": display_target,
                }
            )
    relations.extend(route_relations)

    base_nodes = list(nodes)
    for text in registry["collisions_and_gaps"]:
        kind = issue_kind(text)
        related = _related_nodes(text, base_nodes)
        issue = {
            "id": issue_id(kind, text),
            "type": "issue",
            "kind": kind,
            "summary": text,
            "severity": "blocking" if kind in {"gap", "security"} else "advisory",
            "blocking": kind in {"gap", "security"},
            "related_node_ids": related or [ROOT_ID],
            "source": "registry.collisions_and_gaps",
        }
        issues.append(issue)

    for protocol in protocol_nodes:
        if protocol["sources"][0]["availability"] == "unresolved":
            text = (
                f"{protocol['label']} in {protocol['repo']} has no exact canonical material URL; "
                "the routing display is retained, but exhaustive reading cannot claim this node complete."
            )
            issues.append(
                {
                    "id": issue_id("material", protocol["id"]),
                    "type": "issue",
                    "kind": "material",
                    "summary": text,
                    "severity": "blocking",
                    "blocking": True,
                    "related_node_ids": [protocol["id"], repo_id(protocol["repo"])],
                    "source": "generated.required_material",
                    "source_role": "canonical_material",
                }
            )

    for repository in repository_nodes:
        if repository["sources"][0]["availability"] == "unresolved":
            text = (
                f"{repository['repo']} has no readable standalone repository; "
                "repository identity remains required and explicitly unresolved."
            )
            issues.append(
                {
                    "id": issue_id("material", repository["id"]),
                    "type": "issue",
                    "kind": "material",
                    "summary": text,
                    "severity": "blocking",
                    "blocking": True,
                    "related_node_ids": [repository["id"]],
                    "source": "generated.required_material",
                    "source_role": "repository_identity",
                }
            )

    issue_nodes = []
    for issue in issues:
        node = add_node(
            {
                "id": issue["id"],
                "type": "issue",
                "label": issue["summary"],
                "lifecycle": "not_applicable",
                "status": "unresolved" if issue["blocking"] else "informational",
                "materiality": "gap" if issue["blocking"] else "informational",
                "material_profile": "issue",
                "required_source_roles": [],
                "sources": [],
                "entry_points": [],
                "conformance": "not_applicable",
                "aliases": [],
                "display": copy.deepcopy(issue),
            }
        )
        issue_nodes.append(node)
        relations.append(relation(ROOT_ID, "documents_issue", node["id"]))
        for target_id in issue["related_node_ids"]:
            relations.append(relation(node["id"], "affects", target_id))
            if target_id in protocol_by_id:
                relations.append(relation(target_id, "has_issue", node["id"]))

    relations = sorted(
        {
            (
                item["from"],
                item["type"],
                item["to"],
                item.get("order"),
                item.get("display_target"),
            ): item
            for item in relations
        }.values(),
        key=lambda item: (
            item["from"],
            item["type"],
            item.get("order", -1),
            item["to"],
            item.get("display_target", ""),
        ),
    )

    crawl = {
        "spec": SPEC,
        "generated": generated,
        "what": (
            "The deterministic exhaustive read-only crawl graph for the RAPP spine. "
            "It preserves every rapp-spine/1.0 display field while adding exact typed targets, "
            "material requirements, structured gaps, safety metadata, and completion semantics."
        ),
        "inputs": {
            "registry": {"path": "registry.json", "sha256": registry_sha},
            "foundation": {"path": "foundation.json", "sha256": foundation_sha},
        },
        "safety": {
            "mode": "read_only",
            "allowed_methods": ["GET", "HEAD"],
            "forbidden_actions": ["install", "run", "deploy", "execute", "write"],
            "policy": (
                "A crawler may read only entry points marked safe_for_crawl=true. "
                "Display-only install/run/deploy text is retained for compatibility and never executed."
            ),
        },
        "material_profiles": copy.deepcopy(MATERIAL_PROFILES),
        "layers_order": copy.deepcopy(registry["layers_order"]),
        "doctrine": registry["doctrine"],
        "layers": copy.deepcopy(registry["layers"]),
        "router": copy.deepcopy(registry["router"]),
        "registry": copy.deepcopy(registry["registry"]),
        "collisions_and_gaps": copy.deepcopy(registry["collisions_and_gaps"]),
        "graph": {
            "spec": GRAPH_SPEC,
            "root_id": ROOT_ID,
            "nodes": nodes,
            "relations": relations,
            "traversal_order": ordered,
        },
        "plans": {
            "full": {
                "spec": PLAN_TEMPLATE_SPEC,
                "produces": PLAN_SPEC,
                "graph_spec": SPEC,
                "mode": "full",
                "read_only": True,
                "node_ids": list(ordered),
            }
        },
        "issues": issues,
    }
    validate_crawl(crawl)
    return crawl


def validate_crawl(crawl):
    errors = []
    if crawl.get("spec") != SPEC:
        errors.append(f"spec must be {SPEC}")
    graph = crawl.get("graph")
    if not isinstance(graph, dict):
        raise ValueError("crawl graph is missing")
    if graph.get("spec") != GRAPH_SPEC:
        errors.append(f"graph.spec must be {GRAPH_SPEC}")
    nodes = graph.get("nodes", [])
    relations = graph.get("relations", [])
    ids = [node.get("id") for node in nodes]
    id_set = set(ids)
    if len(ids) != len(id_set):
        errors.append("graph node IDs are not unique")
    for node in nodes:
        for field in (
            "id",
            "type",
            "label",
            "lifecycle",
            "status",
            "materiality",
            "material_profile",
            "required_source_roles",
            "sources",
            "entry_points",
            "conformance",
        ):
            if field not in node:
                errors.append(f"{node.get('id', '<unknown>')} lacks {field}")
        for field, allowed in NODE_ENUMS.items():
            if node.get(field) not in allowed:
                errors.append(f"{node.get('id')} has invalid {field}: {node.get(field)!r}")
        profile = crawl["material_profiles"].get(node.get("material_profile"))
        if profile is None:
            errors.append(f"{node.get('id')} has unknown material profile")
        else:
            required_roles = profile.get("required_source_roles", [])
            if node.get("required_source_roles") != required_roles:
                errors.append(
                    f"{node.get('id')} required_source_roles drift from its profile"
                )
            for role in required_roles:
                required_matches = [
                    source
                    for source in node.get("sources", [])
                    if source.get("role") == role and source.get("required") is True
                ]
                if not required_matches:
                    errors.append(
                        f"{node.get('id')} lacks required=true source role {role}"
                    )
        for source in node.get("sources", []):
            target = source.get("target")
            if source.get("required") and target and not target.startswith(
                ("https://", "http://")
            ):
                errors.append(
                    f"{node.get('id')} required source {source.get('role')} is not absolute"
                )
    for item in relations:
        if item.get("from") not in id_set or item.get("to") not in id_set:
            errors.append(f"dangling relation: {item}")
    relation_keys = {
        (item.get("from"), item.get("type"), item.get("to")) for item in relations
    }
    for node in nodes:
        if node.get("type") == "evidence" and (
            node["id"],
            "uses_artifact",
            "artifact:foundation.json",
        ) not in relation_keys:
            errors.append(f"{node['id']} lacks its foundation artifact dependency")
    protocols_by_identity = {
        (node.get("repo", "").lower(), node.get("canonical_protocol_identity")): node
        for node in nodes
        if node.get("type") == "protocol"
    }
    for repo, legacy_identity, canonical_identity in CANONICAL_WIRE_RELATIONS:
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
            errors.append(
                f"missing canonical wire relation: {repo} "
                f"{legacy_identity} -> {canonical_identity}"
            )
    order = graph.get("traversal_order", [])
    if len(order) != len(set(order)) or set(order) != id_set:
        errors.append("traversal_order must contain every node exactly once")
    full_plan = crawl.get("plans", {}).get("full", {})
    if full_plan.get("spec") != PLAN_TEMPLATE_SPEC:
        errors.append(f"plans.full.spec must be {PLAN_TEMPLATE_SPEC}")
    if full_plan.get("produces") != PLAN_SPEC:
        errors.append(f"plans.full.produces must be {PLAN_SPEC}")
    if full_plan.get("graph_spec") != SPEC:
        errors.append(f"plans.full.graph_spec must be {SPEC}")
    if full_plan.get("mode") != "full" or full_plan.get("read_only") is not True:
        errors.append("plans.full must be a read-only full plan")
    full_plan_ids = full_plan.get("node_ids")
    if full_plan_ids != order:
        errors.append("plans.full.node_ids must exactly equal graph.traversal_order")
    if graph.get("root_id") not in id_set:
        errors.append("root_id is missing")

    route_nodes = [node for node in nodes if node["type"] == "route"]
    route_edges = defaultdict(list)
    for item in relations:
        if item["type"] == "routes_to":
            route_edges[item["from"]].append((item.get("order"), item["to"]))
    for node in route_nodes:
        if len(node.get("target_ids", [])) != len(node.get("display", {}).get("use", [])):
            errors.append(f"{node['id']} does not resolve every display target")
        exact_targets = [
            target_id for _, target_id in sorted(route_edges[node["id"]], key=lambda item: item[0])
        ]
        if node.get("target_ids", []) != exact_targets:
            errors.append(f"{node['id']} route relations do not match target_ids")

    adjacency = defaultdict(list)
    for item in relations:
        adjacency[item["from"]].append(item["to"])
    seen = set()
    queue = deque([graph.get("root_id")])
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        queue.extend(adjacency[current])
    orphans = sorted(id_set - seen)
    if orphans:
        errors.append("orphan nodes: " + ", ".join(orphans))

    issue_ids = {issue.get("id") for issue in crawl.get("issues", [])}
    if len(issue_ids) != len(crawl.get("issues", [])):
        errors.append("structured issue IDs are not unique")
    for issue in crawl.get("issues", []):
        for target_id in issue.get("related_node_ids", []):
            if target_id not in id_set:
                errors.append(f"{issue.get('id')} references missing node {target_id}")

    if errors:
        raise ValueError("\n".join(errors))
    return []


def build_coverage(crawl):
    nodes = crawl["graph"]["nodes"]
    relations = crawl["graph"]["relations"]
    by_type = Counter(node["type"] for node in nodes)
    by_status = Counter(node["status"] for node in nodes)
    protocols = [node for node in nodes if node["type"] == "protocol"]
    unresolved = [
        node["id"]
        for node in protocols
        if any(
            source["required"] and source["availability"] == "unresolved"
            for source in node["sources"]
        )
    ]
    required_sources = [
        (node["id"], source)
        for node in nodes
        for source in node["sources"]
        if source["required"]
    ]
    all_unresolved = [
        {"node_id": node_id, "role": source["role"]}
        for node_id, source in required_sources
        if source["availability"] == "unresolved"
    ]
    blocking = [issue["id"] for issue in crawl["issues"] if issue["blocking"]]
    route_refs = sum(len(node["target_ids"]) for node in nodes if node["type"] == "route")
    return {
        "spec": "rapp-spine-coverage/1.0",
        "source_spec": crawl["spec"],
        "generated": crawl["generated"],
        "inputs": copy.deepcopy(crawl["inputs"]),
        "inventory": {
            "registry_entries_expected": len(crawl["registry"]),
            "registry_nodes_represented": len(protocols),
            "routes_expected": len(crawl["router"]),
            "route_nodes_represented": by_type["route"],
            "route_target_references": route_refs,
            "repositories_represented": by_type["repository"],
            "foundation_records_represented": by_type["evidence"],
        },
        "graph": {
            "nodes": len(nodes),
            "relations": len(relations),
            "nodes_by_type": dict(sorted(by_type.items())),
            "nodes_by_status": dict(sorted(by_status.items())),
            "orphans": [],
            "dangling_relations": [],
        },
        "required_material": {
            "protocols": len(protocols),
            "exact_targets": len(protocols) - len(unresolved),
            "unresolved": len(unresolved),
            "unresolved_node_ids": unresolved,
            "complete": not unresolved,
        },
        "all_required_sources": {
            "required": len(required_sources),
            "exact_targets": len(required_sources) - len(all_unresolved),
            "unresolved": len(all_unresolved),
            "unresolved_sources": all_unresolved,
            "complete": not all_unresolved,
        },
        "known_gaps": {
            "structured_issues": len(crawl["issues"]),
            "blocking": len(blocking),
            "blocking_issue_ids": blocking,
        },
        "estate_coverage_policy": {
            "verifier_input": "https://raw.githubusercontent.com/kody-w/rapp-map/main/estate-map.json",
            "requirement": "Every load_bearing estate repo must resolve to a repository node.",
            "enforced_by": "verify_spine.py",
        },
        "safety": copy.deepcopy(crawl["safety"]),
        "complete": not all_unresolved and not blocking,
    }


def ordered_sources(crawl):
    by_id = {node["id"]: node for node in crawl["graph"]["nodes"]}
    records = []
    seen = set()
    for node_id in crawl["graph"]["traversal_order"]:
        node = by_id[node_id]
        for source in node["sources"]:
            key = (node_id, source["role"], source.get("target"))
            if key in seen:
                continue
            seen.add(key)
            records.append(
                {
                    "node_id": node_id,
                    "node_type": node["type"],
                    "role": source["role"],
                    "required": source["required"],
                    "target": source.get("target"),
                    "availability": source["availability"],
                    "sha256": source.get("sha256"),
                }
            )
    return records


def render_llms(crawl):
    lines = [
        f"# Generated full ordered source list for {crawl['spec']}.",
        "# Generated by generate_crawl.py; do not edit by hand.",
        "# Format: ordinal | availability | role | typed node ID | exact read target",
        "",
    ]
    for index, source in enumerate(ordered_sources(crawl), 1):
        target = source["target"] or "UNRESOLVED"
        lines.append(
            f"{index:03d} | {source['availability']} | {source['role']} | "
            f"{source['node_id']} | {target}"
        )
    lines.append("")
    return "\n".join(lines)


def render_human(crawl, coverage):
    nodes = crawl["graph"]["nodes"]
    node_by_id = {node["id"]: node for node in nodes}
    lines = [
        "<!-- Generated by generate_crawl.py. Do not edit by hand. -->",
        "",
        f"# Exhaustive Crawl Graph — `{crawl['spec']}`",
        "",
        "`python3 crawl.py --full` traverses this complete inventory in read-only mode. "
        "It never executes the retained install/run/deploy display text.",
        "",
        "## Coverage",
        "",
        f"- Registry nodes: **{coverage['inventory']['registry_nodes_represented']} / "
        f"{coverage['inventory']['registry_entries_expected']}**",
        f"- Route nodes: **{coverage['inventory']['route_nodes_represented']} / "
        f"{coverage['inventory']['routes_expected']}**",
        f"- Repository nodes: **{coverage['inventory']['repositories_represented']}**",
        f"- Exact required protocol sources: **{coverage['required_material']['exact_targets']} / "
        f"{coverage['required_material']['protocols']}**",
        f"- Structured issues: **{coverage['known_gaps']['structured_issues']}** "
        f"({coverage['known_gaps']['blocking']} blocking)",
        "",
        "## Exact route targets",
        "",
        "| Situation | Display target | Exact node ID |",
        "|---|---|---|",
    ]
    for node in (item for item in nodes if item["type"] == "route"):
        for label, target_id in zip(node["display"]["use"], node["target_ids"]):
            escaped_situation = markdown_escape(node["label"])
            escaped_label = markdown_escape(label)
            lines.append(
                f"| {escaped_situation} | {escaped_label} | `{target_id}` |"
            )

    lines.extend(
        [
            "",
            "## Full deterministic traversal",
            "",
            "| # | Typed node ID | Type | Lifecycle | Status | Materiality | Required source |",
            "|---:|---|---|---|---|---|---|",
        ]
    )
    for index, node_id in enumerate(crawl["graph"]["traversal_order"], 1):
        node = node_by_id[node_id]
        required = [
            source.get("target") or "UNRESOLVED"
            for source in node["sources"]
            if source["required"]
        ]
        required_cell = markdown_escape("<br>".join(required)) or "—"
        lines.append(
            f"| {index} | `{node_id}` | {node['type']} | {node['lifecycle']} | "
            f"{node['status']} | {node['materiality']} | "
            f"{required_cell} |"
        )

    unresolved = [
        node
        for node in nodes
        if any(
            source["required"] and source["availability"] == "unresolved"
            for source in node["sources"]
        )
    ]
    lines.extend(
        [
            "",
            "## Required material gaps",
            "",
            "| Node | Required role | Status |",
            "|---|---|---|",
        ]
    )
    for node in unresolved:
        roles = ", ".join(
            source["role"]
            for source in node["sources"]
            if source["required"] and source["availability"] == "unresolved"
        )
        lines.append(f"| `{node['id']}` | {roles} | unresolved |")
    lines.extend(
        [
            "",
            "Run `python3 generate_crawl.py --check` to prove this rendering, "
            "`crawl.json`, `coverage.json`, and `llms-full.txt` are fresh.",
            "",
        ]
    )
    return "\n".join(lines)


def build_artifacts(
    registry=None,
    foundation=None,
    registry_bytes=None,
    foundation_bytes=None,
):
    if registry is None:
        registry_bytes = REGISTRY.read_bytes()
        registry = json.loads(registry_bytes)
    elif registry_bytes is None:
        registry_bytes = json_text(registry).encode("utf-8")
    if foundation is None:
        foundation_bytes = FOUNDATION.read_bytes()
        foundation = json.loads(foundation_bytes)
    elif foundation_bytes is None:
        foundation_bytes = json_text(foundation).encode("utf-8")
    crawl = build_crawl(
        registry,
        foundation,
        registry_bytes=registry_bytes,
        foundation_bytes=foundation_bytes,
    )
    coverage = build_coverage(crawl)
    return {
        "crawl.json": json_text(crawl),
        "coverage.json": json_text(coverage),
        "llms-full.txt": render_llms(crawl),
        "CRAWL_GRAPH.md": render_human(crawl, coverage),
    }


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if generated files are stale")
    args = parser.parse_args(argv)
    artifacts = build_artifacts()
    if args.check:
        stale = [
            name
            for name, expected in artifacts.items()
            if not OUTPUTS[name].exists()
            or OUTPUTS[name].read_text(encoding="utf-8") != expected
        ]
        if stale:
            raise SystemExit("stale generated crawl artifacts: " + ", ".join(stale))
        return 0
    for name, content in artifacts.items():
        OUTPUTS[name].write_text(content, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
