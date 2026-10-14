# Add expert PANORAMA lesions — revised admission decision

## Current authority (October 12, 2026)

Quinton explicitly approved: “just keep the 5 uncertain CT scans out. Document all of this,
and fix the old documentation that is weak and unclear. Then, let’s load all of this data
and run our next [experiment].” This is a prospective amendment before mixed training,
not a claim that additional duplicate detection was completed.

For **CAP-EXP-017 only**, this decision supersedes the exhaustive image-level admission
requirement in D-033, DUPLICATE-PROTOCOL, and the version-1 experiment draft. Use the
already reconciled publisher provenance and exclusions. Do not rediscover the 274 imports
or run a broad CT similarity scan. Stronger independent benchmark admission remains separate.

## Exclusions and unchanged protections

- Retain all 194 MSD and 80 NIH source-declared import exclusions and all technical holds.
- Exclude PanTS_00000922, PanTS_00005105, PanTS_00005370, PanTS_00007299, and
  PanTS_00007523 from this experiment's development and comparison set. Do not move them
  to training. These are provenance-uncertain cases, **not confirmed duplicates**.
- Development becomes 70 cases: 36 positive and 34 reference-empty. Preserve original
  split files and parent artifacts; create a separate experiment-specific subset.
- Original test roles remain protected and unused: no test CT, label, prediction or metric
  work is needed for this experiment. The other ambiguous original-role records do not
  become cleared test cases. The 118 ambiguous PanTS training records remain training-only;
  their possible redundancy with PANORAMA limits claims about unique added patients.
- Eligible repeated PANORAMA studies are retained, grouped by source subject, per D-030.
  The draft's one-study-per-subject rule was an unapproved deviation and is corrected.
- PANORAMA contributes expert/manual PDAC lesions only, with machine-generated pancreas
  masks explicitly used for the qualified union ROI. No automatic-lesion expansion or
  assumption that non-PDAC means lesion-negative.

## Evidence reused, not repeated

The August publisher research and exact metadata reconciliation established the declared
imports. The October 10 content/geometry audit and October 11 narrow pass established
345 technically passing expert studies / 344 source subjects, retained holds, five
physical-RAS crop reviews, and successful mixed CUDA/backup/cold-restore engineering.
The narrow provenance report identifies the five exclusions above. Its old “not admitted”
status records the policy at that time, not a requirement to repeat the completed work.

Only missing production cache construction and the production mixed-loader integration
remain new input work. Verify consumed inputs against their recorded identities, check
cache integrity and lesion preservation, and run one bounded changed-path smoke. Reuse
PanTS cache and machine qualification. Do not describe focused engineering QC as a
radiologist review of every scan.

## Fair comparison and interpretation

Recalculate parent metrics from saved case-level reports on exactly these 70 cases; do
not compare a 70-case score with the old 75-case aggregate. Recompute all 12 parent
checkpoint-selection scores from saved tensor case results on the retained 36 positives.
If the selected parent remains the retained 14k checkpoint, reuse its native predictions;
otherwise disclose unavailable checkpoints and revise the comparison before launch.
Treatment selection uses the same 70-case development set, cadence and earliest-tie rule.
Final-24k versus final-24k remains the mandatory secondary comparison.

Removing known provenance ambiguity does not prove absence of undeclared overlap.
This is exploratory, reused-development evidence, not independent/clinical validation.
SuPreM pretraining membership also remains unverified. The hypothesis and numerical
success/guardrail thresholds stay unchanged; exclusion is provenance-driven, not
performance-driven. Record amended design and cohort hashes before treatment updates.

## How to read older documentation

“Overlap passed” means **declared import exclusions reconciled**, not pixel-level clearance.
“1,964 usable / 578 PDAC” is a metadata remainder before annotation and technical holds,
not the training cohort. “345 candidates” is not evidence of completed production loading.
Historical audit artifacts remain immutable. This amendment governs this run; it does not
silently rewrite their findings or waive all future evaluation protections.
