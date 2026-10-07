# Benchmark Standing — where this model sits against published work

**Last updated:** 2026-08-02
**Model:** MLflow `pancreas-lesion-segmenter` **v1**, step 18000, sha `62cc72fd…`
**Recipe:** SegResNet + SuPreM transfer · whole-box (crop-native 16 → 128³ @1.5 mm) · DiceFocal bg0
**Evaluated on:** the **official PanTS in-distribution test set, n=901** (151 tumor-positive, 750 tumor-free), scored **once**

---

## ⚠ READ THIS BEFORE QUOTING ANY NUMBER BELOW

**Our result is PROVIDED-ROI. The published results are autonomous.**

Our model is handed an oracle pancreas bounding box derived from the ground-truth mask, then segments
inside it. MedFormer and R-Super run on the whole CT with no such help. **The DSC column is therefore
not a like-for-like comparison, and must never be presented as one.**

Two further caveats that travel with the number:

1. The oracle box is built from pancreas **∪** lesion (`roi_source=union`), so lesion extent leaks
   into the ROI definition. Our lesion Dice is an **upper bound**. (Found in the metrics audit,
   2026-07-17; all relative comparisons hold because every run used the same crop.)
2. **0.528 and 0.483 are CONTAMINATED** by the `make_scaled_split.py` validation leak and are
   permanently withdrawn. **Never cite them.** 0.474 is the clean test number; 0.415 was the clean
   *validation* number (n=40).

Removing the oracle box is what the capstone is for. Until then, every appearance of this table
carries the caveat in the same breath.

---

## The table

PanTS official in-distribution benchmark (n=901), as published in the
[PanTS repository](https://github.com/MrGiovanni/PanTS):

| model | P-Sen † | T-Sen ‡ | Spe | AUC | DSC |
|---|---:|---:|---:|---:|---:|
| MedFormer | 80.8% | 75.2% | 90.0% | 0.924 | 52.9% |
| R-Super ★ | 80.1% | 80.1% | 93.2% | 0.903 | 53.4% |
| **ours (provided-ROI)** | **96.0%** | *not computed* | **17.0%** | **0.804** | **47.4%** |

† **Patient-wise sensitivity** — a case counts as detected if the model finds any tumor in a patient
who has any tumor, regardless of whether the location is right.
‡ **Tumor-wise sensitivity** — a tumor counts only if correctly localized; multi-tumor patients can
contribute several true positives.
★ R-Super was *"trained with additional external data (1.8K pancreatic lesion reports)"* — their
footnote, on their own table.

**Our supporting numbers:** pancreas Dice 0.827 (positives) / 0.847 (all 901) · detection 145/151 ·
specificity 128/750 · lesion DSC 95% CI [0.42, 0.52] · mean false-positive volume 1,830 mm³ across
622 flagged negatives.

---

## Honest read

**Where we are strong.** Patient-wise sensitivity of **96% exceeds both published models by ~15
points.** We miss 6 of 151 tumor-positive patients. That is not a rounding difference and it is not
an artifact of the oracle box — finding the tumor once you are looking at the pancreas is the part we
do well.

**Where we are competitive.** DSC 47.4% against 52.9 / 53.4% is in the same neighbourhood, from a
single laptop, 706 tumor-positive training cases, and a 4.7 M-parameter backbone — **with the oracle
caveat fully in force.**

**Where we lose, and it is the whole story.** Specificity **17% vs 90 / 93%.** We flag 622 of 750
healthy patients. In any real deployment that is disqualifying.

**Why this is a tractable gap, not a broken model.** Patient-level **AUC 0.804** says the
discriminative signal is present — the model ranks tumor-bearing patients above healthy ones far
better than chance. The threshold is simply in the wrong place. Supporting evidence:

- AUC on **predicted lesion volume alone = 0.843** — better than the model's own thresholded output.
  A volume gate lifts specificity **17% → 43% at 90% detection**, with no retraining at all.
- **EXP-25** proved the axis is movable by data: training on all healthy scans took specificity
  17% → 46%, but detection fell 96% → 88%, below the pre-registered floor, so it was rejected.
- **EXP-15** (8-view flip TTA) reaches 80% specificity, trading lesion Dice — an operating-point dial.

Every one of these says the same thing: **we built a sensitive detector and never tuned its operating
point.** That is the capstone.

---

## Missing row: T-Sen

We have never computed **tumor-wise sensitivity**. It requires per-lesion connected-component
matching between prediction and ground truth rather than the patient-level rollup we use now.
Bounded, concrete, and it fills the one empty cell in our row. **Queued as a capstone deliverable.**

---

## How this becomes a submittable result

The JHU team accepts external evaluation submissions by email (checkpoint + testing script +
in-distribution results + README) and scores them on **26,489 held-out scans** across UCSF (13,458),
a Polish cohort (5,259), Peking University (3,066), and RSNA Abdominal Trauma (4,706, re-annotated by
JHU). Their README states *"We are calling for more baseline methods"* and most rows of their
benchmark table are empty.

**We are not disqualified for our approach:** SuPreM is a listed baseline on their own table, and
R-Super used external data with nothing more than a footnote.

**But there is no oracle pancreas box on their scans.** A provided-ROI model cannot be submitted.
The autonomous localize-then-segment cascade is therefore the precondition for the strongest result
available to this project — not a stretch goal.

**Submission discipline:** one first impression. Do not email until the autonomous number is real.

---

## Sources
- [PanTS benchmark table and submission instructions](https://github.com/MrGiovanni/PanTS)
- [PanTS: The Pancreatic Tumor Segmentation Dataset (arXiv:2507.01291)](https://arxiv.org/abs/2507.01291)
- Our numbers: `deliverables/week4/tuning-orchestration-report.md`, `docs/experiments.md`,
  `docs/codex-metrics-audit.md`
