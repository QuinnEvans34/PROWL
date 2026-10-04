# Proposed next diagnostic — matched early schedule, low-rate tail

**Latest status:** Quinton approved this diagnostic under D-309. See [the versioned launch plan](CAP-EXP-009-LAUNCH-PLAN-2026-10-01.md). The proposal below preserves its pre-approval context.

Status: **proposal for discussion; not implemented, frozen or authorized for launch**. D-308 completed
the [optimization investigation](CAP-EXP-008-OPTIMIZATION-FINDINGS-2026-10-01.md), not another run.

## Question and recommended candidate

Can additional varied case exposure shrink excess foreground while preserving coverage when the
early successful007 schedule is retained and the additional updates use a small rate?008 altered
early optimization by extending the cosine horizon;its stop at300 left longer-duration benefit open.

Propose a fresh seed42 run,600 updates total, with the same113/40,144³/2mm inputs, SegResNet, balanced
CE+Dice, AdamW weight decay, member order, center sampler and argmax/inference policy:

- Updates1–300 use exactly007's **applied** LR sequence:0.0003 times(1+cos(pi*k/300))/2, withk=0…299.
- Updates301–600 use fixed0.00001. That rate is3.33% of the original starting rate and is a
  conservative diagnostic choice, not an established optimum or production recommendation.
- Record both the rate used for each update and the next rate. At completed300,the next rate is
  deliberately0.00001 rather than007's0;all first300 applied rates remain identical.

The tail's summed rates are0.003, compared with the original first300's0.04515. It therefore adds
300 case exposures with much less cumulative LR. This sum is descriptive,not parameter displacement.
600updates mean78 cases get five sampled patches and35 get six. No epoch or full-scale claim follows.

Keep this a single declared optimization intervention. Do not also change padding masks, sampling,
loss coefficients, augmentation, thresholds, components, margins or cohort selection. Their observed
concerns remain subsequent experimental questions. Do not promote held empty references to negatives.

## First300 parity and evaluation

Checkpoint/evaluation boundaries0/300/450/600. Full113/40 at0/600;validation40 at300/450. The
fresh native-label budget is proposed386 reads. Exact per-stage bytes, mount observation and source
pins must be recomputed/validated during preparation;consumed007/008 requests cannot be reused.

Require identical first300 case/crop/rate traces, initialization and the retained007 checkpoint300
model within a predeclared, tested numerical tolerance. Require all40 native hard validation masks
at300 to reproduce007. Record optimizer/scheduler state honestly:the planned next rate differs at
that boundary. If prefix parity fails,stop and investigate;do not call it matched duration evidence.

Retain the008 numeric guards from300:mean validation recall>=0.95,minimum>=0.65,at least38/40
boxes cover>=0.995,and mean recall drop<=0.03 from the best earlier active checkpoint. Step0 stays
warmup. A stop retains the actual completed prefix, checkpoints/evaluation records and independent
recovery. Every case remains in the calculations and cohort. There is no automatic extension.

Assess useful shrinkage separately from stopping:target median volume<=13.873x (25% below007's
18.497x),at least10/40 ROI screens,mean recall>=0.9627 and all40 box-coverage screens retained.
These are proposed diagnostic targets,not contour acceptance. Final train/validation metrics,all
per-case failures,partial/tiny references and exposure counts remain visible. No sealed-test,G5,
lesion containment or model-promotion claim follows from this single-seed development comparison.

## Implementation needed before a request exists

1. Add a separate versioned schedule policy that decouples update budget from cosine duration.
   Identity/config/control/state validators must bind the exact two phases. Never run the old
   scheduler past its horizon or silently widen version1/version2 launch contracts.
2. Test rates at phase boundaries,last update and forbidden continuation;record used/next rates.
   Test save/reload, next-update equivalence, stopped prefixes, reference scopes, parity refusal and
   interrupted-attempt handling with invented data. Preserve all existing version behavior.
3. Perform a source-matched native synthetic MPS/recovery rehearsal. Derive prospective checkpoint/
   keeper/storage/reference budgets and test them. A proposed60-minute/16GiB total budget needs
   measured confirmation before freeze;retain AC/free-space/output/backup limits and exclusive MPS.
4. Freeze one new request and exact launch plan,then obtain the launch decision. After execution,
   verify all sealed artifacts/native exports,independently restore every published keeper,and
   inspect coverage/excess before choosing a subsequent intervention.

This repeats the300-update prefix deliberately to keep the next diagnostic fresh and matched. A
more economical warm-start tail from007 is a distinct possible design,requiring explicit parented
run/checkpoint semantics and its own approval;it is not the selected candidate here. No current
request or stopped session may be resumed by inference from this proposal.
