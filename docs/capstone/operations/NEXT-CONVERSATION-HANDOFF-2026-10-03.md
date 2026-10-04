# PROWL new-conversation handoff — October 3, 2026

This handoff follows Quinton's Saturday retrospective request. Official Week 1 starts Monday,
October 5. Read the [retrospective](PRECOURSE-RETROSPECTIVE-2026-10-03.md) before proposing new work.
It contains recommendations for discussion, not approvals for a new launch or whole component.

## Copyable opening prompt

> We are continuing PROWL, my approved capstone. Start by reading AGENTS.md, the workspace safety
> agreement, CURRENT-CHECKPOINT.md, PRECOURSE-RETROSPECTIVE-2026-10-03.md and
> NEXT-CONVERSATION-HANDOFF-2026-10-03.md in docs/capstone/operations/. Verify the existing checkout
> before edits. Class starts October 5; help me consolidate the weekend work and choose Week 1
> priorities. CAP-EXP-014 is complete under D-335; no run is pending and consumed requests must not
> be reused. We can train both stages, but we do not yet have useful contours or an autonomous
> localize-then-segment baseline. First give me your understanding and discuss the next priorities.
> Likely next tasks are reviewing a concrete Git checkpoint and preparing a bounded segmenter
> duration/coverage comparison, not automatically launching training. Keep this conversational:
> explain evidence and your judgment, document decisions in Markdown, then implement the agreed
> bounded work. Preserve difficult cases and all original membership. Claude owns its separately
> dispatched retrieval lane; confirm its latest handback before touching reserved work. I want to
> know what is going on and what you change. Do not contact publishers or other people for me.

## First reads and authority

1. `AGENTS.md` and [WORKSPACE-SAFETY](WORKSPACE-SAFETY.md).
2. [CURRENT-CHECKPOINT](CURRENT-CHECKPOINT.md): D-335 at the top is current; successive older
   paragraphs are retained history and may describe requests that were later consumed.
3. [CAP-EXP-014 results](CAP-EXP-014-RESULTS-2026-10-03.md) and the retrospective above.
4. [Capstone README](../README.md), [MASTER-PLAN](../MASTER-PLAN.md),
   [Week 1](../weeks/WEEK-01.md) and [DECISIONS](../DECISIONS.md).
5. Targeted evidence below as needed; do not reread hundreds of historical records indiscriminately.

Proposal v3.8 and Technical Appendix v3.1 outrank older drafts. Their root Word files are
`Evans_Quinton_PROWL_Capstone_Proposal_v3.8.docx` and
`Evans_Quinton_PROWL_Capstone_Technical_Appendix_v3.1.docx`; approved hashes are respectively
`00546c805f0f49df2bf11cf452dc29171ede49e6931f23f5186562e39e613612` and
`6c26f2ae2652c32c0fa444cc10bc608ae4a81aab5c7970c294ce4f031f2b64e3`.
Later explicit decisions amend implementation choices. The previous five-week project is history.

The approved outcome is an autonomous pancreatic-lesion annotation-assist workflow with new models,
source controls, measured evaluation, literature retrieve/cite/refuse support and recorded human
review. No diagnosis, clinical certification or guarantee of good model metrics. File-first artifacts
are authoritative; approved literature-only PostgreSQL/pgvector is a supporting implementation choice.
PANORAMA integration is committed but is not a prerequisite to qualified PanTS-only experiments.

## Workspace and native checks

Authoritative checkout:
`/Users/quintonevans/Desktop/Quinn/Desktop-Quinn/GitHub/PROWL`.

Before edits, run from that explicit directory:

```sh
pwd
GIT_OPTIONAL_LOCKS=0 git rev-parse --show-toplevel
python3 scripts/diagnostics/check_workspace.py
GIT_OPTIONAL_LOCKS=0 git status --short
```

Use `.venv-prowl/bin/python` for project tests/dependencies; system Python is not the test environment.
This is a native Mac/MPS workspace. Missing paths mean resolve relocation, not recreate/symlink them.
Inspect existing changes and configuration; do not overwrite them. Use registered artifact/backup
roots and exact stage permissions; the registry is not a blanket grant for arbitrary source jobs.
Do not delete failed evidence, reset quotas, bypass refusals or upgrade dependencies casually.

Latest recorded full native baseline: **2,933 tests**. CAP-EXP-014 ran against **142 frozen producing/
test source pins**. No implementation source changed in the retrospective and it did not rerun tests.
Markdown/navigation changes do not authorize changing those pins or rewriting prior results.

## Current execution state — D-335

CAP-EXP-014 and its independent cold recovery completed. Both requests are consumed. Nothing is
running or pending; no extension, imported weights, model promotion, source activation or follow-up
model/source job was approved by the retrospective. Current v5 real runtime cap remains 48 updates.

- Fresh seed42 SegResNet; 144³/batch1; six train members `3,26,2232,2973,5821,6238`;
  report-only `2514`. Provided-pancreas-reference ROI, zero jitter, AdamW LR0.0003/decay1e-5,
  constant schedule; 48 updates/eight exposures each. Checkpoint/evaluation0/6/24/48, terminal48 primary.
- Controlled change versus CAP-EXP-013: CE allocation/reduction v3 → per-case present-class mean
  CE v5; foreground Dice and substantive input/initialization controls unchanged.
- Five declared training-only screens pass. Native train pancreas Dice0.159877, lesion Dice0.055142,
  lesion recall0.833063; all six lesion components hit. Predicted/reference lesion volumes
  12.78–383.26×; precision0.0026–0.0450. A component hit is not complete coverage.
- Report-only2514 pancreas Dice0.333197; lesion Dice0.006397 and recall0.123936, a major decrease
  versus prior0.025448/0.974468. Do not tune against2514 or omit this failure.
- No useful-contour, specificity, biological patient-independence or generalization claim. All real
  pilot lesion references are positive; invented negative fixtures do not establish clinical specificity.
- Combined producer/recovery supervision525.229s (8.754min). Producer supervisor RSS4.790GiB,
  worker peak4.822GiB, MPS driver4.776GiB. Exactly48 real updates,14 original target reads,
  zero original CT reads. The target grant is consumed.
- Four checkpoints/14artifacts, seven native exports, 387physical files across three copies checked;
  seven native predictions exact and four probability probes delta0. Seven sheets reviewed.
- Real cold recovery performs zero optimizer calls and zero original reads. Primary Python paths/
  descriptors were cooperatively blocked, not OS-unmounted. Next-update tolerance7.45e-9 was proved
  separately in invented rehearsal; do not claim a real cold next update occurred.

Saved terminal training loss still declines (epoch means2.037188→1.692695; ratio0.830898), and
training tensor pancreas/lesion overlap improves through the last measured checkpoint. These are
grounds to discuss a fresh longer-duration hypothesis, not proof of convergence or launch authority.
Qualify any new runtime, budgets, coverage/false-positive policy and exact request separately.

Exact CAP-EXP-014 pins:

| Record | SHA-256 |
|---|---|
| Request | `e63f5613085bf202bbb1157616afc7492f84e0855e81d243dd3981ed41ec4a10` |
| Actual capability transport | `5dfc16d148d159d4edb2b5fcd2109957deb519821871f118c958e8a9b9e53b51` |
| Producer package | `94e4e3daff66d50c582bd30b66a78259d2ef1597af74c764269155c45939c260` |
| Cold package | `d52c445ddc1646c6d352dff5585118bb50ac73ca812dafc700a8738fd655c687` |
| Terminal weights | `6e63d135eea06bf8f60c21a66214890a0734406a614a9a2302691ca84f5096a3` |

Capability transport hash and canonical semantic identity are distinct; do not substitute one for the
other. Primary review controls are under `outputs/prowl/CAP-EXP-014-PREPARED-20261003` and
`outputs/prowl/CAP-EXP-014-PREPARED-20261003-RECOVERY`; associated independent-audit,
before-after, visual-review, history and control-preservation JSONs are under `outputs/prowl/`.

## Preserved evidence and Git debt

D-335 controls were independently preserved:201files/3,447,022bytes, including142 producing/test
sources, at `/Users/quintonevans/PROWL-Backups/segmenter-v5-runs-keepers/controls-D335-20261003`.
Manifest SHA `f7873871de89ddcee42c4be2776a4328192fb289dcabcdc625347016ea431458`.

Final whole-backup inventory17,341,924,636bytes; fixed D-335 ceiling18,318,645,873bytes;
remaining976,721,237bytes. Registered20GiB unchanged. No deletion/reset. A future request must
account for existing evidence plus its own primary/keeper/restore/control payloads.

Latest Git commit is September28 `21f838c`; substantial later code/docs are uncommitted/untracked.
Independent experiment protection does not equal complete repository publication. Recommended next
bounded task: review the exact permitted Git snapshot and obtain approval for that concrete commit/
push. Old approvals for previously published snapshots do not silently publish this one. Exclude raw
imaging, secrets, private evaluation items and large scratch artifacts; preserve ignored evidence
separately. No commit/push occurred during the retrospective.

## Localizer and data context

Original protected base membership remains7200train/1800validation/901publisher-test. Preserve
original membership permanently; permissions are purpose-specific, and training consumes frozen
positively qualified descendants. A study-as-subject implementation is not proof of biological patient
uniqueness. Preserve historical prior-project test exposure disclosures; do not spend publisher test
to select new settings.

Localizer:176candidates →113train/40development-validation qualified,23holds (15CTunits/8empty
references). Difficult cases remain. Current full cache is2mm/144³. Latest relevant
[CAP-EXP-012](CAP-EXP-012-RESULTS-2026-10-01.md) validation Dice0.129078/recall0.962519,
median volume14.2596×, ROI size/box screen15/40, boxes≥.995reference39/40. Usefulness endpoint
failed; no adopted policy. [Structure audit](LOCALIZER-STRUCTURE-AUDIT-RESULTS-2026-10-01.md):
dominant foreground remains oversized; hypothetical largest-component-only size improvements lack
component-containment proof. Do not adopt cleanup based on size alone.

Segmenter: [D-320 freeze](SEGMENTER-COHORT-FREEZE-RESULTS-2026-10-01.md) retains12candidates,
7positive qualifications and5holds. Train6110/4965 and validation2727/7265 have empty lesion
references with unresolved negative meaning; validation5641 has unresolved annotation relationships.
No refill/reassignment. Pancreas-only qualification cannot automatically grant lesion training.
Shared geometry/cache/native scoring were subsequently qualified; use their versioned consumers.
Current segmenter inputs are reference-derived ROIs, not predicted localizer output.

## Parallel work and remaining commitments

- Claude retrieval: read [RUNNING-LOG](../retrieval/planning/RUNNING-LOG.md) and confirm a newer
  handback if Quinton has one. Last local P2 application review still has whole selection policy
  unapproved, provisional seed choices, proposed new workflow candidates, optional reserves and
  second family-2 seed scope unresolved. PANORAMA PDF record remains unsigned/deferred. Codex
  recommendations are not Quinton approvals. P1 frozen25needs; P3 synthetic accepted with182
  retrieval tests at its review. Live acquisition/index/measured retrieval are not complete.
- P4 database/dependency phases keep their separate gates, including psycopg3. Literature-only
  PostgreSQL/pgvector approval is not proof the service was installed or populated.
- PANORAMA integration still owes source/mapping/exclusion/duplicate controls and qualified loading.
- Full Plan04 tool spike/restartable DAG has not been completed by the individual run transactions.
  Its explicit implementation authorization still applies.
- UI has an existing foundation; synthetic viewer-stub tests do not establish real new-model/NiiVue
  alignment, durable reviewer events or end-to-end product acceptance.
- Stakeholder participant/session evidence is not currently confirmed in these records. Quinton
  owns outreach. The [PanTS publisher draft](../data/PANTS-PUBLISHER-EMAIL-DRAFT-2026-09-28.md)
  is for him to send; do not send on his behalf.
- Final autonomous/provided-region evaluation, verified-negative specificity, baseline-derived
  comparison, literature metrics, stakeholder review, integration and release remain committed.

## Recommended first discussion

Confirm the retrospective with Quinton, then agree Saturday/Sunday and Week1 priorities. Suggested
order: concrete Git preservation review; accurate Monday progress account/course requirements;
fresh bounded segmenter duration proposal; next ROI-containment/cascade integration evidence;
varied multiclass/negative qualification plan; current Claude handback and remaining product lanes.
Do not recreate broad investigations of unchanged evidence or launch a long run automatically.

Official milestones: Week1architecture/testing; Week2protectedcohorts; Week3PANORAMA;
Week4DAG; Week5autonomousbaseline/queryableliterature; Week6controlledcomparison/evaluation;
Week7UI/stakeholders; Week8integration/frozenevaluation; Week9buffer; Week10delivery.
Preserve Week8completion and Weeks9–10. Early training is permitted by applicable gates; model
convergence before Monday is not a course-start requirement found in the approved sources.

Quinton prefers a candid, conversational collaboration: explain what evidence means, state your
judgment, discuss consequential choices, record agreed decisions in Markdown and then execute
bounded implementation. Existing autonomy is not blanket permission to rerun consumed requests,
contact people or infer new scientific/phase approvals. Tell him what changed and what remains.
