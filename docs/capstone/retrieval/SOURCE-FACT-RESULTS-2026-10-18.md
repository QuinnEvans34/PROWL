# Source-linked facts preserve the tested volume qualifications

The bounded prototype passes for two reviewed group results from the existing MRI volume paper.
Both assembled answers retain the qualifications missing from the previous generated answers.
This is a deterministic fact-assembly result, **not improved LLM reasoning or full AI-expert acceptance**.
No replacement was promoted; baseline dense/v6.1 remains selected.

Implementation/plan checkpoint `f2ec3f2` preceded the actual-corpus canary. Thirty-three focused
mutation and selection tests pass. One fresh source-only search and zero model-generation calls
completed in5.415s (search5.312s). Both source records were selected through their retrieved result
passage, then expanded with three additional context passages not in top5. All seven mismatched
structured intents selected no record: lesion, head, diameter, broader healthy population, CT, SD
and patient normality. These checks concern explicit metadata requests, not natural-language routing.

## What the prototype establishes

| Required element | Earlier checked-evidence volume draft | Fact-record assembly |
|---|---|---|
| Mean, units, specific study population | Numbers present; citation binding varied | Present with exact group/result binding |
| Sample count | Omitted |14comparison subjects /41diabetes subjects |
| Measurement method | Omitted | MRI explicitly stated |
| Meaning of uncertainty | ±values without explanation | SEM named and explained; no SD or individual-range substitution |
| Matching | Omitted | Age, weight and sex retained |
| Applicability limits | Omitted | Selected study group; not universal average, CT reference or individual-normality decision |

Each record has twelve source fields, mandatory interpretation limits, exact canonical offsets/hashes
and a separate reviewed-record digest. Whole-organ extent is bound to the explicit total-volume
method passage (ordinal18), not inferred from a head/lesion measurement. Result order is checked
against ordinal29; population/count/MRI against ordinal2, statistical convention against ordinal27.
Use analyzed41, not recruited44 from a different paragraph. The two records retain distinct groups
and values; no question strings or expected answers are stored in the catalog or assembler.

The first construction check found an overly strict literal matcher rejecting the sentence-ending
word `sex.` as though its period were a decimal continuation. This was fixed before the canary;
dedicated punctuation and partial-number checks pass. The failed construction made no HTTP/model
calls and is retained in the canary's preparation history. No actual-data run was silently retried.

## Source review and limitations

One engineering agent manually inspected all eight rendered statements and their source bindings.
Both numeric examples are supported within their stated groups. SEM explanation is a labeled,
controlled statistical glossary; the applicability cautions are labeled interpretation policy,
not purported quotations or findings from the authors. The NGT example covers the unchanged
quality-03 requirements, including small selected comparison-group context, MRI, SEM and matching.
Read the actual outputs and originals in local `readable-review.md` under
`outputs/prowl/source-facts-volume-v1-20261018/`.

This review is not independent/human acceptance. Hashes preserve a reviewed extraction; they do not
establish semantic truth. Limited literal checks reject some inconsistent values or locations, but
correct interpretation of result-to-group relationships remains a source-curation responsibility.
Future automated record extraction would need its own review/admission process. A changed trusted
review inventory is a new curation decision, not something the hash guard can authenticate by itself.

Selection and rendering were measured separately. The harness supplies a declared structured intent;
it does not infer one from the question. A matching result passage is required before expansion;
an incidental same-paper methods hit is insufficient. Unsupported requests cannot silently fall
back to another object, population, method or statistic. A complete rendered answer is checked by
exact regeneration, rejecting later omissions, qualifier changes or citation substitution.

The current prototype contains four typed statements and four distinct original passages; its first
statement cites all four. The existing generation service allows three claims/three citations per
claim. A separately qualified adapter or sentence/provenance organization is needed before UI use;
this experiment does not relax that contract. Free-text routing, qualitative disease records,
independent source review, broader retrieval coverage and formal evaluation remain open.

## Evidence and next step

Tracked metadata: `source-facts-volume-v1.json`, its separate review inventory, and
`source-facts-volume-v1-results.json` under `configs/evidence/`. Code: `src/retrieval/fact_records.py`;
canary: `scripts/retrieval/check_source_facts.py`. Full local canonical evidence, exact rendered
answers, request/response, timings and producing snapshots are in the canary directory. Original
labels, incomplete generated answers and all previous failures remain unchanged. All1,179canonical
passage offsets/hashes and actual retrieved records were validated before assembly.

Next, extend this contract to a small qualitative disease record that must preserve focal-mass
context, overlapping appearances and the single-feature limitation. Then qualify free-text selection
and the output adapter before considering a UI switch. Do not scale corpus ingestion or replace the
live model on the strength of two assembled examples. AI-04 remains In Progress; the measurement-aware
extension remains required after core acceptance. No training/full selector, protected content,
model download, source ingestion, patient measurements or human-hours credit occurred.
