# Autonomous native-resolution baseline: completed evaluation

The fixed 70-case exposed-development evaluation completed at 2026-11-04 03:36:37 UTC with 63 saved native predictions and scores, plus seven declared admission failures. Five predictions were reused and 58 were newly produced. No patients were excluded, and failed cases have no imputed Dice.

## Descriptive results

| Measure | Result | Denominator |
| --- | --- | --- |
| Successful execution | 63/70 (90%) | All requested cases |
| Mean positive lesion Dice | 0.3712019132 | 32 positive-reference completed cases |
| Positive cases with any lesion overlap | 30/32 | Positive-reference completed cases |
| Reference-empty cases with a lesion prediction | 31/31 | Reference-empty completed cases |
| Reference lesion components with any overlap | 35/40 | Components across completed cases |
| False-positive predicted components | 394 | All 63 completed cases |
| Full expanded-region pancreas coverage | 63/63 | Completed cases |
| Full expanded-region lesion coverage | 32/32 | Positive-reference completed cases |

Any-voxel overlap is descriptive, not clinical detection. The full annotated fields fit within the expanded regions for completed cases; this does not establish preservation of all detail through resampling or good boundary quality. False-positive behavior remains poor. Empty-reference Dice and recall remain undefined/null, and an empty annotation does not establish verified health.

The six unresolved CT spatial-unit failures are PanTS_00006011, PanTS_00005780, PanTS_00001823, PanTS_00002935, PanTS_00006901 and PanTS_00006115. PanTS_00005592 retained its preflight capacity failure. These seven remain in the ordered denominator, with zero forwards/optimizer updates for their failed disposition. No header was inferred, cap raised or case silently dropped.

## Scope and interpretation

This is inference/scoring, not scientific training. No training hours or MLflow training run were added. The cohort is exposed development; the original probability-equivalence failure remains UNQUALIFIED under the specifically approved numerical exception. H0 is NOT TESTED, model-quality acceptance is false, and this is not an independent-generalization result or a directly matched comparison with a different historical cohort. The report makes no threshold recommendation.

## Saved-record handoff

The adjacent JSON exports only metadata derived from saved records, with the ordered 70-case dispositions, native metrics, localization coverage, component/contour measurements and exact source-report SHA256s. No image arrays, masks, probabilities, checkpoints, credentials or machine source paths are exported. Original producer outputs remain unchanged. Failed and excluded are distinct; nulls are preserved.

The completion records 8323.297 seconds for its internal evaluation interval; evaluation supervision records 8965.312 seconds including its broader process lifecycle. The complete handoff took 9304.906 seconds (2.585 hours), including admission and final verification. These are different nested accounting scopes, not extra training time.

## Closeout verification

All 710 output files (18,537,483,881 bytes) matched their independent C-drive backups by size and SHA256, and relative file sets matched. All 294 repository pins matched. All 121 worker resource records (58 inference and 63 scoring) report success, exit0 and reaped workers. Evaluation supervision also reports success/exit0/reaped, peak owned RSS 4,309,360,640 bytes. A fresh process/GPU check found no remaining evaluation workers or GPU owners.

Preparation backup comparisons also passed; exact count and receipt identities are in the JSON. Source CT/mask pins rely on the completed source-admission evidence, not a repeated data audit. Stored result and scoring prediction hashes agree; the completed producer's original artifact checks remain the authority for expected artifact hashes. No reference inputs were loaded in inference according to its saved audit records (a Python tripwire, not an OS security boundary).

The first report-only exporter completed all output-backup and repository-pin checks, then failed on the older matched-case1070 access schema. A second metadata attempt identified that its artifact hashes also use a structured SHA256/bytes form. Both failures and scripts are preserved. Version3 explicitly handles those case-bound legacy formats; no producer or saved score was altered, and no inference/scoring was repeated. Attempt receipts remain at E:/PROWL/readiness/week05-autonomous70-closeout-20261104-a01. Independent arithmetic checks reproduced all63 saved lesion Dice values and confirmed null Dice/recall for empty references.

JSON SHA256 (UTF-8/LF): `3944ea76135d9f756a22abea7931af43423a7050a928d79db79a8b10fbe78cc6`.
