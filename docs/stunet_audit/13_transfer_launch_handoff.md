# Exploratory STU-Net transfer: authorized execution handoff

The user now explicitly requests transfer training and accepts proceeding with unresolved exposure: “Let’s make sure it works before we go crazy on making sure there is no leakage. … Let’s start the transfer learning now.” This supersedes the earlier setup-only/no-training authorization for **one bounded exploratory pretrained STU-Net-B run**. It does not assert independence or waive operational gates.

**This handoff is not evidence of a scientific launch.** Lenovo is the sole intended scientific host. The GPU, real-input, restoration and launch receipts from that host must establish actual progress. The Mac is not dispatching a competing run.

## Intended experiment

- Audited original STU-Net-B checkpoint SHA256 `7232a6296d320da1d60debe873a1d3fcad74e9404272db8f7440e30d62c5997a`; preserve all 58,157,984 transferred body parameters at initialization and seed 2,991 fresh three-class head parameters.
- One pretrained fine-tuning arm, proposed 12,000 updates, seed 42, batch one, 128³ input, checkpoints every 500 and full 70-case native development validation every 2,000/terminal. Forty-eight-hour total wall bound includes validation. Actual input, loss, augmentation, sampling, recovery, precision and storage recipe must be qualified and frozen before scientific updates.
- Existing 1,333 training members and qualified 70-case development subset; preserve all five other registry development cases in provenance. No quiet 410-case substitution, protected 901-case test reads, or PDAC-TAGS training/evaluation.
- Exploratory development reporting with selected **and terminal** results, all scheduled validations, failures/false positives, MLflow, backups and actual compute. No automatic scratch/control successor, causal pretraining-gain claim, independent-patient interval, or model promotion. A future matched scratch comparison remains separate.

## Host preparation and outstanding dependencies

Mac path-only checks found all 1,403 required CT/lesion/pancreas paths available, with approximately 46.176 GB of compressed CT files. No CT or mask was opened in that availability check.

Lenovo's prior D: data drive is absent. Retained availability evidence covers 410 training CTs; 923 missing paths total 30,264,489,348 bytes, with original archives already on E:. One development path also needs reconciliation. Restoration of these named permitted inputs is authorized as a necessary launch prerequisite. It must preserve original path history, case identities, integrity evidence and resource limits. The peer estimates 1–2 hours from its earlier measured restoration; this is not a guarantee or evidence that extraction has completed.

The peer published preparation commits `13543e8` and `a748b38` on `codex/week05-cuda-readiness`. The Mac inspected the preflight report, strict model loader, explicit deep-supervision loss, tests and CPU preparation report directly from Git without merging or changing old producing files. Lenovo subsequently reported an actual 128³ FP32 CUDA synthetic check: three pretrained updates with finite gradients, approximately 4.1 seconds/update and 5.86 GiB reserved under its 6-GiB cap. These are reported engineering measurements, not a real-data scientific curve. At that rate optimizer time alone would be about 13.7 hours for 12k; loading, validation, backups and qualification add time.

Actual source restoration, real-input/geometry validation, native evaluation cost, full-state cold recovery, independent backups, final request/receipt and a verified scientific worker remain required. Do not convert a chat instruction, dataset extraction or synthetic optimizer update into a claim that the scientific run is live.

The source restoration is advancing: retained peer execution output contains `ct_verified` events at approximately 299 and 725 seconds. These establish real extraction/verification activity, not completion of all 923 missing inputs. The peer's 128³ coverage plan subsequently passed all 1,333 training members with 2,978 reserved coverage windows, 9,000 focused opportunities and 3,000 context opportunities (280.188 supervised worker seconds reported in its output). The new coverage-first sequence repairs the seven undercovered cases that would result from truncating the old 24k sequence. Five input/session CPU tests then passed; real-input optimizer/recovery qualification and scientific dispatch remain pending.

## Mac memory-policy evidence

The Mac performed bounded synthetic tests under an explicitly narrower 6-GiB MPS allocation cap, with CPU fallback disabled, exclusive GPU lock, AC/storage/memory checks, 12-GiB owned RSS and 300-second limits. These probes do not establish what would fit under a different, separately qualified MPS budget.

1. Original 128³ FP32 synthetic forward hit the MPS cap before backward.
2. A new additive block-recomputation policy checkpointed six encoder and five decoder blocks without changing parameters, state keys or inference behavior. Two synthetic unit tests passed, including RNG preservation and gradients without input gradients. With the actual pretrained model on a 32³ CPU fixture, outputs/loss and **every parameter gradient matched exactly**, maximum gradient difference 0. The loss was 7.179463863372803 in both paths; zero optimizer updates and no clinical inputs were used.
3. The checkpointed 128³ MPS probe reached the loss phase but exceeded the cap. A separate fresh probe with unused-cache release at phase boundaries reached backward but also exceeded the cap. Neither reached an optimizer step. All attempts and logs remain intact; all owned workers were reaped. No limit was increased, fallback enabled, source changed in place or scientific run started.

The helper is `src/training/stunet_activation_checkpointing_v1.py`; tests are in `tests/stunet_audit/test_stunet_activation_checkpointing.py`. It is a potential execution policy, not a qualified MPS training solution. CUDA's reported reserved bytes and MPS driver/allocator accounting are different metrics and must not be compared as equivalent memory measurements.

Local receipts: `/Volumes/PROWL-Data/PROWL/artifacts/stunet-transfer-20261106/`. The current user authority is recorded separately under `outputs/prowl/stunet-transfer-20261106/user-launch-authorization.json`. Earlier audit manifests, scientific weights, splits and failed attempts are unchanged. No author outreach or medical-data upload was performed. Audit additions and the Mac memory-policy helper remain uncommitted under the adopted audit instruction.
