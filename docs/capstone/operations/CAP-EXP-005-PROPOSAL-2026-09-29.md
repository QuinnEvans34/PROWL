# CAP-EXP-005 — expanded cohort smoke proposal

**Superseded planning status:** D-285 completed the machinery and froze the exact request.
Read [the executor handback](EXPANDED-EXECUTOR-HANDBACK-2026-09-29.md) for current status.
Real launch approval remains pending; the original proposal below is preserved.

Status: D-284 resource profile and expanded checkpoint/independent-storage checks passed;
final launch executor integration and transaction tests remain.
No launch request or training authorization is created by this document.

Question: does the existing balanced pancreas-localizer recipe learn across the frozen 16 training
members, and how does it behave on the separate 11 development-validation members? This is an
expanded-cohort smoke, not a controlled single-factor comparison to the two-case CAP-EXP-004.
Validation is small and lacks the arterial/thin-slice stratum. No final-test access or lesion claims.

Proposed fixed recipe: fresh seed42 initialization, existing two-output SegResNet, float32 MPS,
96-cube patch, balanced CE plus foreground soft Dice, AdamW LR0.0003/weight decay0.00001,
cosine schedule. Existing equal pancreas/background-center sampling. No loss, threshold or cohort
change based on the untrained forward profile. Native MPS fallback disabled.

Proposed duration:288 updates,18 complete cycles through16 training members in frozen order.
This gives equal case exposure while staying inside the existing300-update configuration ceiling.
That is much less per-case exposure than the earlier two-case run; failure to learn would not by
itself justify removing difficult cases. Separate subsequent experiments can increase the budget.

Evaluate complete training and validation roles at step0 and288, with fixed step144
inspection (the full27-case forward profile took15.45 s). Do not tune the checkpoint or stopping
rule on these results during the run. Record per-case Dice, precision/recall, foreground-volume
ratio and prediction-only box coverage/scan-volume fraction under the existing fixed10-mm policy.
Report partial-coverage cases individually; never average their difficulties away or claim complete
organ coverage. Empty predictions remain explicit failures. These are development measurements.

Retain checkpoint boundaries0/96/192/288. Bind exact role inventories, v2 recipe, RAM-cache policy,
code/environment, schedule, update history and launch controls. Preserve last complete checkpoint
on interruption; no automatic extension/retry. Final outputs must support source-grid restoration.
Publish case exports individually if the aggregate exceeds the existing artifact-size ceiling;
never silently enlarge storage limits or omit cases to make a terminal package fit.

Before freezing a launch request: finish the real-update authorization/executor wrapper, objective
and localization metrics, production artifact/backup bindings and interruption tests. Insert actual
D-284 full-volume timings, choose the explicit total/update budgets, and pin the final tested source.
The readiness module currently refuses real optimizer updates by design. D-284 proves input/model
and checkpoint mechanics; it does not yet implement this complete experiment transaction.

Measured D-284 budget basis:209.28 s input verification/loading,15.45 s per27-case evaluation,
5.53 GiB peak RSS,191.5 MiB cache. Proposed caps remain600 s for updates,1,200 s total,16 GiB
RSS and existing1-GiB/domain storage increment. Two synthetic update timings (1.085/0.871 s)
are indicative only; supervise the actual run and stop at caps rather than extending them.
