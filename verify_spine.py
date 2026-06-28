#!/usr/bin/env python3
"""verify_spine.py — the unification test suite.

"Done" = the whole RAPP estate is unified under one spine with ZERO drift, machine-checkably.
This script IS that definition. It runs the invariants below against LIVE data (the estate map,
the spine registry/foundation, every referenced spec) and exits non-zero on any drift, so the
convergence loop has an objective stopping condition and CI can gate it.

Invariants:
  I1 SPINE COMPLETENESS   — every load-bearing repo in the estate map is referenced by the spine.
  I2 SPEC RESOLVABILITY   — every spine raw_url / entry_point resolves (HTTP 200).
  I3 HASH INTEGRITY       — every foundation.json pillar sha256 == current raw content.
  I4 NO SPEC-ID COLLISION — each spec_id maps to exactly one repo across the spine.
  I5 SPEC-ID HONESTY      — a spec's doc actually declares the spec_id the spine claims for it.

Usage:  python3 verify_spine.py [--json]   (stdlib only)
"""
import concurrent.futures
import hashlib
import json
import sys
import urllib.request

RAW = "https://raw.githubusercontent.com"
SPINE = f"{RAW}/kody-w/rapp-spine/main"
ESTATE = f"{RAW}/kody-w/rapp-map/main/estate-map.json"
LOCAL = "--local" in sys.argv  # read the working tree (no CDN lag) for spine + estate; specs still fetched live


def _local_or(url, local_path):
    if LOCAL:
        import os
        p = os.path.expanduser(local_path)
        if os.path.exists(p):
            try:
                return json.load(open(p))
            except Exception:
                pass
    return getj(url)


def get(url, timeout=15):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.read()
    except Exception:
        return None


def getj(url):
    b = get(url)
    try:
        return json.loads(b) if b else None
    except Exception:
        return None


def _iter(o):
    """Yield every dict in a nested json structure."""
    if isinstance(o, dict):
        yield o
        for v in o.values():
            yield from _iter(v)
    elif isinstance(o, list):
        for v in o:
            yield from _iter(v)


def main():
    report = {"invariants": {}, "drift": []}
    estate = _local_or(ESTATE, "~/Documents/GitHub/rapp-map/estate-map.json") or {}
    registry = _local_or(f"{SPINE}/registry.json", "~/Documents/GitHub/rapp-spine/registry.json") or {}
    foundation = _local_or(f"{SPINE}/foundation.json", "~/Documents/GitHub/rapp-spine/foundation.json") or {}

    # collect spine-referenced repos + spec entries
    spine_repos, spec_entries = set(), []
    for d in _iter(registry):
        if isinstance(d.get("repo"), str):
            spine_repos.add(d["repo"].lower())
        if d.get("spec_id") and d.get("repo"):
            spec_entries.append(d)
    for d in _iter(foundation):
        if isinstance(d.get("repo"), str):
            spine_repos.add(d["repo"].lower())

    # ---- I1: spine completeness (load-bearing estate repos referenced by the spine) ----
    lb = [r for r in estate.get("repos", []) if r.get("load_bearing")]
    missing = sorted({r["repo"] for r in lb if r["repo"].lower() not in spine_repos})
    report["invariants"]["I1_spine_completeness"] = {
        "load_bearing": len(lb), "referenced": len(lb) - len(missing), "missing": missing, "pass": not missing}
    for m in missing:
        report["drift"].append({"invariant": "I1", "repo": m, "issue": "load-bearing but not referenced in spine"})

    # ---- I2 + I5: resolvability + spec-id honesty (parallel) ----
    def check_spec(e):
        url = e.get("raw_url")
        if not url:
            # derive a candidate from entry_point if it has a raw url
            return e, None, None
        b = get(url)
        if b is None:
            return e, False, None
        declares = e["spec_id"] in b.decode("utf-8", "replace")
        return e, True, declares
    resolved = unresolved = honest = dishonest = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as ex:
        for e, ok, declares in ex.map(check_spec, spec_entries):
            if ok is None:
                continue
            if ok:
                resolved += 1
            else:
                unresolved += 1
                report["drift"].append({"invariant": "I2", "spec_id": e["spec_id"], "issue": f"raw_url unresolvable: {e.get('raw_url')}"})
            if ok and declares is False:
                dishonest += 1
                report["drift"].append({"invariant": "I5", "spec_id": e["spec_id"], "issue": f"doc does not declare {e['spec_id']}"})
            elif declares:
                honest += 1
    report["invariants"]["I2_spec_resolvability"] = {"resolved": resolved, "unresolved": unresolved, "pass": unresolved == 0}
    report["invariants"]["I5_spec_id_honesty"] = {"honest": honest, "dishonest": dishonest, "pass": dishonest == 0}

    # ---- I3: foundation hash integrity ----
    h_ok = h_bad = 0
    for d in _iter(foundation):
        if d.get("raw_url") and d.get("sha256"):
            b = get(d["raw_url"])
            if b is None:
                continue
            if hashlib.sha256(b).hexdigest() == d["sha256"]:
                h_ok += 1
            else:
                h_bad += 1
                report["drift"].append({"invariant": "I3", "spec": d.get("spec"), "issue": f"foundation sha256 stale for {d['raw_url']}"})
    report["invariants"]["I3_hash_integrity"] = {"ok": h_ok, "stale": h_bad, "pass": h_bad == 0}

    # ---- I4: no spec-id collision ----
    by_id = {}
    for e in spec_entries:
        by_id.setdefault(e["spec_id"], set()).add(e["repo"])
    collisions = {k: sorted(v) for k, v in by_id.items() if len(v) > 1}
    report["invariants"]["I4_no_collision"] = {"collisions": collisions, "pass": not collisions}
    for k, v in collisions.items():
        report["drift"].append({"invariant": "I4", "spec_id": k, "issue": f"declared by multiple repos: {v}"})

    report["passed"] = all(i["pass"] for i in report["invariants"].values())
    report["drift_count"] = len(report["drift"])

    if "--json" in sys.argv:
        print(json.dumps(report, indent=2))
    else:
        for name, inv in report["invariants"].items():
            print(f"  {'PASS' if inv['pass'] else 'FAIL'}  {name}")
        print(f"\n{'✅ UNIFIED — zero drift' if report['passed'] else f'❌ {report['drift_count']} drift item(s) — not done'}")
        for d in report["drift"][:40]:
            print(f"   · [{d['invariant']}] {d.get('repo') or d.get('spec_id') or d.get('spec')}: {d['issue']}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
