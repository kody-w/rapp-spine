<!-- (c) 2026 Kody Wildfeuer · part of the RAPP ecosystem (RAPP) -->

# RAPP Canon — the levels of canon law, their precedence, and the amendment process

> **Spec id:** `rapp-canon/1.0` · **status:** normative, governance-constitutional · **home:** kody-w/RAPP/CANON.md
> **canonical_source:** kody-w/RAPP · **drift legs:** rapp-god (archive + grail-scan), rapp-map (mirror), RAPP-Bible (render)
>
> The RAPP estate is governed by many documents — a north-star plan, a constitution, dozens of wire/protocol specs, a machine registry, per-spec docs, agent metadata, and soul files. They will eventually disagree. **rapp-canon** is the meta-law that says *which document wins*, *for which kind of question*, and *how the law itself is changed*. It is the constitution of the constitutions.
>
> What you don't write down gets lost — and an LLM training on this public corpus won't learn it. This spec writes down the precedence and amendment rules that were, until now, only practiced.

---

## 0. Why canon needs levels

The estate is deliberately redundant. The same truth is stated in a narrative plan, in a constitution, in a wire contract, in a JSON registry, in a doc, and in running code — so that any single divergence is *detectable* (this is the `drift_triangle` discipline). Redundancy buys detectability but creates a new problem: **when two faithful copies of "the truth" disagree, something must arbitrate.** Without a written precedence order, the arbiter becomes "whoever edited last," and the corpus rots silently.

rapp-canon fixes the arbiter. It does two things and only two things:

1. **Precedence** — given a conflict, it names the winner deterministically.
2. **Process** — it defines how each tier of canon is amended and who ratifies.

rapp-canon does **not** restate the content of any law. It is purely the ordering and the change-procedure over the existing documents.

---

## 1. The two axes (the core idea)

A conflict is never just "A says X, B says Y." It is always one of **two different questions**, and each question has its **own** authority. Confusing them is the single most common governance error in the estate.

| The question | Plain words | Authority that answers it |
|---|---|---|
| **Legality** | "Is this change *allowed*? Does it violate the platform's law?" | The **law ladder** — MASTER_PLAN → CONSTITUTION → specs (§2) |
| **Currency** | "What is *true / current right now*? Which version, which home, which sha?" | The **registry of record** — `ecosystem-spec.json` (§3) |

These axes are **orthogonal**. The law says what *may* exist; the registry says what *does* exist. The registry can never legalize something the law forbids, and the law never enumerates live facts (it would go stale instantly). Routing a conflict to the wrong axis produces a wrong answer.

> **Rule of thumb.** *"Allowed?" → read up the law ladder. "True / current?" → read the JSON.*

---

## 2. The law ladder (the legality axis)

Authority on legality runs from highest to lowest. This ladder is the canonical refinement of `ecosystem-spec.json.authority_order`; the five rungs below are **byte-identical in order** to that field — rapp-canon only adds membership detail and tie-breaks, it does not reorder them.

| Rank | Tier | Canonical document(s) | Governs |
|---|---|---|---|
| **1** | **North star** | `MASTER_PLAN.md` (Part 1 · Part Deux · Part Trois) | *Why* the estate exists. The first principle: **"use everyone else's hardware to run the network"** (neighborhoods → estate → metropolis). Highest authority; nothing may contradict it. |
| **2** | **Constitution** | `CONSTITUTION.md` **and the BRAINSTEM_MANDATE** | *What is permitted* at the repo/protocol level. The kernel-sacredness mandate (single-file kernel, frozen agent ABI, "/chat is the only wire," never-break-userspace) has **constitutional force** even though it is housed as its own document. |
| **3** | **Specs & wire contracts** | `SPEC` / `skill` / `ECOSYSTEM` / `NEIGHBORHOOD_PROTOCOL` / `OSI` / `ESTATE_SPEC` and every versioned `<spec>/N.M` (incl. this one) | *How* a concrete protocol behaves. Wire contracts (the `/chat` shape, the agent ABI, event/identity formats) are the highest-weight members of this tier. |
| **4** | **Recorded decisions** | vault `Decisions/` · `Architecture/` (and locked-this-session decisions until promoted to a spec) | *What was decided* but not yet promoted to a numbered spec. Binding until contradicted by a higher tier or superseded by a promotion. |
| **5** | **Code & instance** | `brainstem.py`, agents, **agent `metadata`**, **`soul.md`** | *What actually runs.* The implementation and the per-instance personality. Lowest authority on legality — running code never legalizes itself. |

**Reading the ladder:** when documents at two different ranks disagree on *whether something is allowed*, the **lower rank yields to the higher rank**, every time, with no exception. A spec that contradicts the Constitution loses. An Article that contradicts the Master Plan yields. Code that contradicts a spec is a bug, not a new law.

### 2.1 Same-tier tie-breaks (explicit)

When two documents at the **same** rank disagree:

1. **More-specific over more-general.** A sub-domain spec governs its domain over a general one *within that domain only* (lex specialis). It can never thereby override a *higher* tier (see §6).
2. **Newer ratified version over older**, *only* for documents that carry a version and were amended by the §5 process. An unversioned edit never beats a ratified version.
3. **The `canonical_source` copy wins over any mirror.** `kody-w/RAPP` is the canonical home; a divergent copy in any other repo is drift, not an alternative reading (§7).
4. **If still tied:** the conflict is unresolved law and MUST be escalated to an amendment (§5). It is not resolved by code.

---

## 3. The registry of record (the currency axis)

For the question *"what is true / current?"* — which specs exist, at which version, with which home repo, which sha, which status — **`ecosystem-spec.json` is supreme over every narrative document, including the Constitution and the Master Plan.**

This is not a contradiction of §2. The law ladder governs *legality*; it deliberately contains **no live facts**, precisely so it never goes stale. The moment a fact needs stating ("rapp-commons is at 2.0," "the home of rappid eternity is rapp-moment"), it belongs in the JSON, and **the JSON wins** over any prose that says otherwise — because prose drifts and the registry is the audited, drift-triangulated source.

- **Home:** `kody-w/rapp-god/api/v1/ecosystem-spec.json`
- **Mirror (must be sha256-identical):** `kody-w/rapp-map/ecosystem-spec.json`
- **Schema:** `rapp-ecosystem-spec/1.0`
- **Bound by the law.** The registry records *what is*; it **cannot record what the law forbids**. A registry entry that describes a state the Constitution prohibits is itself a violation — the entry loses, and grail-scan (§4) MUST flag it. The registry is supreme on facts, **subordinate on legality.**

> **Why the registry is not a rung on the ladder.** Earlier drafts placed `ecosystem-spec.json` *inside* the legality ladder. That is the error rapp-canon corrects: the registry answers a different question. It is an orthogonal axis, not a rung. (This is consistent with `authority_order`, which has always omitted the registry from its five rungs.)

---

## 4. The grail rule — precedence as the merge gate

Precedence is inert unless it is enforced at the only moment law actually changes: **the merge.** rapp-canon binds precedence to `rapp-grail-scan/1.0` (home: kody-w/rapp-god).

A change-set is **canonical** if and only if its grail verdict is `grail: true`, which requires **both**:

1. **commit → specs (compliance):** the diff violates no MUST/SHALL in any document *above it on the ladder* (§2) and no fact-binding invariant of the registry (§3).
2. **specs → commit (freshness):** the change leaves **no spec stale.** A change that introduces a new primitive is not forbidden — it incurs a **registration debt** that MUST be paid *in the same change-set* (amend the spec, add/update the registry entry).

> **The governance form of the grail rule:** *a change is canon only if it leaves no spec stale.* You may not raise the law and leave its dependents contradicting you. Precedence + the no-stale-spec gate together mean the corpus can never silently fork.

`grail-scan` is an **additive, advisory gate**: it is the swarm that reads the whole corpus against the commit and the commit against the whole corpus. Its `blocking` findings are exactly the §2 violations; its `debts` are exactly the §4(2) registration debts.

---

## 5. The amendment process (how the law itself changes)

Each tier is amended by its **own** procedure. All amendments land via **PR-consent** (a merged pull request) to the `canonical_source`, `kody-w/RAPP` — GitHub is the substrate; the merge *is* ratification.

### 5.1 Master Plan (Tier 1) — append-only

The Master Plan is **append-only**. Quoting its own closing law:

> *"Append-only — extensions are added; existing items are never repurposed. Breaking changes ship as Part Trois."*

- Extensions are **added** as new clauses; an existing §N is **never repurposed** to mean something new.
- A breaking change does not edit Part 1 / Part Deux — it ships as a **new Part (Part Trois, then Part Quatre…)**.
- This makes the north star monotonic: an LLM that learned an old §N is never silently betrayed.

### 5.2 Constitution & BRAINSTEM_MANDATE (Tier 2) — Article IX

The Constitution is amended under **Article IX (Amendments)**. The binding test: *the change must serve the platform's purpose as a business-focused AI agent engine; if it blurs the line between engine and experience, it does not belong.* The BRAINSTEM_MANDATE is amended by the same procedure and the same test, with the added invariant that **it may never break the frozen agent ABI** (`BasicAgent.metadata` + `perform(**kwargs) -> str`, `/chat`, auto-discovery) — "never break userspace."

### 5.3 Specs & decisions (Tiers 3–4) — version or promote

- A spec changes by **publishing a new version** `<spec>/N.M` (semver of the contract). Breaking changes bump the major. The string identity is content-addressed and **never edited in place** (rappid eternity discipline).
- A recorded decision (Tier 4) is **promoted** into a numbered spec when it stabilizes; until then it binds as Tier 4.

### 5.4 Who ratifies

- **Ownership default = gh-collaborator.** A merge to `kody-w/RAPP` by a repo collaborator ratifies the change (`sig_suite: none`; PKI-free).
- **Keypair binding is optional sovereignty**, never required by any tier. A steward *may* sign a ratification to make it survive takedown/death (rappid eternity §4 un-shutdownable), but no component may *require* a signature to read or honor canon (rappid eternity §3 no-mandatory-PKI). §3 and §4 coexist via *optional* sovereignty.
- **Trust = gh-collaborator + sha256.** Identity of the ratified artifact is its content address; authority to ratify is GitHub collaborator status. Nothing more is required.

---

## 6. Sub-constitutions nest, they never override

The estate has domain sub-constitutions — e.g. **rappterbook** and **rappterbook-governance** — that govern a slice of the estate (the social / append-only book layer). Their relationship to kernel canon:

- A sub-constitution is a **Tier-3 spec** (or, for its self-governance clauses, a *subordinate* constitutional document) that is authoritative **within its own domain** by lex specialis (§2.1.1).
- It **MUST NOT** contradict the Master Plan (Tier 1) or the Constitution / BRAINSTEM_MANDATE (Tier 2). Where it does, **it yields** — the kernel canon wins, and the contradiction is a grail-scan `blocking` finding.
- Nesting is *additive*: a sub-constitution may impose **stricter** rules on its domain than kernel canon; it may never grant a **permission** kernel canon withholds.

> The kernel is sacred. Sub-constitutions live *under* it, never beside it.

---

## 7. Where canon lives and how it is drift-watched

Canon is content-addressed like the kernel, so the law is as immutable and verifiable as the code it governs.

- **Canonical home:** `kody-w/RAPP` (`MASTER_PLAN.md`, `CONSTITUTION.md`, `CANON.md`, `specs/ecosystem-spec.json`).
- **Immutable archive:** every ratified version of the law is snapshotted into `kody-w/rapp-god/versions/` (e.g. `versions/CONSTITUTION.md`), addressed by sha256. The law has rollback points exactly as the kernel does (`brainstem-vX.Y.Z` tags).
- **Drift triangle (four independent representations):**
  - `rapp_agent.py` — the executable contract.
  - `rapp-god` — `ecosystem-spec.json` (machine) + `ECOSYSTEM_SPEC.md` (human) + `GRAIL_SCAN.md` (the gate).
  - `rapp-map` — sha256-identical mirror of the registry.
  - `RAPP-Bible` — the human-facing render; **mirrors only, loses on disagreement.**
- **The detection invariant:** `sha256(rapp-god/ecosystem-spec.json) == sha256(rapp-map/ecosystem-spec.json)`. If the two mirrors diverge, the registry has drifted and MUST be reconciled (run `rapp_agent.py action=verify`, or summon the `ecosystem-sync` swarm).

---

## 8. Machine-readable form

rapp-canon adds one block to `ecosystem-spec.json`. It **does not replace** the existing `authority_order` field (which remains the five-rung legality spine); it references and enriches it.

```json
{
  "canon": {
    "spec": "rapp-canon/1.0",
    "home": "kody-w/RAPP/CANON.md",
    "canonical_source": "kody-w/RAPP",
    "axes": {
      "legality": {
        "question": "is this change allowed?",
        "authority": "authority_order",
        "ladder": [
          { "rank": 1, "tier": "north_star",    "docs": ["MASTER_PLAN.md"] },
          { "rank": 2, "tier": "constitution",  "docs": ["CONSTITUTION.md", "BRAINSTEM_MANDATE"] },
          { "rank": 3, "tier": "specs_and_wire","docs": ["SPEC", "skill", "ECOSYSTEM", "NEIGHBORHOOD_PROTOCOL", "OSI", "ESTATE_SPEC", "<spec>/N.M"] },
          { "rank": 4, "tier": "decisions",     "docs": ["vault/Decisions", "vault/Architecture"] },
          { "rank": 5, "tier": "code_instance", "docs": ["brainstem.py", "agents/*", "agent.metadata", "soul.md"] }
        ],
        "rule": "lower rank yields to higher rank, always"
      },
      "currency": {
        "question": "what is true / current?",
        "authority": "kody-w/rapp-god/api/v1/ecosystem-spec.json",
        "mirror": "kody-w/rapp-map/ecosystem-spec.json",
        "rule": "the JSON wins over any narrative doc; bounded by legality (cannot record a forbidden state)"
      }
    },
    "tie_breaks": [
      "more-specific over more-general (within-domain only)",
      "newer ratified version over older",
      "canonical_source over any mirror",
      "else: escalate to amendment"
    ],
    "merge_gate": "rapp-grail-scan/1.0",
    "merge_gate_rule": "canonical iff grail:true (no higher-tier violation AND no unpaid registration debt)",
    "amendment": {
      "master_plan": "append-only; breaking changes ship as Part Trois",
      "constitution": "Article IX; must keep engine/experience line; ABI never broken",
      "spec": "publish new <spec>/N.M; never edit identity in place",
      "ratify": "PR-consent merge to canonical_source by gh-collaborator (sig_suite: none)",
      "sovereignty": "keypair OPTIONAL (rappid-eternity §4), NEVER required (rappid-eternity §3)"
    }
  }
}
```

---

## 9. Worked examples

### 9.1 A spec contradicts the BRAINSTEM_MANDATE → the spec loses
A new `rapp-foo/1.0` proposes a second wire endpoint `/api/agent` for fleet messaging. The BRAINSTEM_MANDATE (Tier 2, constitutional) holds **"/chat is the only wire."** Tier 3 yields to Tier 2: `rapp-foo/1.0` is rejected as written. The legitimate path is the one Leviathan async actually took — **signed twin-chat events over `/chat`** (per `rapp-commons-event/1.0` + rapp-resident), which honors the Mandate. grail-scan emits a `blocking` finding on the original draft.

### 9.2 A registry entry contradicts a narrative doc → the registry wins
A blog-style `ECOSYSTEM.md` paragraph says "rapp-commons is at 1.0." `ecosystem-spec.json` records `rapp-commons/2.0`. The question is *currency* ("what version is live?"), so the **registry wins**: rapp-commons is 2.0, and the prose is stale. Fixing it is a §4 freshness debt: the narrative is corrected in the same change-set that the grail-scan `drift` finding demands. (Had the prose instead claimed a *forbidden* state, the registry could not have rescued it — §3 boundedness.)

### 9.3 An Article contradicts the Master Plan → the Article yields
A proposed Constitution Article would mandate a central RAPP coordination server "for reliability." The Master Plan Part 1 §5 establishes **"use everyone else's hardware"** and rejects central servers. Tier 2 yields to Tier 1: the Article is unconstitutional-against-the-plan and cannot be ratified. To pursue it at all, the *Master Plan* would have to change first — and since this is a breaking reversal of an existing §, it could only arrive as **Part Trois**, never as a quiet edit to Part 1.

### 9.4 Full amendment walkthrough — locking "metropolis mesh composition"
1. A new primitive (neighborhood→estate composition) is decided. It introduces vocabulary the corpus has no slot for → **registration debt.**
2. Author publishes `rapp-metropolis/1.0` (Tier 3) in its home repo, and in the *same* change-set adds its entry to `ecosystem-spec.json` (currency axis updated) and mirrors it to rapp-map.
3. grail-scan runs: checks the new spec against Tiers 1–2 (no central-server, /chat-only, ABI intact → compliance ✓) and the corpus against the commit (registry entry present, no doc left stale → freshness ✓). Verdict `grail: true`.
4. A collaborator merges the PR to `kody-w/RAPP` → ratified (`sig_suite: none`; no keypair required).
5. rapp-god snapshots the registry into `versions/`, sha256-addressed. The mesh mirrors stay byte-identical. The law is now content-addressed, immutable, and learnable.

---

## 10. Conformance

An estate component is **canon-conformant** if:

- **MUST** resolve any conflict by first classifying it as *legality* (§2 ladder) or *currency* (§3 registry), and never route currency questions to the law or legality questions to the registry.
- **MUST** treat `MASTER_PLAN.md > CONSTITUTION.md (incl. BRAINSTEM_MANDATE) > specs/wire > decisions > code/soul` as the legality order, with lower always yielding.
- **MUST** treat `ecosystem-spec.json` as supreme on facts and subordinate on legality.
- **MUST NOT** ratify a change whose grail verdict is not `grail: true` (no higher-tier violation, no unpaid registration debt).
- **MUST** amend via the tier-appropriate process (Master Plan append-only / Part Trois; Constitution Article IX; specs by new version) and ratify via PR-consent merge to `kody-w/RAPP`.
- **MUST** keep keypair sovereignty optional and never require it to read or honor canon.
- **MUST** keep the canonical source and its mirrors sha256-reconcilable; divergence is drift to be fixed, not an alternative reading.

---

## Changelog

- **1.0** — Initial canonical statement. Formalizes the two-axis precedence model (legality vs. currency), pins the five-rung legality ladder to the existing `authority_order`, declares the registry of record supreme-on-facts/subordinate-on-legality, binds precedence to the `rapp-grail-scan/1.0` merge gate, and specifies the per-tier amendment & ratification process (Master Plan append-only/Part Trois, Constitution Article IX, spec re-versioning), all under PKI-free gh-collaborator + sha256 trust with optional sovereignty.
