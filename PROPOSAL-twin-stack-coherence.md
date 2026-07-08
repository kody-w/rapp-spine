# PROPOSAL — The twin stack, told once: vbrainstem · twin · DOG/GOD · doorman

> Cortex synthesis 2026-07-08, from primary sources: kody-w/vbrainstem (runtime + kite/tether/
> doorman machinery), kody-w/twin (bones/ vault/ frames/ + succession), kody-w/heimdall (planted
> front door), doorman.skill.md, kite_vtwin.js, ESTATE.md. Resolves drift H3 (RAPP#76) as a
> side-effect. The problem being solved: five surfaces doing similar things with overlapping
> names — which reads as incoherence and drives away usage. The fix is not new software; it is
> ONE ontology, four altitudes, and every existing piece assigned to exactly one.

## The story in one breath

Everything speaks one wire. One runtime lineage runs everywhere. A twin is data, not code —
a public skeleton anyone may hold and a private whole only its owner holds. And a doorman is not
a product: it is a **posting** — a public twin standing at a door, brokering what's behind it.

## The four altitudes

| Altitude | What lives here | The one rule |
|---|---|---|
| **1 · WIRE** | `POST /chat` + signed twin-chat events (rapp-agent/1.0, rapp-twin-chat/1.0, rapp-sealed/1.0) | Every capability rides this wire. No new endpoints, ever. |
| **2 · RUNTIME** | The **brainstem lineage**, one codebase family, three blessed bodies: `brainstem.py` (local kernel, frozen grail), `vbrainstem_sdk.py` (headless stdlib), vBrainstem browser (Pyodide) | One lineage, one home repo, N mirrors — mirrors declare their upstream and sync down. |
| **3 · BEING** | The **twin** — pure data with two strata: **DOG** = `bones/` + `frames/` (public skeleton + signed biography); **GOD** = DOG + `vault/` (device-resident, sovereign) | GOD is derived, never forked: hatch the DOG bones, overlay the local vault. Private data NEVER flows up. |
| **4 · POSTING** | The **doorman** — a DOG twin posted at a door on a vbrainstem host, brokering access to something more private behind it | A doorman is an instance, not a fork. Heimdall is the reference posting, not a brainstem. |

**The DOG/GOD law (altitude 3, the moat):** the DOG is the GOD read backwards — the public
reflection of the private whole. Anyone may hold your DOG (it is your bones walking: soul.md,
facets, card, rappid — all `.public.json` by construction, plus the SHA-signed frames). Only your
device holds your GOD. Inheritance is one-way and continuous: bones updates flow DOWN into every
hatched copy; vault data flows NOWHERE. This is the same upstream→downstream doctrine as the
two-RAPPs ruling — one rule, learned once, applied everywhere in the body.

## What each existing repo IS under this ontology (no new repos)

- **kody-w/vbrainstem** → THE runtime home (altitude 2). Already contains the browser runtime,
  `vbrainstem_sdk.py`, kite/tether transports, doorman machinery. This is the "best version" —
  newest lineage head, richest integration. Canonical.
- **kody-w/rapp-brainstem-sdk** → declared MIRROR of vbrainstem's SDK (header + CI sync), or
  deprecation pointer. Never edited directly again.
- **RAR `virtual-brainstem.html`, twin `vbrainstem.html`** → declared MIRRORS, one canonical
  filename (`vbrainstem.html`), auto-synced. (Today's Bible-mirror drift shows why headers +
  sync beat trust.)
- **kody-w/twin** → the reference BEING (altitude 3) and the template for anyone's twin:
  `bones/` = DOG skeleton · `vault/` = GOD flesh · `frames/` = biography · succession tooling =
  heirloom ceremony. Contains no runtime of record (its vbrainstem.html is a mirror).
- **kody-w/heimdall** → the reference POSTING (altitude 4): a persona-door doorman embodying the
  @kody-w DOG. Its vendored kernel stays Mirror-Spec vendoring (already disciplined). It becomes
  a TEMPLATE: plant-your-own doorman, parameterized by WHICH DOG bones it presents — "Heimdall"
  the character was the vehicle; the pattern is ANY twin's DOG persona at any door.
- **doorman.skill.md** (machine door) → the SAME altitude-4 primitive at a different door: a
  doorman posted at a MACHINE's door brokers sealed-tether access to its local brainstem. One
  definition, two doors — persona-door and machine-door — not two doormen.

## The doorman, fully realized (the missing piece heimdall was reaching for)

A persona-door doorman gives a twin a public life with zero servers:

1. **Public floor (always on):** visitor opens the door URL (GitHub Pages). The DOG twin answers
   in the visitor's own browser — vBrainstem + bones, static hosting, no meter, no backend.
   Humans chat with the persona; kited twins and neighborhood peers speak twin-chat to the same
   door. This is kodyw.com reincarnated — as a being, not a blog.
2. **Escalation (on demand):** when the ask exceeds the DOG's bones — "I need something from
   *Kody's* twin" — the doorman summons through the owner's neighborhood (kite/tether, sealed
   channel). If the owner's device is on, the **GOD answers through the doorman** — the vtwin
   pattern: visitor session and GOD twin in dialed-in collaboration, doorman as broker, private
   data never leaving the device, only answers.
3. **Absence (graceful):** owner offline → the doorman takes a message into the biography
   (signed frame → inbox); the GOD replies asynchronously as a signed frame. The door never
   dead-ends.

Floor → escalation → absence. Every door, any twin, same three beats.

## Migration plan (ordered, small)

1. **Canon first:** add the four-altitude table to the spine narrative (SPINE.md §; no new
   protocol — CRAWL rule 6: this names RELATIONSHIPS between existing specs, like the Leviathan
   STACK note). Register DOG/GOD strata definitions where the twin data model lives.
2. **H3 lands with this ruling (feeds drift fix RAPP#76):** spec repos["run a brainstem"] = the
   ONE lineage (brainstem.py kernel + vbrainstem bodies); heimdall cataloged as reference
   posting/front-door instance, never a brainstem. chat.html rewritten to the layered truth:
   it IS the vbrainstem core chat surface; heimdall is a doorman posting that embodies it —
   GRAIL pointer → vbrainstem.
3. **Mirror discipline sweep (runtime lineage):** MIRROR headers + sync CI on rapp-brainstem-sdk,
   RAR copy, twin copy; unify the artifact filename; VERSION file in vbrainstem; resync lagging
   copies from head.
4. **Heimdall → template-ization:** factor the @kody-w-specific soul/agents out of the repo root
   into a `bones-ref` (points at kody-w/twin bones); add `PLANT.md` — "post this doorman for YOUR
   twin" (fork, point bones-ref at your twin, Pages on). The escalation loop ships as config
   (owner neighborhood address), OFF by default.
5. **Escalation loop v1:** doorman summon → owner neighborhood → sealed vtwin session; absence →
   signed-frame inbox. Build on existing kite/tether/sealed primitives only — zero new transports.
6. **Coherence lint (feeds PLAN-drift-immunity Tier 1):** new-surface rule — every new repo/spec
   declares its altitude (1–4); a second implementation at an occupied altitude needs a MIRROR
   header or a deprecation pointer, else CI fails. This is the standing guard against "5 similar
   things" ever re-accreting.

## The genealogy: body as class, twins as objects (stated precisely)

Kody's directive: the organism is the class; twins born from specific frames are its objects, each
traceable to its frame ancestor. That is the right conceptual picture — and the ecosystem's own
machinery tells us the precise flavor: **RAPP is prototype-based OO, not class-based** — and that
distinction is what makes the DOG/GOD law implementable rather than aspirational.

The mapping, both languages:

| OO concept | RAPP reality |
|---|---|
| **Class definition** | The canon: ecosystem spec + kernel + bones TEMPLATE (kody-w/twin/TEMPLATE.md) + agent contracts |
| **Class *version*** | A **body frame** — the class definition frozen at a slice, content-addressed. The biography is the class's version history |
| **Constructor** | `hatch()` / the installer ceremony — runs with whatever class-version is current |
| **Object / instance** | A twin (a GOD, on its owner's device) |
| **Instantiation record** | `rappid.json` — which ALREADY carries `parent_rappid` + `born_at` (the lineage machinery exists; eggs mint `parent_rappid: rappid:@rapp/origin:…` today) |
| **Prototype delegation** | The DOG/GOD law itself: GOD = derive(DOG bones) + private overlay. Bones updates flow down to every deriving instance — that is prototype semantics (Self/JS), NOT class-copy semantics. A class-copy world couldn't push bone updates to living twins; a prototype world does it natively |
| **Private members** | `vault/` (never flows up — encapsulation is the law, not a convention) |
| **Public members** | `bones/` + `frames/` |
| **Interface / polymorphism** | The wire: every being answers `POST /chat` + twin-chat. Subtype variation = soul/facets, never new endpoints |
| **instanceof / lineage query** | Walk `parent_rappid` + frame-ancestor pins — content-addressed, PKI-free, verifiable by anyone |

**The one concrete mechanism to add — the frame-ancestor pin:** the hatch ceremony stamps the
newborn's `rappid.json` with its constructor context:

```json
"born_of_frame": {
  "body": "rappid:@kody-w/rapp-body:<64hex>",
  "frame_seq": 41,
  "frame_sha256": "<the body-frame's chain hash at hatch time>"
}
```

Every twin can then trace its own life to the exact slice of the organism that defined it — "I was
built when the body knew *this*" — verifiable forever, because both sides are content-addressed
chains. And the genealogy composes with the biography: **the body's worldline is the trunk; each
twin's own frames/ chain is a branch rooted at its `born_of_frame` slice.** The snake has children;
every child is a smaller snake whose tail is pinned to a point on the parent's body.

Two disciplined consequences:
- **The class knows its instances by observation, never coercion:** twin births appear in body
  frames as census/beacon events (estate discovery), not by mandatory registration — same
  observe-never-coerce doctrine as everything else.
- **Races gain a second dimension:** a twin can race its OWN frame-ancestors (its branch), and the
  body can race its class-versions (the trunk) — same workflow, different worldline.

## What this kills (the incoherence inventory)

- "brainstem" meaning four codebases → ONE lineage, three bodies, N declared mirrors.
- "doorman" meaning two products → one primitive, two doors.
- "heimdall" meaning a canon runtime (H3 drift) → a reference posting/template.
- "twin/vtwin/kited twin" ambiguity → twin = the being (data); kited twin = a twin's session
  flown on a kite string (transport state, not a kind of twin); vtwin = the sealed
  visitor↔GOD collaboration session a doorman brokers (a session pattern, not a kind of twin).
- Five onboarding stories → one: *open a door, meet a DOG, and if you need more, the GOD answers
  through it.*
