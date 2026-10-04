# Search and selection protocol: policy v0

**Status:** policy v0, document revision 9. **Selection policy v0 APPROVED as a whole by Quinton on
2026-10-03** ("Yes, I agree on the search policy, continue with that"). Revision 9 records that
approval only; no rule text changed.
- **Amendment A1-A3 and the seven interpretations were APPROVED by Quinton on 2026-09-28**, adopting
  the Codex decision-sheet review. A1-A3 are folded into sections 2, 4, 11.3 and 12; section 13
  records them.
- **Nothing has been run.** No counts here were produced by this policy.
- **v0 is approved, but not frozen and never run.** The approved policy text is this revision. Its
  SHA-256 is recorded in `RUNNING-LOG.md` as v0's **policy-text identity**. The code hash is added
  when the P6 matching code exists, and the selection freeze is in P6.
- Revision 7 added the proposed amendment and the requested clarifications.
- The group B settings (cap, language, dates, seed-recall and precision bars, revision limits) were
  **approved as provisional** by Quinton on 2026-09-28 (SCOPE 12B).
- Revisions 5-6 add section 11, which gives every rule an exact execution definition, and section 12,
  which gives conformance examples. It changes no concept block, branch, term list, bar or
  exclusion rule.
- **Seven interpretations, APPROVED by Quinton (2026-09-28)** as Codex recommended. Each settles a
  point the earlier text left open.
  1. The upper date bound is the snapshot itself. A later issue year is kept and flagged
     (`date_after_cutoff_year`), not excluded (11.5).
  2. `OtherAbstract` and `VernacularTitle` are not matched (11.1).
  3. Only the six listed publication types exclude (11.2).
  4. Deleted PMIDs count in the reconciliation universe (5.1, 7.1).
  5. Seed recall is measured on the stage-1 candidate set (7.2).
  6. The qualifier test uses the CORE development sample, split after the fact (section 3).
  7. Stage-2 licence eligibility is fixed in run record B before stage 2 runs (section 9).
- **Quinton approved A1-A3 and the seven interpretations (2026-09-28), and v0 as a whole
  (2026-10-03).** The section 5.2 rules are therefore approved as part of v0.
- **From now on, any change to the policy text creates a new version** (v0.1 before the first run,
  under section 8), with its reason logged. v0 itself is never rewritten.
**Route:** L-03. Selection runs locally over the ordered, parsed 2026 PubMed baseline plus update
files (`ACQUISITION-PLAN.md`). It is **PROWL's own versioned selection policy**, not a PubMed web
search and not PubMed's automatic term mapping.
**Inputs:**
- approved `INFORMATION-NEEDS.md`;
- a frozen `SEED-SET.md`;
- MeSH 2026 descriptor data (for tree-number explosion);
- the final parsed state of each PMID (last event wins, deletions removed).

**Freeze:** the selected version freezes in P6, before question labelling (P7).

## 1. Record fields used

Exact XML paths are in section 11.1.

- PMID;
- `MedlineCitation/@Status` (indexing status);
- title and all abstract sections;
- MeSH headings (descriptor UI, major flag, qualifiers);
- author keywords;
- publication types;
- `Language` elements;
- date fields (section 5.3);
- article IDs (PMC, DOI);
- CommentsCorrections (retraction, erratum, expression of concern).

## 2. Concept blocks

Each block matches if **any** MeSH rule **or** text rule matches. MeSH rules use descriptor UIs
verified in MeSH 2026 and exploded through that file's tree numbers. Names below are candidates to
verify.

| Block | MeSH (exploded) | Text rules (title, abstract, keywords) |
|---|---|---|
| **P: Pancreas** | Pancreas; Pancreatic Neoplasms; Pancreatic Ducts; Pancreatic Cyst | `pancrea*` |
| **C: CT** | Tomography, X-Ray Computed | `computed tomograph*`; case-sensitive tokens `CT`, `MDCT`, `CECT` |
| **A: AI/computation** | Artificial Intelligence; Neural Networks, Computer; Image Processing, Computer-Assisted; Radiographic Image Interpretation, Computer-Assisted; Diagnosis, Computer-Assisted | `segmentation`; `deep learning`; `machine learning`; `neural network*`; `convolutional`; `U-Net`; `nnU-Net`; `artificial intelligence`; `computer-aided`; `radiomic*`; case-sensitive token `AI` (A1) |
| **M: Measurement/annotation** | Observer Variation | `interobserver`; `inter-observer`; `intraobserver`; `intra-observer` (A2); `observer variab*`; `annotat*`; `contour*`; `delineat*`; `manual segmentation`; `ground truth` |
| **W: Workflow/trust** | none (text only) | `automation bias`; `human-in-the-loop`; `reader study`; `reader studies` (A3; one concept with `reader study`); `AI-assisted`; `computer-assisted reading` |
| **IMG: Imaging context** (defined here, used by WORKFLOW) | Diagnostic Imaging (exploded) | the C block; `radiolog*`; `medical imaging`; `diagnostic imaging` |

## 3. Selection logic

```text
CORE     = P AND C
AI       = P AND A
MEASURE  = P AND M
WORKFLOW = W AND A AND IMG AND NOT (CORE OR AI OR MEASURE)   # general imaging-AI workflow
CANDIDATE = CORE OR AI OR MEASURE OR WORKFLOW_CAPPED
```

`not_candidate` means **none of CORE, AI, MEASURE or WORKFLOW before the cap**. A WORKFLOW record
removed by the cap gets `workflow_capped_out`, not `not_candidate`.

**WORKFLOW hard cap:** at most **500** records (APPROVED as provisional, SCOPE 12B).
- The cap is applied **after hard exclusions** (section 5, stage 1), so excluded records never
  consume slots.
- Deterministic order:
  1. number of distinct W-term matches, descending;
  2. derived publication year, descending, with **missing years placed after all dated records**;
  3. PMID, ascending.
- Take the first 500.
- Records that later become `metadata_only` in stage 2 do **not** trigger a refill. Their count is
  reported.
- The uncapped count is always reported.

**Diagnostic-imaging qualifier:**
- **v0 does not use it for inclusion.** Each CORE record with MeSH gets a recorded feature
  `has_dx_imaging_qualifier` (the "diagnostic imaging" qualifier on any P-block descriptor). The
  feature is recorded **only** for CORE records with MeSH.
- **Stratification:** counts are reported by the feature. The CORE development sample (50 records,
  section 7.3) is **not** split when it is drawn. Its labels are reported afterwards by subgroup:
  qualifier present, qualifier absent with MeSH, and no MeSH.
- **Pre-set v1 rule (trigger):** v1 requires the qualifier for CORE records that have MeSH if, in
  the v0 CORE development sample:
  - the qualifier-absent-with-MeSH subgroup has at least 10 records, and its point estimate is
    below either precision bar; **and**
  - the qualifier-present subgroup has at least 10 records, and its point estimate meets both
    bars.

  If CORE is a census (fewer than 100 records), the same test uses the census labels. Adopting the
  rule counts as one of the 3 policy revisions. Records without MeSH are never affected. The
  trigger result is reported whether or not it fires.
- **What the v1 rule removes:** it removes only **CORE** membership. A record that fails the
  qualifier requirement is still a candidate if AI or MEASURE admits it (and it is then stratified
  by that branch). Insufficient subgroup counts mean no trigger. The report states the uncertainty
  and makes no causal claim about the qualifier.

## 4. Text matching (deterministic)

- Normalize: Unicode NFKC; casefold, except for the case-sensitive tokens; collapse whitespace.
- Tokenize on non-alphanumeric boundaries, so a hyphen in the text is a separator. The **listed**
  hyphenated terms also match with the hyphen removed (section 11.3). Unlisted spellings are not
  added: for example, `inter observer` in the text matches the listed `inter-observer`, but an
  unlisted variant such as "interrater" matches nothing. Plural forms match only where they are
  listed (for example `reader studies`, A3).
- `*` is a single-token prefix wildcard. Quoted phrases match consecutive tokens.
- No stemming or synonyms beyond the listed terms. Any change creates a new policy version.
- The matching code and its unit tests are versioned with the policy.

## 5. Dispositions and reason codes

### 5.1 Model: two stages

Selection is **bibliographic** first. Full-text availability is resolved afterwards, so a candidate
without an abstract stays eligible for a permitted-full-text lookup.

**Stage 1: bibliographic disposition.** The **reconciliation universe** is every PMID with at least
one event in the snapshot's event log, including PMIDs whose last event is a delete. Each PMID in
it gets exactly one of:

| Precedence | Stage-1 disposition | Triggered by any reason code in |
|---|---|---|
| 1 | `deleted` | `deleted_by_update` |
| 2 | `excluded` | `not_candidate`, `pubtype_excluded`, `retracted`, `animal_only`, `language_non_english`, `year_out_of_range` |
| 3 | `excluded` | `workflow_capped_out` (applied after the rules above) |
| 4 | `candidate` | none of the above |

The frozen **bibliographic candidate set** is the stage-1 output. Precision sampling and seed recall
run on it. Deleted PMIDs belong in the accounting only. They are **never** members of the candidate
set or of the seed-recall denominator.

**Stage 2: representation and rights** (after run record B's PMC lookup for every candidate with a
PMCID):

| Final disposition | Rule |
|---|---|
| `selected` | Has abstract text and/or permitted full text |
| `metadata_only` | No abstract **and** no permitted full text after the lookup (`no_abstract_no_permitted_fulltext`) |

Every record keeps all its reason codes; the disposition comes from precedence.

Informational codes do not change the disposition:
- `language_missing`, `date_missing`, `date_after_cutoff_year`, `no_mesh`;
- `indexing_status_<value>`;
- `erratum_linked`, `concern_linked`;
- `has_dx_imaging_qualifier`;
- `fulltext_rights_unknown`;
- `has_other_abstract`, `has_vernacular_title` (presence recorded; section 11.1).

### 5.2 Rules

| Code | Rule | Status |
|---|---|---|
| `pubtype_excluded` | **Any** `PublicationType` equals one of {Comment, Editorial, News, Letter, Published Erratum, Retraction of Publication}, even alongside other types. Notices are linked as notices, not documents | APPROVED (v0, 2026-10-03) |
| `retracted` | Record carries a retraction link (RetractionIn) or publication type "Retracted Publication" | APPROVED (v0, 2026-10-03) |
| `animal_only` | MeSH includes Animals and not Humans. Records without MeSH never receive this code | APPROVED (v0, 2026-10-03) |
| `no_abstract_no_permitted_fulltext` | Stage 2 only: no abstract text and no eligible PMC object after the lookup | APPROVED (v0, 2026-10-03; from appendix A6) |

### 5.3 Language and dates

- **Language:** English if any `Language` element equals `eng`. No `Language` element gives
  `language_missing`, and the record is **included**. Otherwise `language_non_english`.
  English-only is APPROVED as provisional (SCOPE 12B).
- **Derived publication year:** the first available of:
  1. `JournalIssue/PubDate/Year`;
  2. the first 4-digit year in `PubDate/MedlineDate`;
  3. `ArticleDate/Year` (electronic);
  4. `PubmedData/History/PubMedPubDate[@PubStatus="pubmed"]/Year`.

  If none exists: `date_missing`, and the record is **included**. Competing fields are recorded, and
  the first by this order wins.
- **Range:** 2000 to cutoff, APPROVED as provisional (SCOPE 12B). A derived year before 2000
  gives `year_out_of_range`. The upper bound is the snapshot itself (section 11.5); a later year
  is kept and flagged, not excluded (interpretation 1 in the status block, approved 2026-09-28).

## 6. Treatment-focused literature

No keyword rule removes treatment literature. Its share is measured by precision sampling. Refusal
safety never depends on corpus content: the query gate and response validator enforce refusals
regardless.

## 7. Evaluation per policy version (bars set before the first run)

### 7.1 Counts

Report:
- counts per block, per branch, and overlaps;
- dispositions and reason codes, with multiple codes counted per code;
- no-MeSH inclusions by `indexing_status`;
- WORKFLOW uncapped versus capped counts.

Totals reconcile to the reconciliation universe (section 5.1): final-state records plus deleted
PMIDs, reported separately.

### 7.2 Seed recall

The share of frozen, verified seeds whose stage-1 disposition is `candidate`, with each miss
diagnosed by rule. Stage 2 does not affect seed recall. Stage-2 usable-text coverage of the seeds
(abstract and/or permitted full text) is reported separately. A `metadata_only` seed still counts as
a recall hit, but it is not delivered evidence. Bar: at least 90%,
with every miss explained (APPROVED as provisional, SCOPE 12B). Scope probes and non-PubMed
references are reported but not counted (`SEED-SET.md` rules 7 and 10).

### 7.3 Precision sampling

- **Scope:** sampling runs on the stage-1 **bibliographic candidate set**. Records without an
  abstract are labelled from the title and flagged.
- **Strata:** each candidate gets one primary stratum by precedence CORE, then AI, then MEASURE,
  then WORKFLOW. Overlaps are reported separately. Every record is inspected at most once.
- **Confirmation reserve (created before any development sampling):**
  - A PMID is reserved if `SHA-256(salt || PMID) mod 10 == 0` (about 10%), with the salt fixed and
    recorded in advance.
  - The reserve is independent of policy version.
- **Global inspected-PMID ledger (append-only):**
  - Every PMID shown to a labeller, in any policy version, stratum, round or census, is recorded
    with version, stratum, purpose and date.
  - **Seeded at creation** with the pre-run exposure list in `RUNNING-LOG.md` (entry "Codex P2 review
    received; exposure disclosures"). This includes PMID 33840636, whose NLM page showed its abstract
    and MeSH. Those PMIDs, and PMIDs later mapped from the listed PMCIDs and DOIs, are marked
    `pre_run_exposure`, and are therefore never eligible for independent confirmation.
  - **A PMID in the ledger is permanently ineligible for independent confirmation,** even if a later
    policy version moves it to a different stratum or expands its stratum.
- **Development samples:** 50 per stratum (fixed seed) from non-reserved, not-yet-inspected
  candidates. A stratum with 50 or fewer such records is labelled in full.
- **Confirmation (after the freeze):**
  - Up to 50 per stratum from **reserved PMIDs not in the ledger**.
  - It estimates precision for the **unseen remainder** of the stratum, and is reported that way.
  - **Minimum:** if fewer than 20 unseen reserved records remain in a stratum, no independent
    confirmation is claimed for it. The limitation is reported, and isolation is never relaxed to
    make up the number.
- **Small strata:** a stratum with fewer than 100 candidates at a given version is labelled as a
  **census**, which includes its reserved records. Those records enter the ledger. The stratum is
  reported as a census with **no independent confirmation claimed**, including in any later
  version.
- **Revision limits (preset):**
  - at most **3 policy revisions** during development (v0 to v3);
  - at most **2 confirmation rounds**, the second using only unseen reserved records;
  - a second failure escalates to Quinton;
  - **all attempts are reported**.
- **Rubric** (Quinton labels from title and abstract):

  | Label | Meaning |
  |---|---|
  | `relevant` | Directly addresses at least one approved need within D-074 scope, with usable text |
  | `partial` | On-topic (pancreas CT or imaging-AI workflow) but addresses no need directly, or only in passing |
  | `not_relevant` | Otherwise, including treatment-focused records with no need addressed |

- **Reporting:** `relevant` and `partial` counts reported **separately**, each with a 95% Wilson
  interval.
- **Bar (confirmation or census):** at least 60% `relevant` + `partial`, and at least 40%
  `relevant`, per stratum (APPROVED as provisional, SCOPE 12B). These are provisional selection
  controls, not evidence that the evidence assistant is accurate or useful.

### 7.4 Need coverage

For each approved need: whether any sampled candidate record was labelled `relevant` for it. Gaps are
reported.

### 7.5 Disclosure

Labelling titles and abstracts is literature inspection of this run. It happens after the needs and
seeds are frozen and is recorded in `RUNNING-LOG.md`. Prior exposure (proposal, appendix, earlier
project, planning research) is disclosed in `INFORMATION-NEEDS.md`.

## 8. Versioning

Each version records:
- policy text hash and code hash;
- MeSH version;
- input snapshot ID and cutoff;
- output PMID-list hash;
- the evaluation results above.

Versions are never overwritten. A post-freeze change creates a new corpus version under the
compatibility rules in `../QUESTION-SET-AND-EVALUATION.md` and PHASES P7.

## 9. PMC linkage (P6)

All stage-1 candidates with a PMCID are looked up, including those without an abstract.
- Eligibility comes from per-article JSON licence metadata, with OAI-PMH as corroboration.
- **The licence allowlist** (which licence values count as "permitted full text" for stage 2) is not
  part of v0. It is fixed in run record B, and approved by Quinton at B's signing, before stage 2
  runs. Until then, no record can be `selected` on the strength of full text.
- Unknown or conflicting rights mean no full text.
- Selection confers **no** display or index rights; those come only from each representation's
  rights decision.
- XML text objects only.
- Bytes are frozen at retrieval (`ACQUISITION-PLAN.md` run record B).

## 10. Historical reference (not our policy)

The v2 proposal draft recorded a live PubMed query, "Pancreatic Neoplasms[MeSH] AND Tomography,
X-Ray Computed[MeSH]":
- 8,422 records;
- 6,949 with an abstract;
- about 880 in PMC OA.

That was a different route and date. It is orientation only.

## 11. Execution definitions (revision 5)

This section makes every rule above executable without interpretation. Where it is more precise than
a section above, this section governs. The P6 selection packet implements it, and section 12 gives
its first unit-test oracles.

### 11.1 Fields (paths within each final-state `PubmedArticle`)

| Field | Path | Notes |
|---|---|---|
| PMID | `MedlineCitation/PMID` | Decimal text |
| Indexing status | `MedlineCitation/@Status` | Informational only |
| Title | `MedlineCitation/Article/ArticleTitle` | All descendant text, in document order |
| Abstract sections | `MedlineCitation/Article/Abstract/AbstractText` (each) | All descendant text. `@Label` is recorded but not matched |
| Keywords | `MedlineCitation/KeywordList/Keyword` (all lists, any owner) | |
| MeSH | `MedlineCitation/MeshHeadingList/MeshHeading/DescriptorName` `@UI`; `QualifierName` `@UI` and text | Qualifiers stay attached to their heading |
| Publication types | `MedlineCitation/Article/PublicationTypeList/PublicationType` (text and `@UI`) | |
| Language | `MedlineCitation/Article/Language` (each) | |
| Dates | `MedlineCitation/Article/Journal/JournalIssue/PubDate/Year`; `MedlineCitation/Article/Journal/JournalIssue/PubDate/MedlineDate`; `MedlineCitation/Article/ArticleDate/Year`; `PubmedData/History/PubMedPubDate[@PubStatus="pubmed"]/Year` | The section 5.3 order |
| Article IDs | `PubmedData/ArticleIdList/ArticleId[@IdType="pmc"]` or `[@IdType="doi"]`; `MedlineCitation/Article/ELocationID[@EIdType="doi"]` | DOIs compared case-insensitively |
| Notices | `MedlineCitation/CommentsCorrectionsList/CommentsCorrections/@RefType` | `RetractionIn`, `ErratumIn`, `ExpressionOfConcernIn` |

- `OtherAbstract` and `VernacularTitle` are **not matched**. They are often non-English, and
  matching them would change the language policy. Their presence is recorded (`has_other_abstract`,
  `has_vernacular_title`). This is an explicit **v0 field limitation**: it is not equivalent to
  matching every abstract, and it is not a language guarantee.
- **Has an abstract:** at least one `AbstractText` is non-empty after normalization (11.3).
- **No MeSH:** `MeshHeadingList` is absent or has no `MeshHeading`.

### 11.2 MeSH resolution and explosion

- **Resolving block descriptors.** Each descriptor named in section 2 is resolved in the MeSH 2026
  descriptor file by **exact, case-sensitive match** of `DescriptorRecord/DescriptorName/String`.
  Exactly one record must match. Zero or several matches **stop the run**; a close name is never
  substituted.
- **Before the run,** the resolved UIs and their tree numbers are written into the policy version
  record (section 8).
- **Explosion:** a descriptor D is in a block's exploded set if any of D's tree numbers equals, or
  starts with (followed by "."), any tree number of a resolved block descriptor.
- **Block match:** a record matches a block's MeSH rule if any of its `DescriptorName/@UI` values
  is in that block's exploded set.
- **Check tags are not exploded.** `animal_only` uses the exact descriptors named `Animals` and
  `Humans`, resolved the same way.
- **Diagnostic-imaging qualifier:** a heading whose descriptor is in the exploded P set carries a
  `QualifierName` whose text is exactly `diagnostic imaging`.
- **Publication types** are compared by exact `PublicationType` text against the names in
  section 5.2. Every publication-type name is counted in the report. Only the six listed names
  exclude; no other name has any effect.

### 11.3 Text normalization, tokens and terms

- **Matched units:** the title, each abstract section and each keyword separately. A phrase never
  spans two units.
- **Normalization of each unit:**
  1. Unicode NFKC.
  2. Every maximal run of whitespace becomes one space.
  3. Two views are kept: a **casefolded** view (`str.casefold`) for ordinary terms, and the
     **original-case** view for the case-sensitive tokens.
- **Tokens:** maximal runs of characters for which `str.isalnum()` is true. Every other character,
  including a hyphen, slash, apostrophe or period, is a separator. For example, `PET/CT` gives the
  tokens `PET` and `CT`, and `CT-based` gives `CT` and `based`.
- **Terms:**
  - A term is its words, each tokenized the same way.
  - Every multi-word term is a **phrase**: its tokens must appear consecutively in one unit.
  - A `*` on the last word matches any token that starts with that word's prefix. For example,
    `pancrea*` matches `pancreas` and `pancreatic`; `neural network*` needs the token `neural`
    immediately followed by a token starting with `network`.
  - **Hyphenated terms** (`inter-observer`, `intra-observer`, `U-Net`, `nnU-Net`, `computer-aided`,
    `human-in-the-loop`, `AI-assisted`, `computer-assisted reading`):
    - each hyphenated **word** matches either its hyphen-split tokens consecutively, or one token
      equal to the word with its hyphens removed;
    - the term's other words match as usual, and the whole term is still one phrase.

    For example, `U-Net` matches `U Net`, `U-Net` and `UNet`, all compared casefolded.
    `computer-assisted reading` matches `computer assisted reading` and `computerassisted reading`.
- **Case-sensitive tokens** `CT`, `MDCT`, `CECT` and `AI` match only a token exactly equal to them in
  the original-case view. `AI` has no lowercase alias and no substring match, so `AIDS`, `XAI` and
  `AIP` do not match it, while `AI-based` gives the token `AI`. For example, `CTs`, `ct` and `Ct` do not match.
- **W-concept count** (for the cap order): the number of distinct section 2 W **concepts** that
  match in any unit of the record, from 0 to 5. `reader study` and `reader studies` are one concept;
  every other W term is its own concept. Section 3's "distinct W-term matches" means this count.
- There is no stemming, synonym list or spelling correction. After the first run, any change to a
  term or to this section creates a new policy version. Before the first run, changes go through
  section 13.
- **Pinned runtime:** `str.isalnum`, `str.casefold` and NFKC depend on the Unicode version. The
  version record (section 8) stores the Python version and `unicodedata.unidata_version` used. A
  rerun on a different Unicode version is a new run, and its output hash is compared, not
  assumed.

### 11.4 Order of evaluation

1. Build the final state from the ordered event log. Deleted PMIDs get `deleted_by_update`.
2. Compute the blocks, then the branches (section 3), without the cap.
3. Apply the stage-1 hard-exclusion rules (section 5.1, precedence 2) to every record.
4. Among the remaining WORKFLOW-only records, apply the cap in the section 3 order. The rest get
   `workflow_capped_out`.
5. Assign each stage-1 disposition by precedence, keeping every reason code.
6. Stage 2 runs after run record B only.

### 11.5 Dates and cutoff

- **Year fields:** a year is valid only if it is 4 ASCII digits.
- **`MedlineDate`:** the first match of the regular expression `(?<![0-9])[0-9]{4}(?![0-9])` gives
  the year.
- **Cutoff:** the snapshot boundary named in run record A (the last update file applied). Every
  record in the snapshot is inside the cutoff by construction.
- **Later years:** a derived year later than the calendar year of the cutoff file's listing date is
  kept and flagged `date_after_cutoff_year` (informational). Issue dates in the following year are
  common and are not excluded.
- **`year_out_of_range`** means only a derived year before 2000.

### 11.6 Deterministic sampling and the confirmation reserve

- **Keys:** at the start of P6, before any sampling, three independent 32-byte values are drawn
  from the operating system's cryptographic random source. They are recorded in hex in
  `RUNNING-LOG.md` with the date:
  - the reserve salt;
  - the development key;
  - the confirmation key.

  They are never changed. A lost key stops sampling rather than being regenerated.
- **Reserve:** a PMID is reserved if
  `int(SHA-256(salt_bytes || ascii(PMID)), 16) mod 10 == 0`, where `ascii(PMID)` is the decimal
  PMID without leading zeros.
- **Sample order:** within a stratum, eligible PMIDs are sorted ascending by
  `SHA-256(key_bytes || ascii(policy_version) || 0x00 || ascii(stratum) || 0x00 || ascii(PMID))`.
  Here `policy_version` is the exact string `v0`, `v1`, and so on, and `stratum` is the exact
  string `CORE`, `AI`, `MEASURE` or `WORKFLOW`. Ties are broken by PMID. The first N are taken:
  - development samples use the development key;
  - confirmation samples use the confirmation key.
- **Eligible for development:** in the stratum, not reserved, and not in the ledger.
- **Eligible for confirmation:** in the stratum, reserved, and not in the ledger.
- **Census:** a stratum with fewer than 100 candidates at that version (section 7.3).
- **Wilson interval** at 95%: z = 1.959964; reported as the lower and upper bounds, rounded to 3
  decimals.

### 11.7 Outputs of each policy version

- The candidate PMID list, sorted ascending, as one PMID per line followed by a newline. Its
  SHA-256 is the "output PMID-list hash" of section 8.
- A per-record reason-code table.
- The count report of section 7.1, reconciling to the reconciliation universe (section 5.1).

## 12. Conformance examples (invented records; oracles for the P6 matching tests)

These are synthetic records for the future matching code's unit tests, not literature.
- Only the fields that matter are shown; everything else is empty. "Title" means the only matched
  unit, unless stated.
- Each oracle asserts the **branch set, the stage-1 disposition and the codes named**. Other
  informational codes that follow from empty fields (`no_mesh`, `language_missing`,
  `date_missing`) are not asserted, unless named.

| # | Record (synthetic) | Expected |
|---|---|---|
| E1 | Title "Pancreatic lesion conspicuity on CT"; `eng`; 2021 | CORE, `candidate` |
| E2 | Title "Pancreatic lesion conspicuity on MRI"; no MeSH | No block C, A or M, so `not_candidate`, `excluded` |
| E3 | Title "Deep learning for pancreas segmentation" | AI (P and A, via `pancrea*`, `deep learning` and `segmentation`), `candidate` |
| E4 | Title "Interobserver variability of pancreas contours" | MEASURE (P and M), `candidate` |
| E5 | Title "Automation bias when radiologists review deep learning output"; no P | WORKFLOW (W via `automation bias`, A via `deep learning`, IMG via `radiolog*`); `candidate` if within the cap |
| E5b | **Historical only: the pre-amendment draft; not a P6 test.** Title "Automation bias in AI-assisted CT reading"; no P | Under the draft without A1: A fails, so `not_candidate`. **Superseded by E5c** |
| E6 | E1 plus publication type `Editorial` | `excluded` (`pubtype_excluded`); still CORE for counts |
| E7 | E1 plus `CommentsCorrections/@RefType="RetractionIn"` | `excluded` (`retracted`) |
| E8 | E1 plus MeSH `Animals`, without `Humans` | `excluded` (`animal_only`) |
| E9 | E1 with no `MeshHeadingList` | `candidate`, with `no_mesh`. `animal_only` can never apply |
| E10 | E1 with `Language` `ger` only / with no `Language` | `language_non_english` (`excluded`) / `candidate` with `language_missing` |
| E11 | E1 with year 1998 / with no date fields | `year_out_of_range` (`excluded`) / `candidate` with `date_missing` |
| E12 | Title "PET/CT of pancreatic cancer" | Token `CT` matches, so CORE |
| E13 | Title "A UNet for pancreas delineation" | `U-Net` matches `UNet`; M matches via `delineat*`; AI and MEASURE |
| E14 | Title "pancreatic ct findings" (lowercase `ct`) | `CT` does not match; no C, A or M: `not_candidate`, `excluded` |
| E15 | E1 whose last event is a delete | `deleted` (`deleted_by_update`) |
| E16 | Title "Tumour imaging"; `OtherAbstract` contains "pancreatic CT" | `OtherAbstract` is not matched, so `not_candidate` |
| E17 | Title "pancreatic neural networks on CT" | `neural network*` matches `neural networks`; CORE and AI |
| E18 | Title "Organ phantom"; MeSH `Pancreas` with the qualifier `diagnostic imaging`; no CT anywhere | P matches through MeSH only; C does not; no branch: `not_candidate`, `excluded`. `has_dx_imaging_qualifier` is **not** recorded (CORE only) |
| E19 | Title "Imaging study on CT"; MeSH: a descriptor whose tree number is a child (`<P tree>.xxx`) of the resolved `Pancreatic Neoplasms` | P matches by explosion; CORE, `candidate` |
| E20 | E1 plus MeSH `Animals` **and** `Humans` | `animal_only` does not apply: `candidate` |
| E21 | E1 with publication types `Journal Article` and `Comment` | `pubtype_excluded` (any listed type excludes): `excluded` |
| E22 | Title "Computer assisted reading of deep learning output in radiology" | W via `computer-assisted reading` (hyphen-split form); A via `deep learning`; IMG via `radiolog*`; no P: WORKFLOW, `candidate` if within the cap |
| E23 | E1 with only `MedlineDate` "2019 Nov-Dec" / only `MedlineDate` "Winter 1998-1999" | Derived year 2019, `candidate` / derived year 1998 (the first match), `year_out_of_range`, `excluded` |
| E24 | E1 with `PubDate/Year` one year after the cutoff file's listing year | `candidate`, with `date_after_cutoff_year` |
| E25 | 501 WORKFLOW-only records that pass the hard exclusions: 500 with 2 W terms, and one with 1 W term, year 2025 | The 1-term record is last in cap order: `workflow_capped_out`, `excluded`, **not** `not_candidate` |
| E26 | Two WORKFLOW-only records tied on W-term count, one dated 2020 and one with no year | The dated record orders first; the undated one orders after every dated record |
| E27 | Stage 2: a stage-1 candidate with no abstract, and a PMCID whose licence is not on run record B's allowlist | `metadata_only` (`no_abstract_no_permitted_fulltext`). It still counts as a stage-1 candidate for seed recall |
| E5c | E5b's record: title "Automation bias in AI-assisted CT reading"; no P | W (`automation bias`, `AI-assisted`), A via `AI`, IMG via `CT`: WORKFLOW, `candidate` if within the cap |
| E28 | Title "ai-assisted ct reading with automation bias"; no P | W matches (ordinary terms are casefolded), but lowercase `ai` is **not** `AI` and `ct` is not `CT`. A and IMG fail: `not_candidate`, `excluded` |
| E29 | Title "AIDS and XAI in pancreatic CT" | `AIDS` and `XAI` are not the token `AI`. P and C match, so CORE only (no AI branch), `candidate` |
| E30 | Title "AI for pancreatic CT" | P, C and A (`AI`): CORE and AI, `candidate` |
| E31 | Titles "Intra-observer agreement of pancreas volume" / "intra observer agreement of pancreas volume" (no other M term) | M via `intra-observer` (both spellings), MEASURE, `candidate`. |
| E32 | Title "Reader studies of deep learning in radiology"; no P | W via `reader studies`, A via `deep learning`, IMG via `radiolog*`: WORKFLOW, `candidate` if within the cap |
| E33 | A WORKFLOW-only record whose units contain both "reader study" and "reader studies", plus `automation bias` | W concept count = 2 (the reader-study concept counts once), not 3 |
| E34 | 501 WORKFLOW-only records passing the hard exclusions: 500 with 2 W concepts dated 2020, and one dated 2026 with only `reader study` and `reader studies` | It has 1 concept, so it is last in cap order: `workflow_capped_out`. A miscount of 2 would tie it on count and put it first by year, inside the cap. So this example detects that bug |

*Historical note, not a P6 test:* under the pre-amendment draft, E31's titles had no M, C or A
term, so they were `not_candidate`.

## 13. Amendment A1-A3 (APPROVED by Quinton, 2026-09-28; folded in before the first run)

**Status: APPROVED and applied.** Quinton approved A1-A3 on 2026-09-28, adopting the Codex
decision-sheet review (`RUNNING-LOG.md`). They are folded into sections 2, 4, 11.3 and 12 before
v0's identity is recorded. v0 has never been run.
- **Reason:** obvious language variants found while writing the execution rules, before any run.
- **Not seed-driven** (`SEED-SET.md` rule 11). The one candidate whose diagnostic column changes is
  the corrected S-01 ("AI applications").
- **Side effect disclosed:** the single W term `AI-assisted` now also satisfies block A through its
  token `AI`, so WORKFLOW needs only an IMG match for such a record (E5c). Precision sampling
  measures the effect.

| ID | Block | Change | Exact rule |
|---|---|---|---|
| A1 | A | Case-sensitive token `AI` | Whole token, original-case view, as for `CT`. No lowercase alias; no substring match |
| A2 | M | `intra-observer` | A listed hyphenated term (11.3). `intraobserver` stays |
| A3 | W | `reader studies` | A phrase with no general stemming. One W concept together with `reader study` |

Examples E5c and E28-E34 are now in section 12. E5b and the pre-amendment counter-oracle in E31 are
historical and are not P6 tests.
