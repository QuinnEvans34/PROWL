# Expanded localizer preprocessing results — September 29, 2026

D-283 complete. All **16 frozen training and 11 frozen validation members** passed the bounded
loader/preprocessing diagnostic. All 27 transformation sheets were reviewed. No member was dropped,
replaced or promoted by this job; case 6350 remains held. No model forward or optimizer update ran.

## Implementation and verification

`src/data/expanded_localizer_inputs.py` resolves/replays the D-282 frozen bundle, checks explicit
optimizer/evaluator roles and permitted uses, binds decoder implementation and full source bytes,
and enforces a shared 54-file read budget. `src/data/localizer_preprocessing_v2.py` adds header-only
allocation projection and a bounded 64-million source-voxel limit. The separate v2 recipe retains
RAS, 3 mm spacing, HU [-100,300], nearest-neighbor targets, minimum 96 padding and no cropping,
augmentation or cache. The old two-case/v1 implementation and recipe remain unchanged.

Native full suite: **1,146 passed**, two existing upstream warnings, 16.22 seconds. Fifteen new
checks cover roles, held/changed inputs, budgets, allocation refusal, restoration, target-independent
images, v1 compatibility, renderer geometry and decoder lineage. Command:

```sh
env PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv-prowl/bin/python -m pytest tests -q -p no:cacheprovider
```

## Measured result

| Measure | Result |
|---|---:|
| Source files | 54 / 54 |
| Compressed bytes read | 684,668,314 |
| Expanded bytes verified | 1,759,247,955 |
| Supervised wall time | 237.48 s |
| Frozen-bundle metadata replay | 171.89 s |
| Peak sampled worker RSS | 12,417,138,688 bytes (11.56 GiB) |
| Receipted evidence payload | 12,166,981 bytes across 64 files |
| Numerical failures | 0 |
| Reference round-trip Dice min / median / max | 0.8171 / 0.9285 / 0.9553 |

The 20-minute/16-GiB job limits were respected. Every target remains nonempty; images produced
with and without targets match exactly. Restoration returns the source shape and affine. All 64
receipted files were independently rehashed; all 54 source-read receipts match qualified descriptor
hashes/lengths, and exact role membership matches the frozen capability. Source/environment were
rechecked by the runner before completion. Reference round-trip Dice measures preprocessing loss,
**not model quality or generalization**.

All 27 sheets show no obvious gross displacement/axis reversal in the sampled views. This is a
limited engineering review, not expert annotation acceptance or exhaustive slice review. Case 4965
has the lowest round-trip Dice (0.8171) and only 59 processed foreground voxels: its partial-coverage
target survives, with no claim of complete-organ coverage. Case 3717 retains its boundary-contact
target (338 voxels; Dice 0.8926). Noisy cases, including 8037, remain included. No case crossed the
predeclared <0.75 closer-review trigger. The validation arterial/thin-slice gap remains recorded.

## Retained evidence and failed attempt

Successful request: `outputs/prowl/expanded-preprocessing-request-39db165d-0d0e-432d-8806-1cbdc16fc5e9`,
SHA `810ff1bcfb7a39bab0717fc1fc89a37771343a8a3790145c345c9b6bd8b21e65`.
Diagnostic: `outputs/prowl/expanded-preprocessing-a8321976-3634-4464-9df1-1811dc39922d`; receipt SHA `8a9274a5815d6acfd466487e5d17c7c1d5f6fd5463dd1d9373daf155d3ab0bff`.
Separate visual review: `outputs/prowl/expanded-preprocessing-review-f38a04d0-f10e-445a-a1bb-5d52456030a5`; receipt SHA `f6314db209999bb282b37a236ea4312edd4df0c3aac7dc0b2cb3f1669fce82f7`.
The original job's `visual_review_pending` state is preserved as historical evidence; the separate
review completes that step without rewriting the job receipt. Images and raw data remain ignored.

The first attempt, `expanded-preprocessing-41bcb797-9a69-44e8-ba04-21da7f6c8c20`, stopped at a
renderer affine-list TypeError after first-case processing (180.92 s, exit 1). Its incomplete evidence
is preserved. A synthetic rendering regression and corrected conversion preceded the new single-use
request; cases, recipe and budgets did not change. No consumed request was reused.

## Next bounded implementation

1. Adapt the scratch runner to these role-specific inputs. The existing two-case executor remains
   v1-only; this diagnostic alone does not make expanded training launch-ready.
2. Choose a bounded in-memory processed-data cache or verified derived artifacts so training does
   not repeatedly decompress/hash/resample all sources. Keep training and validation roles enforced.
   Header projections put the 16 training images near 93 MiB in float32, but this excludes labels,
   model/optimizer state and working allocations. Measured preprocessing RSS was much higher.
3. Verify multi-case scheduling, pancreas targets, full-volume separate validation, checkpoint
   save/reload and recovery, including the new cohort/recipe identity. Preserve difficult cases and
   report partial-coverage performance separately. Fit decisions use development data only.
4. Run a bounded resource profile, then freeze a fresh scratch experiment with exact update count,
   seed, evaluation cadence, stronger localization metrics and stop/backup limits before launch.

No further broad qualification is needed to start that implementation. This result does not grant
source redistribution rights, establish biological patient uniqueness, or resolve case 6350. No
literature files, source data or Git publication were changed by D-283.
