# CT diameter versus volume — bounded development improvement

User-approved next step after parking the invented labeling rehearsal: improve a missing formal
question family using existing papers, compare a fixed before/after set, and promote only after
source/answer/UI checks. AI-04 remains in progress; this is not independent evaluation or scan
measurement qualification.

## Question and source boundary

Selected exposed development case dev2-08: why pancreatic tumor diameter and volume differ,
with a CT study example. The frozen 14-question matrix is
`configs/evidence/evaluation/measurement-method-development-v1.json`: three supported wordings,
nine boundaries, two existing volume/disease controls. Frozen before baseline queries or candidate
changes. All questions and tests are exposed development material; exclude them and semantic
near-duplicates from protected authoring. Existing accepted v6 labels/approvals are unchanged.

Actual canonical paper: Choi et al.2020, PMID33027288 / PMC7540900,
“Benefits of the multiplanar and volumetric analyses of pancreatic cancer using computed tomography.”
Read the retained methods/discussion/limitations independently of the evaluation labels. No new
paper, ingestion or model training. The source catalog binds full canonical passage hashes and
within-passage spans; fact and wording review hashes bind the curated interpretation.

Manually reviewed source mapping:

| Fact | Canonical ordinal | Review |
| --- | --- | --- |
| Diameter as length versus segmented three-dimensional volume |17,38| Supported paraphrase of unidimensional analysis and reconstructed volume; no conversion formula |
| Semi-automated segmentation, radiologist trims each slice, three planes, reconstructed volume |16,17| CT methods preserved; no claim of autonomous model measurement |
| Volume may represent irregular lesion extent |38| “May”/potential advantage retained; no universal superiority or prognosis claim |
| Retrospective, one institution, Korean patients, upfront surgery |46| Population and preoperative-treatment application limit retained |

Independent semantic review remains pending. Paragraph one cites the three methods/rationale
passages; paragraph two cites the study limitation. The separate application limit is explicitly
system scope, not a new claim from the paper. Both reviewed wording variants were inspected;
the actual model selected the same valid variant combination on all three questions.

## Implementation

New `measurement_interpretation.py` adds a narrow CT tumor-method intent, reviewed qualitative
fact catalog and complete-source selection. It precedes the existing whole-pancreas volume route
only for admitted method comparisons. Numeric, current-case, prognosis, conversion, unrepresented
modality/organ/population and negative/instruction requests cannot select this record. Unmatched
requests retain existing routing/fallback. This grammar is not general semantic understanding.

The shared Qwen3:8b composer selects reviewed sentence variants. Code validates every mandatory
unit and attaches canonical citations. It does not generate unconstrained medical prose. Missing
model units produce an explicitly labeled reviewed fallback; changed evidence fails before a model
call. A new response policy/schema and UI validator verify exact wording and citation membership.
Source text stays behind the existing Sources/Read passages controls. New public Vite contract
allowlist entries are exact files, not a wider repository allowance.

Activation flag: `--measurement-answers` includes existing volume/disease answers. Rollback:
restart the literature API with `--volume-answers`; existing policies and catalogs are preserved.

## Results before activation

- Live baseline:0/3 supported wordings matched a reviewed record; all returned unassessed dense
  passages with no composed answer. This is a selection/coverage gap, not a failed model attempt.
- Candidate:3/3 completed local-model composition, no fallback; HTTP times6.279,4.078,4.062seconds.
  Exactly3 chat calls, no retries/sweep. Nine boundaries avoided the new record; all11 non-target
  selection objects exactly match the baseline, including both existing controls. These are
  routing controls, not a fresh full old-policy answer-quality evaluation.
- Factual support: methods and rationale match the paper. Completeness: all four units present.
  Readability: two paragraphs with length-versus-3D explanation first and study limits separate;
  anatomical plane terms are retained for the intended radiologist audience. Citations: manually
  inspected4 unique passages/12 paragraph-citation instances across3 answers; exact canonical
  content and full required closure verified mechanically. No inference of patient size or outcome.
-162Python checks pass across measurement and existing volume/disease selection/composition.
-76UI checks pass, including all14 actual HTTP response replays, rendered answer/fallback/source
  navigation and corrupt prose/qualifier/citation/policy rejection. Production build passes with
  the existing large-chunk advisory. No real-browser visual walkthrough claimed.

Local evidence: `outputs/prowl/measurement-interpretation-20261021/`: frozen plan, baseline,
original request-error record, candidate actual responses/model plans/producer pins and review packet.
The tracked check script requires a fresh output directory and enforces3 chat calls. Retained corpus
passages/model-call payloads stay local; Git carries code, reviewed derived facts and test matrix.

## Infrastructure and retained failures

Initial baseline request failed400 because the harness omitted the request schema/UUID; corrected
without a product change. Next request failed503: existing API process was listening but PostgreSQL
was stopped. Correct drive UUID/path/storage floors passed. A checked start failed with Docker's
known stale bind-mount “not a directory” error. Restarted Docker under prior user authorization,
restored previously running XML-Adventure and started the existing literature DB. No deletion,
reinitialization, download, ingestion or training. Subsequent actual searches passed inventory checks.
An initial build invocation used unsupported `--root`; corrected to Vite's positional root.

## Tracking and next step

Trello AI-04 read timed out; no card mutation attempted without its returned ARI. Pending comment:
“CT tumor diameter-versus-volume coverage added from existing PMC7540900. Fixed development check:
0/3 reviewed baseline matches →3/3 complete local-model answers in4.1–6.3s;9boundaries and2existing
routes unchanged;162Python/76UI checks and build pass. Source qualifications/citations reviewed.
Independent evaluation and reliable scan measurements remain open. Report:
MEASUREMENT-INTERPRETATION-2026-10-21.md.” Sync this once the connector recovers.

Next bounded family: contour/reader variability, if actual canonical evidence supports it. Keep
protected labeling parked until its isolation/admission work is selected; do not call this narrow
coverage improvement completion of the expert system or measurement-aware extension.

## Local activation

After passing the fixed candidate and source review, implementation commit `0d89eb6` was activated
on8016 with `--measurement-answers` (owned session22902). API and Vite5180 proxy both report
`source-literature-answer-v3` / `source-linked-literature-search-v3`. A real query through the UI
proxy selected the four canonical passages; all four newly imported public contracts returned200.
No additional generation call was made beyond the three-call experiment. Database is healthy;
XML-Adventure is restored. The old5182 invented labeling app remains separate.

After adding the suggested question,59 affected UI checks were repeated and passed; this does not
increase the76distinct UI count above. Activation receipt is retained locally as `activation.json`.
Try: “How does measuring pancreatic tumor diameter differ from measuring its volume on CT?”
Trello remains pending because the read connector timed out; no successful sync is claimed.
