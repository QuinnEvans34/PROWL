# Pancreas-assisted lesion outlining with complete coverage and interleaved views

## Authorization and scope

October19: user explicitly authorizes provided pancreas masks to define regions,
verification of complete pancreas/lesion coverage and sampling, then one fresh
scientific run with MLflow and the phone dashboard. Qualification must pass first.
No automatic retry, restart, resume, PANORAMA, EMA or teacher-distillation run.

The JSON experiment specification is authoritative for numerical recipe and
statistical endpoints. This is a provided-pancreas-assisted experiment, not
autonomous whole-CT detection or an external benchmark comparison.

## Region and input

The provided pancreas mask alone selects the region. Start with its original
10mm margin and expand by additional source-index-plane distances81/43/71mm.
These are training-only maxima from the existing671-positive mask coverage audit,
rounded upward plus1mm safety; development lesion labels do not choose, enlarge,
repair or tune regions. Development labels are only used to audit containment and
evaluate predictions. Any coverage failure blocks launch; no case is dropped.

The region is losslessly reoriented, then the existing physical voxel-cell
subdivision preserves acquired fine spacing and brings coarse axes to<=1.00001mm.
There is no whole-region squeezing/downsampling.144-cube windows/72-stride native
reconstruction retain the prior physical numerical implementation. Predictions
outside the region are background and scoring remains on the complete native CT.
No mask becomes an input channel.

The complete annotation field is exposed across a coverage bank, not necessarily
within each144-cube input. Focused banks cover the UNION of pancreas and lesion;
this is not the previous lesion-only focused bank. Every fourth global update is
a random contextual region window; the other three advance that patient's
independent focused counter. These counters are saved/restored with the model,
optimizer, RNG and exposure state. Full24k case-order simulation must prove every
patient reaches every required focused window, with a3:1 mix in every four steps.

## Verification and launch sequence

1. New region-specific label-only verification of1333train/70development; reuse
   completed source identity/CT-content audits. No duplicate-provenance audit or
   protected-test data access.
2. Twelve original difficult training cases rendered through the real loader.
   Compare region and actual windows; keep unusual annotations. Source-index
   display aspect must not be mistaken for physical reformats.
3. Synthetic geometry, role, boundary/padding, reconstruction, sampling, executor
   and tracking tests, plus full24k schedule accounting.
4. Four nonpromotable CUDA updates including the context transition, independent
   checkpoint backup, two native development qualification examples, then a cold
   restore repeating the fourth update with exact inputs/counters and numerically
   close weights. No qualification Dice is a scientific result.
5. Freeze evidence/code/configuration/environment hashes. Only then dispatch the
   fresh24k scientific job. Verify real advancing updates, backup and MLflow loss
   points before claiming training is live. Register a separate dashboard card.

## Hypothesis and interpretation

H0: selected native positive-case macro Dice improvement over the augmented
PanTS control is<=0. Practical acceptance requires>=.02 improvement, paired95%
interval lower bound>0, and the predefined detection/false-alarm/pancreas/empty
voxel-burden guards. Report terminal24k comparison separately. Bootstrap10,000
paired positive cases with seed20261019. Development is reused, so this remains
exploratory. Old control selection used tensor validation, whereas this run uses
native selection; acknowledge that difference. The stopped full-CT run is only
a diagnostic comparator, not the primary scientific control.

## Costs and preservation

Source CTs still load on demand; this change does not promise to remove the
previous per-update IO/preprocessing cost. Region inference should require fewer
tiles, but its ETA must be measured. Keep96h hard wall ceiling including validation,
12GiB owned-worker RSS,100GiB C/E free-space floors, existing32GiB cache and backup
caps, AC requirement and supervised process cleanup. No new dense cache.

Original producing sources, receipts, runs and checkpoints remain unchanged.

## October19 qualification results

The complete region audit passed all1,403 cases:1,333 training (671positive) and
70development (36positive). All7,145,665 annotated lesion voxels and all provided
pancreas voxels were retained. Every audited coverage-bank window passed exact
native-label round-trip checks. No cases were excluded; no protected-test data or
CT-content audit was reread. The separate12-case real-CT pilot was reviewed.

The final continuation reused431 completed checks and verified972 remaining;
all workers exited. Total charged audit time was5,173.937seconds, including the
preserved earlier serial work and reporting-failure attempt. The final continuation
peaked at2,537,549,824bytes combined owned RSS. Its append-only progress reporting
replaced a Windows file-sharing failure; numerical audit code was unchanged.

Median region volume is43.57% of the source CT. The70development cases require
2,600 inference windows, versus7,698 for the previous full-CT representation.
These are window counts, not measured runtime speedups.

Full24k schedule simulation passed:18,000 focused and6,000 contextual updates,
exactly one contextual view in each four global updates,5–18 focused visits per
patient, and enough visits for every patient's complete coverage bank.

The actual executor completed4CUDAupdates and2native development cases in
195.297seconds. Producer/cold workers exited cleanly (peak ownedRSS2,689,945,600/
1,677,889,536bytes). Cold restoration and next input matched exactly; maximum
next-state numerical difference1.7462298274040222e-8 passed tolerance. These are
nonpromotable qualification updates, excluded from scientific hours.

Scientific training launched October19 about15:31MDT. Receipt SHA256:
`53b264490b2eb6e50b3e7b9c38e17ccf9e8b244b692b8edbf12fa3434edc1ffe`.
All503 frozen pins verified after dispatch; initial E:/C: checkpoint copies match.
MLflow run `1edf56ad4b7b48a5a5baa0e729e46a5c` is RUNNING with stored train/loss.
Actual updates and the sixth dashboard card were verified;21monitor tests pass.
The primary scientific hypothesis remains untested until native results exist.

New readiness directory: E:/PROWL/readiness/pancreas-region-20261019-a01.
New artifacts (only created at scientific launch):
E:/PROWL/artifacts/pants_pancreas_region_24k_20261019.
