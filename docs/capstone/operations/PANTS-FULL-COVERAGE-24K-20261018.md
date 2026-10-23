# Preserve the full lesion field without squeezing away detail

The user approved autonomous final setup and one scientific launch after the full intake
qualification passed. This run tests whether preserving the complete annotated lesion
field and native target detail improves outlining over the successful augmented PanTS run.
It uses PanTS only. PANORAMA, EMA, lower learning rate and distillation remain separate work.

## Evidence review and decision

All 1,333 training and 70 development cases passed intake qualification. All 7,145,665
annotated lesion voxels and 868 components were preserved. The 43 previously clipped
positive training cases remain included. Twelve actual input image sets were reviewed;
target reconstruction was exact, and real GPU updates, independent backup, cold restore
and large full-scan reconstruction passed. The original 445 scientific producing pins
remain unchanged. No new dataset or overlap audit is required.

Proceed with the qualified physical-detail-windows-1 path. It subdivides coarse voxel
axes to approximately 1 mm or finer without downsampling already finer axes. Training uses
144³ windows, complete lesion-field coverage visits, component variations and uniform CT
views. Inference uses full-CT tiling with stride 72 and native probability reconstruction,
without reference masks selecting windows. A single forward pass still sees one window.
Interpolation cannot recover detail absent from the acquisition.

## Frozen scientific recipe

- Original SuPreM initialization plus a fresh head, seed 42; not diagnostic or prior trained weights.
- 24,000 optimizer updates, DiceFocal, AdamW learning rate 0.0001 and weight decay 0.00001.
- 500 warmup updates and the original 24,000-step cosine schedule; existing augmentation.
- Unchanged 1,333 training cases and matched 70 development cases (36 positive, 34 reference-empty).
- Checkpoint every 500 updates; retain the state before every 2,000-step native validation.
- Twelve complete native full-CT validations; select the highest positive-case macro Dice,
  keeping the earliest checkpoint on a tie. Keep selected and terminal reports separately.

Native validation uses 7,698 windows per complete development pass. Measured large-scan
stress evaluations took 292 and 230 seconds, including loading and metrics. Full validation
will therefore be substantially more expensive than the old single-crop proxy. Keeping
the 2,000-step cadence preserves twelve selection opportunities; it does not make the
selection methods identical, since the old run selected using tensor Dice.

The hard wall-clock ceiling is 96 hours, including validation, not a promised duration.
Four integration timings are insufficient for a dependable full-run estimate. Retain the
12 GiB owned-RSS cap, 100 GiB free-space floors on C:/E:, existing 32 GiB cache cap,
27,917,287,424-byte backup cap, AC requirement and supervised process cleanup. No dense
fine-grid cache is created. Any failure stops the run; no automatic restart, resume or
budget extension is authorized.

## Hypotheses and acceptance

H0: selected-checkpoint native positive-case macro Dice improvement over the augmented
PanTS control is at most zero. H1: it is greater than zero. The control's selected 18k
native Dice is 0.4237607557; its final 24k native Dice is 0.3937226670.

Accept the practical intervention only if the primary Dice gain is at least 0.02, its
paired 95% percentile-bootstrap lower bound is above zero, detection decreases by no more
than 0.03, empty-case alarm fraction increases by no more than 0.03, pancreas Dice decreases
by no more than 0.02, and total empty-case predicted lesion-voxel burden does not increase.
Use 10,000 paired positive-case bootstrap replicates with seed 20261018. Keep every matched
case, including misses. The final24k comparison is mandatory secondary evidence and cannot
replace a failed primary result. Point-estimate guardrails are not statistical noninferiority.

This is an exploratory bundled input, sampling and inference experiment. The old control
used provided-pancreas inference and tensor-based selection; this run uses full-CT inference
and native selection. Differences cannot be attributed to cropping alone. Development reuse
does not establish external generalization. The project target of Dice 0.5 is an objective,
not an acceptance threshold invented after observing results.

## Launch and observability

The qualified numerical input/session modules remain untouched. A separate executor and
receipt-gated launch wrapper add full native validation, pre-validation checkpoints, durable
progress and independent backups. Eleven focused orchestration tests cover selection,
tie handling, malformed/incomplete evaluations, role rejection, failure journaling and
native-only MLflow naming. A bounded two-update/two-case integration smoke exercises this
new orchestration; it is nonpromotable and excluded from scientific training hours.

MLflow mirrors live training loss, learning rate, elapsed time and complete native development
metrics. Local journals/checkpoints remain authoritative if tracking degrades. The existing
private phone dashboard reads actual journals and shows update count, runtime, loss, native
Dice once evaluated, and scan/window progress during validation. No public exposure or new
AI schedule is introduced. A final claim of launch requires observed scientific updates,
verified initial backup, live MLflow metrics and dashboard readback—not merely process creation.

Specification: `PANTS-FULL-COVERAGE-24K-20261018.json`.
Setup: `E:/PROWL/readiness/pants-full-coverage-24k-20261018-a01/`.
Scientific output: `E:/PROWL/artifacts/pants_full_coverage_physical_24k_20261018/`.
Initial intake receipt SHA256:
`837bfbce8f81198c4ee1fd1a939456e7d1ea2e49551d90ff07fec5cb2ad924da`.

## Launch confirmed

Scientific training launched October 18 at approximately 15:45 MDT, with actual optimizer
updates observed in the durable journal and phone dashboard. The final launch receipt is
`E:/PROWL/readiness/pants-full-coverage-24k-20261018-a01/ready.json`, SHA256
`63d1aeb3abf8af1a71366a6e18086151fcf3972eba05df3a07c5fed679608d2c`.

The production integration smoke finished in 107.719 supervised seconds with two updates
and two complete native development evaluations, peak owned RSS 2,102,202,368 bytes and
workers reaped. All four retained smoke checkpoints matched their independent backups.
Eleven orchestration tests and eighteen dashboard checks passed. These diagnostic updates
are excluded from the scientific run and its training-hour total.

Live local MLflow run `ecb6e402f0f84bc8a9df5e11239e5972` is RUNNING; initial training metrics
were read back successfully with no tracking-warning artifact. The initial scientific
checkpoint and C: backup match SHA256
`1a6922e10a33f63d649254c002dfc6808fa5effefa947f69b8e95dd23caaf56b`.

The existing private dashboard shows the new run first, correctly labeled native full CT,
with live updates, loss and elapsed training time. The actual private URL was opened and
checked at a 390×844 phone-sized viewport. Dice stays unmeasured until the first complete
70-case native validation after step 2,000. The monitor service was restarted independently
of training; existing networking and exposure were unchanged.
