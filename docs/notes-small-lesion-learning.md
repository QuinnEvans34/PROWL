# Note — small-object learning, from a computer vision assignment

**Captured 2026-08-23.** Parked for later discussion; not acted on.

Source: a separate Claude conversation during a computer vision assignment, where Quinn asked why a
detector misses small tumours and how a model goes from *"I am wrong"* to *"I know why I am wrong."*
The material below is recorded first, then mapped against this project's actual experimental record.

The reason to keep it: most of it is correct textbook reasoning, **and this project has already run
four of the five recommended levers and got nulls.** The gap between the standard answer and our
measured results is the interesting part, and it is worth a conversation.

---

## Part 1 — the source material, as received

### Why small tumours get missed, ranked

1. **Resolution loss (dominant).** Structural, and no threshold fixes it. A 14-pixel lesion becomes
   0.9 pixels after ÷16 downsampling. There is nothing left for a bias to be lenient about.
2. **Class imbalance in the loss (the real learning problem).** A 14-pixel lesion in a 262,144-pixel
   slice. A model that outputs "no tumor anywhere, ever" is 99.995% correct pixel-wise. The loss
   barely twitches. Gradient descent is doing exactly what you asked — you just asked wrong.
3. **Bias / threshold (real, secondary).** A detector trained mostly on large tumours calibrates its
   threshold to large-tumour evidence levels.

> "It learns small things are noise" is directionally right, but the loss function teaches that
> lesson; the bias merely stores it. **Bias is where the symptom lives, not the disease.**

### How a model "knows why it is wrong"

It never knows why. **It computes a derivative.**

For every parameter `w`, backprop computes `∂L/∂w` — "if I nudge this one number up a hair, does the
loss rise or fall, and how steeply?" Then `w ← w − η·∂L/∂w`.

"Why am I wrong" translates exactly to *"which parameters, changed slightly, would have made me less
wrong."* That is not an explanation. It is a direction. The chain rule is the blame-assignment
machinery: each layer receives *how much my output contributed to the error* and passes back *how
much your output contributed to mine*.

**If small tumours are 0.1% of the training signal, they contribute 0.1% of the gradient pull.** The
model is not stubborn. It is correctly optimizing a target that was specified badly.

### The machinery — every piece works by amplifying the gradient from the rare case

**Loss engineering — make the mistake more expensive**

- **Focal loss** (Lin et al., 2017): `FL = −α(1−p)^γ log(p)`. The `(1−p)^γ` factor crushes the
  contribution of confidently-correct pixels so hard examples dominate. Built for dense detection
  with extreme imbalance.
- **Tversky loss:** generalizes Dice with tunable α/β so false negatives can be penalized harder than
  false positives — mathematically, *"missing a small tumour should hurt more than a false alarm."*
- **Dice loss:** overlap-based, so it does not scale with object size the way pixel-wise
  cross-entropy does.

**Architecture — stop destroying the resolution**

- **U-Net skip connections.** The direct fix for cause #1: high-resolution feature maps are carried
  across to the decoder so fine detail never has to survive the bottleneck.
- **Dilated / atrous convolution** — grow the receptive field without downsampling.
- **Feature pyramid networks** — detect at multiple scales; small objects handled at high-res levels.
- **Patch-based training at native resolution** — never downsample the CT; train on small crops at
  full resolution.

**Sampling** — oversample lesion-containing patches; hard negative mining.

**Inference threshold tuning** — lowering the decision threshold trades specificity for sensitivity,
which in cancer screening is usually the trade you want. Adjusting that threshold post-hoc *is*
adjusting a bias.

**Diagnostic:** Grad-CAM shows which regions drove a prediction. It does not help the model learn,
but it tells you whether it is looking at the pancreas or at a scanner artifact.

---

## Part 2 — how this maps onto THIS project

### ⚠️ The framing does not match our failure mode, and the mismatch matters

The argument in Part 1 predicts a **timid** model: one that learns to say "no tumour" because silence
is cheap. **Ours does the opposite.** On the official 901-scan held-out test set:

| | measured |
|---|---|
| detection sensitivity | **96%** (145/151) |
| specificity | **17%** (128/750) |
| small tumours < 1 cm³, Dice | **0.067** — over-segmented **25–50×** |

The model finds nearly every tumour and paints far too much. It is **trigger-happy, not timid.** So
the "gradient descent learns to ignore the rare class" story, while a correct account of the generic
case, is not the account of our model. Whatever we conclude later has to explain *over*-prediction.

The small-tumour failure is real but its mechanism is inverted: we do not miss small lesions, we
**smear** them. Dice on a small object collapses when the prediction is an order of magnitude too
big, even though detection succeeds.

### Levers already tested here — with results

| lever from Part 1 | status in this repo | outcome |
|---|---|---|
| Focal loss | **in use** — DiceFocal `include_background: false` is the locked base | is the baseline, not an untried fix |
| Dice loss | **in use** (Dice term of DiceFocal) | — |
| Tversky (penalize FN harder) | **EXP-18, run** | pure Tversky α=0.7 **REJECTED** — pancreas collapsed to 0.000; the global FP penalty made the large organ not worth predicting. `tversky_focal` α=0.6 recovered pancreas to 0.833, lesion ~0.34 in-loop, run interrupted, never finished |
| Oversample lesion patches | **EXP-05, run** | **RULED OUT** — 1:1 vs heavy positive sampling came out numerically identical (lesion 0.169 both) |
| Hard negative mining | coded (`strategy: classes`, `class_ratios [1,1,2]`) | wired, never conclusively run |
| Patch-based at finer resolution | **EXP-16, run** | **REJECTED** — 160³ @1.2 mm: pancreas 0.778→0.805 but lesion 0.257→0.248 |
| Native-resolution small crops | **EXP-11, run** | **REJECTED** — 64³ @0.7 mm gave only a 45 mm field of view on a 150–200 mm organ; starved the model |
| Larger context | **EXP-08, run** | **REJECTED on accuracy** — 128³ vs 96³: lesion 0.206→0.187 |
| Threshold tuning | **done repeatedly** (`evaluate.py --sweep`) | works as a dial, not a fix — thr 0.90 → lesion 0.319 / spec 70% |
| U-Net skip connections | **already present** — SegResNet is an encoder–decoder with skips | not an available fix; we never had the plain-bottleneck problem |
| Dilated conv / FPN | not tried | genuinely open |
| **Grad-CAM** | **not tried** | genuinely open, and cheap |

### What actually moved the number

Five recipe axes — sampling ratio, loss background, context size, resolution, and loss family — were
each tested against a pre-registered bar and each returned a null or a rejection. **The only change
that ever moved lesion Dice was more data:** EXP-17 tripled the tumour cases with the recipe held
fixed and took lesion Dice 0.263 → 0.313 (+0.05), the first result to beat the standing best.

That is the empirical finding this project actually has, and it sits in tension with Part 1's
framing, which locates the problem in the loss and the architecture. Both can be true — a badly
specified target *and* insufficient signal — but our ablations say the binding constraint here was
signal.

One more measured result that complicates the standard advice: **EXP-25** raised specificity 17% → 46%
by adding healthy cases, and the cost landed almost entirely on small tumours — detection fell to 56%
and small-tumour Dice to 0.013 on that class. Pushing the model to be less trigger-happy is exactly
what Part 1 warns against, and we have the number for what it costs.

### The two items worth actually doing

1. **Grad-CAM (or attention rollout) on false positives.** We have 622 flagged negatives and a mean
   false-positive volume of 1,830 mm³, and **we have never looked at what drives them.** If the model
   is firing on scanner artifacts, bowel gas, or a specific contrast phase, that is a data fix, not a
   loss fix — and it is the cheapest unexplored diagnostic on the list.
2. **Finish `tversky_focal`.** EXP-18b was interrupted for transport and never scored at full eval.
   It is the one loss-side lever with an unresolved result rather than a rejection, and its stated
   purpose — penalizing false positives — targets our actual failure mode rather than the generic one.

### The correct restatement for our case

Part 1's closing line is *"bias is where the symptom lives, not the disease."* For this project the
honest version is:

> **Over-segmentation is where the symptom lives. Insufficient tumour signal is the disease we have
> evidence for. Everything else we tried was a dial, not a cure.**

Neither claim is settled. Both belong in the capstone conversation, not in a report, until tested.

---

## Related

- `docs/experiments.md` — EXP-05, 07, 08, 11, 16, 17, 18, 25 in full
- `docs/SUBMISSION-READINESS.md` — why specificity is a submission blocker, not a tuning nicety
- `deliverables/week4/tuning-orchestration-report.md` — the by-size failure analysis
