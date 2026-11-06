# Transfer candidates and the route to defensible evaluation

November 6, 2026. Research and audit-scope preparation, not a downloaded/qualified
replacement or GPU launch. No new CT, mask, model-weight, publisher-test record,
workbook or duplicate-image audit was performed. Prior source pins remain intact.

## Recommendation

Keep Universal as an attributed exploratory reference while seeking its lineage.
The best alternative to **audit next** is STU-Net-B pretrained on TotalSegmentator
anatomy. That recommendation concerns the narrower published pretraining source
and useful model scale, not demonstrated lesion accuracy or verified independence.
No alternative reviewed here is certified leak-free. A scratch-initialized model
removes external imaging-pretraining exposure but still requires patient-safe
separation within PROWL's own data.

| Candidate | Published initialization/task | Why consider it | Remaining limitation |
| --- | --- | --- | --- |
| Universal Swin, exact retained checkpoint | Task-trained multi-organ/tumor model, including pancreatic tumor; 62.6M locally loaded parameters | Existing CT-only inference proof and four positive saved results | Shared public sources with PanTS; all four exact patient exposures unknown; no negative screen or PROWL adaptation |
| STU-Net-B, TotalSegmentator-only release | 58.26M convolutional model, pretrained for 104 anatomical targets plus background | More narrowly described source pool; general anatomy transfer rather than an already trained pancreatic-tumor head | Needs new lesion head/training, exact checkpoint and split audit, annotation mapping, rights/load/resource qualification; source/patient separation not yet proven |
| Original MONAI Swin UNETR SSL encoder | CVPR 2022 self-supervision on approximately 5,050 CTs | Similar transformer family; a possible representation-learning initialization | No ready lesion head; unlabeled exposure still counts; exact five-source memberships and downstream checkpoint identity need checking |
| Newer MONAI SSL tutorial weights | Described as roughly 50,000 CT/MR volumes, different from the original 5,050-CT release | Another possible initialization | Broad multi-source pool, no automatic exposure advantage; do not silently substitute it for the original release |
| SuPreM Swin UNETR | General abdominal pretraining, with multiple published variants | Larger-family alternative to the existing SegResNet initialization | Existing source-use review leaves patient membership unresolved; switching its backbone does not clear the underlying data |
| Same architecture from random initialization | No external pretrained image weights | Essential control for the effect of pretraining | May take more training; within-project train/dev patient duplicates and repeated selection still matter |

## Why STU-Net-B is worth inspecting

The [authors' repository](https://github.com/uni-medical/STU-Net) describes
TotalSegmentator pretraining and separate downstream FLARE22, AMOS22 and AutoPET22
fine-tuning. Its base release is `base_ep4k.model`; select that original anatomy
checkpoint rather than a downstream adaptation. The repository advertises 58.26M
parameters and 128-cube pretraining patches. Actual laptop training fit is unknown.

The [paper](https://arxiv.org/html/2304.06716v1) describes a 1,204-image dataset,
104 anatomical targets, and a new randomly initialized head for downstream labels.
It reports a 1,081/57/65 train/validation/test division. Those numbers sum to 1,203,
so do not manufacture a corrected count or membership list: resolve the exact
release/split ledger before execution. Pancreatic lesion is not one of those
original anatomical outputs. A successful pancreas contour is not a lesion result.

The [original TotalSegmentator publication](https://arxiv.org/abs/2208.05868)
describes its CT anatomy dataset, and the
[publisher's dataset release](https://zenodo.org/records/8367088) identifies
University Hospital Basel. Version 2 has 1,228 images/117 structures; it must not
be substituted for the older STU-Net pretraining dataset. This narrower provenance
is promising, but institution names and absence from a short PanTS dataset list
are not themselves proof that no patient or repackaged source overlaps.

Pin source revision, original download, weight digest, exact initialization and
checkpoint-selection split. Check for downstream fine-tuning, inherited weights,
and selection exposure. Retain artifact-specific license evidence. Its older
nnU-Net environment/plan serialization needs isolated qualification, not package
installation in the live project environment or an unsafe pickle fallback.

## Why SSL and another SuPreM release are not automatic fixes

The [original MONAI pretraining README](https://github.com/Project-MONAI/research-contributions/blob/main/SwinUNETR/Pretrain/README.md)
names HNSCC, LUNA16, CT Colonography, COVID-19 CT and LIDC, and links an SSL encoder
checkpoint. The
[current tutorial](https://github.com/Project-MONAI/tutorials/blob/main/self_supervised_pretraining/swinunetr_pretrained/README.md)
instead documents approximately 50,000 CT/MR volumes and a broader source list.
These are different releases. Do not describe a BTCV-fine-tuned model as the pure
SSL initialization. Removing labels during pretraining does not make previously
seen evaluation images independent. Original patient/series membership remains
the relevant comparison, including nested datasets.

The [SuPreM release table](https://github.com/MrGiovanni/SuPreM) distinguishes
architectures and initialization variants. The retained
[SuPreM provenance review](SUPREM-PUBLIC-PROVENANCE-REVIEW-2026-10-06.md) already
records missing patient-specific separation. There is no basis to assume that a
different SuPreM architecture has a clean evaluation pool.

## Correct audit population: 1,333 train and all 75 development cases

Both reported development counts have a valid historical scope. The protected
[portable cohort](../data/PORTABLE-COHORT-2026-10-12.md) has 1,333 train and 75
development-role cases. The retained KD source manifest has the same 1,333 training
members and a 70-member development subset. Historical design retained five
uncertain-case exclusions without editing the original 75-member registry.

The two named metadata files were checked here, without opening their image
members. The [scope record](TRANSFER-AUDIT-SCOPE-20261106.json) binds their hashes,
exact membership-set relationship and the five cases outside the KD subset:
922, 5105, 5370, 7299 and 7523. They remain visible in the provenance audit; this
does not re-admit them for scoring or settle their annotation uncertainty. Existing
reference-state labels are not independent annotation adjudication.

Do not conflate a two-file membership reconciliation with a completed original-source
or duplicate audit. The portable identity records retain limited identity assurance.

## Auditing Universal, or any alternative

1. **Fix the artifact first.** Bind the exact checkpoint and all inherited image
   pretraining. Obtain its train and checkpoint-selection case lists, or sufficiently
   specific publisher evidence. Published code defaults are supporting evidence,
   not a training receipt for a released binary.
2. **Inspect metadata schema, then allowed rows only.** Check whether retained
   publisher metadata can map the 1,408 permitted train/dev aliases to original
   dataset/release, case/series and stable patient group. The existing JSONs lack
   that crosswalk; this does not establish that the publisher workbook or authors
   lack it. A mixed-partition workbook needs a bounded permitted-row reader; do
   not open test rows or payloads as a shortcut. Preserve an immutable crosswalk
   with evidence/hash and confidence per mapping.
3. **Join patients and nested sources, not just filenames.** Check series, repeated
   phases/timepoints and renamed/reoriented cases. Existing exact source hashes
   can confirm byte identity but cannot clear different files. Reuse prior duplicate
   evidence first; any additional voxel-based fingerprinting needs its own bounded
   read/compute plan. Do not acquire entire source collections just to hash them.
4. **Separate decisions by role.** Pretraining overlap with PROWL train-role cases
   is not evaluation leakage. An evaluation patient used in external training or
   selection cannot be labeled verified unseen. Keep `confirmed_seen`,
   `verified_unseen` and `unknown`, with reasons. Unknown is not a pass. Freeze
   grouping and eligibility before scores, preserve old cohorts/results, and
   never drop bad-scoring cases to obtain a clean-looking average.
5. **Keep a final evaluation out of the loop.** A repeatedly used development
   cohort remains development even after provenance improves. Select the system
   on designated development data, freeze it, and evaluate the final cohort once.
   Clinical independence also depends on annotation quality and deployment scope;
   pretraining separation alone does not qualify clinical use.

## The PanTS external route is a service, not the public 901-case split

The [current official README](https://github.com/MrGiovanni/PanTS#external-out-of-distribution-test-set)
distinguishes 9,000 public training cases, the 901-case in-distribution test set,
and external out-of-distribution evaluation. The latter asks for a model checkpoint,
testing script, in-distribution results and usage README; the team evaluates on
three external sets and an RSNA dataset. It is not an invitation to download a
new final holdout and tune against it.

This is a promising final-evaluation route, conditional on the authors confirming
separation from the exact pretrained checkpoint, its upstream initialization and
any model-selection exposure. Being external to PanTS training does not establish
being external to every pretrained model. Local protected-test permission and
submission prerequisites remain separate; no protected test was run or submitted.

Questions to prepare for the publishers (not sent):

- Universal: which original train/selection patients and inherited image weights
  produced checkpoint SHA `cde35d9ca344a744c849ebe0cd086cb64984e79f605376c56bd04531c767ed07`?
- PanTS: is there a permitted alias-to-original patient/series crosswalk for our
  fixed train/dev list, and can the external evaluation establish checkpoint-specific
  non-overlap before we commit a frozen submission?
- STU-Net: does the exact TotalSegmentator base checkpoint contain only the declared
  anatomy pretraining, and what case/selection ledger and artifact terms bind it?

## Smallest useful next comparison

Audit the original STU-Net-B release and Universal lineage in parallel as research,
without another GPU experiment. If STU-Net-B separation can be established, freeze
one short train-role-only lesion adaptation and compare it with the **same
architecture from scratch**, keeping the cohort, head, preprocessing, sampling,
selection policy and evaluation fixed. This tests transfer benefit rather than
confounding architecture and prior task training. Report runtime as well as updates;
it is not automatically a perfectly compute-matched comparison.

Do not start with the 440M/1.46B variants: their training fit and value on the
laptops are unmeasured. A bounded base-model pilot must establish memory, throughput,
recovery and native prediction geometry before a long run. Keep Universal's saved
four-case result as its original exploratory reference. A teacher/KD use requires
the same exposure audit; distillation does not erase a teacher's evaluation exposure.
