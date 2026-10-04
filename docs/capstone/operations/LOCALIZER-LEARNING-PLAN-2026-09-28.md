# Localizer synthetic learning and recovery plan

September 28, 2026. Quinton explicitly requested the model-input adapter, synthetic learning
checks, and checkpoint save/reload/recovery (D-271). Implement in new localizer modules under
src/training, focused tests, a diagnostic script and this handback. Preserve historical trainers,
sealed data policies and Claude's files. No real CT reads, MPS job, downloads or real training.

## Contract and acceptance before execution

Reuse the existing MONAI SegResNet builder with scratch initialization, one CT channel, two logits,
GroupNorm, 16 initial filters and (1,2,2,4)/(1,1,1) blocks. Float32; no dropout. Candidate real patch
size 96³; synthetic tests may explicitly use 16³. AdamW and foreground Dice plus cross-entropy;
step-based cosine schedule. Final real learning rate/steps/sampling budget remains Phase E work.

Training adapter selects a reproducible pancreas-centered or background-centered crop with equal
probability, zero-pads small inputs and records its origin/choice. This is pancreas-only supervision,
not lesion sampling. A background center does not imply an all-background crop. Empty targets use
background sampling and CE; foreground Dice is undefined when the reference is empty and is reported
as null with predicted foreground count. Inference accepts only image tensors, covers the full volume
with sliding windows and stitches on CPU; no target-derived inference region. Restore probabilities
with the existing physical transform record before taking the final argmax.

CPU restart boundary: completed optimizer + scheduler update. Zero workers/cache/augmentation,
stateless crop randomness keyed by seed, step and member; dropout absent. Capture CPU RNG as well.
Save optimizer, scheduler, model, completed step and exact run identity. Resume explicitly from an
independently pinned completion receipt into a fresh session; no latest-file discovery or fallback to
fresh optimizer. The existing bounded artifact store supplies lock, fsync, hidden partial attempts,
completion hashes and non-overwriting publication. Synthetic store roots are temporary/internal only;
production checkpoint root capability and real-run identity integration remain Phase E prerequisites.

Acceptance: finite outputs/loss/gradients, changed parameters, known-signal learning (final fixed-fixture
loss < initial * 0.8 within 40 CPU updates), exact CPU predictions after reload, identical continued
states after interruption at a completed step, invalid/corrupt/partial/wrong-identity rejection,
image-only coverage and source-grid restoration. Test real 96³ adapter shape separately without a
96³ training job. Diagnostic budget: 40 updates, 10 minutes, 2 CPU threads, <=256 MiB artifact payload,
no source data. No real-data performance or bitwise MPS-resume claim.

Canonical local records are the required tracking evidence in this slice. No tracking service is
required or contacted; an MLflow export is deferred and cannot replace immutable records. Report this
explicit limitation rather than claim all of Phase D or Plan 06 complete.
