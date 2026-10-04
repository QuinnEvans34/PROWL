# Proposed next step — foreground pressure before more duration

**October1 update:** Quinton subsequently authorized this audit underD-311. It is complete;
[results](LOCALIZER-FOREGROUND-AUDIT-RESULTS-2026-10-01.md) and
[next proposed class-mean comparison](LOCALIZER-CLASS-MEAN-REBALANCE-PROPOSAL-2026-10-01.md).
The recommendation/approval status below is the original pre-audit proposal,retained as history.
No loss change or new training run has been authorized byD-311.

Codex recommendation following [CAP-EXP-010](CAP-EXP-010-RESULTS-2026-10-01.md), not a new Quinton
decision or an exact launch request. No new experiment is implemented, frozen or authorized by this
file. D-310's300-new-update request is complete and consumed.153members/23holds remain unchanged.

The low-rate tail reduces all40 validation mask volumes and improves all40 Dice scores, while
preserving the coverage guards. However, median volume16.541x and ROI2/40 miss the useful-shrinkage
target. Case3115's recall and7604's training box coverage worsen. Simply adding duration does not
yet address the dominant excess-foreground problem. The result does not prove a particular cause.

## First: bounded frozen-model objective audit

Use retained qualified cache, exact300 child crop traces and independently backed-up007/010 terminal
models. No original CT/label reads, optimizer updates, source rewrites, cohort changes or threshold
selection. Propose at most16 patch forwards: eight fixed training-only patches through both models.
Prepare a separate source/runtime-bound600s/16GiB/128MiB audit before native execution; independent
backup reads and model hashes must verify, and weights must remain unchanged. No sealed-test use.

Choose patches from the saved replay, before looking at new logits: first empty patch, smallest
positive target, median positive target, high-padding positive patch, and first exposures of7604/7684;
fill to eight unique absolute indices with deterministic representative positives. Save exact indices,
member identities, crop/padding/target hashes and selection reasons. Tiny/difficult cases are represented.
Use the current role policy; no validation case may silently become a training example.

Report foreground/background CE contributions, foreground soft-Dice term, false-positive mass,
reference probability separation and the current class-coefficient ratio. Contrast the current
per-present-class mean CE with plain voxel-mean CE and explicitly specified capped/fixed-weight
counterfactuals on the same logits, as diagnostic arithmetic only. Check loss direction with respect
to a foreground-logit shift; do not call that a model-parameter gradient or proof of a better loss.
Record empty-target behavior and how padding enters each calculation. No candidate loss is adopted
by looking at these scalars. The early unbalanced-loss empty-mask failure remains relevant history.

## Then: one controlled training comparison

Discuss the audit before selecting an exact loss formula/weight/normalization. A candidate should
increase pressure on excessive foreground while protecting sparse targets and recall. Avoid changing
loss, sampler, crop geometry and LR simultaneously. A proposed loss comparison should begin from
the same exact007step300 parent and AdamW state, use sampler300–599 and constant0.00001, and compare
against010's frozen records. This tests a loss change under one specific parent/rate/budget; it is
not a global architecture or learning-rate conclusion.

Require synthetic arithmetic/finite-gradient/empty-target checks, native checkpoint recovery and
exact initial40-mask qualification before a separate launch. Preserve old recipes/requests and
deny consumed replay. Keep coverage guards active from the parent; evaluate all40 at the same
boundaries and113/40 at completion. Freeze resource/read budgets and useful-shrinkage criteria
before running. Report actual stopped prefixes, individual regressions and the existing partial/tiny
references. If no clearly bounded candidate is justified, discuss a higher-rate tail or longer fixed
tail as a separate single-factor alternative; no automatic extension follows.

Sampling is a separate later factor.155/145 foreground/background centers produced290 positive
and only10 empty patches. More background centers alone may not create more negative exposure.
Any future negative-patch policy must qualify its target semantics and preserve each member's
membership/eligibility. Held empty-reference studies do not become trusted negatives by convenience.

FormalG5, lesion containment/cascade, larger cohorts and sealed evaluation remain separate work.
This proposal prepares the next discussion; it does not certify contours, promote a model or commit
the project to a specific counterfactual loss.
