# PROWL project inventory — 6 November 2026

> Initial audit snapshot. Read [the later clearance follow-up](09_clearance_followup.md) for newly verified publisher checksums, historical test-use evidence, sidecar plans and candidate-image findings. The initial release is preserved.

This additive audit inspects existing evidence. It does not change datasets, checkpoints, splits, training code or production behavior. Audit source files and reports remain uncommitted, as requested in the supplied outline. No STU-Net patient inference or optimizer update has been run.

## Actual cohort and source paths

- Portable cohort: `outputs/prowl/portable-cohort-20261012/cohort.json`, SHA256 `0e63126be7df03072b0064e9740c9fe6ca7efec766f2324e79a49ddde278d8e2`.
- Source CT root: `/Volumes/PROWL-Data/PROWL/sources/pants/extraction-3b1cd6110811-20260922`. Original acquisition and metadata: `/Volumes/PROWL-Data/PROWL/sources/pants/acquisition-3b1cd6110811`.
- **1,333 training cases:** 671 annotation-positive, 662 reference-empty. **75 development cases:** 38 annotation-positive, 37 reference-empty. These are retained cohort reference states, not a new label audit or verified clinical cancer status.
- KD used the identical 1,333 training members and a 70-case development subset: 36 positive / 34 reference-empty. Cases 922, 5105, 5370, 7299 and 7523 remain outside that historical subset. This audit does not readmit them for model selection.
- All 1,408 portable members use `study_as_subject_fallback` with `identity_assurance=unverified_unique`. Study pseudonyms are **not verified patient identifiers**. No patient-independent split claim is established. A cached within-development audit later found no duplicate original-file or exact orientation-normalized scaled-float32 voxel hashes among the 75 cases. The previously questioned pair 6755/2889 is not image-identical under those checks, but same-patient/repeat-acquisition status remains unresolved. This is not a training-versus-development image audit or a patient crosswalk. Its supervised cache-only run took 5.711 seconds, peaked at 207,798,272 bytes owned RSS and reaped all workers.

The local project partition draws from publisher training data; it is not the publisher's official test split. The [PanTS repository](https://github.com/MrGiovanni/PanTS#pants-dataset-paired-image-mask-report) separately lists 9,000 public training cases and a 901-case in-distribution benchmark. Local registry boundaries must remain intact. The audit did not inspect protected test images or labels. A complete historical test-use ledger is still required before describing any candidate test set as untouched.

## Existing models and metrics

The completed matched Mac KD experiment uses a three-class MONAI SegResNet, initialized from SuPreM, approximately 14.1 million parameters. It is already pretrained; it must not be described as a scratch-trained baseline. Its fixed recipe uses 144-cube inputs, seed 42, AdamW 1e-4, weight decay 1e-5, 500-step warmup / 24k cosine schedule and DiceFocal. Training mixes three focused views to one context view. Evaluation uses provided pancreas regions, not an autonomous CT-only localizer. Teacher exposure to development patients remains unresolved.

The completed KD receipt binds the **R-Super PanTS Merlin EMA teacher**, using a MedFormer implementation with 37,886,548 parameter elements and 26 sigmoid channels (pancreatic lesion at zero-based channel 19). Its converted tensor file SHA256 is `68a3b5b2dc77dbdabb4fc2b8d981c486c131be97379a681b333ae479490161f8`; original source checkpoint SHA256 is `38535f10430265e431ca3ffa7fe3ff15efed5bccb65ba909b6e3ce18af11e459`. This is distinct from an earlier MedFormer-PanTS preparation and from STU-Net. The receipt explicitly describes teacher-assisted exploratory scope with unknown teacher membership. Existing teacher/source license distinctions remain in their original records.

The completed 24k report contains twelve full 70-case native evaluations per arm. Both selected at 20k: control lesion Dice **0.383592868**, KD **0.389083939**. Terminal 24k values are 0.381964037 and 0.383438943. Selected component overlap was 39/45 versus 37/45, and reference-empty alarms were 33/34 in both arms. These are descriptive results; higher mean Dice alone does not establish practical improvement. See `docs/capstone/operations/KD-DESCRIPTIVE-ANALYSIS-20261106.md` and `MAC-KD-COMPLETION-20261105.md`.

The verified historical augmented selected native result is **0.423760756**, not a blanket 0.45 baseline. Other tensor/crop/native scores are not interchangeable. The newer Universal-Swin screen's approximately 0.710754 Dice used only four positive development cases, unchanged pretrained weights and zero training updates. It cannot be compared directly with the 70-case KD result. Its pancreas/tumor supervision and source-family overlap are documented in `UNIVERSAL-SWIN-SCIENTIFIC-USE-RESEARCH-20261106.md`.

The separate Lenovo autonomous workflow has its own completed baseline: 70 requested development cases, 63 completed predictions/scores and seven declared admission failures. Mean lesion Dice is **0.3712019132 on 32 completed positive cases**; component overlap is 35/40 and all 31 completed reference-empty cases have a lesion prediction. This is conditional on completed cases, not a 70-case mean, and cannot be compared directly with provided-region KD as a matched inference experiment. See `docs/capstone/operations/WEEK-05-AUTONOMOUS70-METADATA-REVIEW-20261104.md`. The seven failures and all existing geometry/units restrictions remain intact; this audit's appearance-only reading does not readmit them for model evaluation.

`src/inference/saved_prediction_scoring.py` evaluates native grids after checksum/shape/affine checks. Lesion Dice is undefined for empty reference masks, including empty/empty pairs; predicted volume and false-positive mL are reported separately. Classes are 0 background, 1 pancreas excluding lesion, 2 lesion. Pancreas/lesion union is a separate metric. Annotated masks can overlap before conversion; lesion takes precedence.

## Immediate methodological limits

Development scans have repeatedly informed model selection and visual review. They are development data, not an untouched final test. Unknown patient groups, pretraining membership and partial annotations limit patient-level claims. Train-only fitting, protected test boundaries, target preservation and independent checkpoint backups remain required. New STU-Net preprocessing and inference need their own qualification; the existing production gates are not inherited automatically.

## Metadata access wording

The source-workbook helper selects and retains only the 1,408 allowlisted aliases and the site/detail/nationality/year fields. Reading the XLSX container necessarily traverses XML and shared-string storage that also contains other rows and fields. The summary's `*_fields_decoded=0` counters describe **selected/extracted study fields**, not proof that protected metadata bytes were never parsed. No nonallowlisted clinical record was output, examined as evidence, or used to choose cases. No protected test CT or label was opened.
