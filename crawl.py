#!/usr/bin/env python3
"""
crawl.py — crawl the RAPP spine.

Given a SITUATION, the spine tells you which protocol(s) of the ~60-repo RAPP stack
govern it and how to act — instead of re-deriving the architecture each time.

  python crawl.py                          # print the whole spine (layers + router)
  python crawl.py "drive my LAN brainstems as one fleet"   # match -> protocol(s)
  python crawl.py --layer network          # everything in one layer
  python crawl.py --collisions             # the name/port collisions the spine resolves
  python crawl.py --json "..."             # machine-readable match
  python crawl.py --remote ...             # fetch registry.json from the CDN instead of local

It reads registry.json (stdlib only, no deps).
"""
import json
import os
import re
import sys
import urllib.request

REMOTE = "https://raw.githubusercontent.com/kody-w/rapp-spine/main/registry.json"
LOCAL = os.path.join(os.path.dirname(os.path.abspath(__file__)), "registry.json")
_STOP = set("a an the i to my of for and or is are with no on in it this that you your me we so".split())


def load(remote=False):
    if remote:
        with urllib.request.urlopen(REMOTE, timeout=15) as r:
            return json.loads(r.read())
    with open(LOCAL, encoding="utf-8") as handle:
        return json.load(handle)


def _toks(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if w not in _STOP and len(w) > 2}


def match(spine, situation, n=3):
    q = _toks(situation)
    scored = []
    for r in spine["router"]:
        hay = _toks(r["situation"] + " " + r["why"] + " " + " ".join(r["use"]))
        scored.append((len(q & hay), r))
    scored.sort(key=lambda x: -x[0])
    return [r for sc, r in scored[:n] if sc > 0]


def print_spine(spine):
    print(f"\n  THE RAPP SPINE ({spine['spec']})  ·  crawl from situation -> layer -> protocol\n")
    print("  COLUMN:", " -> ".join(spine["layers_order"]))
    print("\n  ROUTER:")
    for r in spine["router"]:
        print(f"   • {r['situation']}")
        print(f"       -> {', '.join(r['use'])}")
    print(f"\n  ({len(spine['registry'])} protocols, {len(spine['router'])} routes. `crawl.py \"<situation>\"` to route. `--collisions` for the seams.)\n")


def main(argv):
    remote = "--remote" in argv
    as_json = "--json" in argv
    argv = [a for a in argv if a not in ("--remote", "--json")]
    spine = load(remote)

    if argv and argv[0] == "--layer":
        want = argv[1] if len(argv) > 1 else ""
        for L in spine["layers"]:
            if want.lower() in L["layer"].lower():
                print(f"\n  {L['layer']}\n  {L['summary']}\n  protocols: {', '.join(L['protocols'])}\n")
        return
    if argv and argv[0] == "--collisions":
        print("\n  COLLISIONS & GAPS the spine resolves:\n")
        for c in spine["collisions_and_gaps"]:
            print(f"   - {c}\n")
        return
    if not argv:
        print_spine(spine)
        return

    situation = " ".join(argv)
    hits = match(spine, situation)
    if as_json:
        print(json.dumps(hits, indent=2))
        return
    if not hits:
        print(f"\n  No direct route for: {situation!r}\n  Crawl the whole spine: `python crawl.py`\n")
        return
    print(f"\n  CRAWLING THE SPINE for: {situation!r}\n")
    for r in hits:
        print(f"   → USE: {', '.join(r['use'])}")
        print(f"     situation: {r['situation']}")
        print(f"     why: {r['why']}\n")


if __name__ == "__main__":
    main(sys.argv[1:])
