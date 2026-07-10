import json
import subprocess
import sys
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import crawl  # noqa: E402
import verify_spine  # noqa: E402,F401


class SpineContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spine = crawl.load()

    def test_machine_documents_are_valid_json(self):
        for filename in ("registry.json", "foundation.json", "index.json"):
            with self.subTest(filename=filename):
                with (ROOT / filename).open(encoding="utf-8") as handle:
                    self.assertIsInstance(json.load(handle), dict)

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
        with (ROOT / "foundation.json").open(encoding="utf-8") as handle:
            foundation = json.load(handle)
        kernel = next(p for p in foundation["pillars"] if p["spec"] == "rapp-agent/1.0")
        self.assertEqual(kernel["version"], "0.6.16")
        self.assertIn(f"/{kernel['commit']}/", kernel["raw_url"])
        self.assertIsNone(kernel["release_tag"])

    def test_every_locked_foundation_record_has_proof(self):
        with (ROOT / "foundation.json").open(encoding="utf-8") as handle:
            foundation = json.load(handle)
        locked = [record for record in verify_spine._iter(foundation) if record.get("locked")]
        self.assertGreater(len(locked), 0)
        for record in locked:
            with self.subTest(record=record.get("spec") or record.get("doc")):
                self.assertIsInstance(record.get("raw_url"), str)
                self.assertTrue(verify_spine.valid_sha256(record.get("sha256")))

    def test_rendered_spine_contains_all_layers_in_order(self):
        text = (ROOT / "SPINE.md").read_text(encoding="utf-8")
        positions = []
        for layer in self.spine["layers_order"]:
            marker = f"### {layer}"
            positions.append(text.index(marker))
        self.assertEqual(positions, sorted(positions))

    def test_rendered_spine_matches_registry(self):
        subprocess.run(
            [sys.executable, str(ROOT / "render_spine.py"), "--check"],
            check=True,
        )

    def test_registry_has_no_duplicate_spec_ids(self):
        counts = Counter(entry["spec_id"] for entry in self.spine["registry"])
        self.assertFalse({spec: count for spec, count in counts.items() if count > 1})


if __name__ == "__main__":
    unittest.main()
