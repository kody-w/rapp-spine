import ast
import contextlib
import copy
import io
import json
import subprocess
import sys
import unittest
from collections import Counter, defaultdict
from pathlib import Path
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import crawl  # noqa: E402
import generate_crawl  # noqa: E402
import verify_spine  # noqa: E402


class _SpineFixture:
    @classmethod
    def setUpClass(cls):
        cls.spine = crawl.load()
        cls.crawl = crawl.load_crawl()
        cls.nodes = {
            node["id"]: node for node in cls.crawl["graph"]["nodes"]
        }
        with (ROOT / "foundation.json").open(encoding="utf-8") as handle:
            cls.foundation = json.load(handle)
        with (ROOT / "coverage.json").open(encoding="utf-8") as handle:
            cls.coverage = json.load(handle)


class SpineContractTests(_SpineFixture, unittest.TestCase):
    def test_machine_documents_are_valid_json(self):
        for filename in (
            "registry.json",
            "foundation.json",
            "index.json",
            "crawl.json",
            "coverage.json",
        ):
            with self.subTest(filename=filename):
                with (ROOT / filename).open(encoding="utf-8") as handle:
                    self.assertIsInstance(json.load(handle), dict)

    def test_crawl_is_backward_compatible_1_1_surface(self):
        self.assertEqual(self.crawl["spec"], "rapp-spine/1.1")
        for field in (
            "layers_order",
            "doctrine",
            "layers",
            "router",
            "registry",
            "collisions_and_gaps",
        ):
            with self.subTest(field=field):
                self.assertEqual(self.crawl[field], self.spine[field])

    def test_layer_order_starts_with_kernel(self):
        self.assertEqual(
            self.spine["layers_order"],
            ["kernel", "map", "runtime", "distribution", "identity", "network", "leviathan"],
        )

    def test_every_router_situation_routes_to_itself_first(self):
        for route in self.spine["router"]:
            with self.subTest(situation=route["situation"]):
                self.assertEqual(crawl.match(self.spine, route["situation"], n=1), [route])

    def test_openrappter_routes_to_consumer_substrate_distro(self):
        hits = crawl.match(self.spine, "openrappter", n=1)
        self.assertEqual(len(hits), 1)
        self.assertIn("consumer substrate-distro", hits[0]["use"][0])
        self.assertIn("agent.py", hits[0]["situation"])
        self.assertIn("Conversation is the control surface", hits[0]["why"])

    def test_spec_ids_have_one_owner(self):
        owners = {}
        for entry in self.spine["registry"]:
            owners.setdefault(entry["spec_id"], set()).add(entry["repo"])
        collisions = {spec: repos for spec, repos in owners.items() if len(repos) > 1}
        self.assertEqual(collisions, {})

    def test_callable_index_does_not_advertise_legacy_direct_route(self):
        with (ROOT / "index.json").open(encoding="utf-8") as handle:
            index = json.load(handle)
        self.assertNotIn("run an agent directly (no LLM, ~tens of ms)", index["ride"])
        self.assertNotIn(
            "POST http://<brainstem>:7071/api/agent",
            json.dumps(index["ride"]),
        )

    def test_kernel_foundation_pin_is_immutable(self):
        kernel = next(
            pillar
            for pillar in self.foundation["pillars"]
            if pillar["spec"] == "rapp-agent/1.0"
        )
        self.assertEqual(kernel["version"], "0.6.16")
        self.assertIn(f"/{kernel['commit']}/", kernel["raw_url"])
        self.assertIsNone(kernel["release_tag"])

    def test_every_locked_foundation_record_has_proof(self):
        locked = [
            record
            for record in verify_spine._iter(self.foundation)
            if record.get("locked")
        ]
        self.assertGreater(len(locked), 0)
        for record in locked:
            with self.subTest(record=record.get("spec") or record.get("doc")):
                self.assertIsInstance(record.get("raw_url"), str)
                self.assertTrue(verify_spine.valid_sha256(record.get("sha256")))

    def test_rendered_spine_contains_all_layers_in_order(self):
        text = (ROOT / "SPINE.md").read_text(encoding="utf-8")
        positions = []
        for layer in self.spine["layers_order"]:
            positions.append(text.index(f"### {layer}"))
        self.assertEqual(positions, sorted(positions))

    def test_rendered_spine_matches_registry(self):
        subprocess.run(
            [sys.executable, str(ROOT / "render_spine.py"), "--check"],
            check=True,
        )

    def test_registry_has_no_duplicate_spec_ids(self):
        counts = Counter(entry["spec_id"] for entry in self.spine["registry"])
        self.assertFalse({spec: count for spec, count in counts.items() if count > 1})


class CrawlGraphTests(_SpineFixture, unittest.TestCase):
    def test_typed_node_ids_are_unique_and_complete(self):
        ids = [node["id"] for node in self.crawl["graph"]["nodes"]]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(set(ids), set(self.crawl["graph"]["traversal_order"]))
        for node in self.crawl["graph"]["nodes"]:
            self.assertIn(":", node["id"])
            for field in (
                "type",
                "lifecycle",
                "status",
                "materiality",
                "required_source_roles",
                "sources",
                "entry_points",
            ):
                self.assertIn(field, node)

    def test_all_registry_entries_are_graph_nodes(self):
        protocol_nodes = [
            node for node in self.nodes.values() if node["type"] == "protocol"
        ]
        self.assertEqual(len(protocol_nodes), len(self.spine["registry"]))
        by_index = {node["display"]["registry_index"]: node for node in protocol_nodes}
        self.assertEqual(set(by_index), set(range(len(self.spine["registry"]))))
        for index, entry in enumerate(self.spine["registry"]):
            self.assertEqual(by_index[index]["display"]["spec_id"], entry["spec_id"])
            self.assertEqual(by_index[index]["display"]["repo"], entry["repo"])

    def test_foundation_only_load_bearing_repos_are_inventory_nodes(self):
        repository_names = {
            node["repo"].lower()
            for node in self.nodes.values()
            if node["type"] == "repository"
        }
        for repo in (
            "kody-w/RAPP-Bible",
            "kody-w/rapp-hologram",
            "kody-w/rapp-oneclick-deploy",
        ):
            self.assertIn(repo.lower(), repository_names)

    def test_route_targets_are_exact_and_referentially_closed(self):
        route_errors = verify_spine.validate_route_integrity(self.crawl, self.spine)
        self.assertEqual(route_errors, [])
        route_nodes = [
            node for node in self.nodes.values() if node["type"] == "route"
        ]
        self.assertEqual(len(route_nodes), len(self.spine["router"]))
        for route in route_nodes:
            self.assertEqual(len(route["target_ids"]), len(route["display"]["use"]))
            for target_id in route["target_ids"]:
                self.assertIn(target_id, self.nodes)

    def test_alias_routes_emit_intended_fixed_targets(self):
        routes = {
            node["label"]: node
            for node in self.nodes.values()
            if node["type"] == "route"
        }
        law = routes[
            "What does the governing law say — is this change allowed, and which discipline/article governs it?"
        ]
        self.assertTrue(law["target_ids"][0].startswith("evidence:foundation/law/"))
        neighborhood = routes[
            "I'm implementing or documenting ANY neighborhood concern — peer, transport, session, sealed channel, agent-in-a-link."
        ]
        self.assertEqual(neighborhood["target_ids"][0], neighborhood["target_ids"][1])

    def test_leviathan_identity_links_foundation_evidence_and_rce_issue(self):
        legacy_id = "protocol:kody-w/leviathan/leviathan/1.0"
        replacement_id = "protocol:kody-w/leviathan/rapp-fleet-chat/1.0"
        evidence_id = next(
            node["id"]
            for node in self.nodes.values()
            if node["type"] == "evidence"
            and node.get("canonical_protocol_identity") == "leviathan/1.0"
            and node.get("repo", "").lower() == "kody-w/leviathan"
        )
        relation_keys = {
            (item["from"], item["type"], item["to"])
            for item in self.crawl["graph"]["relations"]
        }
        self.assertIn((legacy_id, "supported_by", evidence_id), relation_keys)
        self.assertIn(
            (legacy_id, "canonical_wire", replacement_id),
            relation_keys,
        )
        missing_wire = copy.deepcopy(self.crawl)
        missing_wire["graph"]["relations"] = [
            item
            for item in missing_wire["graph"]["relations"]
            if (
                item["from"],
                item["type"],
                item["to"],
            )
            != (legacy_id, "canonical_wire", replacement_id)
        ]
        with self.assertRaisesRegex(ValueError, "missing canonical wire relation"):
            crawl.build_plan(missing_wire, mode="full")
        self.assertIn(
            (evidence_id, "uses_artifact", "artifact:foundation.json"),
            relation_keys,
        )
        broken = copy.deepcopy(self.crawl)
        broken["graph"]["relations"] = [
            item
            for item in broken["graph"]["relations"]
            if (
                item["from"],
                item["type"],
                item["to"],
            )
            != (evidence_id, "uses_artifact", "artifact:foundation.json")
        ]
        with self.assertRaisesRegex(ValueError, "foundation artifact dependency"):
            crawl.build_plan(broken, mode="full")

        rce_issue = next(
            issue
            for issue in self.crawl["issues"]
            if issue["summary"].startswith("SECURITY GAP:")
        )
        self.assertIn(legacy_id, rce_issue["related_node_ids"])
        self.assertIn(replacement_id, rce_issue["related_node_ids"])

        hits = crawl.match(
            self.crawl,
            "run several brainstem nodes as a signed fleet",
            n=1,
        )
        route = crawl.route_nodes_for_hits(self.crawl, hits)[0]
        plan = crawl.build_plan(
            self.crawl,
            mode="scoped",
            route_ids=[route["id"]],
            situation="leviathan fleet",
            batch_size=500,
        )
        self.assertIn(legacy_id, plan["node_ids"])
        self.assertIn(replacement_id, plan["node_ids"])
        self.assertIn(evidence_id, plan["node_ids"])
        self.assertIn("artifact:registry.json", plan["node_ids"])
        self.assertIn("artifact:foundation.json", plan["node_ids"])
        fleet_sources = [
            source["target"]
            for source in plan["read_targets"]
            if source["node_id"] == replacement_id and source.get("target")
        ]
        self.assertEqual(
            fleet_sources,
            ["https://raw.githubusercontent.com/kody-w/leviathan/main/FLEET_CHAT.md"],
        )
        receipt = crawl.build_receipt(
            self.crawl,
            plan,
            crawl.unprobed_sources(plan),
        )
        self.assertIn(
            rce_issue["id"],
            receipt["completion"]["known_gaps"]["blocking_issue_ids"],
        )

    def test_heuristic_route_resolution_fails_on_ambiguity(self):
        synthetic = [
            {"id": "protocol:a", "type": "protocol", "aliases": ["same"], "repo": "x/a"},
            {"id": "protocol:b", "type": "protocol", "aliases": ["same"], "repo": "x/b"},
        ]
        with self.assertRaisesRegex(ValueError, "ambiguous route target"):
            generate_crawl.resolve_route_target("same", synthetic)

    def test_graph_has_no_dangling_relations_or_orphans(self):
        health = crawl.graph_health(self.crawl)
        self.assertEqual(health["dangling_relations"], [])
        self.assertEqual(health["orphan_node_ids"], [])

    def test_full_plan_copy_has_exact_traversal_parity(self):
        self.assertEqual(
            self.crawl["plans"]["full"]["spec"],
            "rapp-crawl-plan-template/1.0",
        )
        self.assertEqual(
            self.crawl["plans"]["full"]["produces"],
            "rapp-crawl-plan/1.0",
        )
        self.assertEqual(
            self.crawl["plans"]["full"]["node_ids"],
            self.crawl["graph"]["traversal_order"],
        )
        broken = copy.deepcopy(self.crawl)
        broken["plans"]["full"]["node_ids"] = broken["plans"]["full"]["node_ids"][:-1]
        with self.assertRaisesRegex(ValueError, "plans.full.node_ids"):
            generate_crawl.validate_crawl(broken)
        with self.assertRaisesRegex(ValueError, "plans.full.node_ids"):
            crawl.build_plan(broken, mode="full", batch_size=1000)
        plan = crawl.build_plan(self.crawl, mode="full", batch_size=1000)
        self.assertEqual(plan["node_ids"], self.crawl["graph"]["traversal_order"])

    def test_every_rapp_crawl_plan_object_validates(self):
        def dictionaries(value):
            if isinstance(value, dict):
                yield value
                for child in value.values():
                    yield from dictionaries(child)
            elif isinstance(value, list):
                for child in value:
                    yield from dictionaries(child)

        runtime_plan = crawl.build_plan(self.crawl, mode="full", batch_size=1000)
        candidates = [
            value
            for value in [*dictionaries(self.crawl), runtime_plan]
            if value.get("spec") == "rapp-crawl-plan/1.0"
        ]
        self.assertEqual(candidates, [runtime_plan])
        for plan in candidates:
            self.assertIs(crawl.validate_plan(plan, self.crawl), plan)

    def test_unsupported_crawl_and_plan_versions_fail_closed(self):
        unsupported_crawl = copy.deepcopy(self.crawl)
        unsupported_crawl["spec"] = "rapp-spine/2.0"
        with self.assertRaisesRegex(ValueError, "unsupported crawl spec"):
            crawl.build_plan(unsupported_crawl, mode="full")

        unsupported_graph = copy.deepcopy(self.crawl)
        unsupported_graph["graph"]["spec"] = "rapp-crawl-graph/2.0"
        with self.assertRaisesRegex(ValueError, "unsupported graph schema"):
            crawl.build_plan(unsupported_graph, mode="full")

        plan = crawl.build_plan(self.crawl, mode="full", batch_size=1000)
        plan["spec"] = "rapp-crawl-plan/2.0"
        with self.assertRaisesRegex(ValueError, "unsupported plan schema"):
            crawl.unprobed_sources(plan)
        with self.assertRaisesRegex(ValueError, "unsupported plan schema"):
            crawl.build_receipt(self.crawl, plan, {})

    def test_required_material_profiles_have_no_silent_gaps(self):
        self.assertEqual(verify_spine.validate_material_profiles(self.crawl), [])
        unresolved = [
            node
            for node in self.nodes.values()
            if node["type"] == "protocol"
            and node["sources"][0]["availability"] == "unresolved"
        ]
        self.assertEqual(len(unresolved), 34)
        issues_by_node = defaultdict(list)
        for issue in self.crawl["issues"]:
            for node_id in issue["related_node_ids"]:
                issues_by_node[node_id].append(issue)
        for node in unresolved:
            self.assertTrue(
                any(
                    issue.get("source") == "generated.required_material"
                    and issue.get("source_role") == "canonical_material"
                    for issue in issues_by_node[node["id"]]
                )
            )
        unresolved_repositories = [
            node
            for node in self.nodes.values()
            if node["type"] == "repository"
            and node["sources"][0]["availability"] == "unresolved"
        ]
        self.assertEqual(
            {node["repo"] for node in unresolved_repositories},
            {"kody-w/rapp_leviathan_factory", "kody-w/wrap_leviathan"},
        )

    def test_profile_required_role_rejects_required_false_source(self):
        broken = copy.deepcopy(self.crawl)
        artifact = next(
            node
            for node in broken["graph"]["nodes"]
            if node["id"] == "artifact:registry.json"
        )
        artifact["sources"][0]["required"] = False
        with self.assertRaisesRegex(ValueError, "required=true source role"):
            generate_crawl.validate_crawl(broken)
        self.assertTrue(
            any(
                "required=true source role" in error
                for error in verify_spine.validate_material_profiles(broken)
            )
        )

    def test_every_resolved_required_source_uses_an_absolute_url(self):
        for node in self.nodes.values():
            for source in node["sources"]:
                if source["required"] and source.get("target"):
                    self.assertTrue(
                        source["target"].startswith(("https://", "http://")),
                        f"{node['id']} has non-absolute source {source['target']!r}",
                    )

    def test_issue_classification_uses_token_boundaries(self):
        self.assertEqual(
            generate_crawl.issue_kind("SOURCE integrity and availability"),
            "clarification",
        )
        self.assertEqual(
            generate_crawl.issue_kind("The legacy route is an RCE."),
            "security",
        )

    def test_issue_repo_links_use_exact_repository_tokens(self):
        nodes = [
            {
                "id": "repo:kody-w/rapp",
                "repo": "kody-w/RAPP",
                "aliases": [],
            },
            {
                "id": "repo:kody-w/rapp-bible",
                "repo": "kody-w/RAPP-Bible",
                "aliases": [],
            },
        ]
        self.assertEqual(
            generate_crawl._related_nodes("See kody-w/RAPP-Bible.", nodes),
            ["repo:kody-w/rapp-bible"],
        )

    def test_safe_entry_points_are_read_only_and_display_actions_are_never_run(self):
        for node in self.nodes.values():
            for entry_point in node["entry_points"]:
                if entry_point.get("safe_for_crawl"):
                    self.assertTrue(entry_point["read_only"])
                    self.assertIn(entry_point["method"], {"GET", "HEAD"})
                    self.assertIn("target", entry_point)
                if entry_point["kind"] == "display_only":
                    self.assertFalse(entry_point["safe_for_crawl"])
                    self.assertEqual(entry_point["policy"], "never_execute")

    def test_full_plan_covers_every_graph_node_and_all_registry_nodes(self):
        plan = crawl.build_plan(self.crawl, mode="full", batch_size=17)
        self.assertEqual(plan["expected_node_ids"], self.crawl["graph"]["traversal_order"])
        self.assertEqual(plan["node_ids"], plan["expected_node_ids"])
        visited_protocols = sum(
            self.nodes[node_id]["type"] == "protocol" for node_id in plan["node_ids"]
        )
        self.assertEqual(visited_protocols, 58)
        self.assertGreater(plan["batch_count"], 1)
        required_roles = Counter(
            source["role"] for source in plan["read_targets"] if source["required"]
        )
        self.assertEqual(
            required_roles,
            Counter(
                {
                    "authoritative_input": 2,
                    "canonical_material": 58,
                    "integrity_evidence": 11,
                    "repository_identity": 46,
                    "supporting_evidence": 8,
                }
            ),
        )

    def test_scoped_plan_uses_fuzzy_selection_then_exact_graph_closure(self):
        hits = crawl.match(self.crawl, "openrappter", n=1)
        route_nodes = crawl.route_nodes_for_hits(self.crawl, hits)
        plan = crawl.build_plan(
            self.crawl,
            mode="scoped",
            route_ids=[route_nodes[0]["id"]],
            situation="openrappter",
            batch_size=50,
        )
        self.assertIn(route_nodes[0]["id"], plan["node_ids"])
        self.assertIn(route_nodes[0]["target_ids"][0], plan["node_ids"])
        self.assertIn(
            "repo:kody-w/openrappter",
            plan["node_ids"],
        )
        self.assertNotIn(
            "protocol:kody-w/rapp-frame-net/rapp-frame/2.0",
            plan["node_ids"],
        )

    def test_scoped_receipts_include_blocking_repo_and_root_issues(self):
        wrapped_hits = crawl.match(
            self.crawl,
            "create transport full digital being across five estates",
            n=1,
        )
        wrapped_route = crawl.route_nodes_for_hits(self.crawl, wrapped_hits)[0]
        wrapped_plan = crawl.build_plan(
            self.crawl,
            mode="scoped",
            route_ids=[wrapped_route["id"]],
            situation="wrapped organism",
            batch_size=500,
        )
        repository_issue_ids = {
            issue["id"]
            for issue in self.crawl["issues"]
            if issue.get("blocking")
            and issue.get("source_role") == "repository_identity"
        }
        self.assertTrue(repository_issue_ids.issubset(wrapped_plan["node_ids"]))
        wrapped_receipt = crawl.build_receipt(
            self.crawl,
            wrapped_plan,
            crawl.unprobed_sources(wrapped_plan),
        )
        self.assertTrue(
            repository_issue_ids.issubset(
                wrapped_receipt["completion"]["known_gaps"]["blocking_issue_ids"]
            )
        )

        governance_hits = crawl.match(
            self.crawl,
            "what does the governing law say",
            n=1,
        )
        governance_route = crawl.route_nodes_for_hits(self.crawl, governance_hits)[0]
        governance_plan = crawl.build_plan(
            self.crawl,
            mode="scoped",
            route_ids=[governance_route["id"]],
            situation="governance",
            batch_size=500,
        )
        root_issue_ids = {
            issue["id"]
            for issue in self.crawl["issues"]
            if issue.get("blocking")
            and self.crawl["graph"]["root_id"] in issue.get("related_node_ids", [])
        }
        self.assertTrue(root_issue_ids)
        self.assertTrue(root_issue_ids.issubset(governance_plan["node_ids"]))
        self.assertIn("artifact:registry.json", governance_plan["node_ids"])
        self.assertIn("artifact:foundation.json", governance_plan["node_ids"])
        governance_receipt = crawl.build_receipt(
            self.crawl,
            governance_plan,
            crawl.unprobed_sources(governance_plan),
        )
        self.assertTrue(
            root_issue_ids.issubset(
                governance_receipt["completion"]["known_gaps"]["blocking_issue_ids"]
            )
        )

    def test_batch_receipt_is_partial(self):
        plan = crawl.build_plan(self.crawl, mode="full", batch_size=10, batch=1)
        results = crawl.unprobed_sources(plan)
        for source in plan["read_targets"]:
            if source["required"] and source.get("target"):
                results[source["key"]] = {
                    "status": "read",
                    "target": source["target"],
                    "integrity": "verified"
                    if source.get("sha256")
                    else "not_pinned",
                }
        receipt = crawl.build_receipt(
            self.crawl,
            plan,
            results,
        )
        self.assertTrue(receipt["passed"])
        self.assertFalse(receipt["complete"])
        self.assertFalse(
            receipt["completion"]["inventory_graph_coverage"]["complete"]
        )
        sources = receipt["completion"]["source_integrity_availability"]
        self.assertEqual(sources["expected_required_sources"], 125)
        self.assertEqual(
            sources["visited_required_sources"],
            sum(source["required"] for source in plan["read_targets"]),
        )
        self.assertEqual(sum(sources["counts"].values()), 125)
        self.assertEqual(sum(sources["integrity"].values()), 125)
        self.assertEqual(
            sources["integrity"]["not_checkable"],
            sources["counts"]["not_read"],
        )

    def test_receipt_is_incomplete_when_required_material_is_unreadable(self):
        plan = crawl.build_plan(
            self.crawl,
            mode="full",
            batch_size=len(self.nodes),
        )
        results = crawl.unprobed_sources(plan)
        exact = next(
            source
            for source in plan["read_targets"]
            if source["required"] and source.get("target")
        )
        results[exact["key"]] = {
            "status": "unreadable",
            "target": exact["target"],
            "integrity": "not_checkable",
        }
        receipt = crawl.build_receipt(self.crawl, plan, results)
        self.assertFalse(receipt["complete"])
        failures = receipt["completion"]["source_integrity_availability"]["failures"]
        self.assertTrue(
            any(
                failure["node_id"] == exact["node_id"]
                and failure["status"] == "unreadable"
                for failure in failures
            )
        )

    def test_receipt_stays_incomplete_when_only_known_unresolved_sources_remain(self):
        plan = crawl.build_plan(
            self.crawl,
            mode="full",
            batch_size=len(self.nodes),
        )
        results = {}
        for source in plan["read_targets"]:
            if source.get("target"):
                results[source["key"]] = {
                    "status": "read",
                    "target": source["target"],
                    "integrity": "verified"
                    if source.get("sha256")
                    else "not_pinned",
                }
            else:
                results[source["key"]] = {
                    "status": "unresolved",
                    "target": None,
                    "integrity": "not_checkable",
                }
        receipt = crawl.build_receipt(self.crawl, plan, results)
        self.assertTrue(receipt["passed"])
        self.assertFalse(receipt["complete"])
        self.assertFalse(
            receipt["completion"]["source_integrity_availability"]["complete"]
        )
        self.assertEqual(
            receipt["completion"]["source_integrity_availability"]["counts"],
            {"read": 89, "unresolved": 36},
        )

    def test_receipt_separates_all_completion_dimensions(self):
        plan = crawl.build_plan(
            self.crawl,
            mode="full",
            batch_size=len(self.nodes),
        )
        receipt = crawl.build_receipt(
            self.crawl,
            plan,
            crawl.unprobed_sources(plan),
        )
        self.assertEqual(
            {
                "inventory_graph_coverage",
                "graph_integrity",
                "source_integrity_availability",
                "known_gaps",
                "operational_conformance",
                "complete",
            },
            set(receipt["completion"]),
        )
        self.assertTrue(
            receipt["completion"]["inventory_graph_coverage"]["complete"]
        )
        self.assertFalse(
            receipt["completion"]["source_integrity_availability"]["complete"]
        )
        self.assertGreater(receipt["completion"]["known_gaps"]["blocking"], 0)

    def test_generator_validation_detects_orphan(self):
        broken = copy.deepcopy(self.crawl)
        orphan = next(
            node["id"]
            for node in broken["graph"]["nodes"]
            if node["type"] == "repository"
        )
        broken["graph"]["relations"] = [
            relation
            for relation in broken["graph"]["relations"]
            if relation["to"] != orphan and relation["from"] != orphan
        ]
        with self.assertRaisesRegex(ValueError, "orphan nodes"):
            generate_crawl.validate_crawl(broken)


class GeneratedSurfaceTests(_SpineFixture, unittest.TestCase):
    def test_python_311_grammar_accepts_runtime_tools(self):
        for filename in (
            "crawl.py",
            "generate_crawl.py",
            "render_spine.py",
            "verify_spine.py",
        ):
            with self.subTest(filename=filename):
                ast.parse(
                    (ROOT / filename).read_text(encoding="utf-8"),
                    filename=filename,
                    feature_version=(3, 11),
                )

    def test_generated_artifacts_are_fresh(self):
        subprocess.run(
            [sys.executable, str(ROOT / "generate_crawl.py"), "--check"],
            check=True,
        )

    def test_generation_is_deterministic_in_memory(self):
        self.assertEqual(
            generate_crawl.build_artifacts(),
            generate_crawl.build_artifacts(),
        )

    def test_coverage_matches_graph(self):
        self.assertEqual(self.coverage, generate_crawl.build_coverage(self.crawl))
        self.assertEqual(self.coverage["inventory"]["registry_nodes_represented"], 58)
        self.assertEqual(self.coverage["inventory"]["routes_expected"], 31)
        self.assertEqual(self.coverage["required_material"]["exact_targets"], 24)
        self.assertEqual(self.coverage["required_material"]["unresolved"], 34)
        self.assertEqual(self.coverage["all_required_sources"]["required"], 125)
        self.assertEqual(self.coverage["all_required_sources"]["exact_targets"], 89)
        self.assertEqual(self.coverage["all_required_sources"]["unresolved"], 36)
        self.assertFalse(self.coverage["complete"])

    def test_secondary_ai_and_human_surfaces_are_full(self):
        llm_text = (ROOT / "llms-full.txt").read_text(encoding="utf-8")
        human_text = (ROOT / "CRAWL_GRAPH.md").read_text(encoding="utf-8")
        self.assertIn("001 |", llm_text)
        self.assertIn("UNRESOLVED", llm_text)
        self.assertIn("## Exact route targets", human_text)
        self.assertIn("## Full deterministic traversal", human_text)
        self.assertIn("## Required material gaps", human_text)

    def test_legacy_json_situation_cli_is_preserved(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "crawl.py"), "--json", "openrappter"],
            check=True,
            text=True,
            capture_output=True,
        )
        value = json.loads(result.stdout)
        self.assertIsInstance(value, list)
        self.assertIn("OpenRappter", value[0]["situation"])

    def test_legacy_bare_cli_prints_spine_summary(self):
        result = subprocess.run(
            [sys.executable, str(ROOT / "crawl.py")],
            check=True,
            text=True,
            capture_output=True,
        )
        self.assertIn("THE RAPP SPINE", result.stdout)
        self.assertIn("ROUTER:", result.stdout)
        self.assertNotIn("COMPLETION RECEIPT", result.stdout)

    def test_full_json_cli_emits_plan_and_receipt_without_network(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "crawl.py"),
                "--full",
                "--json",
                "--no-probe",
                "--batch-size",
                "50",
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        value = json.loads(result.stdout)
        self.assertEqual(set(value), {"plan", "receipt"})
        self.assertEqual(value["plan"]["mode"], "full")
        self.assertEqual(len(value["plan"]["node_ids"]), len(self.nodes))
        self.assertTrue(value["receipt"]["passed"])
        self.assertFalse(value["receipt"]["complete"])
        self.assertIsInstance(
            value["receipt"]["completion"]["source_integrity_availability"]["counts"],
            dict,
        )
        self.assertIsInstance(
            value["receipt"]["completion"]["known_gaps"]["blocking"],
            int,
        )
        documented = (ROOT / "CRAWL.md").read_text(encoding="utf-8")
        self.assertIn('"plan": {"spec": "rapp-crawl-plan/1.0"', documented)
        self.assertIn('"receipt": {', documented)
        self.assertIn("`--receipt` emits the receipt object directly", documented)
        self.assertIn(".plan.node_ids | length", documented)
        self.assertIn(
            ".receipt.completion.source_integrity_availability.counts",
            documented,
        )
        self.assertIn(".receipt.completion.known_gaps.blocking", documented)

    def test_receipt_only_cli_matches_documented_jq_root(self):
        result = subprocess.run(
            [
                sys.executable,
                str(ROOT / "crawl.py"),
                "--full",
                "--receipt",
                "--no-probe",
            ],
            check=True,
            text=True,
            capture_output=True,
        )
        receipt = json.loads(result.stdout)
        self.assertEqual(receipt["spec"], "rapp-crawl-receipt/1.0")
        self.assertIsInstance(receipt["completion"]["known_gaps"]["blocking"], int)
        self.assertNotIn("receipt", receipt)
        documented = (ROOT / "CRAWL.md").read_text(encoding="utf-8")
        self.assertIn(".completion.known_gaps.blocking", documented)

    def test_legacy_layer_and_collision_json_flags_are_preserved(self):
        layer = subprocess.run(
            [sys.executable, str(ROOT / "crawl.py"), "--layer", "network", "--json"],
            check=True,
            text=True,
            capture_output=True,
        )
        collisions = subprocess.run(
            [sys.executable, str(ROOT / "crawl.py"), "--collisions", "--json"],
            check=True,
            text=True,
            capture_output=True,
        )
        self.assertEqual(json.loads(layer.stdout)[0]["layer"].split(" ", 1)[0], "network")
        self.assertEqual(len(json.loads(collisions.stdout)), 16)

    def test_local_mode_maps_canonical_artifact_urls_to_local_files(self):
        self.assertEqual(
            crawl.read_target(crawl.REMOTE, remote=False),
            (ROOT / "registry.json").read_bytes(),
        )
        self.assertEqual(
            crawl.read_target(
                "https://raw.githubusercontent.com/kody-w/rapp-spine/main/foundation.json",
                remote=False,
            ),
            (ROOT / "foundation.json").read_bytes(),
        )

    def test_remote_mode_uses_canonical_urls(self):
        remote_graph = copy.deepcopy(self.crawl)
        with mock.patch.object(crawl, "_load_url", return_value=remote_graph) as loader:
            self.assertEqual(crawl.load_crawl(remote=True), remote_graph)
            loader.assert_called_once_with(crawl.REMOTE_CRAWL)

        class Response:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return False

            def read(self):
                return b"remote registry"

        with mock.patch.object(
            crawl.urllib.request,
            "urlopen",
            return_value=Response(),
        ) as urlopen:
            self.assertEqual(
                crawl.read_target(crawl.REMOTE, remote=True),
                b"remote registry",
            )
            request = urlopen.call_args.args[0]
            self.assertEqual(request.full_url, crawl.REMOTE)

    def test_remote_origin_checks_use_fetched_bytes_and_surfaces(self):
        remote_registry = copy.deepcopy(self.spine)
        remote_registry["generated"] = "2099-01-01"
        registry_bytes = generate_crawl.json_text(remote_registry).encode("utf-8")
        foundation_bytes = (ROOT / "foundation.json").read_bytes()
        remote_artifacts = generate_crawl.build_artifacts(
            registry=remote_registry,
            foundation=self.foundation,
            registry_bytes=registry_bytes,
            foundation_bytes=foundation_bytes,
        )
        remote_crawl = json.loads(remote_artifacts["crawl.json"])

        self.assertEqual(
            verify_spine.input_hash_errors(
                remote_crawl,
                registry_bytes,
                foundation_bytes,
            ),
            [],
        )
        self.assertEqual(
            verify_spine.deterministic_artifact_errors(
                remote_registry,
                self.foundation,
                registry_bytes,
                foundation_bytes,
                remote_artifacts,
            ),
            [],
        )

        local_artifacts = {
            name: (ROOT / name).read_text(encoding="utf-8")
            for name in generate_crawl.OUTPUTS
        }
        self.assertTrue(
            verify_spine.deterministic_artifact_errors(
                remote_registry,
                self.foundation,
                registry_bytes,
                foundation_bytes,
                local_artifacts,
            )
        )

    def test_remote_verifier_fixture_never_uses_local_generated_artifacts(self):
        remote_registry = copy.deepcopy(self.spine)
        remote_registry["generated"] = "2099-02-02"
        protocol_bodies = {}
        for index, entry in enumerate(remote_registry["registry"]):
            target = f"https://fixture.test/protocol/{index}"
            entry["raw_url"] = target
            protocol_bodies[target] = entry["spec_id"].encode("utf-8")

        remote_foundation = copy.deepcopy(self.foundation)
        evidence_bodies = {}
        for section in ("pillars", "law", "spec_corpus", "core_infra"):
            for index, record in enumerate(remote_foundation[section]):
                target = f"https://fixture.test/evidence/{section}/{index}"
                record["locked"] = False
                record.pop("sha256", None)
                if section in {"pillars", "law"}:
                    record["raw_url"] = target
                else:
                    record["url"] = target
                evidence_bodies[target] = b"fixture evidence"

        registry_bytes = generate_crawl.json_text(remote_registry).encode("utf-8")
        foundation_bytes = generate_crawl.json_text(remote_foundation).encode("utf-8")
        artifacts = generate_crawl.build_artifacts(
            registry=remote_registry,
            foundation=remote_foundation,
            registry_bytes=registry_bytes,
            foundation_bytes=foundation_bytes,
        )
        remote_crawl = json.loads(artifacts["crawl.json"])
        estate = {
            "repos": [
                {"repo": node["repo"], "load_bearing": True}
                for node in remote_crawl["graph"]["nodes"]
                if node["type"] == "repository"
            ]
        }
        commit = "a" * 40
        pinned_spine = f"{verify_spine.SPINE_REPO_RAW}/{commit}"
        responses = {
            verify_spine.SPINE_COMMIT_API: json.dumps({"sha": commit}).encode("utf-8"),
            verify_spine.ESTATE: json.dumps(estate).encode("utf-8"),
            f"{pinned_spine}/registry.json": registry_bytes,
            f"{pinned_spine}/foundation.json": foundation_bytes,
            f"{pinned_spine}/crawl.json": artifacts["crawl.json"].encode("utf-8"),
            f"{pinned_spine}/coverage.json": artifacts["coverage.json"].encode(
                "utf-8"
            ),
            f"{pinned_spine}/llms-full.txt": artifacts["llms-full.txt"].encode(
                "utf-8"
            ),
            f"{pinned_spine}/CRAWL_GRAPH.md": artifacts["CRAWL_GRAPH.md"].encode(
                "utf-8"
            ),
            **protocol_bodies,
            **evidence_bodies,
        }

        calls = []

        def fake_get(url, timeout=20):
            del timeout
            calls.append(url)
            if url.startswith("https://github.com/"):
                return b"fixture repository"
            return responses.get(url)

        output = io.StringIO()
        with mock.patch.object(verify_spine, "get", side_effect=fake_get):
            with contextlib.redirect_stdout(output):
                result = verify_spine.main(["--json"])
        report = json.loads(output.getvalue())
        self.assertEqual(result, 0)
        self.assertTrue(report["passed"])
        self.assertFalse(report["complete"])
        self.assertTrue(report["invariants"]["I6_schema_shape"]["pass"])
        self.assertTrue(report["invariants"]["I10_deterministic_generation"]["pass"])
        self.assertEqual(
            report["invariants"]["I0_input_availability"]["expected_spine_origin"],
            "remote",
        )
        self.assertEqual(
            report["invariants"]["I0_input_availability"]["resolved_remote_commit"],
            commit,
        )
        self.assertTrue(
            all(
                origin["kind"] == "remote"
                for name, origin in report["invariants"]["I0_input_availability"][
                    "origins"
                ].items()
                if name != "estate_map"
            )
        )
        self.assertTrue(
            all(
                origin["target"].startswith(f"{pinned_spine}/")
                for name, origin in report["invariants"]["I0_input_availability"][
                    "origins"
                ].items()
                if name != "estate_map"
            )
        )
        self.assertFalse(
            any(url.startswith(f"{verify_spine.SPINE}/") for url in calls)
        )
        self.assertEqual(calls.count(f"{pinned_spine}/registry.json"), 1)
        self.assertEqual(calls.count(f"{pinned_spine}/foundation.json"), 1)
        self.assertEqual(calls.count(verify_spine.SPINE_COMMIT_API), 1)

    def test_remote_json_loader_ignores_local_file_and_returns_exact_body(self):
        body = b'{"origin":"remote"}\n'
        with mock.patch.object(verify_spine, "get", return_value=body) as getter:
            value, origin, loaded_body = verify_spine.load_json_source(
                "https://example.test/registry.json",
                ROOT / "registry.json",
                prefer_local=False,
            )
        self.assertEqual(value, {"origin": "remote"})
        self.assertEqual(origin["kind"], "remote")
        self.assertEqual(loaded_body, body)
        getter.assert_called_once_with("https://example.test/registry.json")

    def test_strict_local_loader_does_not_fall_back_to_remote(self):
        with mock.patch.object(verify_spine, "get") as getter:
            value, origin, body = verify_spine.load_json_source(
                "https://example.test/registry.json",
                ROOT / "missing-origin-fixture.json",
                prefer_local=True,
                allow_remote_fallback=False,
            )
        self.assertIsNone(value)
        self.assertIsNone(body)
        self.assertEqual(origin["kind"], "local")
        self.assertTrue(origin["missing"])
        getter.assert_not_called()


if __name__ == "__main__":
    unittest.main()
