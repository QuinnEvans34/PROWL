# Plan 07 lane running log

**Rules:**

- **Append-only.** New entries go at the bottom. Earlier entries are never edited. Corrections are
  new entries that name what they correct.
- Each entry records what was actually done, why, what was decided and by whom, what was **not**
  done, and what comes next.
- Plans and intentions go in `SCOPE.md` and `PHASES.md`, not here.

---

## 2026-09-28: Lane opened; planning set drafted (Claude)

**Context:** Quinton asked Claude to own the Plan 07 lane while Codex focuses on imaging/data
readiness. Quinton wants all problems found on paper before code, reasoning documented throughout,
and all three team members kept current, including Notion.

**What Claude did:**

1. Read the approved design:
   - `implementation/07-literature-retrieval.md`;
   - `retrieval/CORPUS-AND-RIGHTS.md`, `QUESTION-SET-AND-EVALUATION.md` and `README.md`;
   - relevant rows of `DECISIONS.md` (D-073..D-087, D-202, D-209, D-211, D-401);
   - `operations/STORAGE-ROOTS-AND-ARTIFACTS.md` excerpts;
   - Codex's `CLAUDE-PLAN07-FOUNDATION-PACKET-2026-09-28.md` and
     `PLAN07-CODEX-DECISION-RESPONSE-2026-09-28.md`;
   - proposal v3.8/v3.9 and appendix v3.1 text (read-only extraction), and the historical v2 draft
     `docs/_build_proposal.md` / `_build_appendix.md`.
2. Checked current public facts (web):
   - the PubMed 2026 baseline (1,334 files, released 2026-01-30; updates from n1335);
   - NLM data-use conditions;
   - the PMC distribution change (OA Web Service API retired, datasets off FTP, August 2026; PMC
     Cloud Service on AWS);
   - the E-utilities API-key rate guidance.

   Sources are cited in `ACQUISITION-PLAN.md`. The NLM FTP terms README could not be fetched by
   Claude's web tool (robots policy) and was not bypassed. Quinton reviews it at signing.
3. Wrote a decision brief (D1-D8) for Codex through Quinton. Codex answered in
   `PLAN07-CODEX-DECISION-RESPONSE-2026-09-28.md`.
4. Created six planning documents in this directory (hashes below) and this log. Directory and
   files were checked absent first. HEAD at start: `f4d7109b466fc12854be4a86c9893750399a0672`.

**Decisions made by Quinton (2026-09-28):** see `SCOPE.md` section 2.

- L-01 Tier 1 committed.
- L-02 Tier 2 as a gated extension.
- L-03 bulk baseline + updates acquisition.
- L-05 PostgreSQL + pgvector for the literature layer.
- L-06 literature only.
- L-07 files authoritative.
- L-08 frozen embeddings.
- L-09 database on the external drive (procedure pending).
- L-12 two documents for scope and phases.
- Docker preferred (L-10, proposed).
- Lexical baseline delegated to Claude (L-11, proposed).

**How the reasoning evolved (recorded for honesty):**

- Claude first framed PubMed only as an API. Quinton pointed out it is also a downloadable dataset.
  That was correct; the annual baseline is an approved NLM route.
- Claude argued against embedding all of PubMed as the graded corpus. Codex corrected two
  overstatements in that argument:
  - removing treatment papers is not a safety proof; refusal gates are required at any size;
  - a small corpus does not guarantee complete relevance labels.

  Claude accepted both. The conclusion still holds: Tier 1 is focused and graded, and broader
  coverage is tested through Tier 2 rather than assumed.
- On acquisition, Claude first recommended bulk, then agreed with Codex's recommendation of
  E-utilities for Tier 1. The reasons were the MeSH gap on recent records, selection being a new
  search policy, and no need for a decision amendment. Quinton chose bulk (L-03). Codex's cautions
  are carried into `SCOPE.md` section 6 as requirements.
- On storage, Claude recommended the internal SSD for the live database. Quinton chose the external
  drive because internal space is limited and everything is in one place. Claude agrees this is
  acceptable **because** L-07 makes the database rebuildable. The residual risks (Docker/fsync
  durability, drive latency, memory) are measured in P4 with a stop rule.
- The vector database was never in question. The approved proposal requires vector search.
  PostgreSQL + pgvector replaced the SQLite + LanceDB direction on Quinton's decision, with Codex's
  rundown (literature only, files authoritative).

**What was NOT done:**

- No code written.
- Nothing downloaded, installed or pulled (no Docker, PostgreSQL, models).
- No shared or Codex-owned file edited. No commit, stage or push.
- No PubMed or PMC query issued.
- The foundation packet remains on hold (L-14).

**Files created (SHA-256):**

| File | SHA-256 |
|---|---|
| `SCOPE.md` | `708967652b442b1e54a9666b21a5d7a4d4de004979683c1bf62797cd87d4b931` |
| `PHASES.md` | `8d50491b56ef7c32e658f646234ccae2198ac7bfaa0f188ab16333be21b80602` |
| `INFORMATION-NEEDS.md` | `b92f504c0894ece49b5b22281b345ecbbd2ad15f7721fa9b8772fdc29c8db171` |
| `SEARCH-AND-SELECTION.md` | `d4c82214258f6cbc3d288f0248c2ac763563d15743cca2ca4a42dc4e3e8d5ee1` |
| `SEED-SET.md` | `df6136575ad218bfe004f135811eb8c7e930f3e15aab2f1b7efd86f8082e3d9a` |
| `ACQUISITION-PLAN.md` | `f32d1351b122bf5fe46f106d508dd2c25557ef3100f838b9d8b0b322cc5961a6` |

**Pending decisions (owner):**

- Quinton:
  - approve or revise the PROPOSED L-items;
  - edit `INFORMATION-NEEDS.md`;
  - add and freeze seeds;
  - set the seed-recall and precision bars;
  - decide language and date rules.
- Codex: record the SCOPE section 10 amendments; revise the foundation packet (L-14); add the storage
  aliases.

**Next:** Quinton and Codex review this planning set. No phase beyond P0 starts until approved.

---

## 2026-09-28: Correction to SCOPE section 10 (Claude)

After the planning set was written, `git status` showed that Codex had concurrently added a PMC
route-verification note to `retrieval/CORPUS-AND-RIGHTS.md`. That file was not touched by Claude.
The SCOPE section 10 row for that file was updated to say the PMC part is done and only the bulk
baseline channel remains. New `SCOPE.md` SHA-256: `b29a15956cee3d183f2fd9088100e45af3b59d343c83c191e07262e4353d5346`. No other file changed.

---

## 2026-09-28: Notion work-log entry (Claude)

Created one Work Log entry in the PROWL Notion hub: "Plan 07 evidence system: lane opened and
planning set drafted" (Session, 2026-09-28).

- Hours left blank.
- Evidence is labelled local and uncommitted.
- The hub snapshot page was not edited; Codex keeps it.
- Entry: https://app.notion.com/p/3e9171a931408152ac59ecb71794a23d

---

## 2026-09-28: Revision 2 after Codex review (Claude)

**Trigger:** Codex reviewed all seven v1 files (message relayed by Quinton). It accepted the
architecture in principle and required revisions before implementation approval. Claude
revised only its own planning files. No shared or Codex-owned file was edited. No code, installs
or downloads.

**Corrections to Claude's earlier claims (recorded plainly):**

1. **Wrong recovery claim.** In v1 (SCOPE L-09, R-01) and in chat to Quinton, Claude said files
   being authoritative turns worst-case corruption into "a rebuild, not data loss". That was
   wrong. The database and the canonical artifacts share `PROWL-Data`, so a drive or filesystem
   failure can take both. Recovery then depends on verified independent backups or reacquisition,
   and upstream bytes (PMC objects, past-year baselines) may no longer be available. Fixed in
   SCOPE 5.7.
2. **Drills over-claimed.** A container kill proves process-crash recovery only, not durability
   under USB disconnection or power loss. `amcheck` does not validate pgvector indexes. v1's
   automatic "drop and rebuild" became a scoped recovery that preserves evidence. v1 assumed
   "smart shutdown"; the actual stop signal and grace period are now recorded at pin time.
3. **Unmeasured claims.** "Nothing on the internal SSD" and "mostly memory-resident" were removed.
   Moving Docker's disk image is a global setting, so it now needs inventory and approval.
4. **Wrong decision attribution.** L-05/L-06/L-07 now cite **D-260** (which Claude had not read
   before v1). L-03, L-08 and L-09 are attributed to Quinton's Claude discussion and need his
   confirmation to be recorded. D-077's text permits approved services generally; the
   E-utilities specificity is in P07-05 and `CORPUS-AND-RIGHTS.md`.
5. **Phase contradictions.** v1 said "11 phases" but listed 12 (P0-P11). P4 was described as fully
   parallel despite depending on P3's contracts. P8 did not gate on P7's freeze. P9's held-out run
   came before response development.
6. **Seed-set errors.** v1 wrongly said family 2 was empty (S-01 covers it). It treated a recent
   publication year as evidence of missing MeSH. It proposed treatment papers as negative seeds,
   which the current rules do not exclude.

**Changes by file:**

- **SCOPE v2:**
  - status labels distinguish D-260 approvals from discussion approvals;
  - embedding and generation choices marked PROPOSED (L-13, L-14);
  - packet hold renumbered L-15, selection specifics L-16;
  - 5.2 verification now covers content hashes and embedding checksums;
  - 5.3 adds `source_event` and content-hash revision IDs;
  - 5.5 covers Docker scope, measured footprint and numeric coexistence limits on a synthetic
    workload;
  - 5.6 is the corrected procedure;
  - 5.7 is new: recovery honesty and a rebuild-set backup table (the shared 20 GiB cap is not
    assumed to be available);
  - reconciliation list rewritten.
- **PHASES v2:**
  - 13 phases (P0-P12) plus X1;
  - P4 split into P4a (infrastructure, independent) and P4b (contract-bound, after P3 review);
  - P4a starts with exact search plus one approximate configuration, with numeric triggers for
    expansion;
  - P8 gates on P7;
  - development selection (P9) and response development (P10) are separate, then a complete freeze
    and one held-out run (P11), then integration (P12);
  - P7 defines span coordinates, grade mapping, span-hit recall (denominator fixed across
    chunking), label versions and the required second consistency pass;
  - fresh confirmation sampling added to P6.
- **SEARCH-AND-SELECTION (policy v0, revision 2):**
  - IMG defined;
  - WORKFLOW cap of 500 with a deterministic order;
  - qualifier used as a recorded feature with a preset v1 rule;
  - one disposition plus multiple reason codes with precedence;
  - language, missing-date and competing-date rules;
  - sampling rubric, strata, census for small strata, relevant/partial reported separately,
    development versus fresh confirmation samples.
- **ACQUISITION-PLAN revision 2:**
  - full envelope for run B;
  - capacity model with every component;
  - parsed-store location, authority, format and lifecycle;
  - event-log revision identity and replay;
  - required downloader and parser tests;
  - upstream-availability caveat.
- **SEED-SET revision 2:**
  - assisted citation-chaining discovery with Quinton's review;
  - identifiers verified against the local baseline;
  - indexing status taken from `MedlineCitation/@Status`;
  - negative seeds must be genuinely outside the policy;
  - prior exposure disclosed;
  - coverage table corrected.
- **INFORMATION-NEEDS revision 2:**
  - prior exposure disclosed;
  - N1.4 and N3.4 phrased as general and literature-based;
  - RF8 narrowed to prohibited disclosure, with answerable provenance questions separated.

**New SHA-256 (this entry does not include its own hash):**
- `SCOPE.md`: `009a596afc764f804f84ab0247f000c55390c0d31db09276b4dfb1f26f680112`
- `PHASES.md`: `9ed4af47ace244134336f4a9d5a9a825f6b0993d34d9b810087d778d0f006744`
- `INFORMATION-NEEDS.md`: `5e9764cc94c6d06db4b9b84ec766128aaa6c1d3599fe18f04c8e8d8e9f1a0721`
- `SEARCH-AND-SELECTION.md`: `9dc44a5d16506f2c3af65a4277400d116135ebfc42c2bf8eecb82338a0a54315`
- `SEED-SET.md`: `6581117aad954af13b661b067bfc04c75a74baad586930b73e72670338b0185c`
- `ACQUISITION-PLAN.md`: `d8a611fcdc84c86d099b26d85d8f974e4b6d32164bae5f3c6e907ae9f1b56591`

**Unresolved decisions:**

- **Quinton:**
  - confirm L-03, L-08 and L-09 for recording;
  - approve PROPOSED items (L-04, L-10, L-11, L-13, L-14, L-15);
  - selection OPEN items (English-only, the 2000-cutoff range, WORKFLOW cap, seed-recall and
    precision bars);
  - Docker inventory approval if any shared setting is proposed;
  - record the Mac's RAM so the coexistence limits can be confirmed;
  - literature backup allocation after the P6 measurement;
  - whether to plan a second independent drive for raw sources.
- **Codex:**
  - SCOPE section 10 reconciliation;
  - revised foundation packet;
  - storage aliases;
  - the downloader/parser packet allowlist.

**Next:** Quinton and Codex review v2. No phase beyond P0 starts until approved.

---

## 2026-09-28: Notion work-log entry for revision 2 (Claude)

Created the Work Log entry "Plan 07 planning set revised (v2) after Codex review" (Session,
2026-09-28). Hours blank. Evidence labelled local and uncommitted.
https://app.notion.com/p/3e9171a9314081b89933fc2498fdf11a

---

## 2026-09-28: Revision 3 after second Codex review (Claude)

**Trigger:** Codex reviewed v2, confirmed the six document hashes against this log, and accepted
the architecture and phase structure. It requested six targeted corrections. It also verified the
Mac has **64 GiB physical RAM**, now recorded in SCOPE 5.5 and PHASES P4a; resource limits stay
PROPOSED until P4a measures them. Claude edited only its own planning files. No code, installs,
downloads or shared-file edits.

**Corrections (what was wrong in v2, and the fix):**

1. **The 50% span-overlap rule was unsound.** The missing half of a span can hold the negation or
   qualification that changes its meaning.
   - Gold spans are now minimal and self-contained, and direct support requires **complete
     containment**. Partial overlap counts only as partial evidence.
   - Span-hit recall is now a **proposed additional metric**; D-085's metrics stay official. A D-085
     amendment was added to SCOPE section 10.
   - Retrieved token volume is recorded, and cross-chunking comparisons use a fixed context budget
     (proposed 2,000 tokens).
   - The P9 primary metric is preregistered from the D-085 set (proposed: source-level recall@10).
2. **Capacity dependency cycle.** v2 required sample measurements and future Tier 1 artifacts
   before run A could be signed.
   - Added **run record S**, a separately authorized, tightly bounded sizing preflight (at most 3
     baseline + 2 update files + MeSH, at most 10 GiB, at most 2 h, not promoted).
   - The capacity model is now measured-plus-capped (100 GiB caps for Tier 1 artifacts and for
     database/recovery), rechecked before each phase.
3. **Selection depended on PMC eligibility before PMC was looked up.**
   - Selection is now two-stage: bibliographic candidates are frozen first; full-text availability
     and rights are resolved after.
   - `metadata_only` is assigned only after the lookup, so no-abstract candidates are looked up too.
   - The WORKFLOW cap is applied after hard exclusions, with missing years sorted last. There is no
     refill after stage 2, and that is reported.
4. **Confirmation edge case.**
   - A hash-based confirmation reserve (about 10%, salt fixed in advance, independent of policy
     version) is created before any development sampling.
   - Confirmation estimates the unseen remainder of each stratum.
   - Strata under 100 candidates are a census, with no independent confirmation claimed.
   - Preset limits: 3 policy revisions and 2 confirmation rounds. A second failure escalates. All
     attempts are reported.
5. **Backups conflicted with held-out isolation.**
   - Added SCOPE 5.8, a protected held-out store: an encrypted disk image using the built-in
     `hdiutil`, Quinton holds the passphrase, an independent encrypted copy is kept on the internal
     backup, evaluator access only in P11, and every access audited.
   - Git holds schemas, synthetic examples and the held-out manifest hash only.
   - Stated plainly: a local commit is not an independent backup until pushed.
   - Regenerated embeddings get a new artifact and build identity.
6. **Contract details.**
   - The filtered-search invariant now returns up to `min(k, eligible_count)`, with an explicit
     count and reason.
   - Seed verification uses the final baseline-plus-updates snapshot.
   - The missing-MeSH test condition is actual absence of MeSH headings, not non-MEDLINE status.

**New SHA-256 (this entry does not include its own hash):**
- `SCOPE.md`: `1568a473e1ff5f37baecb37896da0aa684a9b35e98b6d513a5d56c0d905580b5`
- `PHASES.md`: `a045dcce9f146cafb8109c8301deefcf4a659fa10ac6134002e79e6b676d954e`
- `SEARCH-AND-SELECTION.md`: `e09a4456d2cb908f95f747aad4f041b7dca3deba5b4cfb318ab63b72f2828da8`
- `ACQUISITION-PLAN.md`: `27bf156d47ac17dc31f6990b599641f94ef865f137e0ae14efdd8e2d5f05a0d2`
- `SEED-SET.md`: `39ee09bc8327c6bccc9f15f859ebf041345bde68385d4a3639134aa6f8f66d81`
- `INFORMATION-NEEDS.md`: `5e9764cc94c6d06db4b9b84ec766128aaa6c1d3599fe18f04c8e8d8e9f1a0721`
- `INFORMATION-NEEDS.md` is unchanged in this revision.

**Remaining decisions:**

- **Quinton: confirm for recording.**
  - L-03 bulk PubMed acquisition. Codex's view: reasonable if you want the reusable snapshot; not
    required for a capable focused expert; confirm separately from the database choice.
  - L-08 frozen embeddings. Codex: yes.
  - L-09 external-drive database as a direction to test, with the SCOPE 5.7 backup limits
    understood. Codex: acceptable.
- **Quinton: approve or revise the provisional selection controls.** Codex: reasonable as
  provisional controls, not proof of accuracy.
  - English-only, with explicit missing-language handling.
  - 2000 to cutoff; known foundational-paper misses are reviewed through seed recall.
  - WORKFLOW cap of 500.
  - Bars: seed recall at least 90%; confirmation at least 60% relevant+partial and at least 40%
    relevant.
- **Quinton: the remaining PROPOSED items.**
  - L-04, L-10, L-11, L-13, L-14, L-15.
  - Proposed context budget of 2,000 tokens.
  - Protected held-out store design (SCOPE 5.8).
  - Run record S caps.
  - Tier 1 and database capacity caps (100 GiB each).
- **Codex / Quinton:** the D-085 span-hit metric amendment; SCOPE section 10 reconciliation; the
  revised foundation packet; storage aliases; the downloader/parser packet allowlist.
- **Later (measured):** literature backup allocation (P6); a second drive for raw sources (OPEN).

**Next:** Quinton decides. Codex reviews v3 only if Quinton wants another pass. Nothing executes
until the relevant authorizations exist.

---

## 2026-09-28: Notion work-log entry for revision 3 (Claude)

Created the Work Log entry "Plan 07 planning set revision 3 (second Codex review)". Hours blank.
Evidence labelled local and uncommitted.
https://app.notion.com/p/3e9171a93140816891e5c6ea623c77d7

---

## 2026-09-28: Revision 4 after third Codex review (Claude)

**Trigger:** Codex accepted the architecture and asked for four procedural corrections plus an
approval checklist that separates design, provisional settings and execution permissions. Claude
edited only its own planning files.

**Corrections:**

1. **Run S dependency cycle.** v3 listed "run S completed" among the prerequisites for signing,
   which included run S itself.
   - Prerequisites are now separated for S, A and B.
   - Added a **sizing-only parser mode**: per-file, no event log or snapshot, outputs refused by
     selection and promotion.
   - Run S gets a total scratch cap of 40 GiB (downloads + decompressed + parsed) alongside the
     10 GiB download cap.
   - Volume and free-space checks happen before each file and every 60 s.
2. **Confirmation isolation.**
   - Added a global, append-only **inspected-PMID ledger** across versions, strata, rounds and
     censuses. Any inspected PMID is permanently ineligible for confirmation.
   - A stratum with fewer than 20 unseen reserved records gets no confirmation claim, and the
     limitation is reported.
   - A census stratum never later claims confirmation.
3. **Held-out lifecycle.** v3's "access only in P11" was impractical, because authoring, the
   consistency pass, freezing and backup verification all need access.
   - SCOPE 5.8 now defines authoring (read-write, logged), freeze (a new frozen image, hashes
     recorded), backup verification (image-hash comparison) and evaluation (read-only mount,
     logged).
   - The access boundary is stated honestly as procedural: a mounted image is readable by any
     process running as Quinton's user, so it is mounted outside agent-connected folders and the
     passphrase is not given to agents. The static path check is not an access-control guarantee.
   - This is not drive-wide encryption.
4. **Ranked metrics versus context-budget metrics.**
   - Part A (ranked): a defined 50-passage ranking, deterministic tie-breaking, source
     deduplication by first occurrence with renumbered ranks, the official D-085 metrics, and
     proposed span-hit recall.
   - Part B (delivered evidence): 2,000-token starting budget, pinned and named tokenizer,
     whole-passage packing that skips rather than truncates, and support counted only if a span is
     completely inside the text actually supplied.

**Added:** SCOPE section 12, an approval checklist in three groups:
- A. architecture and design;
- B. provisional experimental settings;
- C. execution permissions, none granted.

The 100 GiB caps are labelled ceilings, not expected sizes. The model choices are listed as
needing specific named models before any download.

**New SHA-256 (this entry does not include its own hash):**
- `SCOPE.md`: `e603d5799939b19fd4e12c2afd603e4837c196b948a823c11ecd192063c8956a`
- `PHASES.md`: `98bd849e3bfbb76310d9d29fddb66951878bca7c79d42f5c09f8d0c0682d261c`
- `SEARCH-AND-SELECTION.md`: `bcddbb4b78ba6ab50be059936ecb606fb145b9a1db81f1ab58761edd30c0728c`
- `ACQUISITION-PLAN.md`: `39e3752005907483d60667603a520ab549f9219dcb17d213f9c6de4f9e99fd2d`
- `SEED-SET.md` and `INFORMATION-NEEDS.md` are unchanged in this revision.

**Next:** Quinton decides the SCOPE section 12 groups A and B. Group C items are requested one at a
time. Codex issues the revised synthetic foundation packet (P3).

---

## 2026-09-28: Notion work-log entry for revision 4 (Claude)

Created the Work Log entry "Plan 07 planning set revision 4 (architecture accepted; approval
checklist)". Hours blank. Evidence labelled local and uncommitted.
https://app.notion.com/p/3e9171a931408136bd83f8f24ca388ea

---

## 2026-09-28: Quinton approves the planning set (Claude records)

**Decision (Quinton, in the Claude discussion, 2026-09-28):** "full approve on everything
suggested". Recorded with this exact scope:

- **Approved (SCOPE section 12, group A, design):**
  - Plan 07 scope, the 13-phase structure, and development/held-out separation;
  - L-03 bulk PubMed baseline + updates as the intended route;
  - L-08 frozen embedding artifacts;
  - L-09 external-drive database as a direction, subject to the P4a trial and the SCOPE 5.7 backup
    limits;
  - L-10 Docker and L-11 `ts_rank_cd` baseline as prototype candidates;
  - the encrypted held-out container (SCOPE 5.8);
  - two-stage selection, the confirmation reserve and the inspected-PMID ledger.

  L-04 (the PMC Cloud route) and L-15 (the packet plan) are recorded as approved as part of the
  approved scope. L-03, L-08 and L-09 are **confirmed for recording** by Codex.
- **Approved as provisional (group B):** every setting in SCOPE 12B. Each is changeable by a
  recorded decision.
- **Not granted (group C):** every execution permission. That means:
  - no install, dependency, download (runs S, A, B) or model pull;
  - no Plan 04 coding.

  Each is requested separately when its phase is reached.
- **Still PROPOSED:** L-13 and L-14. Specific models must be named, with licences and sizes,
  before approval.
- **Not covered by this approval, and still Quinton's work:**
  - editing and freezing `INFORMATION-NEEDS.md` (P1);
  - reviewing seed candidates (P2).

**Files updated to show approval status (status lines only; no content changes):**
- `SCOPE.md`: header, section 2 register status cells, section 12 statuses.
- `PHASES.md`: header, and the P0 checklist row.

New SHA-256:
- `SCOPE.md`: `ca9a0de192cf5d6b241c17ca1796f02b7c39b006e2e9d872afc1c3b767861672`
- `PHASES.md`: `b4abe42d9d1b43504087175ab8f168356fd16356e6868402713ada862d1da4ca`

The other planning files are unchanged since revision 4.

**Notion:** Task Board rows created (Plan 07):
- "Plan 07: scope, phases and protocols planning set" (Done);
- "Plan 07 P1: Quinton reviews and freezes information needs" (Ready);
- "Plan 07 P3: synthetic retrieval foundation (revised packet)" (Planned);
- "Plan 07: record approvals and reconcile shared documents" (Ready, Codex);
- "Plan 07 P4a: PostgreSQL + pgvector platform prototype" (Planned; requires drive).

A matching Work Log entry is added separately.

**Handoff to Codex (integration owner):**

1. Record Quinton's approvals (L-03, L-08, L-09, and the approved lane design) in `DECISIONS.md`,
   citing this entry and SCOPE section 12.
2. Record the D-085 span-hit/delivered-evidence amendment as a **proposal** for Quinton's decision.
3. Work through the SCOPE section 10 reconciliation list.
4. Add the storage aliases `literature_source` and `prowl_literature_db`.
5. Issue the revised P3 synthetic foundation packet: records, passages, query gate, span-based
   labels, metrics (ranked plus delivered-evidence), with no SQLite FTS5.
6. Decide whether the uncommitted planning set joins the pending scoped Git checkpoint (Notion task
   "Review and publish a scoped Git checkpoint"). That checkpoint needs Quinton's explicit
   authorization.

**Claude's next action:** none until the revised P3 packet is issued and dispatched by Quinton.

---

## 2026-09-28: Phase 1 complete, information needs frozen v1 (Claude records)

**Decision:** Quinton reviewed the drafted needs with Codex and approved Codex's recommended
revisions as the final version.

- 11 needs kept; 11 edited to Codex's wording.
- 3 added: N4.6 reported performance and comparison limits; N5.5 public-dataset label provenance;
  N5.6 incomplete coverage and uncertain labels.
- The cystic/solid topic is folded into N2.4 (target extent), with no subtype inference.
- None dropped.
- Refusals: RF2, RF5, RF7 and RF8 edited. **RF9 added:** no case-specific certification of a
  contour and no acceptance decision on the reviewer's behalf.
- Authorship recorded as: Claude drafted, Codex recommended revisions, Quinton reviewed and approved.
- The added needs do not change the 60-question set (D-209).

**Frozen file:** `INFORMATION-NEEDS.md` v1, SHA-256
`d71577c27cebd5d54f516a7b2120273c3afba7dc077be3799bae4ccecbde8ac0`. Any change creates v2 with a
recorded reason.

**Observed (not reviewed in depth by Claude):**
- Codex has recorded D-261 to D-265 in `DECISIONS.md` (acquisition route, frozen embeddings, drive
  placement, design, provisional settings).
- Codex has issued `operations/CLAUDE-PLAN07-P3-PACKET-2026-09-28.md`, plus
  `PLAN07-INTEGRATION-HANDOFF` and `GIT-CHECKPOINT-SCOPE` documents.

Claude's other planning files are unchanged by this entry.

**Next:** Claude reads the P3 packet and begins the synthetic foundation once Quinton dispatches it.

---

## 2026-09-28: P3 started (Claude)

Quinton dispatched `operations/CLAUDE-PLAN07-P3-PACKET-2026-09-28.md`: "Go on P3 using Codex's
revised packet. Follow its write allowlist and synthetic-only scope. Keep the additional metrics
explicitly provisional, run the required tests, and stop after preparing your handback."

**Preflight:**
- `pwd` / `git rev-parse --show-toplevel` point to the PROWL checkout, as seen from Claude's Linux VM
  mount.
- `check_workspace.py` passed.
- HEAD is `f4d7109b466fc12854be4a86c9893750399a0672`, with 154 existing modified/untracked entries
  preserved.
- None of the allowlisted P3 paths existed.

**Environment:** the native `.venv-prowl` is a Mac venv. Its interpreter is a broken symlink inside
Claude's Linux VM, so native tests cannot run here. Claude develops and tests in a Linux container
(Python 3.12.3, jsonschema 4.26.0 and pytest 9.1.1 pinned as in the project). Native verification is
left to Codex.

**Scope held:**
- pure Python, synthetic fixtures only;
- no SQL, services, tokenizers, downloads, real text or held-out data;
- the span-hit and delivered-evidence metrics are labelled as a proposal.

---

## 2026-09-28: P3 handback to Codex (Claude)

**Delivered (allowlist only; 31 files):**
- `src/retrieval/`: 7 modules;
- `tests/retrieval/`: 7 test files plus 2 fixture files;
- `docs/capstone/contracts/retrieval/`: 12 schemas plus README;
- `docs/capstone/retrieval/FOUNDATION-DESIGN-2026-09-28.md`;
- `docs/capstone/retrieval/CLAUDE-FOUNDATION-HANDOFF-2026-09-28.md`, SHA-256
  `522e341bbe2754c5b3b021113d36127dfc0682d44ee69eb2f807e3a2a0b72b53`.

Every file's hash on the Mac was verified against the container copy (all 31 match; per-file hashes
are in the handoff).

**Tests (Linux container; NOT native):**
- `tests/retrieval`: 120 passed, stable over 3 runs;
- pyflakes clean;
- 10 reverted fault injections, all caught. One (duplicate span credit) was missed at first, and a
  new test was added to catch it.

The full native suite was not run; Codex runs both packet commands on the Mac. Two hand oracles
were corrected during development, as disclosed in the handoff; the implementation was never
changed to fit a test.

**Scope held:**
- no SQL/FTS5, services, tokenizer, downloads, real text, held-out data or shared-file edits;
- span-hit and delivered-evidence metrics labelled `proposed_provisional_not_official`;
- the D-085 metrics remain the official ones.

**Concurrent change observed (not Claude's):** HEAD moved from `f4d7109` to `21f838c` during P3
(Codex checkpoint commits "Checkpoint September data qualification and approved retrieval planning"
and "Record verified checkpoint publication and current handoff"). `git status` now lists the P3
paths as untracked; they were not part of those commits.

**Ownership:** handed back. Claude does not edit these files during Codex review. P4b waits for the
contract review and a separate psycopg 3 approval.

---

## 2026-09-28: P3 corrections R1–R5 started (Claude)

**Trigger:** `docs/capstone/retrieval/CODEX-P3-REVIEW-2026-09-28.md` (changes requested; P3 contract
review not accepted). Quinton asked Claude to address R1–R5, add regression tests and return an
updated handback.

**Scope:** the existing P3 write allowlist only. Same synthetic-only rules. The frozen needs and
existing decisions are unchanged; the proposed metrics stay proposals. No P4b work.

**Plan:**
- R1: recompute revision, rights and event identities at replay/assembly/permission boundaries;
  reject duplicate logical records.
- R2: bind evaluation to question, accepted query, configuration and corpus; verify passages and
  representations against the manifest; reject duplicate questions.
- R3: delivered evidence takes the verified ranking/corpus records, derives counted text from
  verified slices and enforces display permission separately from indexing.
- R4: bind per-paragraph original length/hash and the offset map into representation identity;
  validate coverage, order and bounds.
- R5: persist and verify an eligible count bound to the corpus (P3: all corpus members) and require
  min(50, eligible) results.

The P3 files on the Mac were confirmed unchanged since the first handback before work began.

---

## 2026-09-28: P3 corrections handback to Codex (Claude)

**Addressed:** R1–R5 from `CODEX-P3-REVIEW-2026-09-28.md`, each with regressions at the public entry
points. Codex's probes are now assertions, and every one is rejected.
- **R1:** revision, rights and event identities are recomputed at replay, assembly and permission
  checks. Byte-identical duplicate records are refused.
- **R2:** `evaluate` requires `queries` and binds each ranking to its question, accepted query,
  configuration and corpus. It refuses duplicate question IDs and re-verifies passages and
  representations against the manifest.
- **R3:** `delivered_evidence` takes the verified ranking, corpus and rights. It counts only verified
  slices and enforces display permission separately from indexing (`display_not_permitted`).
- **R4:** the offset map, original length and original SHA-256 are in the representation identity.
  `verify_offset_map` checks coverage, order and bounds. `verify_representation_source` proves
  provenance where the originals are available.
- **R5:** the ranking persists `eligibility_policy=all_corpus_members` and `eligible_count` (equal to
  the corpus members) and requires exactly min(50, eligible) results.

**Files:** 15 of the 31 P3 files changed, all inside the P3 allowlist. The three changed schemas are
`representation`, `supplied-ranking` and `context-result`; they stay at 1.0.0 because they were never
accepted, and Codex is asked to confirm or request 1.1.0. The functions whose signatures changed are
listed in the handoff. Every one of the 31 files on the Mac was verified by SHA-256 against the
container copy.

The handoff is `docs/capstone/retrieval/CLAUDE-FOUNDATION-HANDOFF-2026-09-28.md` (revision 2), SHA-256
`c6a072db9194c1d94b9f26fafec17eaf26db5c1a6d662cd2043923acefdb3c48`.

**Tests (Linux container; NOT native):**
- `tests/retrieval`: 182 passed (was 120), stable over 3 runs;
- pyflakes clean;
- 33 reverted fault injections on the new guards, all caught. Two were missed at first
  (representation re-verification, counter-kind guard); tests were added for them, and the
  implementation was not changed.
- One R4 oracle was corrected by adding a documented single-space-or-cluster rule. This is disclosed
  in the handoff.

**Scope held:**
- no SQL, services, tokenizer, downloads, real text, held-out data, dependency changes or shared-file
  edits;
- the frozen needs and decisions are unchanged;
- span-hit and delivered-evidence metrics remain `proposed_provisional_not_official`.

HEAD is still `21f838c`, and the P3 paths are still untracked.

**Ownership:** handed back. Claude does not edit these files during re-review. P4b waits for an
accepted contract review and a separate psycopg 3 approval.

---

## 2026-09-28: P3 accepted by Codex (recorded by Claude)

**Source:** `docs/capstone/retrieval/CODEX-P3-REREVIEW-2026-09-28.md`, relayed by Quinton. Codex
accepted handback revision 2 (SHA-256 `c6a072db…`) for the dispatched P3 synthetic scope. R1–R5 are
closed.

**Native evidence (Codex, Mac):**
- `tests/retrieval`: 182 passed;
- full suite: 813 passed, with the 2 existing torch.jit warnings;
- all 31 files hash-verified.

Codex reviewed Claude's mutation campaign as evidence and did not rerun it.

**Schema decision:** 1.0.0 is confirmed as the first accepted baseline and is identified by the
exact hashes in the accepted handback. The superseded pre-acceptance draft is not compatible merely
because it shares the version string. Future incompatible changes need version and migration review.

**Downstream obligations recorded by Codex (Claude carries these forward):**
- **P5 parser acceptance:** at real ingestion, call `verify_revision` with the pinned source bytes and
  `verify_representation_source` with the original paragraphs before publishing a representation.
- Identities detect change but do not authorize it. Production consumers resolve approved, pinned
  builds through the later artifact boundary.
- Fixture query rules and synthetic counters are not a security sandbox, anonymizer, tokenizer or
  permission to send text externally.
- `all_corpus_members` is the only accepted ranking-pool rule. New filters need a verifiable
  inventory and policy.
- Span-hit and delivered-evidence metrics remain proposed and provisional, not D-085.

**Gates now:**
- P3's contract-review dependency is satisfied.
- P4b still needs P4a plus a separate psycopg 3 approval; P4a needs its own authorization.
- No new phase is dispatched.

The proposed next literature task (Codex's week plan, `PRECOURSE-TRAINING-WEEK-2026-09-28.md`) is
bounded P2 seed-candidate work and acquisition-plan preparation for Quinton's review. It must not
compete with imaging for accelerator, memory or storage during a run.

---

## 2026-09-28: P2 started, protocols on paper (Claude)

**Dispatch:** Quinton, in the Claude discussion ("move onto P2 now"), after Codex accepted P3.
Codex's week plan names this bounded P2 work as the proposed next literature task.

**Scope (PHASES P2):**
- make `SEARCH-AND-SELECTION.md` policy v0 executable;
- propose seed candidates by citation chaining (`SEED-SET.md` rules 1-2) for Quinton's review;
- make run record S in `ACQUISITION-PLAN.md` ready for signature.

**Write set (Claude's planning lane; no shared files):**
- `planning/SEARCH-AND-SELECTION.md`, `planning/SEED-SET.md`, `planning/ACQUISITION-PLAN.md`;
- a new `planning/SEED-CANDIDATES.md`;
- append-only entries here.

Nothing else is touched: no code, downloads, installs, data, `DECISIONS.md` or Codex-owned
documents. `INFORMATION-NEEDS.md` stays frozen at v1.

**Literature inspection disclosed (SEED-SET rules 2 and 9).** This is citation chaining only,
before any selection run exists. Only reference-list metadata was read (titles, authors, venues,
years, DOIs); no abstracts and no full text. Every fetch went through Claude's web-fetch tool on
2026-09-28:
- **PanTS** (arXiv 2507.01291v1, HTML): full reference list read (69 entries).
- **Medical Segmentation Decathlon** (Nat Commun 2022, nature.com): full reference list read
  (45 entries).
- **S-02** (UEG J 2025, doi:10.1002/ueg2.12723): the Crossref record was read (130 deposited
  references, DOIs only). OpenAlex gave its PMID as 39865461, which matches the appendix. Titles were
  looked up in Crossref for 13 of the DOIs. One lookup (10.1148/radiol.220329) was rate-limited and
  skipped.
- **Cao 2023** (Nat Med, doi:10.1038/s41591-023-02640-w; second-level chaining from PanTS): Crossref
  reference list read (53 entries).
- **Spot checks:** three DOIs taken from the extracted lists were re-read in Crossref; title and
  year matched each time.
- **Web search** was used only to locate the S-02 and Cao 2023 article pages, never to find
  candidates.

**Gaps (could not read):**
- S-01 (Suman 2021): the Europe PMC references endpoint was rate-limited, and a Crossref
  bibliographic search found no match for the appendix citation.
- S-02: the full reference list with titles was not available. PMC required a CAPTCHA (not
  bypassed), Wiley returned 403, the Europe PMC endpoint was rate-limited, and OpenAlex returned 429.
- PANORAMA protocol: the Zenodo PDF (6.3 MB) could not be parsed by the fetch tool. Downloading it
  needs Quinton's permission.

Nothing was fetched from the device shell (it has no network) and no rate limit was bypassed.
Identifiers are "per source" and unverified until P5 verifies them against the local snapshot.

---

## 2026-09-28: P2 handback, for Quinton's review and Codex review (Claude)

**Delivered (Claude's planning lane only):**
- `SEARCH-AND-SELECTION.md` **revision 6**, policy v0:
  - the OPEN markers now read APPROVED-provisional, per D-265 / SCOPE 12B;
  - new section 11, execution definitions: exact XML paths, MeSH resolution and explosion,
    tokenizer, wildcard and hyphen rules, evaluation order, the reconciliation universe, dates and
    cutoff, deterministic sampling keys and order, the Wilson interval, a pinned Unicode runtime, and
    outputs;
  - a precise qualifier-trigger rule;
  - new section 12: 28 synthetic conformance examples (E1-E27 plus E5b), as oracles for the P6
    matching tests.

  No concept block, term list, branch, bar or exclusion rule was changed. Seven interpretations are
  listed in its status block for Quinton to confirm.
- `SEED-SET.md` **revision 5**:
  - second-level chaining;
  - named metadata lookups;
  - the P5 resolution order and citation check;
  - outcomes that are never auto-repaired;
  - scope probes (rule 10) and no tuning to seeds (rule 11);
  - the `title_only_branches` field;
  - a proposed rule 6 addition.
- `SEED-CANDIDATES.md` (new):
  - 22 PubMed candidates, 17 recommended and 5 optional;
  - 8 scope probes, 10 non-PubMed references and 3 optional negative seeds;
  - title-only branch predictions, coverage and gaps, and 7 decisions for Quinton.
- `ACQUISITION-PLAN.md` **revision 6**: run record S's envelope is complete for signature:
  - a deterministic file choice (`n0001`, `n0667`, `n1334`, the two newest updates, MeSH);
  - the executor is Quinton's Mac, not the Cowork VM;
  - a prerequisite status table, a pre-run checklist, and the post-run state;
  - a receipt location;
  - signing of a frozen copy (`RUN-S-SIGNED-<date>.md`, hashed in this log).

  The run A table is unchanged. Run B gains a licence-allowlist row, and the prerequisite lists
  read "before running", with signing last.

**File SHA-256 at handback:**
- `SEARCH-AND-SELECTION.md`: `be5edc3781f0216581c5ea5c07aab2a5c6a136e7bf523be74b9b63005f1382f1`
- `SEED-SET.md`: `91fabc6cddd4393bf8a96037644c0369c14feb186ade1b82fd05e9c6fef51276`
- `SEED-CANDIDATES.md`: `e60b7fc0754839b1b51e053884497373b019c3ff111b0d2248579bc5a4ca5850`
- `ACQUISITION-PLAN.md`: `1e0612f7a177201234a44a9fb8e4037e4a45cf9335fe07667d495d493a390b1c`

**Verification:** an independent Claude subagent reviewed the drafts adversarially, over two rounds
(33 findings, then 13). Everything it raised was fixed, or turned into an explicit question for
Quinton. It confirmed:
- every conformance example follows from the rules;
- every title-only branch prediction and every seed-versus-probe placement is correct;
- the counts and the 90% arithmetic.

This is desk review only. No code or data exists yet to test against.

**Findings that matter for Quinton:**
- **Family 5 is below the 2-seed minimum.** Eleven needs have no section A candidate, and the
  WORKFLOW branch has no seed. The chaining sources cannot fill these gaps, so papers Quinton has
  read or another named chaining source are needed.
- **With 17 seeds, the 90% bar allows one miss.**
- **Pre-run policy questions** (not seed-driven): whether to add a bare `AI` token to block A,
  `intra-observer`, or "reader studies".

**Incident (caused by Claude, fixed):** a `git status` from the Cowork VM created
`.git/index.lock`, and the VM could not delete it. That lock would have blocked Git on the Mac. It
was renamed to `.git/index.lock.stale-claude-20260928` (0 bytes). The lock is gone, and Quinton can
delete the renamed file. From now on Claude uses only `git --no-optional-locks`, read-only.

**P2 exit status (PHASES):**
- selection v0 and the seed list are **awaiting Quinton's review**;
- run S's envelope is **complete**; signing waits for S1 (aliases, Codex) and S2 (sizing-tool
  packet, group C, not granted);
- Codex's storage-alias and L-03 channel items are unchanged by Claude.

**Ownership:** handed back for review. Claude makes no further P2 edits until Quinton or Codex
responds.

---

## 2026-09-28: Codex P2 review received; exposure disclosures (Claude records)

**Review:** `docs/capstone/retrieval/CODEX-P2-REVIEW-2026-09-28.md`. **Revisions requested before P2
acceptance or seed freeze.** Codex verified the four handback hashes.

**Required revisions:**
- **R1:** seed eligibility must not depend on matching policy terms.
- **R2:** correct S-01 and recompute coverage.
- **R3:** tighten run S into a bounded execution contract.

Codex also recommended:
- **yes** to the three pre-run term changes: uppercase `AI`, `intra-observer`, `reader studies`;
- **keep** all seven written interpretations;
- a candidate-by-candidate list.

These are recommendations, not Quinton's decisions.

**S-01 citation conflict (confirmed):**
- Codex read the NLM record for PMID 33840636. It is Suman et al., "Quality gaps in public
  pancreas imaging datasets: Implications & challenges for AI applications", *Pancreatology*
  2021;21(5):1001-1008, doi:10.1016/j.pan.2021.03.016.
- Claude re-checked that DOI in Crossref, reading metadata only (title, authors, venue, pages). It
  matches.
- The appendix v3.1 citation ("Assessment of pancreatic ductal adenocarcinoma using CT imaging")
  does not match. The appendix is not edited.

**Pre-sampling exposure list** (to transfer into the inspected-PMID ledger when it is created in P6;
these records are kept out of independent confirmation):
- **Codex, 2026-09-28** (review):
  - web search `site.pubmed.ncbi.nlm.nih.gov "automation bias" radiology systematic review`;
  - the snippets included abstract-derived text;
  - PMIDs 21685142, 21335679, 27516495, 38635456, 42436051, 42446358, 42565207;
  - DOI 10.1148/radiol.222176;
  - the NLM page for PMID 33840636 (abstract and MeSH shown).
- **Claude, 2026-09-28** (P2 locating searches, disclosed for completeness): result **titles**
  were shown while locating the S-02 and Cao 2023 pages. Of those shown, these were not used:
  - PMC12286379, PMC13227626, PMC13236442, PMC13292061, PMC13103180, PMC12346778;
  - PMIDs 39830259, 42169791, 39665541;
  - nature.com articles s41746-025-01970-y, s41598-025-00512-6, s41746-025-02260-3,
    s41598-026-51814-2, s41591-025-03785-6, s41572-026-00699-6, s41591-026-04589-y.

  The Crossref records fetched in P2 may contain deposited abstracts. The fetch tool was told to
  return metadata only, and Claude did not see abstract text.

None of these is a seed candidate by virtue of the exposure. No relevance labels were assigned.

**Next:** Claude revises R1-R3 and prepares the S-01 correction and the policy amendment for
Quinton's approval. No freeze, download, tool build or phase start.

---

## 2026-09-28: P2 revision 2 handback, response to the Codex P2 review (Claude)

**Response to each finding:**
- **R1 (seed eligibility): addressed.**
  - SEED-SET rule 10 is now a topic-and-use test: Quinton judges need plus Tier 1 scope, and no
    policy term has to match.
  - Title-only branches are a diagnostic column only.
  - The eight probes were reassessed individually. Six are recall-eligible again (C-25 to C-30);
    C-25 still needs Quinton's scope decision. P-02 and P-03 remain probes, with reasons.
  - Known relevant misses stay in the denominator and are reported as coverage limitations.
- **R2 (S-01 and coverage): addressed.**
  - The corrected S-01 is proposed under the new rule 12, with the original citation and the
    conflict kept.
  - Its needs were reassessed to N5.5, N5.6 and N4.3; the old N1.1 and N2.1 are not carried over.
  - C-06 drops N1.3.
  - There is now one authoritative coverage table: 10 of 25 needs are uncovered. Family 2 meets
    rule 5 only if C-25 is accepted. WORKFLOW has no seed.
  - Set size is not tied to the bar.
- **R3 (run S contract): addressed on paper.** Changes:
  - listings are frozen, with strict name resolution and no substitution;
  - the MeSH size is taken before transfer;
  - caps count every byte, are enforced while streaming, and are cumulative per signed copy;
  - proposed parser safeguards: 4 GiB memory, 20x expansion, DOCTYPE tolerated but never fetched,
    external entities and entity expansion refused;
  - a representativeness record;
  - an append-only journal with a fallback, and no `completed` marker on partial work (a shell
    quoting slip dropped this word as the entry was being written; it was restored immediately);
  - the signed copy has literal values and replaces the status table;
  - S1 reflects Codex's observations (not complete).

  **Run S is not ready to sign.**
- **Policy questions:** amendment A1-A3 is written as **proposed** in SEARCH-AND-SELECTION section
  13, with oracles E5c and E28-E34 (E5b kept as historical). The A1 side effect on WORKFLOW is
  disclosed. Nothing has been applied.
- **Seven interpretations:** Codex's "keep" recommendation is recorded. The requested
  clarifications are added in sections 3, 5.1, 7.2, 9 and 11.1.
- **Candidate table:** Codex's recommendations are shown per row, and the priorities are
  rebalanced:
  - R: 16, plus C-25 if accepted;
  - O: 11.
- **Chaining source and exposure:**
  - Goddard 2012 is offered only as a search-suggested source for Quinton to designate, under a
    proposed rule 1 route.
  - The exposure list is logged, and the section 7.3 ledger is seeded from it at creation.
- **Operational status:** SCOPE section 10 gets a status note. The ACQUISITION prerequisite A1 is
  marked done (wording only).

**Files changed:**
- `SEARCH-AND-SELECTION.md`: `7f9cf5283d72983de8f61086039c1772f33e97833c021d8e5cb5472f66ad3964`
- `SEED-SET.md`: `e9801dac45bde04603396055101a70da9ddd2f8eecd0d383de75e0b61289d569`
- `SEED-CANDIDATES.md`: `6d57a7bf23f91169092c8400bf11d5e6cb198b909538c7976169e61c0f06565c`
- `ACQUISITION-PLAN.md`: `0867311c8d6304821dcdf8e088c23bf0353959b06938e7546b6c375b071eacc6`
- `SCOPE.md`: `8ebd22f023b744dfbd36e97a04053ecc628604085440156ea99fa6d960dd0273`

INFORMATION-NEEDS.md (frozen v1) and PHASES.md are unchanged.

**Verification:** a fresh Claude subagent checked the revision against the Codex review over two
rounds (23 findings, then 5 more). All were fixed, or made explicit decisions for Quinton.

**For Quinton (10 decisions, listed in SEED-CANDIDATES.md):**
1. the S-01 correction;
2. C-25's scope;
3. the scope bases for C-26 to C-30;
4. a second family-2 seed;
5. accepting each candidate;
6. the WORKFLOW source;
7. the probes;
8. the negative seeds;
9. amendment A1-A3 and the seven interpretations;
10. the PANORAMA PDF (it would need its own small signed run record).

**Not done, by instruction:** no seed freeze, no sizing run or download, no tool build, no new phase.

---

## 2026-09-28: Codex P2 re-review; wording fixes and decision sheet (Claude)

**Review:** `docs/capstone/retrieval/CODEX-P2-REREVIEW-2026-09-28.md`.
- R1-R3 are addressed at the planning level. This is **not** P2 exit, seed freeze, tool dispatch or
  a signed download.
- Codex measured `SEED-CANDIDATES.md` at `6d57a7bf...`, which matches this log's revision 2 handback
  entry.

**Hash discrepancy, explained (Claude's error):** Claude's chat message quoted `023a3254...` for
`SEED-CANDIDATES.md`. That hash was taken **before** a last one-line cross-reference fix ("decision
6"). The file was not rolled back. The hash in this log (`6d57a7bf...`) was the correct one at
handback.

**Codex's three wording fixes, applied:**
1. SEED-SET: the section "References outside PubMed seed recall" is renamed "Appendix references:
   where each now sits". C-30 is described as a proposed candidate.
2. SEED-CANDIDATES (draft 5) and the SEED-SET status now read "28 proposed candidates: 27 with stated
   scope bases, plus one scope-pending". Freeze counts use accepted, verified candidates only.
3. ACQUISITION-PLAN: the first/middle/last baseline samples are described as file-sequence
   positions, with no claim about publication-date coverage. The receipt records any observed year
   distribution.

**New:** `P2-DECISION-SHEET.md`, a compact sheet of 10 decisions for Quinton, prepared as Codex
recommended. It covers:
- the S-01 correction;
- amendments A1-A3;
- the seven interpretations;
- the seed subset;
- how to settle C-25's scope: a factual check, or another family-2 candidate;
- the WORKFLOW source;
- the rule 1 route;
- probes and negative seeds;
- the PANORAMA PDF.

**Hashes:**
- `SEED-SET.md`: `a702a3c4e4984c4d5b0b2c8ed12bbe294a99b70b146869437d4456f3416021fa`
- `SEED-CANDIDATES.md`: `76c751b086b49abcb985b432bdb016b587fdbde0402cc462ad961afb4c6fd95a`
- `ACQUISITION-PLAN.md`: `7e1323c0c90c26521042be73af86e6f6573145d4d375bf58b3d438b8fa8306d2`
- `P2-DECISION-SHEET.md`: `53e91ab48ce20315e2e38ecd907184e5b571073334e47d4359d4108912a40c5a`

**Unchanged:** SEARCH-AND-SELECTION.md (`7f9cf528...`), SCOPE.md, PHASES.md and INFORMATION-NEEDS v1.

No literature was read for this entry. Claude waits for Quinton's decisions.

---

## 2026-09-28: Quinton adopts the Codex decision-sheet review as the P2 outline (Claude records)

**Source:** `docs/capstone/retrieval/CODEX-P2-DECISION-SHEET-REVIEW-2026-09-28.md` (SHA-256 recorded
below). Quinton, in the Claude discussion: "Codex and I went over the decisions ... I would like you to
review that, and use that as the outline moving forward."

**Recorded as Quinton's decisions:** the review's recommendation table, with its item-6 wording
correction.

| Item | Decision | Status |
|---|---|---|
| 1 | Corrected S-01 approved as a candidate. The original citation and conflict are kept; P5 still verifies it | Approved |
| 2a-c | Amendments A1 (`AI`), A2 (`intra-observer`) and A3 (`reader studies`, one concept) approved | Approved |
| 3 | All seven interpretations approved as written | Approved |
| 4 | The 16 R candidates accepted **provisionally** as a candidate subset, not a seed freeze, with room kept within 15-25 for WORKFLOW candidates and a family-2 replacement. C-25 only if supported | Approved |
| 5 | Factual abstract scope check of C-25 authorized. Exposure is logged and excluded from confirmation. An inconclusive result is reported as inconclusive | Approved |
| 6-7 | Goddard 2012 designated as a chaining source, and the designated-source route in SEED-SET rule 1 approved. Designating it does **not** approve the review itself as a seed. That would be a separate, explicit decision | Approved |
| 8 | P-02 and P-03 kept as scope probes | Approved |
| 9 | The three negative controls kept | Approved |
| 10 | The PANORAMA PDF is allowed **in principle** only. It needs its own bounded, **signed** one-file run record, and is lower priority | Pending signature |

**Not decided:** P2 is not Done. There is no seed freeze, no run S signature, no tool dispatch and no
download.

**Next (Claude):**
- record these decisions in the planning files, and fold A1-A3 and the interpretations into v0;
- run the C-25 abstract check;
- chain Goddard's references (metadata only);
- draft the unsigned PANORAMA run record;
- hand back.

Decision-sheet review SHA-256: `4830b3e48ceb60adacc9c5c5bfbc2603546da1ed973c00de94a15c21d152061e`.

---

## 2026-09-28: Decisions applied; C-25 check; Goddard chaining; run record P drafted (Claude)

**Applied** (following the adopted decision-sheet review):
- **P2-DECISION-SHEET.md:** the decisions are recorded, and the item-6 wording is corrected.
- **SEARCH-AND-SELECTION.md revision 8:**
  - A1-A3 are folded into sections 2, 4, 11.3 and 12 (E5c and E28-E34 moved in; E5b and the E31
    counter-oracle marked historical);
  - the seven interpretations are marked approved.
  - **Selection v0 as a whole is NOT yet approved.** That is still an open P2 exit item, and the
    section 5.2 rules stay PROPOSED.
- **SEED-SET.md revision 7:** the rule 1 designated-source route and the S-01 correction are marked
  approved. The rule 6 addition is still proposed.
- **SEED-CANDIDATES.md draft 6:**
  - S-01 is approved, and the 16 R candidates are accepted provisionally;
  - the C-25 result is added;
  - new section A2 holds the WORKFLOW candidates.
- **ACQUISITION-PLAN.md revision 8:** unsigned run record P for the single PANORAMA PDF. It has a
  cap-aware retry, a signed-copy procedure, and a prerequisites entry.

**C-25 factual scope check: not performed; scope unresolved.**
- Crossref returned HTTP 429 twice.
- To locate the article, a web search restricted to link.springer.com was run:
  `Joskowicz "Inter-observer variability of manual contour delineation of structures in CT" European Radiology 2019`.
- The Springer article page (doi:10.1007/s00330-018-5695-5) was then rate-limited by the fetch
  proxy (HTTP 429), which instructed not to refetch that page.
- **No abstract was read.** Nothing is inferred about pancreas coverage.

**Goddard 2012 chaining** (designated source; metadata only):
- Crossref's deposited reference list for doi:10.1136/amiajnl-2011-000089 was read: 75 entries,
  mostly DOIs, plus some unstructured citations.
- Titles were then looked up in Crossref for 9 imaging-related DOIs (refs. 16, 33, 34, 36, 37, 38,
  39, 42 and 54).
- **Proposed:** C-31 to C-39 (section A2), with 4 marked R. Ref. 42 (Moberg 2001) was looked up but
  not proposed.
- The review itself is **not** a candidate.
- Finding: no proposed title contains a W term, so WORKFLOW reaches them only through their
  abstracts or keywords. This is reported, not tuned.

**Pre-sampling exposure additions** (for the P6 ledger):
- **Titles seen in the locating search, not used:** doi:10.1007/s11548-025-03331-2,
  doi:10.1007/s00784-024-05753-9, doi:10.1007/s10916-025-02263-3.
- **Titles seen from Goddard references:** the 9 DOIs above, plus the unstructured entries in the
  deposited list.
- No abstracts were seen. The Crossref records may contain deposited abstracts, but the fetch tool
  was told to return metadata only.

**Housekeeping (Claude's mistake):** a temporary file, `RUNNING-LOG.md.tmp`, was created in
`planning/` while hashing, and could not be deleted. It was moved to
`_to_delete/claude-RUNNING-LOG.md.tmp` at the repository root. It contains one hash line. Quinton
can delete it or the folder.

**Verification:** an independent Claude subagent checked the files against the outline and found 1
high, 3 medium and several low issues. All were fixed. The high issue: an over-claim that selection
v0 as a whole was approved, now corrected.

**Remaining decisions for Quinton** (`SEED-CANDIDATES.md`):
1. accept, reject or edit the A2 candidates, and confirm their analogical N5.1 mappings;
2. the section A O candidates;
3. the family-2 second candidate: retry C-25's check, or replace it;
4. signing run record P, when wanted.

P2 is not Done. There is no freeze, signature or download.

**Hashes:**
- `SEARCH-AND-SELECTION.md`: `44e0bcb9617568b9e2805c73b4947142fb689b74fcf76f6a30862552e78f96e1`
- `SEED-SET.md`: `fd7006a1fd160ae64de5f66d973c52b85dd1c596e6ea6a0567f75be3abe4cc8b`
- `SEED-CANDIDATES.md`: `e34f439f2303005bea83774027ff0ad8db66c697db02bf177e7c830eb5221c9b`
- `ACQUISITION-PLAN.md`: `7a9b4e3a153c527fcc1145594387e1731fd67e201936a65a47e6c01d857f2ed9`
- `P2-DECISION-SHEET.md`: `768ec25bb3d63cbd985036f3698401ee2fd27f1194b7fd5c1ba81a2779ff68a6`

Unchanged: INFORMATION-NEEDS.md (frozen v1), PHASES.md, SCOPE.md.

---

## 2026-09-28: Codex outline-application review; corrections applied (Claude)

**Review:** `docs/capstone/retrieval/CODEX-P2-OUTLINE-APPLICATION-REVIEW-2026-09-28.md`.
- All five handback hashes match. **P2 is not ready to freeze.**
- Keeping selection v0 as a whole unapproved is correct.
- The recorded adoption covers only the decision-sheet items. It does not cover C-31 to C-39,
  whole-policy approval, or any signature.

**Note:** Quinton's relay in the Claude discussion pasted Claude's own previous reply by mistake.
Claude worked from the review file in the repository.

**Corrections applied:**
1. **N5.1 kept open.** The section A2 needs column now separates direct needs from related
   background. N5.1 is related background only, and it is not counted as coverage.
2. **N5.2 claim qualified.** C-31 is a strong direct candidate. C-36 is plausible but needs
   verification. C-32, C-33 and C-35's titles do not establish automation bias.
3. **Run P attempt wording.** The record now reads: one target file, at most two attempts, aggregate
   received bytes at most 10 MiB, retry only when the remaining allowance covers the full file, and
   partial bytes and wall time recorded.
4. **Coverage bookkeeping.**
   - The table is renamed as the combined proposed pool.
   - Counts are given by status: accepted provisionally, proposed, verified or frozen.
   - The direct gap count is 9 in the combined pool (only N5.2 added), and N5.1 stays open.
   - The family-2 cross-reference is fixed to decision 3.

**Codex recommendations, recorded as recommendations** (not Quinton's decisions):
- **A2 working priority:**
  - R: C-31, C-32 and C-33;
  - verify scope first: C-36;
  - reserve: C-34, C-35, C-37 and C-38;
  - not in the initial subset: C-39.
- **O candidates:** keep all 11 as a reserve.
- **Family 2:** first a bounded exact-DOI PubMed lookup for C-25, if Quinton adopts it; otherwise
  chain C-10's reference list.
- **Run P:** stays deferred and unsigned.

No literature was read for this entry. The `_to_delete` temporary file is preserved; Codex
inspected it.

**Files:** SEED-CANDIDATES.md (draft 7), SEED-SET.md (reference to draft 7 only) and
ACQUISITION-PLAN.md (run P caps row). Hashes follow.
- `SEED-CANDIDATES.md`: `4f027137e94f42543447f9ea0c8231499f8b75e00f6ecf4b8429cb7043fde545`
- `SEED-SET.md`: `6c2ed18f9ce843e9c8250467af8e266eae01e2cfbb21d2d4e9f829d6512d5d0e`
- `ACQUISITION-PLAN.md`: `a2be620c6b03373bc6a84b6cd88bf4f2177313bddc1992da7f3991ca713fc826`

---

## 2026-10-03: Quinton's round-2 decisions; family 2 resolved by chaining; PANORAMA status (Claude)

**Quinton, in the Claude discussion (2026-10-03):** "I think we should continue on without codex's
direction. I trust you, you know what to do, and you should continue on."

**Working arrangement from now on (as Claude records it):**
- Claude proceeds on its own judgment within the Plan 07 lane, without waiting for Codex review.
- Claude keeps its own safeguards:
  - independent subagent checks;
  - disclosure and exposure logging;
  - no edits to Codex-owned shared files (DECISIONS, registry, contracts, operations);
  - no downloads, installs or signatures without Quinton.
- Codex reviews remain welcome, but they are no longer a gate on this lane's planning work.

**Decisions:**
1. **Section A2 working priority accepted:**
   - C-31, C-32 and C-33 accepted provisionally;
   - C-36 to verify;
   - C-34, C-35, C-37 and C-38 as reserves;
   - C-39 out.
2. **All 11 section A O candidates kept** as reserves.
3. **Family 2: left to Claude's judgment.**
4. **PANORAMA:** a question, answered below.

**Family 2 (Claude's action):**
- An official E-utilities DOI lookup for C-25 (`esearch`, `doi:10.1007/s00330-018-5695-5`) was
  refused by the fetch tool under robots.txt. It was **not** worked around, and no abstract was
  read.
- C-25's factual scope check therefore moves to P5, using the local snapshot (record and abstract
  read locally, exposure logged).
- Claude then chained C-10's Crossref-deposited reference list (doi:10.1097/RCT.0000000000001374;
  32 entries; titles, venues and years as deposited; no abstracts). Seven candidates are proposed
  as section A3, C-40 to C-46.
  - **C-40** (Med Phys 2021, doi:10.1002/mp.14782; pancreas intra- and inter-reader reliability) is
    recommended R. It **restores the family-2 minimum** with C-10.
  - **C-42** (Pancreatology 2021; normal pancreas CT attenuation by age and sex; N3.3) is
    recommended R.
  - The other five are reserves.
  - Convergence: S-01, C-02 and C-03 all appear in C-10's list. C-02's DOI (10.2214/AJR.21.26014)
    and C-03's DOI (10.1016/j.pan.2020.07.410) are now recorded per source.
- **Coverage warning (not tuned):** block M has no `reader` variant, so "inter-reader" in C-40's
  title does not match M. C-40 still enters as CORE and AI.
- The working recommended set is now **21** (22 if C-36 verifies), with at least two per family.
  There are 9 needs with no direct candidate; N5.1 stays open.

**PANORAMA:**
- The PANORAMA **dataset** (Zenodo CT batches 13715870, 13742336, 11034011 and 10999754, plus the
  labels at a pinned commit) was acquired in September. See
  `docs/capstone/data/PANORAMA-INVENTORY.md` and `acquisition-2026-09-19.json`.
- The **study protocol PDF** is a separate Zenodo record, 10599559. It is not in that inventory and
  not in the repository.
- Run record P stays unsigned and optional. It would only add a reference list for chaining.

**Pre-sampling exposure additions:**
- the titles of the 32 entries in C-10's deposited reference list;
- the robots-refused E-utilities request (nothing returned).

**Files:**
- `SEED-CANDIDATES.md` draft 8: section A3, statuses, the C-25 note, coverage, and the remaining
  decisions;
- `SEED-SET.md`: status counts;
- `P2-DECISION-SHEET.md`: round-2 decisions.

**Unchanged:** SEARCH-AND-SELECTION, ACQUISITION-PLAN, SCOPE, PHASES and INFORMATION-NEEDS v1.

**Hashes:**
- `SEED-CANDIDATES.md`: `931a668b44006d8575f484ede67501e5dceb37541fd44681ccdbd0afd5029e01`
- `SEED-SET.md`: `c37108a43e67affde53ba45c15248f747fd15ccedacfcb5948fbdb2574dd76a5`
- `P2-DECISION-SHEET.md`: `7b4a72bf18d9bcc36d2bc289364e837b59882e1a36eb0bf87df64bb579f1871b`

**Post-entry check (same day):** an independent Claude subagent reviewed draft 8 and found 10
issues. All were fixed:
- three places described Claude's steps as Quinton's decisions;
- stale sentences (the family-2 dependency on C-25, and N5.2 still in the uncovered-needs table);
- the reference-key numbering of C-10's list;
- missing disclosure pointers;
- the C-25 DOI's provenance (from a web search, so not per source).

The A3 title-only branches, the counts and the bar arithmetic were confirmed correct.

**Corrected hashes:**
- `SEED-CANDIDATES.md`: `7fcd2b783c9b99c55085f70a48e32220b4a2ca9abea072874b5b7b60bfcc044f`
- `SEED-SET.md`: `d68b0b18e1085f87cc413f91ca1ad8b720a86d9d7517cf4eea5dc6006fff604c`

## 2026-10-03: Quinton approves selection v0 as a whole; handoff to Codex written (Claude)

**Quinton's words:** "Yes, I agree on the search policy, continue with that. Then write out a prompt
for codex to work on whatever it needs to work on."

**Recorded:**
- `SEARCH-AND-SELECTION.md` revision 9: selection policy v0 **approved as a whole**. Revision 9
  records the approval only; no rule text changed. Any later change creates a new version (v0.1
  before the first run).
- `SEED-CANDIDATES.md` draft 8: the 21-seed working list is approved (22 if C-36 verifies in P5).
  This is a working list, not a freeze. Seeds are verified in P5 and frozen in P6; the 90% recall
  bar is unchanged.
- `P2-DECISION-SHEET.md`: round 3.

**P2 status:** all of Quinton's P2 approvals are complete. Remaining before run S can be signed:
- S1, the storage aliases and controlled literature writer (Codex-owned; creation needs Quinton's
  OK);
- S2, the sizing-tool packet (Group C; draft by Codex, dispatch by Quinton).

**New file:** `CLAUDE-HANDOFF-TO-CODEX-2026-10-03.md`. It holds the Plan 07 state and a paste-ready
Codex packet:
- L1: decision records;
- L2: the S1 plan;
- L3: the S2 packet draft;
- L4: the checkpoint file list;
- L5: housekeeping deletions, on Quinton's OK;
- L6: an options list (shared contract checks, D-085 amendment, P4a timing).

It dispatches nothing. No literature was read, fetched or downloaded in this step, so there are no
new exposures.

**Unchanged:** SEED-SET, ACQUISITION-PLAN, SCOPE, PHASES and INFORMATION-NEEDS v1.

**Hashes:**
- `SEARCH-AND-SELECTION.md`: `1cb96a960f04b58cb07a796a5ef0b2ea53e0337503279c8d373aa849f4b5c46a`
- `SEED-CANDIDATES.md`: `eceaa8bf57c7863f9cb2c1842f893b5e1d386002f05786364ca12099eda195f2`
- `SEED-SET.md`: `d68b0b18e1085f87cc413f91ca1ad8b720a86d9d7517cf4eea5dc6006fff604c`
- `P2-DECISION-SHEET.md`: `8f3abc520162a8edca3fc70bbe18c5ba48fc68b8e693724ad6c1f7b266074311`
- `CLAUDE-HANDOFF-TO-CODEX-2026-10-03.md`: `9978b8088d25fa9dc24bcc1999470a2feec51e4d822ab7352f1afb5d4e1142df`

## 2026-10-03: Codex L1-L6 handback reviewed; Quinton's S1/S2, cleanup and integration decisions; S2 dispatched to Claude (Claude records)

**Claude's review of the Codex handback (read only):**
- The nine Claude planning files and the handoff are byte-identical to the last logged hashes.
- D-336 to D-340 in `DECISIONS.md` match the logged approvals. They keep Claude's own steps
  distinct from Quinton's decisions, and no earlier approval is backdated as whole-policy approval.
- The S2 draft's run S annex was checked block by block: all ten blocks are byte-identical
  substrings of ACQUISITION-PLAN (SHA `a2be620c...`).
- Every path on the S2 allowlist is absent today. `tests/retrieval/` exists from P3;
  `scripts/retrieval/` does not.
- Gaps foreseen and raised with Quinton before dispatch:
  - macOS does not enforce `RLIMIT_AS`/`RLIMIT_RSS`, so a standard-library "hard" 4 GiB cap
    needs a watchdog;
  - urllib counts HTTP-layer bytes, not TLS bytes on the wire;
  - the parsed-store field set is only "events plus parsed fields" in ACQUISITION-PLAN, so S2 must
    declare the exact proposed field list it uses.

**Quinton's decisions (2026-10-03, answers to Claude's questions):**
1. **S1 and S2: "Approve both."**
   - S1: Codex implements and sets up the bounded literature storage. This covers the two child
     areas plus the necessary `artifacts/literature` parent, one capability-scoped writer, and the
     proposed internal fallback `/Users/quintonevans/PROWL-Literature-Receipts/`. The writer is
     enabled only after tests pass.
   - S2: the packet is dispatched to Claude for code and invented offline tests only.
2. **Memory cap: "Watchdog is fine."**
   - The parser runs in a child process. A parent polls its resident memory about every 0.5 s and
     kills it on exceeding 4 GiB (`stopped_memory_cap`).
   - Overshoot is bounded by the growth within one poll interval and documented.
   - The signed run S copy must name this method.
3. **Cleanup: "Delete both."** Codex rechecks and deletes exactly
   `_to_delete/claude-RUNNING-LOG.md.tmp` (SHA `0c1f14cf...`) and
   `.git/index.lock.stale-claude-20260928` (0 bytes).
4. **Integration: "Accept all three"** of Codex's recommendations:
   - the 12 retrieval schemas join the shared offline contract checks;
   - the D-085 span-hit and delivered-evidence metrics are approved as additional, separately
     reported metrics, with the official metrics unchanged and their preconditions kept;
   - P4a is prepared after the imaging queue and run in an idle window.

   Each choice still needs its own scoped packet.

**Not authorized by these decisions:** signing run S, S3/S4, any download, any install,
committing or pushing, or P4/P5 execution.

**S2 dispatch:** Claude starts S2 under packet
`operations/CLAUDE-PLAN07-S2-PACKET-DRAFT-2026-10-03.md`, within its write allowlist only:
- invented fixtures;
- network denied in tests;
- no edits to the P3 producers or schemas, shared files, roots or dependencies.

The code is written and tested in Claude's cloud workspace, then copied into PROWL. Native macOS
qualification is a separate review.

**Hashes (pre-dispatch state):**
- `retrieval/CODEX-PLAN07-L1-L6-HANDBACK-2026-10-03.md`: `39c6d96df7b17954a5ee25e59583c8ef7a9c263ee56e0e1f8eae1c16cdd29c8f`
- `retrieval/CODEX-PLAN07-INTEGRATION-OPTIONS-2026-10-03.md`: `3b22ccc79e3603db49d05afd6bdd287b666b2675a225b4e19050c13795fc9eda`
- `operations/CLAUDE-PLAN07-S2-PACKET-DRAFT-2026-10-03.md`: `0ac7eb939e9cfaf17d4c0365f0e29aaa439b5aabe4d2b1c10d8a9622635b80ef`
- `operations/PLAN07-LITERATURE-S1-PROPOSAL-2026-10-03.md`: `3356a34ac3f7eee3f6a6774d4eb1958c348e69b9eacbb8307fe0b3b41a2b2695`
- `DECISIONS.md`: `98c188822ecd82f977f8e84750a812c0b4ab0aaf5e2f9d844dad02b31395d0c9`

## 2026-10-03: S2 sizing tool implemented and tested offline; handback written (Claude)

**What was done:** `sizing_v1` was implemented within the S2 packet allowlist:
- the downloader subset and the sizing-only parser mode;
- the journal and runner;
- a readiness CLI that refuses live execution.

Testing used invented fixtures only, with the network denied. Code was written and tested in
Claude's cloud workspace, then copied into PROWL. Hashes were verified identical on the device.

**Results:**
- 131 sizing tests: 130 passed, 1 skipped (a directory-permission case that skips as root).
- Full retrieval suite: 312 passed, 1 skipped. P3 unchanged: 182 passed.
- Python 3.11.15, expat 2.6.1.
- `py_compile` passes under 3.10.12 on the device.
- **A native run on Quinton's Mac is still required.**

**Tool code identity:** `814b89c5dac055b59df4c28ff14cca008d7831d63ba31b418e380831fad837aa`.

**Independent review:** a Claude subagent reviewed the work in three adversarial rounds. All
confirmed defects were fixed, including the three HIGH findings from round 1:
- unexpected exceptions skipped the final status;
- blocking reads were not bounded by the deadline;
- journal sequence breaks blocked a valid re-run.

The last three round-3 items were fixed afterwards and verified by tests.

**Decisions recorded in the handback for the signed copy:**
- the network counter is HTTP-layer, with a 1% reserve;
- the watchdog memory method;
- the zero-user-entity XML bound;
- decompressed bytes are charged to scratch;
- samples are never reused;
- partition format `prowl-parsed-partition-v0-proposed`.

**Still unmet before run S can be signed:**
- the S1 live binding (Codex);
- native qualification;
- the live listing format, which fails closed if it differs;
- no proxy support;
- S3 and S4.

**Side effect:** `py_compile` created `__pycache__/` under `src/retrieval/sizing_v1/` and
`scripts/retrieval/`. Both are gitignored.

**No exposure:** no literature was read or fetched. Nothing was downloaded, installed in the repo,
signed, committed or dispatched.

**Hashes:**
- `CLAUDE-S2-HANDBACK-2026-10-03.md`: `07040e5712adf9b364017ac17f34ab39e1d9a98d0e84dd72b5e2c552e2704ab3`
- Code and test file hashes: listed in the handback, 21 files, all verified on the device

**Addendum (same day):** Claude wrote `CLAUDE-HANDOFF-TO-CODEX-2026-10-03-R2.md` (round-2 Codex prompt: M1 decisions, M2 S1 setup and interface, M3 native S2 qualification, M4 cleanup, M5 integration scoping, M6 checkpoint scope). SHA-256 `7cb99b807633f107525d8cc698c44accdc225ce4cd743f6d95bffc0a4ff79de7`. It dispatches nothing.

## 2026-10-04: Codex M1-M6 handback reviewed; Quinton approves the S2 filesystem hook, a local commit and the shared-contract packet (Claude records)

**Claude's review of `operations/PLAN07-M1-M6-HANDBACK-2026-10-04.md` (read only):**
- S2 native qualification: 131 sizing tests passed (no skip natively) and the full retrieval suite
  passed 313 on Python 3.12.13 / expat 2.7.4. The code identity `814b89c5…` and all 21 pins match.
  The S2 files on the device are byte-identical to Claude's handback.
- S1: four areas created and 49 tests pass. The interface is
  `NativeVolume(...).observe()`, giving uuid, mount, writable, free_bytes and role. Literal paths
  are in `operations/PLAN07-S1-RESULTS-2026-10-04.md`.
- D-341 to D-345 were added. The two leftover files were deleted (D-342). This RUNNING-LOG was not
  edited by Codex: its hash was unchanged at `2643ddbf…` before this entry.
- **Open gap, correctly identified by Codex** (S1-S2-BINDING-V1, item 4): S2 opens literal paths,
  so S1's no-follow descriptor guards cannot cover S2's writes from outside. Claude wrote
  `CLAUDE-S2-IO-HOOK-PROPOSAL-2026-10-04.md`, which lists every S2 filesystem touchpoint and
  proposes an injected `SizingFs`. The parser child would receive descriptors only.

**Quinton's decisions (2026-10-04, answers to Claude's questions):**
1. **"Claude adds the hook first."**
   - Claude implements `sizing_v1.1` with `PlainFs` as the default.
   - Codex then builds S1-S2-BINDING-V1 and re-runs native qualification.
   - No download or signature.
2. **"Commit locally, no push."** Codex re-verifies the pending checkpoint list and makes a local
   commit only. Pushing remains a separate decision.
3. **"Yes, build it"** for the shared-contract packet
   (`operations/PLAN07-SHARED-CONTRACT-PACKET-2026-10-04.md`): offline tests only, with no schema
   or Claude-code change.

**Not authorized:** run S signature or execution, S3, downloads, installs, P4a, or the D-085
producer migration (which still needs its own scoped packet).

**Hashes:**
- `retrieval/CLAUDE-S2-IO-HOOK-PROPOSAL-2026-10-04.md`: `270436ae6e19fd73730bfbbd05d5c5e94725dc52aeb64d9f5b6b353deedea87b`
- `operations/PLAN07-M1-M6-HANDBACK-2026-10-04.md`: `7ec0bc7d9b5d81f476e652a3634e44b6691357a49608f7f148d741800ae7dc60`
- `operations/PLAN07-S1-S2-BINDING-FOLLOWUP-2026-10-04.md`: `a0591b74de0b2e1928e92d87b610256028de2a307d7c131d2214af0d29e66adc`
- `DECISIONS.md`: `03ce8af4e66019522078cc50ec9ffd58e290efbebb28742a744fc2a82d396cc2`

## 2026-10-04: `sizing_v1.1` filesystem hook implemented and tested offline; round-3 Codex prompt written (Claude)

**Implemented** (Quinton's "Claude adds the hook first"):
- An injected `SizingFs` (new `fsio.py`), with `PlainFs` as the default.
- All scratch, receipts and fallback I/O in `run_sizing`, `journal` and `transfer` goes through the
  hook.
- The parser child receives only descriptors. It checks that they are regular files, that the
  output is empty and that the two are distinct, and rewinds both.
- The parent writes the manifest. The partial charge comes from `fstat` on the handle.
- Any `Exception` from a journal write moves to the fallback.

No change to caps, checks, journal semantics, run S rules, `listings.py`, the CLI or the fixtures.

**Tests** (Linux, Python 3.11.15):
- 144 sizing tests: 143 passed, 1 skipped as root;
- the full retrieval suite: 325 passed, 1 skipped, in 10 of 10 runs;
- the `GuardFs` bypass detector is mutation-checked.

`py_compile` passes under Python 3.10.12 on the device. **A native re-run on the Mac is required.**

**New code identity:** `df585e2b10a69f55e24db8cc0f96822151a43d52be15ad5bb4917bd9a0a24d4e`.

**Review:** rounds 4 and 5 by the same reviewer subagent.
- Round 4: three MEDIUM findings and two LOW, all fixed.
- Round 5: confirmed the fixes and found nothing at MEDIUM or above.
- One timing-sensitive test margin was widened.

**Not done:** nothing was committed, dispatched or signed, and nothing was downloaded.

**Hashes:**
- `CLAUDE-S2-V1.1-HANDBACK-2026-10-04.md`: `3d00e92aac6f12ae4a052c70988a630522bd5af3ad210e40cc846d8a1f13b2c6`
- `CLAUDE-HANDOFF-TO-CODEX-2026-10-04-R3.md`: `726d556b09c8b6f520561549a35d202afec2961b82680f07ec544cab34ec16c4`
- Code and test pins: in the v1.1 handback (22 files, verified on the device)
