# D-308 — retained-model optimization investigation

Quinton authorized: “Investigate the learning rate schedule and anything else that could be giving
us issues.” This authorizes retained-record/cache/model diagnostics, not another training run.
Keep CAP-EXP-007/008 requests consumed and all original memberships, qualification and holds intact.

## Already completed CPU checks

Replay all300 saved patches from the113-member qualified cache and compare both runs' traces;
replay the installed PyTorch scheduler on an invented scalar; check class-balanced CE/foreground
Dice on invented logits. No original CT/label reads, primary-drive access, learned-model updates or
forwards. Per-attempt ceiling600s/8GiB RSS; cache-read upper bound6,233,594,545 bytes. One audit-helper
attempt required replacing exact float equality in an empty-target assertion with1e-6 tolerance;
its log is preserved. The second attempt passed. This was not a production-loss correction.

## Bounded retained-checkpoint probe

Read only independently backed-up step300 checkpoints from CAP-EXP-007 and CAP-EXP-008, validate
their receipts and complete checkpoint state with existing codecs, and load one model at a time.
Use the exact D-300 cache/binding. No original source or primary-drive file may be opened. Verify
the current source/environment still matches the consumed CAP-EXP-008 snapshot before and after.
Refuse real optimizer calls in the probe; hash all weights before/after each model's work.

For each model, perform:

- Four single-patch forwards: saved updates3/155 for tiny training6110, saved update300, and the
  largest-foreground saved patch. Replay and verify the exact traces; use identical inputs for both.
  Record foreground/background CE separately, Dice loss, soft probabilities, hard counts and target
  fraction. Compare the earlier recorded losses only as historical traces, not matched terminal loss.
- Three standard full-volume validation forwards:6186 (worst recall),6534 (former ROI pass),1004
  (best current Dice). Re-export and require exact native-array parity with each retained step300 mask.
  Record cached processed-reference/background/missed-reference probability distributions and loss
  components. These use processed targets, not new native-reference reads or new native recall scores.
- One Gaussian-blending full-volume forward for6186 only, with the same144³ window/overlap0.25.
  Compare processed hard metrics and probability differences against standard constant blending.
  This is a fixed inference-mechanism probe, not threshold/blending selection or a changed run result.

Maximum16 forwards total; no backward calls, optimizer updates or training continuation. Model
train/eval effects are reviewed from the installed architecture (group norm/dropout0), not assumed
from a generic network. No adaptive threshold sweep, new candidate, lesion target or test exposure.

Native MPS float32/fallback0, two CPU threads, no workers; exclusive existing MPS lock. Supervise at
600s/16GiB RSS and sampled driver,128MiB output, AC and100GiB free floor. Cache verification plus
selected inputs stays below8GiB read bytes; each keeper stays within its existing96MiB cap. No keeper,
backup or source writes. Preserve incomplete attempts and observed limits. These bounds are separate
from consumed training/read requests. Record actual work and parity failures honestly.

## Interpretation and exit

Distinguish verified mechanics, measured associations and unresolved causes. A correct schedule
does not establish an appropriate schedule; a functioning balanced loss does not establish suitable
probabilities or crop coverage. Padding, sparse foreground, limited exposures, missing negative-only
patches and visible partial references remain candidates for explicit comparisons, not grounds to
filter cases. Document findings and propose one controlled next experiment. No new training request
or launch approval is implied by completion of this investigation.
