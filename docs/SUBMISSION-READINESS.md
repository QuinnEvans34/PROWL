# ⛔ SUBMISSION READINESS — BLOCKERS FOR THE JOHNS HOPKINS EVALUATION

**Created 2026-08-15. This document is about STRUCTURAL CORRECTNESS, not accuracy.**

The question this file answers is **not** *"is the model good enough to submit?"* It is
***"is the model computing the right thing, in the right form, to be submittable at all?"***

A model with mediocre accuracy that is structurally correct can be submitted, scored, and improved.
A model with excellent accuracy that measures the wrong thing produces a number that means nothing
and cannot be compared to anyone. **The second failure is worse and it is invisible until someone
else runs your code.**

Every item below must be closed before a checkpoint goes to `zzhou82@jh.edu`.

---

# 🔴 BLOCKER 1 — LARGEST-CONNECTED-COMPONENT POST-PROCESSING IS INCOMPATIBLE WITH THEIR PRIMARY METRIC

## FIX THIS FIRST. BEFORE ANY TRAINING. BEFORE ANYTHING ELSE.

### The metric
From the PanTS benchmark table, verbatim:

> **Tumor-wise sensitivity (T-Sen):** A tumor is considered a true positive **only if it is correctly
> localized**. **Patients with multiple tumors can contribute multiple true positives.**

### What our pipeline does
`src/inference/postprocess.py` keeps the **largest connected component** of the predicted lesion mask
and discards the rest. It has been applied to every "cleaned" number this project has ever reported.

### Why this is fatal to the metric
**A largest-CC filter structurally caps the model at one detected tumour per patient.**

On a patient with three tumours, the model may find all three — and the post-processing throws two
away before scoring. T-Sen would count 1 of 3. Not because the model failed, but because the pipeline
deleted correct predictions.

**This is not a tuning problem. It is a design decision that contradicts the definition of the metric
being used to rank us.** It cannot be fixed by changing a threshold.

### Why it went unnoticed
Every metric this project has reported to date is **patient-level**: detection sensitivity, specificity,
patient AUC, and Dice pooled over the whole volume. Largest-CC is harmless — even helpful — for all of
those, because a patient is a true positive if *any* tumour is found. The incompatibility only appears
the moment the metric becomes **per-lesion**, and we have never computed a per-lesion metric.

### The fix — three parts, all required
1. **`largest_cc` becomes an explicit, off-by-default flag at inference.** It must never be silently
   applied. Any reported number states whether it was on.
2. **T-Sen is computed on the RAW multi-component prediction**, before any component filtering.
   Implement per-lesion matching: connected components of prediction against connected components of
   ground truth, matched by overlap, with the matching rule and overlap threshold recorded.
3. **Every existing "cleaned" number is relabelled** in the log as *largest-CC applied, patient-level
   metrics only, not valid for tumour-wise sensitivity.*

### Impact on prior results
Patient-level numbers remain valid — 0.474 lesion Dice, 96% detection, 17% specificity are unaffected,
because none of them is per-lesion. **The T-Sen column of the benchmark table has simply never been
computable with our current pipeline.** That is the honest statement.

### Verification that the fix worked
Find the multi-tumour cases in the frozen test cohort. Confirm that with `largest_cc` off, the raw
prediction contains more than one component on those cases, and that T-Sen can exceed 1 per patient.
**If T-Sen never exceeds 1 for any patient, the fix is not in effect.**

---

# 🔴 BLOCKER 2 — T-SEN HAS NEVER BEEN COMPUTED

There is no per-lesion matching code in this repository. The benchmark table has a T-Sen column
(MedFormer 75.2%, R-Super 80.1%) and our row would be blank.

**Required:** connected-component matching between prediction and ground truth, with an explicit and
recorded rule for what counts as "correctly localized" — overlap threshold, centroid containment, or
whatever their evaluation uses (see Blocker 4).

Downstream of Blocker 1: computing T-Sen on largest-CC output would produce a wrong number that looks
right, which is worse than a blank cell.

---

# 🔴 BLOCKER 3 — SPECIFICITY WILL BE TESTED HARDEST, AND IT IS OUR WEAKEST METRIC

The out-of-distribution suite is **26,489 scans**:

| set | n | character |
|---|---:|---|
| UCSF Pancreatic | 13,458 | proprietary |
| Polish Pancreatic | 5,259 | proprietary |
| Peking University | 3,066 | proprietary |
| **RSNA Abdominal Trauma** | **4,706** | **trauma patients, overwhelmingly no pancreatic cancer** |

At our current **17% specificity**, RSNA alone would produce roughly **3,900 false positives** — a
published number attached to our name, on the largest of the four sets.

**Consequence: the tumour-presence gate is a precondition for submission, not an enhancement.** A
submission at 17% specificity is not worth making.

---

# ✅ BLOCKER 4 — RESOLVED 2026-08-15. THEIR METRIC CODE HAS BEEN READ.

**The risk was real and it was worth checking.** Our conventions — detection at ≥ 50 mm³, Dice pooled
over tumour-positive cases with `ignore_empty`, specificity against mask-negative cases — differ from
theirs in five identified ways, two of them material. Same class of error as the validation leak: a
number that looks right, computed slightly wrong, believed for months. This one was caught before it
was published rather than after.


## What their code actually does — read verbatim from the repository

Two scripts, both public at `github.com/MrGiovanni/R-Super/rsuper_train/`:

- **`eval_AUC.py`** — turns saved prediction masks into per-case volumes and probabilities
- **`calculate_sensitivity_specificity_F1_AUC.py`** — turns those into sensitivity, specificity, F1, AUC

### Their volume computation, step by step

1. Load the predicted **probability** map.
2. **Resample to 1 x 1 x 1 mm with `order=1` — linear interpolation, on the probability map, before
   thresholding.** Voxel count therefore equals mm³ exactly.
3. For each confidence threshold in **0.1 … 0.9**:
   - binarise at that threshold
   - **`binary_erosion`**, 3x3x3 structure, **1 iteration**
   - **`binary_dilation`**, 3x3x3 structure, **2 iterations**
   - **multiply back by the original binarised mask** (`arr *= original`) so dilation cannot grow
     beyond the original prediction
   - volume = voxel sum
4. **`max_prob = np.max(array)`** over the resampled probability map.

The organ constraint is **already applied when predictions are saved** — the code raises an error if
you pass an organ mask at evaluation time.

### Their detection metric

```python
gt["gt_pancreatic"] = (gt["number of pancreatic lesion instances"] >= 1).astype(int)
preds = (vols >= vthr)
sens = tp / (tp + fn)        # patient-level
spec = tn / (tn + fp)        # patient-level
f1   = 2*tp / (2*tp + fp + fn)
auc  = roc_auc_score(gt_binary, "pancreatic tumor maximum probability")
```

Threshold grids: **9 confidence values (0.1–0.9)** crossed with **~300 volume thresholds** starting at
**10 mm³**. They do not fix an operating point in this code — they emit the whole grid.

---

## ★ THE FIVE DIFFERENCES THAT MATTER

### 1. ★★ Their denoising preserves multiple lesions. Ours destroys them.
They use **morphological erosion-then-dilation**, which deletes specks and thin structures but
**keeps every surviving component**. We use **largest connected component**, which deletes every
component but one.

This is independent confirmation of Blocker 1 from their own source code, and it hands us the
replacement: **swap largest-CC for erode(1)/dilate(2)/AND-original.** It achieves the same
false-positive pruning without capping tumour count.

### 2. ★★ AUC is computed on MAXIMUM VOXEL PROBABILITY, not volume
`roc_auc_score(gt, max_probability)`. Our reported patient-level AUC of 0.804 must be recomputed as
max-voxel-probability AUC before it can sit next to their 0.924 and 0.903. Our separately measured
"AUC on predicted volume = 0.843" is **not** the same quantity as theirs.

### 3. ★ Volume is measured at 1 mm isotropic, after linear-interpolating the probability map
Interpolating probabilities and *then* thresholding gives a different volume than thresholding and
then resampling. Our volumes are computed in our own space. **These are not the same number.**

### 4. ★ Their detection ground truth is report-derived, not mask-derived
`number of pancreatic lesion instances >= 1`, extracted from radiology reports by an LLM. Ours is mask
presence. We already measured the size of this discrepancy on PanTS: 122 of 750 mask-negative test
cases carry a report-described lesion, and reclassifying them moves specificity 17% → 19%. Small, but
it is a **definitional** difference that must be stated, not absorbed.

### 5. ★ They sweep; we fix
Our detection threshold is a single 50 mm³. Theirs sweeps ~300 volume thresholds at 9 confidence
levels. 50 mm³ sits inside their grid, so we are comparable at that point — but the honest comparison
is **curve against curve**, or the same (confidence, volume) pair on both sides.

---

## ⚠ STILL UNKNOWN — two leaderboard columns are not in the released code

**Neither script computes DSC. Neither script computes T-Sen.** The published table has both
(MedFormer 75.2% T-Sen, 52.9% DSC), but the released evaluation code produces only sensitivity,
specificity, F1, and probability-AUC.

So:
- **Our DSC convention** (pooled over tumour-positive cases, `ignore_empty`, NaN on empty ground
  truth) cannot be verified against theirs.
- **The T-Sen matching rule** — what counts as "correctly localized" — cannot be verified either.

**Action:** state both conventions explicitly in the submission README, and ask directly in the
submission email. This is a legitimate question to put to them, and asking is better than guessing.

---

## What we must change before any number is called comparable

- [ ] Replace largest-CC with erode(1) / dilate(2) / AND-original — matches their denoising **and**
      fixes Blocker 1
- [ ] Compute volume their way: resample probability to 1 mm isotropic with linear interpolation,
      then threshold, then denoise, then count
- [ ] Recompute AUC on **maximum voxel probability**
- [ ] Report detection under **both** ground-truth conventions — mask-derived and report-derived —
      and state which is which
- [ ] Emit the full confidence x volume grid rather than a single operating point
- [ ] Document our DSC and T-Sen conventions explicitly, and ask them for theirs

---

# 🔴 BLOCKER 5 — A PROVIDED-ROI MODEL CANNOT BE SUBMITTED

There is no oracle pancreas box on their scans. The autonomous localize-then-segment cascade is the
precondition for the submission existing at all. Already the core of the capstone; restated here so
the blocker list is complete.

---

# 🟡 ITEM 6 — INTERFACE COMPATIBILITY

Their inference expects:

```
/path/to/dataset/
├── BDMAP_0000001/ct.nii.gz
├── BDMAP_0000002/ct.nii.gz
```

and produces binary masks, with optional `--save_probabilities` and `--organ_mask_on_lesion`.

**Required:** a testing script that accepts this layout and emits masks in their expected form.
Symlinks are acceptable per their documentation. This is small work, but it is what "testing script"
means in their submission request and it must actually run on a machine that is not ours.

---

# 🟡 ITEM 7 — THE SUBMISSION PACKAGE

They ask for four things:

- [ ] model checkpoint
- [ ] testing script
- [ ] **in-distribution test results** — our 901-scan numbers, computed with *their* metric
      definitions (Blocker 4)
- [ ] a brief README with usage instructions

Plus, for our own integrity: the checkpoint must carry its embedded config, cohort hash, and git sha
so the result is reproducible if they ask.

---

# ✅ WHAT IS ALREADY COMPATIBLE

- **Three-class output is sufficient.** Every metric on their table concerns `pancreatic_lesion`. Their
  26 classes are means, not ends.
- **Detection framing is aligned.** Their 2025 headline is sensitivity and specificity versus
  radiologists, not Dice. We already treat detection as primary.
- **The anatomical constraint matches theirs.** Their `--organ_mask_on_lesion` flag is our
  `constrain_lesion_to_pancreas`, and they use the predicted organ mask, as we would need to.
- **Patch size matches.** Their `training_size: [128,128,128]` is identical to ours.
- **We are not disqualified.** SuPreM is a listed baseline on their own table, and R-Super used
  external data with only a footnote.

---

# ORDER OF OPERATIONS

| # | item | when |
|---|---|---|
| 1 | **Blocker 1** — make `largest_cc` optional; never silent | **first code change of the capstone** |
| 2 | ~~**Blocker 4** — extract their metric definitions~~ **DONE 2026-08-15.** Implement the six changes listed above | before any number is called comparable |
| 3 | **Blocker 2** — implement T-Sen on raw predictions | once 1 and 4 are done |
| 4 | **Blocker 5** — autonomous cascade | weeks 3–5 |
| 5 | **Blocker 3** — the gate | week 7 |
| 6 | Items 6 and 7 — adapter and package | week 10 |

**Nothing gets emailed until items 1 through 5 are closed.** One first impression.
