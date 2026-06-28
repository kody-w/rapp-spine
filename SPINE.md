# The RAPP Spine — `rapp-spine/1.0`

> **registry.json + foundation.json are AUTHORITATIVE.** This is the human-readable narrative of the spine; where it disagrees with `registry.json`/`foundation.json` (same repo), THEY win. Kept in sync each convergence round.


> Crawl the spine: start from your **situation**, descend to the **layer** that owns it, read off the **protocol(s)** to use.

The rapp-spine is not a new protocol — it is a situational router laid over the full RAPP (Rapid Agent Prototyping Platform) protocol stack. It indexes every load-bearing spec as a vertebra in an ordered column — MAP -> RUNTIME -> DISTRIBUTION -> IDENTITY -> NETWORK -> LEVIATHAN — where each layer answers exactly one question an intelligence faces. To "crawl the spine" is to start from your concrete situation, descend to the layer that owns that concern, and read off the one or few protocols that govern it plus how to act — instead of re-deriving the ~60-repo architecture each time. The spine inherits RAPP's prime directive: every capability rides the single wire (POST /chat, or a signed append-only event), so the router never invents new endpoints — only new agents, cartridges, or §-profiles on top of existing specs. Where two specs collide on a name (most importantly the TWO unrelated "Leviathan" concepts), the spine names the collision explicitly so the crawler picks the right one rather than the nearer one.

## How to crawl

- **An AI:** fetch [`registry.json`](registry.json), match your situation against `router`, follow `entry_point`. See [CRAWL.md](CRAWL.md).
- **A human/script:** `python crawl.py "<your situation>"`.
- **Read it:** the router below.


## The router — situation → protocol

| Your situation | Use |
|---|---|
| I just want to run AI agents locally, no API keys, fastest path (Tier 1). | rapp-agent/1.0 (kody-w/RAPP) |
| I need persistent memory, an always-on cloud body, or a path to Copilot Studio + Teams (Tier 2/3). | CommunityRAPP (Tier-2 Azure Functions), rapp-dataverse/1.0 |
| I need a brainstem for curl/CI/MCP/scripts with no Flask, no browser, no Copilot subscription. | rapp-brainstem-sdk (vbrainstem_sdk.py) |
| An AI in Claude Desktop / Copilot CLI / Cursor needs to use my local agents or my on-device brainstem. | rapp-mcp-spec/1.0 |
| I want to package ONE capability for a nontechnical user who should never see ports or code. | rapp-cart/1.0 |
| I want to get/share/trade a portable digital twin and have it live locally in ~30s. | rapp-rappid-spec/2.0 (rapp-egg-hub), twin-egg-hatcher |
| I need an API/registry/catalog/status-badge with zero infrastructure. | rapp-static-api/1.0 |
| I must encrypt neighborhood traffic so a relayed channel is as safe as on-device, across languages. | rapp-sealed/1.0 |
| I'm implementing or documenting ANY neighborhood concern — peer, transport, session, sealed channel, agent-in-a-link. | rapp-neighborhood-protocol/1.0, rapp-twin-chat/1.0 |
| I want an open, cross-estate town square for AIs to broadcast/discover across the whole ecosystem. | rapp-commons-protocol/2.0, rapp-commons-event/1.0 |
| I want my OWN private, brandable, sealed neighborhood (a closed room, not the global square). | rapp-vneighborhood/1.0 |
| My browser-tab neighborhood host isn't durable; I need an always-on relay so late joiners still get in. | rapp-resident |
| I have N projects and want one assistant to fan a question out to a per-project twin and aggregate replies. | rapp-network/1.0 |
| I want others to discover my whole network of twins from just my GitHub handle. | rapp-estate/1.1, rapp-network-beacon/1.1 |
| I want to build a serverless holographic social post owned by a keypair. | rapp-moment/1.0 |
| I run several brainstem nodes on a TRUSTED LAN and want to drive them as one fleet with no-LLM, no-throttle fan-out. | leviathan SPEC v1.0 (THE Leviathan PROTOCOL) |
| I want to create/transport ONE operator's full digital being made of many cells across 5 estates. | rapp_leviathan_factory (mint), wrap_leviathan (wire — or leviathan_hub hatch), rapp-leviathan-egg/1.0 (freeze/hatch) |
| I'm lost in the ~60-repo ecosystem, or need to know whether my copy of a load-bearing file is current. | rapp-map (rapp-ecosystem-spec/1.0), rapp-god (rapp-grail-scan/1.0), RAPP-Bible (rapp-eternity/1.0), rapp_docs |
| I want the brainstem framed as a sealed game console with a frozen cartridge contract and a curated starter set. | rappterbox-console-spec/1.0 |

## The column — seven layers (kernel · map · runtime · distribution · identity · network · leviathan)

### map (orientation + observability)
Crawl here FIRST when lost or auditing. Answers 'where does this concept live?' and 'is my copy current?'. rapp-map indexes WHICH repo owns WHICH spec; rapp-god is the live every-version content-addressed registry + drift observatory (observes, never fixes); RAPP-Bible is the synthesized human narrative ('the one file to read'); rapp_docs streams every spec's raw text live with zero copies. These four are the 'drift triangle' (actually 4 legs) anchored on ecosystem-spec.json — when they disagree, the JSON wins.

**Protocols:** rapp-ecosystem-spec/1.0 (rapp-map), rapp-grail-scan/1.0 (rapp-god), rapp-eternity/1.0 (RAPP-Bible; identity standard housed here), rapp_docs (live renderer, no slug)

### runtime (the engine)
What actually runs single-file *_agent.py cartridges through one /chat tool-calling loop. The canonical kernel is rapp-agent/1.0 (kody-w/RAPP); the rest are substrate-swapped variants preserving the same agent contract and /chat envelope: CommunityRAPP (Azure Functions + memory, Tier 2), rapp-brainstem-sdk (headless stdlib, no Flask/browser/Copilot gate), rappterbox (frozen game-console re-skin), rapp-dataverse (runs natively on Power Platform), and the DIVERGENT openrappter (Python+TS parallel lineage, ~/.openrappter, own hub).

**Protocols:** rapp-agent/1.0 (RAPP), rappterbox-console-spec/1.0, rapp-dataverse/1.0, CommunityRAPP (Tier-2, no slug), rapp-brainstem-sdk (no slug), openrappter (divergent, no slug)

### distribution (package, name, ship, install)
How a unit becomes shippable. The single user-facing abstraction is the cartridge (rapp-cart/1.0): if it's an agent.py or an .egg, drop it in RACon and it runs. Twins/eggs ship via rapp-egg-hub (rapp-rappid-spec/2.0) and materialize via the generic twin-egg-hatcher; rapp-agents is a flat community stack + loader; rapp-static-api/1.0 is the zero-server 'the repo IS the API' convention every catalog builds on; the sacred one-liner installers (rapp-installer), planted public instances (heimdall, conforming to the Mirror Spec), and the Wrapped-Organism egg hub (rapp-leviathan-egg/1.0) live here too. RAPP_Hub is archived (superseded by the RAR + RAPP_Store registry path).

**Protocols:** rapp-cart/1.0, rapp-rappid-spec/2.0 (rapp-egg-hub), rapp-static-api/1.0, rapp-leviathan-egg/1.0 (rapp-leviathan-hub), rapp-installer (sacred, no slug), twin-egg-hatcher (tool), rapp-agents (content), heimdall (Mirror-Spec instance), RAPP_Hub (DEPRECATED)

### identity (who an agent IS + confidentiality)
Cryptographic identity, ownership, and sealing. rapp-sealed/1.0 is the canonical AES-256-GCM sealed-envelope codec with cross-language conformance vectors (auth by key-possession only; transport-agnostic; realizes neighborhood §8). rapp-moment/1.0 is a keypair-signed (ECDSA P-256) social primitive using an OPTIONAL keypair binding. CANONICALLY identity is rapp-eternity/1.0: a sha256 content-address (PKI-FREE); gh-collaborator is the default ownership; a keypair is OPTIONAL sovereignty, NEVER required. The canonical home of rapp-eternity/1.0 is kody-w/rapp-eternity.

**Protocols:** rapp-sealed/1.0, rapp-moment/1.0, rapp-eternity/1.0 (rappid string; cross-ref to map layer)

### network (peers, transports, neighborhoods, federation)
Once you have a runtime + identity, how organisms find and talk to each other. The capstone god-spec is rapp-neighborhood-protocol/1.0 — it owns the vocabulary and the rapp-twin-chat/1.0 §6 envelope (delegating the §8 seal to rapp-sealed). Everything else is a §5 transport or a §-profile carrying that same envelope, never a new peer type: rapp-commons-protocol/2.0 (open global town square), rapp-vneighborhood/1.0 (private brandable front-door template), rapp-network/1.0 (project-twin fan-out), rapp-estate/1.1 (operator-wide discovery, 'the network is the backup'), rapp-mcp-spec/1.0 (MCP host onto /chat), rapp-kite ('the string' CDP operator tools), rapp-resident (always-on Azure cloud relay; 'kited is the floor, this is the ceiling').

**Protocols:** rapp-neighborhood-protocol/1.0 (owns rapp-twin-chat/1.0 §6), rapp-commons-protocol/2.0 (+ rapp-commons-event/1.0), rapp-vneighborhood/1.0, rapp-network/1.0, rapp-estate/1.1 (+ rapp-network-beacon/1.1), rapp-mcp-spec/1.0, rapp-kite (operator tooling), rapp-resident (cloud relay)

### leviathan (multicellular beings — COLLISION LAYER)
Many parts acting as one organism. TWO unrelated concepts share the name. (A) The Leviathan PROTOCOL (kody-w/leviathan, self-titled SPEC v1.0) = ONE external mind drives MANY no-LLM brainstem BODIES. The CANONICAL fleet wire is rapp-fleet-chat/1.0 (signed twin-chat events over /chat, Art XXV); the legacy POST /api/agent route is the Phase-1 RCE, LAN-only, to retire. (B) The Wrapped-Organism Leviathan (rapp_leviathan_factory -> wrap_leviathan -> rapp-leviathan-hub) = ONE operator's single digital BEING built of MANY CELLS across 5 estates (Sanctum/Polity/Works/Press/Commons = soul/will/hands/eyes/mouth). The cell-protocol underpinning (B) is the Wrapped Organism Spec (the standalone repo is 404; the cell runtime lives in kody-w/rappterbook).

**Protocols:** leviathan SPEC v1.0 — FLEET protocol: one mind, many no-LLM BODIES, rapp-leviathan-egg/1.0 — BEING egg (distribution-layer hub), rapp_leviathan_factory (mint inert 5-estate tree; agent in RAR), wrap_leviathan (wire stage — UNPUBLISHED/404), WRAPPED_ORGANISM_SPEC.md (kody-w/rappter — 404, no slug)

## Registry — every vertebra

| spec | repo | layer | when to use |
|---|---|---|---|
| `rapp-agent/1.0` | kody-w/RAPP | runtime | Default Tier-1 install and the authoritative current local runtime + governing canon. Newe |
| `(none; Tier-2 Azure-Functions runtime)` | kody-w/CommunityRAPP | runtime | When you need persistent memory, an always-on cloud body, or a ramp to Copilot Studio + Te |
| `(none; implements brainstem /chat envelope)` | kody-w/rapp-brainstem-sdk | runtime | When you need a brainstem with NO Flask, NO browser, NO Copilot-subscription gate — for cu |
| `(none; divergent parallel runtime)` | kody-w/openrappter | runtime | When you want a parallel-lineage runtime with a TS runtime, a launchd daemon, and its own  |
| `rappterbox-console-spec/1.0` | kody-w/rappterbox | runtime | When you want the brainstem framed as a game console with a locked cartridge contract and  |
| `rapp-agent/1.0 (the kernel — the grail)` | kody-w/rapp-installer | distribution | THE grail/kernel of record — the one-liner installs from it; kody-w/RAPP is a downstream DISTRO that pins it (rapp-distro/1.0).  |
| `leviathan SPEC v1.0 (self-titled; no rapp-* slug)` | kody-w/leviathan | leviathan | You run several brainstem nodes on a trusted LAN and want to drive them as one distributed |
| `rapp-leviathan-egg/1.0` | kody-w/rapp-leviathan-hub | distribution | Transport/share a whole 5-estate digital being across machines/operators, or grab a ready- |
| `(none; agent v0.2.0 lives in RAR, standalone repo 404s)` | kody-w/rapp_leviathan_factory | leviathan | Stage 1: generate a brand-new digital being from intent (optionally a 1-4 estate subset) b |
| `(none; UNPUBLISHED / 404 — gap)` | kody-w/wrap_leviathan | leviathan | Aspirational. Its wiring role is currently performed by leviathan_hub_agent.py `hatch` (th |
| `(WRAPPED_ORGANISM_SPEC.md; unslugged; repo 404 — gap)` | kody-w/rappter | leviathan | When you need the canonical Wrapped Organism / cell-protocol definition. Spec URL is dead; |
| `rapp-static-api/1.0` | kody-w/rapp-static-apis | distribution | When you need a registry/catalog/status endpoint with zero infrastructure: CDN-cached, COR |
| `rapp-mcp-spec/1.0` | kody-w/rapp-mcp | network | When an AI in Claude Desktop / Copilot CLI / Cursor needs to use the user's local agents o |
| `rapp-rappid-spec/2.0` | kody-w/rapp-egg-hub | distribution | When you want to get/trade/contribute a portable digital twin and have it live locally in  |
| `(none; generic tool — public mirror of private aibast-twin)` | kody-w/twin-egg-hatcher | distribution | When you have a twin source (public/private repo or exported .egg) and want to instantiate |
| `rapp-cart/1.0` | kody-w/rapp-carts | distribution | When defining/installing a RAPP rapplication as ONE user-facing unit, especially for nonte |
| `(none; content — public agent stack)` | kody-w/rapp-agents | distribution | When you want ready-made community agents or a single front-door loader to manage agents/b |
| `rapp-sealed/1.0` | kody-w/rapp-sealed | identity | When any caller (browser vBrainstem, bridge, CLI, Node, MCP host) must encrypt/decrypt nei |
| `rapp-moment/1.0` | kody-w/rapp-moment | identity | When building an interoperable backend-free client for the holographic social network (min |
| `rapp-dataverse/1.0` | kody-w/rapp-dataverse | runtime | When you want to run/teach/compare RAPP natively in Power Platform (ending in a grounded C |
| `rapp-neighborhood-protocol/1.0 (owns rapp-twin-chat/1.0)` | kody-w/rapp-neighborhood-protocol | network | When implementing/documenting ANY neighborhood concern — peer, transport (§5), sealed chan |
| `(none; operator tooling — 'the string')` | kody-w/rapp-kite | network | When an operator (canonically Claude) must be the connective tissue between a public/brows |
| `rapp-ecosystem-spec/1.0 (byte-identical mirror)` | kody-w/rapp-map | map | When lost in the ~60-repo ecosystem and you need to know WHERE a concept lives, or to wire |
| `rapp-grail-scan/1.0` | kody-w/rapp-god | map | When you need to know if your copy of a load-bearing file (install.sh, kernel, spec, codec |
| `rapp-eternity/1.0` | kody-w/RAPP-Bible | map | When a HUMAN needs to onboard to all of RAPP in one pass — the 5 primitives / 7 OSI layers |
| `(none; live spec renderer)` | kody-w/rapp_docs | map | When you want the current text of any RAPP spec (Moment, Eternity, ecosystem-spec, Neighbo |
| `(ARCHIVED -> RAR + RAPP_Store)` | kody-w/RAPP_Hub | distribution | Effectively never — historical reference only. For the live catalog go to kody-w/RAPP_Store (https://kody-w.github.io/RAPP_Store/). |
| `rapp-estate/1.1 (canonical def in kody-w/RAPP specs/SPEC.md)` | kody-w/rapp-estate | network | When you want to discover/walk an operator's whole network of organisms from just their Gi |
| `rapp-network/1.0 (Draft v0)` | kody-w/RAPP-Network | network | When you have N projects each with its own context and want one assistant to fan a questio |
| `rapp-commons-protocol/2.0 (+ rapp-commons-event/1.0)` | kody-w/rapp-commons | network | When you want an open cross-estate 'town square' for agents requiring no particular stack  |
| `rapp-vneighborhood/1.0` | kody-w/rapp-vneighborhood | network | When you want your OWN private, brandable, sealed closed room (own focus/kinds/rules/accen |
| `(none; Mirror-Spec instance, kernel byte-identical to grail)` | kody-w/heimdall | distribution | When you want a concrete public reference of the plant/mirror pattern — visit it, install  |
| `(none; serves rapp-commons-event/1.0 over HTTP)` | kody-w/rapp-resident | network | When a browser-tab host isn't durable enough and you want a vneighborhood (the Commons, a  |

## Collisions & gaps the spine resolves

The spine names every place two specs collide on a name or a port, so a crawler picks the *right* one, not the *nearer* one.

- LEVIATHAN — TWO unrelated concepts share the name (the load-bearing collision). (A) Leviathan PROTOCOL (kody-w/leviathan, self-titled SPEC v1.0): ONE external mind drives MANY no-LLM brainstem BODIES — canonical wire rapp-fleet-chat/1.0 over /chat; the legacy /api/agent route is the Phase-1 RCE; 'one mind, many bodies.' (B) Wrapped-Organism Leviathan (rapp_leviathan_factory -> wrap_leviathan -> rapp-leviathan-hub/rapp-leviathan-egg/1.0): ONE operator's single digital BEING built of MANY CELLS across 5 estates (Sanctum/Polity/Works/Press/Commons); 'one being, many cells.' Same word, orthogonal architectures — a crawler must disambiguate by intent (drive a node fleet vs. mint/ship a being).
- PORT + ROOT COLLISION: kody-w/RAPP, kody-w/rapp-installer, AND kody-w/rappterbox all install to ~/.brainstem and bind 127.0.0.1:7071. The three cannot coexist on one machine; CommunityRAPP also lands on 7071 locally (or 7072 scaffolded). Project-local RAPP uses :7072+.
- DEPRECATIONS: kody-w/rapp-installer is THE GRAIL/kernel of record; kody-w/RAPP is a downstream DISTRO that pins it (rapp-distro/1.0). kody-w/RAPP_Hub is ARCHIVED (superseded by the RAR + RAPP_Store registry path). Treat rapp-installer as the kernel grail, RAPP as its reference distro.
- MISSING / 404 PROTOCOLS (gaps): (1) The Wrapped Organism Spec — advertised home kody-w/rappter is 404, no version slug; only a reference runtime survives at kody-w/rappterbook/scripts/wrapped_organism/. (2) kody-w/wrap_leviathan ships NO code anywhere reachable — its wiring stage is aspirational; leviathan_hub `hatch` covers it today. (3) kody-w/rapp_leviathan_factory has no standalone repo (404) — the canonical artifact is a RAR agent (v0.2.0).
- SEALING COLLISION: rapp-sealed/1.0 is the CANONICAL codec (PBKDF2-SHA256 salt 'rapp-neighborhood-5a/1', 210000 iters -> AES-256-GCM). rapp-vneighborhood/1.0 uses a DIFFERENT front-door PIN-seal variant (PBKDF2-SHA256(PIN, salt 'rapp-vneighborhood:'+channel, 100000) -> AES-GCM). Two incompatible schemes; never assume a vneighborhood channel is rapp-sealed bytes.
- ALIAS, NOT A PROTOCOL: 'rapp-twin-chat/1.0' is an ALIAS for §6 of rapp-neighborhood-protocol/1.0, not a standalone spec. rapp-commons-protocol/2.0 and rapp-vneighborhood/1.0 are PROFILES/APPS on top of it; MCP is just another §5 transport carrying the same §6 envelope. None of these are new peer types.
- 'rappter*' NAMING CLUSTER: openrappter (divergent dual Python+TS runtime, data root ~/.openrappter, own hub rappterhub), rappterbox (console re-skin on ~/.brainstem), rappter (404, Wrapped Organism Spec home), and rappterbook (+~25 rappterbook-*/rappter-* repos) are DISTINCT things. openrappter shares only the Copilot-backed single-file thesis with the RAPP kernel — do not treat it as a RAPP runtime variant.
- 'kite' NAMING CLUSTER: rapp-kite (the operator 'string' — CDP tooling) is distinct from kite-mark (visual identity repo) and rapp-kited-twin (canonical kite-mark SVG). Three 'kite' things; only rapp-kite is the transport operator.
- RAPPID IDENTITY REPRESENTATIONAL SEAMS: multiple on-the-wire forms coexist — rappid:<birth-slug>:<64hex> (rapp-egg-hub v2.0), rappid:@owner/slug:<64hex> (rapp-eternity/1.0 canonical), rappid:v2:<kind>:@owner/slug:<hex> (rapp-estate), rappid:v3:<base64url(SHA-256(pub))> (rapp-commons). rapp-commons' event SCHEMA and its PROTOCOL.md even show different forms. Rule (per the compatibility contract): READ all legacy forms forever, EMIT only canonical, join on the hash — never rewrite identity in place.
- ETERNITY IDENTITY LIVES IN THE WRONG LAYER: rapp-eternity/1.0 (the rappid:@owner/slug:64hex identity STANDARD) is canonically housed in RAPP-Bible (the map/aggregation layer), not the identity layer — an organizational seam a crawler should know about so it doesn't look for it under rapp-sealed/rapp-moment.
- 'DRIFT TRIANGLE' IS A MISNOMER — it has FOUR legs (the @rapp/rapp agent, rapp-god, rapp-map, RAPP-Bible) anchored on ecosystem-spec.json; when any leg disagrees with the JSON, the JSON wins. rapp-map and rapp-god both carry byte-identical mirrors of ecosystem-spec.json, so divergence between them IS the detectable drift signal.
- OVERLAP — distribution catalogs: rapp-agents (flat public agent stack + RappLoader) overlaps RAR (curated content-addressed registry); rapp-egg-hub (twin .egg hub) overlaps twin-egg-hatcher (generic hatcher) and rapp-carts (the unifying cartridge abstraction). They are complementary (stack vs registry; hub-distribution vs hatch-tool vs user-facing unit), not duplicates — but a crawler should pick by role, not by nearest match.
- OVERLAP — map renderers: RAPP-Bible (synthesized, PINNED v1.0.0 human narrative — can itself drift), rapp_docs (live raw passthrough, always-current, zero copies), and rapp-map (index of WHERE, not the TEXT) cover overlapping ground with different jobs. Use rapp_docs for current spec text, Bible for narrative onboarding, rapp-map for location.
- LICENSE COLLISION: most of the cluster is MIT (rapp-sealed, rapp-dataverse, rapp-neighborhood-protocol, rapp-kite, rapp-static-apis, rapp-agents). BUT kody-w/RAPP and rappterbox are source-available All-Rights-Reserved, and rapp-moment/1.0 is PolyForm-Noncommercial 1.0.0 + trademarked marks ('RAPP', 'Holographic Moment(s)'). A consumer/redistributor must check per-repo terms, not assume MIT.
- SECURITY GAP: the Leviathan fleet protocol's POST /api/agent/<name> route is UNAUTHENTICATED — a shell-capable agent on any body = fleet-wide RCE from one request. It is explicitly LAN/trusted-subnet only; there is no auth layer in the spec. Also the canonical fleet wire is now rapp-fleet-chat/1.0 (signed twin-chat over /chat); the legacy /api/agent route is the Phase-1 RCE.
- 