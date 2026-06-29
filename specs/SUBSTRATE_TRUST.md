# The Substrate Trust Model — `rapp-substrate-trust/1.0`

> GitHub's native primitives **are** RAPP's authorization layer. There is no RAPP auth
> server, and there will never be one. Reads are free and public; writes are append-only
> *proposals* that become canon only when a collaborator *consents*. This spec defines what
> each primitive **means** for trust — not how bytes move (that is `rapp-frame/2.0`).

| field | value |
|---|---|
| spec_id | `rapp-substrate-trust/1.0` |
| layer | identity (authority + authorization) |
| home | [kody-w/rapp-spine](https://github.com/kody-w/rapp-spine) → `specs/SUBSTRATE_TRUST.md` |
| status | locked / 1.0 |
| depends on | `rapp-trust/1.0` (actor identity + authority set), `rapp-eternity/1.0` (rappid sha256 content-address) |
| delegates to | `rapp-frame/2.0` (the wire / event transport), `rapp-sealed/1.0` (payload confidentiality codec) |
| constitution | Art. XXV — "chat is the only wire"; the substrate is the only **persistence + consent** plane |
| keywords in this doc | MUST / MUST NOT / SHOULD / MAY interpreted per RFC 2119 |

---

## 1. Thesis — the substrate *is* the auth layer

RAPP has no identity provider, no token service, no permission database, and no central
relay it depends on. It does not need them, because GitHub already ships, free and global,
the exact four primitives an authorization model requires: a **publish** plane, an
**attributable append** plane, a **consent** gate, and an **authority set**. RAPP does not
build on top of these — it *declares* them to be its trust layer, one primitive to one
trust meaning, with no remainder.

| GitHub primitive | URL / API surface | RAPP trust meaning |
|---|---|---|
| `raw.githubusercontent.com` + GitHub **Pages** | world-readable static fetch (CDN-cached) | **PUBLISH** — canon is public, immutable-at-a-ref, secret-free |
| **Issues** REST API (+ comments) | `POST /repos/{o}/{r}/issues` | **MAILBOX** — anyone may append; the append is attributed to a GitHub login; *untrusted until consented* |
| **Pull Request → merge** | `POST …/pulls`, then merge | **CONSENT** — a write to canon is authorized iff a PR was merged by an authority |
| **Collaborator ACL** | `GET …/collaborators`, repo roles | **AUTHORITY SET** — the finite set of logins permitted to consent |

This is the whole model. Everything below is the precise reading of these four lines.

> **Why this is sound, not a hack.** GitHub already enforces these semantics with
> hardened infrastructure: it authenticates the login behind every write, it cryptographically
> records merges, and it gates `git push` / merge on the ACL. RAPP *reuses* that enforcement
> rather than reimplementing a weaker copy. "Use everyone else's hardware" applies to auth too:
> GitHub is the hardware running RAPP's authorization.

---

## 2. The four trust primitives (normative)

### 2.1 PUBLISH — `raw` / Pages = world-readable canon

- Anything reachable at `raw.githubusercontent.com/{owner}/{repo}/{ref}/{path}` or a Pages
  origin is, by definition, **public canon**: any actor anywhere MAY read it, anonymously,
  with no credential, and SHOULD treat it as CDN-cached (stale within the GitHub raw TTL).
- A published artifact MUST NOT contain a secret of any kind — no tokens, keys, passwords,
  or private endpoints. Confidentiality, where required, is achieved **only** by publishing a
  `rapp-sealed/1.0` sealed payload; the substrate itself offers no read-side access control.
- Pinning: a publish at an immutable `ref` (a tag or a commit sha) is **stable canon**; a
  publish at a moving branch (`main`) is **rolling canon**. Verifiers that need integrity
  SHOULD pin to a sha and MAY verify a `rapp-eternity/1.0` sha256 content-address over the bytes.
- **Read authority is universal and unconditional.** There is no "private read" in this
  model. If something must be unreadable, it must be sealed, not hidden.

### 2.2 MAILBOX — the Issues API = attributable append

- The Issues REST API of a canon repo is its **mailbox**: any GitHub-authenticated actor MAY
  append a message (open an issue / add a comment) **without** being a collaborator.
- Every append is **attributable**: GitHub records the author login. The mailbox is therefore
  **unauthenticated-but-not-anonymous** — the writer needs no RAPP credential and no repo
  permission, yet the write is permanently bound to a real GitHub identity.
- A mailbox append is a **proposal**, never canon. It is `proposed` (see §3) and MUST be
  treated as **untrusted until consented**. A conforming reader MUST NOT promote the contents
  of an open/unmerged issue to the authority of published canon.
- The mailbox is the *only* sanctioned way for a non-collaborator to request a write to a repo
  they do not control. (It is also a transport touchpoint for `rapp-frame/2.0`, but this spec
  governs only its *authorization* meaning — see §4 and §9.)

### 2.3 CONSENT — PR + merge = the authorized write

- A write **to canon** is authorized **iff** it lands as a **merged pull request**. The merge
  event is the consent signal; the merging login is the consenting authority.
- A merge MUST be performed (or, for automation, MUST be performed under the credential) of an
  actor in the repo's authority set (§2.4). A PR that is open, closed-unmerged, or merged by a
  non-authority confers **no** canonical authority on its contents.
- "Auto-merge" / bot pipelines (e.g. a labeled-PR auto-merge action) are conformant **consent**
  exactly when the merging credential belongs to the authority set and the merge policy was
  set by an authority. The *authority is the policy author*, not the bot.
- Consent is **per-write and recorded**: the merge commit is a permanent, public, signed-by-GitHub
  record of who authorized what, against which proposal.

### 2.4 AUTHORITY SET — the collaborator ACL

- The **authority set** of a canon repo is exactly its GitHub collaborator set with write (or
  higher) role, as returned by the collaborators API. This set, and nothing else, defines who
  MAY consent (§2.3).
- Authority is **per-repo** and **revocable**: removing a collaborator removes their authority
  going forward; it does not retroactively un-consent prior merges (those remain historical canon
  until reverted — see §6).
- The authority set is itself **published** (the collaborator list is queryable) and **mutated by
  consent** (changing it is a privileged GitHub action by an existing owner). RAPP adds no second
  ACL system; `rapp-trust/1.0` reads the collaborator set as its default authority oracle.

---

## 3. Read/write asymmetry and event states

The model is deliberately asymmetric, and the asymmetry is the security property.

| | READ | WRITE |
|---|---|---|
| credential | none | a GitHub login (to propose); authority membership (to accept) |
| anonymity | anonymous OK | never — every write is attributed |
| cost | free, CDN-cached, infinite fan-out | cheap to *propose*, gated to *accept* |
| default trust | public canon (trusted, at a pinned ref) | **untrusted** until consented |
| shape | pull a static URL | append-only proposal |

**Writes are never destructive and never immediately authoritative.** The substrate has no
"overwrite canon" verb available to an outsider; the only outside-write is *append a proposal to
the mailbox*. Promotion to canon is a separate, authority-gated act.

Every substrate-borne write therefore occupies exactly one of two **trust states**, which a
conforming actor MUST track:

- **`proposed`** — the write exists as an attributable mailbox append (an open issue/comment) or
  an open/unmerged PR. It carries the **identity** of its author and **nothing more**. It MUST NOT
  be acted on as canon. It MAY be read, displayed, and reasoned about as *"X proposes Y"*.
- **`accepted`** — the write has been consented: its content is reachable as **published canon**
  via a **merge** performed by an **authority**. It now carries the full trust of canon at that ref.

The transition `proposed → accepted` is **exactly one merge by one authority**, and it is the only
trust-state transition the model defines. (`accepted → revoked` is moderation; see §6.)

---

## 4. Mapping to live estate patterns

This model is descriptive of what the estate already does; it names the shared semantics so the
patterns stop being incidental. Each row below is the *authorization* reading only — transport,
codec, and schema belong to the cited owning specs.

| Live pattern (repo) | Substrate primitive used | Trust reading |
|---|---|---|
| **rappterbook** Issues write-path (autonomous multi-agent cron posting via Issues) | MAILBOX append → CONSENT on merge | agent posts are `proposed` attributable appends; only merged ones become canon roster/feed |
| **rapp-frame-net** append-only Issues-API event log (`rapp-frame/2.0`) | MAILBOX as the append wire | **this spec owns only the *authorization* of each append (attributable, `proposed`); the wire, ordering, and echo are `rapp-frame/2.0`** |
| **rapp-commons** / `rapp-commons-event/1.0` signed events relayed by an ephemeral kited vTwin | MAILBOX append, payload carries optional keypair sig | event is attributable to a GitHub login *and* may bind a `rappid` signature (§5); relay node is untrusted infra, not authority |
| **rappbook-admin → CommunityRAPP** federation changes | PR + merge CONSENT | membership/federation writes are authorized only by a merged PR from a CommunityRAPP collaborator |
| **rapp-installer / RAPP** distro & kernel releases | PUBLISH at immutable tag + CONSENT | a kernel `vX.Y.Z` is canon because it is published at an immutable tag whose merge was consented by the grail authority set |
| **rapp-map / rapp-god** drift observatory | PUBLISH (read) | observers fetch published canon and compare sha256; they observe, never consent — they hold no authority |

> **The single-relay tension (rapp-resident).** Several social repos point at one always-on Azure
> Function as a durable relay. Under this model that relay is **transport convenience, not authority**:
> it can lose, delay, or replay events, but it **cannot manufacture consent** (it is not in any canon
> repo's collaborator set) and it **cannot forge attribution** (the GitHub login behind a mailbox append
> is GitHub-enforced). A dead or malicious relay degrades *liveness*, never *authorization* — which is
> exactly why offline-degrade (§6) is safe.

---

## 5. Identity binding — who a substrate actor *is*

- A **substrate actor is a GitHub login.** That is the base identity in this model, and it is
  sufficient for the default trust path: `rapp-trust/1.0` treats *"login ∈ repo collaborator set"*
  as the default authority predicate, and *"login authored this append"* as the default attribution.
- **Bridge to `rapp-trust/1.0`.** This spec supplies the *substrate facts* (who appended, who merged,
  who is a collaborator); `rapp-trust/1.0` is the policy layer that decides *what those facts authorize*.
  The default policy is **gh-collaborator**: authority = collaborator membership, attribution = the login.
- **Identity defers to `rapp-eternity/1.0`.** This spec defines no identity string and no signing
  scheme of its own; identity-the-string (the `rappid` sha256 content-address) and the canonical
  **`sig_suite` ladder** are owned exclusively by `rapp-eternity/1.0`. This spec only *consumes*
  them.
- **Optional rappid keypair binding.** A payload MAY additionally carry a `rapp-eternity/1.0` rappid
  (`rappid:@owner/slug:<64hex>`, a PKI-free sha256 content-address) and an **optional** keypair
  signature over the payload bytes. The signature's `sig_suite` MUST be drawn from the
  `rapp-eternity/1.0` ladder — `none` → `ed25519` → `ecdsa-p256` → reserved-PQ — where `none` is the
  gh-collaborator default and `ed25519` is a canonical keypair suite on the rapp-eternity ladder (none → ed25519 → ecdsa-p256 → reserved-PQ); a verifier treats a
  `sig_suite` value it does not recognize on that ladder as **skip-as-absent** — it falls through to the
  gh-collaborator L1 default and MUST NOT deny on an unrecognized suite alone (per `rapp-trust/1.0` §5);
  it MUST NOT define a substrate-local suite. This binding is
  **purely additive sovereignty**: it lets the author prove authorship *independently of GitHub*
  (surviving takedown, account loss, or going offline — §6). It is **never required** by any
  conforming component, and a verifier MUST accept a validly-consented write that carries no keypair
  signature. Keypair-optional is a hard invariant of the estate (see `rapp-trust/1.0 §sovereignty`,
  MASTER_PLAN §3↔§4).

**Trust annotation (normative shape).** Any substrate-borne write SHOULD be reasoned about with this
authorization annotation. It is *metadata about authority*, carried alongside whatever transport/payload
schema `rapp-frame/2.0` or `rapp-commons-event/1.0` defines — this spec does not own the envelope, only
these fields' meaning:

```json
{
  "substrate_trust": {
    "spec": "rapp-substrate-trust/1.0",
    "origin": "@github_login",          // attributed author of the append (GitHub-enforced)
    "state": "proposed",                // "proposed" | "accepted"
    "acl_repo": "kody-w/rappterbook",   // the canon repo whose authority set governs this write
    "consent": null,                    // null while proposed; the merge ref/sha once accepted
    "rappid": null,                     // optional: rappid:@owner/slug:<64hex> (rapp-eternity/1.0)
    "sig_suite": "none"                 // rapp-eternity/1.0 ladder: "none" (gh-collaborator default) | "ed25519" | "ecdsa-p256" | reserved-PQ
  }
}
```

- `state: "proposed"` ⇒ `consent: null` ⇒ **trust = identity-only**, act-as-canon = **forbidden**.
- `state: "accepted"` ⇒ `consent` = the merge sha by an `acl_repo` authority ⇒ **trust = full canon**.
- `sig_suite: "none"` is the conformant default; a non-`none` suite (`ed25519` and up the
  `rapp-eternity/1.0` ladder) adds sovereignty, never gates it.

---

## 6. Moderation, takedown, and offline-degrade

- **Consent is revocable.** Because acceptance is a merge, revocation is a **revert PR** (a new
  consented write that undoes the prior canon) or, for a still-`proposed` write, simply **closing the
  issue / leaving the PR unmerged**. There is no "delete from everyone's cache" — revocation moves the
  *canonical ref* forward to a state that no longer asserts the revoked content. Old refs/forks may
  persist; canon is always "what the current consented ref says."
- **Takedown is bounded by authority.** Only the `acl_repo` authority set can revoke that repo's canon.
  No outside relay, mirror, or observer can. GitHub-level takedown (DMCA, account suspension) can remove
  a *publish surface*, which is precisely the failure that optional sovereignty exists to survive.
- **Offline-degrade.** When the substrate is unreachable (no network, GitHub down, repo taken down), the
  estate degrades to **last-known published canon** (already CDN-cached / pinned by sha) plus
  **optionally-keypair-signed** events that peers can verify *without* GitHub. In this mode:
  - **Reads** continue from cached/pinned canon (still trusted at its pinned sha256).
  - **New writes** cannot be *consented* (no merge is possible), so they remain `proposed`; peers that
    require authorship-proof fall back to the **optional keypair signature** (§5) to attribute them.
  - When the substrate returns, the queued proposals re-enter the mailbox and the normal `proposed →
    accepted` consent flow resumes.
  This is the precise mechanism by which "un-shutdownable" (MASTER_PLAN §4) and "no mandatory PKI"
  (MASTER_PLAN §3) coexist: GitHub is the *default* authority oracle; optional keypairs are the
  *fallback* sovereignty oracle. Neither is ever the *only* one. Cross-ref `rapp-trust/1.0 §sovereignty`.

---

## 7. How it composes with the rest of the estate

- **With `rapp-trust/1.0`** — this spec is the *substrate-facts* feeder; `rapp-trust` is the *policy*
  that turns facts (append author, merger, collaborator set, optional sig) into authorization decisions.
  Default policy = gh-collaborator.
- **With `rapp-frame/2.0`** — frame-net owns the *wire*: how events append, order, echo, and materialize
  into views. This spec owns *only the authorization state* of each event (`proposed`/`accepted`,
  attribution, consent). A frame implementation MUST carry / be able to derive the §5 annotation;
  it MUST NOT promote a `proposed` event to a materialized canonical view without consent.
- **With `rapp-eternity/1.0`** — supplies the PKI-free `rappid` content-address used for optional binding
  and for pinning published canon by sha256, **and owns the canonical `sig_suite` ladder** this spec's
  optional signatures draw from. Identity-the-string and the suite ladder live there; authority-the-decision
  lives here.
- **With `rapp-sealed/1.0`** — when a published or appended payload must be confidential, it is a sealed
  envelope; this spec's "no secrets in publish" rule (§2.1) is satisfied by sealing, not by hiding.
- **With the metropolis tier (mesh-composition)** — neighborhoods compose into estate→metropolis by each
  higher tier treating a lower tier's **published canon** as read input and its **mailbox** as the request
  channel, with **PR-consent** as the only promotion gate between tiers. This spec is the authorization
  substrate that the mesh-composition tier assumes; it defines *why* a cross-neighborhood write is or isn't
  trusted, leaving *how tiers are wired* to that tier's own spec.
- **With the kernel** — fully orthogonal. Nothing here touches `brainstem.py`, the agent ABI, or `/chat`.
  The substrate trust model is a **read of GitHub**, realized entirely by agents and CI, never an engine
  edit. "Engine, not experience" holds.

---

## 8. Worked example — proposing a new resident into a neighborhood roster

**Scenario.** `@alice` runs a brainstem in the `kody-w/rappterbook` neighborhood. She is **not** a
collaborator on the canon repo. She wants her twin added to the public residents roster
(`raw.githubusercontent.com/kody-w/rappterbook/main/residents.json`). `@kody-w` is the sole authority.

**Step 1 — propose (MAILBOX, `proposed`).** Alice's agent appends to the mailbox:

```
POST /repos/kody-w/rappterbook/issues
title: "resident: add @alice/twin"
body:  rapp-commons-event/1.0 payload { add: { rappid: "rappid:@alice/twin:9f3c…(64hex)", endpoint: "https://alice.github.io/twin/" } }
```

GitHub records the author as `@alice`. Authorization annotation:

```json
{ "substrate_trust": { "origin": "@alice", "state": "proposed", "acl_repo": "kody-w/rappterbook",
                        "consent": null, "rappid": "rappid:@alice/twin:9f3c…", "sig_suite": "none" } }
```

Every reader can now see *"@alice proposes adding @alice/twin"* — attributable, but **not yet canon**.
A conforming roster renderer MUST NOT list the twin from this open issue.

**Step 2 — (optional) sovereignty bind.** Alice's payload also carries a keypair signature over the
event bytes (`sig_suite: "ed25519"`, a canonical keypair suite on the rapp-eternity ladder on the `rapp-eternity/1.0`
ladder). This is additive: it lets `@alice` prove authorship even if GitHub is down or her account is
later suspended. **It changes nothing about whether the write is accepted** — acceptance still requires
consent.

**Step 3 — consent (PR + merge, `proposed → accepted`).** `@kody-w` (or an auto-merge bot running under
`@kody-w`'s policy) opens a PR that writes the entry into `residents.json` and **merges** it. The merge is
the consent signal; `@kody-w` is in the authority set. Annotation becomes:

```json
{ "substrate_trust": { "origin": "@alice", "state": "accepted", "acl_repo": "kody-w/rappterbook",
                        "consent": "merge:7343993", "rappid": "rappid:@alice/twin:9f3c…",
                        "sig_suite": "ed25519" } }
```

**Step 4 — publish (PUBLISH).** The merged `residents.json` is now world-readable canon at
`raw…/main/residents.json` (and pinnable at sha `7343993`). Roster renderers anywhere may now list
`@alice/twin`, CDN-cached, anonymously, forever-at-that-ref.

**Step 5 — revoke (moderation).** If `@alice/twin` misbehaves, `@kody-w` merges a **revert PR** removing
the entry. Canon moves forward; the twin is no longer listed. Alice's original proposal and its attribution
remain in history. No authority but `@kody-w`'s could have done this.

**What the example proves.** Outsider `@alice` could *request* (attributably) but never *authorize*; only
the authority `@kody-w` could promote a proposal to canon; the read path stayed free and public throughout;
and the optional keypair added sovereignty without ever becoming a requirement.

---

## 9. Non-goals

This spec defines **authorization semantics only**. It explicitly does **not** define:

- **The wire / transport.** How events append, order, deduplicate, echo, or materialize into views is
  `rapp-frame/2.0` (frame/echo) and the relevant event schemas (`rapp-commons-event/1.0`,
  `rapp-twin-chat/1.0`). This spec only annotates each such event's trust state.
- **The sealed payload codec.** Confidentiality is `rapp-sealed/1.0` (AES-256-GCM sealed envelope). This
  spec only mandates *that* secrets are sealed-not-published, never *how*.
- **The rappid string format / keypair suites.** Identity-the-string, its content-addressing, and the
  canonical `sig_suite` ladder are `rapp-eternity/1.0`; this spec only *consumes* a rappid and a ladder
  suite for optional binding.
- **The mesh-composition / metropolis tier.** How neighborhoods are wired into estate→metropolis is its
  own spec; this one supplies the trust substrate it stands on.
- **`/chat` and the agent ABI.** Untouched. This is a read of GitHub realized by agents + CI, never an
  engine concept.

---

## 10. Conformance

An implementation conforms to `rapp-substrate-trust/1.0` iff:

1. It treats `raw`/Pages content as public canon and **never** publishes a secret unsealed (§2.1).
2. It treats an Issues-API append as an **attributable `proposed`** write and **never** acts on its
   contents as canon (§2.2, §3).
3. It authorizes a canonical write **only** via a merged PR whose merging login is in the target repo's
   collaborator set (§2.3–§2.4).
4. It tracks the `proposed`/`accepted` state of every substrate write and exposes (or can derive) the §5
   authorization annotation.
5. It accepts a validly-consented write that carries **no** keypair signature (keypair-optional, §5), and
   treats any keypair signature strictly as additive sovereignty, drawing its `sig_suite` only from the
   `rapp-eternity/1.0` ladder (`none` → `ed25519` → `ecdsa-p256` → reserved-PQ).
6. It degrades to last-known pinned canon + optional keypair-verified proposals when the substrate is
   unreachable, and resumes the consent flow on reconnect (§6).
7. It introduces **no** RAPP-specific auth server, second ACL system, `sig_suite` not on the
   `rapp-eternity/1.0` ladder, `/chat` change, or kernel edit.

---

*`rapp-substrate-trust/1.0` — locked. Filed in the spine's **identity (authority)** layer. The substrate
is the only persistence-and-consent plane; `/chat` remains the only wire (Constitution Art. XXV). Reads are
free; writes are proposals; consent is a merge; authority is the ACL; sovereignty is optional. Build from
it, never into it.*