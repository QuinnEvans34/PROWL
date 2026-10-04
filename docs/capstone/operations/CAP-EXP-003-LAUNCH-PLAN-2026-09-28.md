# CAP-EXP-003 — lower LR, otherwise identical balanced comparison

D-278 records Codex's controlled follow-up under Quinton's D-277 overnight authority. CAP-EXP-002
made predictions nonempty but too broad; final mean Dice0.05497 failed the preset indicator. Test
whether LR reduction improves this behavior without changing the objective, data or training duration.

Exactly copy [CAP-EXP-002's plan](CAP-EXP-002-LAUNCH-PLAN-2026-09-28.md), changing only starting LR
from0.003 to0.0003. Keep balanced CE+foreground Dice,100 updates,cosine T_max100,weight decay1e-5,
scratch seed42 and the identical original initialization digest; no pretrained/previous weight reuse.
Same cases3/26, recipe/purpose/input pins,96³/batch1/fp32 MPS, crop keys/member order, inference argmax,
no augmentation/cache/workers. Same objective-aware telemetry at0/25/50/75/100 and fixed patch probes.

Same learning indicator: balanced mean loss reduction≥10% AND mean foreground Dice improvement≥0.10;
report per-case false-positive volume and original objective too. Preserve fixed-step terminal outcome,
not the best checkpoint. This is tiny-set training behavior, not validation/generalization.

Exactly one fresh real attempt after tests/native verification and immutable request preparation.
100 updates,600s update phase/1,200s total,16GiB RSS/MPS ceilings,1GiB new bytes/domain,existing free
floors,AC and accelerator lock. Same complete checkpoints,terminal exports and independent backup/
fresh-process restore tolerance1e-5. No automatic extension/retry or threshold change. Further work
must be justified by the recorded result and separately bounded before compute.
