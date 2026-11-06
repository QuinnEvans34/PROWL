# What the Universal checkpoint demonstrates, and whether PROWL can use it

Research date: November 6, 2026. This supplements the earlier provenance plan;
it does not clear the model for independent evaluation, replace a frozen design,
or authorize another execution. Only publications, existing model source and
retained evidence were read. No new inference, training or protected-data access.

## Direct answer

We downloaded an already task-trained pancreas/tumor segmenter and ran it unchanged
on four positive cases. The learned capability belongs to its authors. PROWL
implemented local execution, native-coordinate restoration, evaluation, supervision,
tracking and backup checks. That is an engineering feasibility result, not evidence
that PROWL trained a better model or discovered a new segmentation method.

Honest result description:

> We evaluated the authors' released CLIP-Driven Universal Swin UNETR checkpoint
> without fine-tuning on four positive, exposed-development PanTS cases. Mean
> native lesion Dice was .710754. Exact pretraining/model-selection exposure of
> these cases is unknown; negative-case performance was not measured.

The .710754 must not be described as a clean held-out score, a PROWL-trained
result, an architecture-only gain, or a direct improvement over the 70-case KD
aggregate. Preserve the original result rather than deleting or rebranding it.

## Authorship and identity

It is **City University of Hong Kong**, not the University of Hong Kong. The
official repository lists Jie Liu at CityU, Yixiao Zhang/Jie-Neng Chen/Alan Yuille/
Zongwei Zhou at Johns Hopkins, and Yucheng Tang at NVIDIA among its contributors.
There are additional collaborators and version-dependent affiliations. This is
academic coauthorship; it does not imply NVIDIA product approval or endorsement
of PROWL. See the [pinned official README](https://github.com/ljwztc/CLIP-Driven-Universal-Model/blob/43c12399cc98a40f447342a8dc2cecae5edae84c/README.md).

The original work is *CLIP-Driven Universal Model for Organ Segmentation and Tumor
Detection* (ICCV 2023). A related expanded journal article appeared in Medical
Image Analysis in 2024. We retain an exact source revision and exact checkpoint
hash, not an assumption that every result in both publications describes the same
binary. The [source/model audit](UNIVERSAL-SWIN-OVERNIGHT-20261105.md) records those
identities and strict loading without missing/randomly filled parameters.

There is an important version distinction: our pinned implementation has one
shared `controller`; the journal extension describes independent class-specific
MLPs. Therefore citing the later paper does not establish that the downloaded
binary implements every later extension. This is a source/paper comparison, not
an inference about an undocumented training command.
[Pinned model class](https://github.com/ljwztc/CLIP-Driven-Universal-Model/blob/43c12399cc98a40f447342a8dc2cecae5edae84c/model/Universal_model.py),
[journal extension, sections 2.5 and 3.2](https://arxiv.org/html/2405.18356v1).

## What it was taught and what it outputs

The [original paper](https://arxiv.org/html/2301.00785v3) describes supervised
learning across fourteen public CT datasets with partial organ/tumor annotations.
Source families include Pancreas-CT, LiTS, KiTS, AbdomenCT-1K, CT-ORG, CHAOS,
MSD CT tasks, BTCV, AMOS and WORD. MSD includes direct pancreatic-tumor supervision.
This is not merely a general organ backbone or a model encountering pancreatic
lesions for the first time in PROWL. Not every scan supplies every target label.

**Count clarification:** the journal abstract loosely describes 3,410 training
volumes, but section 4.1.1 explicitly divides the 3,410 development volumes into
**2,100 training and 1,310 validation**. Earlier PROWL shorthand saying "3,410
training CTs" should be read with this correction. These are publication-level
counts, not a verified manifest for our binary. Exact training, inherited
initialization and model-selection membership remain missing.
[Journal experimental setting](https://arxiv.org/html/2405.18356v1#S4.SS1.SSS1).

The released template has 32 outputs: 25 anatomical structures, six tumor targets
and kidney cyst. Organs include pancreas, liver, kidneys, spleen, stomach, bowel,
adrenals, lungs, vessels, bladder and femoral heads. Tumor targets are kidney,
liver, pancreas, hepatic vessel, lung and colon. Our screen retained pancreas
(class 11) and pancreatic tumor (class 28), indexed 10/27 internally.
[Official label mapping](https://github.com/ljwztc/CLIP-Driven-Universal-Model/blob/43c12399cc98a40f447342a8dc2cecae5edae84c/utils/utils.py).

These are voxel-wise sigmoid scores converted into masks, not a free-text answer,
pathology determination, tumor-subtype diagnosis or validated patient cancer risk.
Channels can overlap; they are not a mutually exclusive 32-class diagnosis.
CLIP supplies stored embeddings of class names, not a conversational interface
or image-specific clinical reasoning. Pancreas and tumor were known output tasks
before we downloaded the checkpoint.
[Authors' explanation of text embeddings](https://github.com/ljwztc/CLIP-Driven-Universal-Model/blob/43c12399cc98a40f447342a8dc2cecae5edae84c/documents/common_paper_questions.md).

## Why our current evaluation cannot establish generalization

The [PanTS paper, section 3.2 and Appendix A](https://arxiv.org/html/2507.01291v1)
describes a public partition assembled from earlier public datasets, including
several Universal source families. Our custom development split comes from that
partition. A new split or a later dataset name does not erase upstream exposure.

The [completed retained-crosswalk review](UNIVERSAL-SWIN-RETAINED-CROSSWALK-20261106.md)
found no original collection/patient/series mapping for any of the four cases.
Published training lists contain Pancreas-CT and MSD pancreas filenames, but no
checkpoint-bound ledger establishes which lists, selections or inherited weights
produced this binary. The checkpoint's identifiable tensor state does not provide
that missing lineage.

Thus shared source datasets are confirmed; exact patient overlap is unknown.
Different hashes, aliases, annotation versions or orientations cannot certify
independence. Replacing the output head or fine-tuning also cannot make a previously
seen evaluation CT unseen. Case 6755/2889 linkage is separately unresolved for the
larger development cohort. Do not infer independent patients from case IDs.

Apply the same standard to the earlier SuPreM initialization and KD teacher;
their prior exposure limitations do not disappear because Universal is the new
candidate. Existing teacher-assisted/exploratory labels remain. This research
does not newly classify those older cases as seen or unseen or rerun their audits.

Our screen also changed architecture, pretraining, normalization, spatial sampling
and inference context relative to the student. It selected four positives by
predeclared physical-unit eligibility. That avoids choosing high scores after
inference, but the eligibility subset is still small and not representative of
negative-case errors. None of these limitations is repaired by averaging .71.

## Usability has three separate decisions

| Use | Current position | Requirement |
| --- | --- | --- |
| Attributed research reference/baseline | Appropriate description of the completed screen | Disclose pretrained authorship, exposure unknown and four-positive scope |
| Claim of independent accuracy or superiority | Not supported | Reliable evaluation separation, fair scope, fixed cohort/metrics and patient grouping |
| New PROWL transfer-learning experiment | Candidate, not yet qualified | Frozen train/eval lineage, actual adaptation, training/resource/recovery checks and baseline comparison |
| Substitute unchanged publisher weights for capstone-created trained model | Does not satisfy the current lineage contract by itself | Actual capstone training/model record or an explicit agreed scope change |
| Public redistribution/commercial deployment | Not cleared by this research | Artifact-specific rights and appropriate validation; do not infer permission from a repository label |

Using attributed third-party pretraining is an ordinary transfer-learning design.
Scientific value comes from an answerable experiment and sound evaluation, not
from pretending the initialization was ours. Possible PROWL contributions include
qualified laptop adaptation, error analysis, reproducible full-CT inference and
reviewer workflow integration. Merely changing a filename, training briefly, or
obtaining a higher score does not establish novelty or independent performance.
The [capstone lineage contract](../imaging/MODEL-LINEAGE-AND-TRAINING.md) distinguishes
permitted third-party initialization from a capstone-created trained model and
prohibits contaminated protected-evaluation use.

The weight repository shows an MIT tag but an empty substantive model card; the
pinned source LICENSE states CC BY-NC-ND 4.0. These are separate artifact records,
not interchangeable grants. CC's deed restricts sharing adapted material and
commercial use. Keep weights/adaptations private and resolve exact rights before
publishing a model or redistributing upstream code. This is a record of stated
terms, not blanket legal clearance.
[Weight card](https://huggingface.co/ljwztc/CLIP-Driven-Universal-Model),
[source license](https://github.com/ljwztc/CLIP-Driven-Universal-Model/blob/43c12399cc98a40f447342a8dc2cecae5edae84c/LICENSE),
[CC deed](https://creativecommons.org/licenses/by-nc-nd/4.0/).

## Recommended decision

Keep Universal as an attributed pretrained comparator and a conditional adaptation
candidate. Do not launch a long fine-tuning run or advertise .71 as the new clean
project score before provenance is resolved.

Minimum next evidence is a PanTS-to-original collection/patient/series crosswalk
and an exact-checkpoint training/selection/inherited-pretraining ledger, or an
authoritative publisher statement sufficient to establish evaluation separation.
Those questions can be prepared for the dataset/model authors; no message has
been sent to them. If lineage cannot be resolved, use a separately justified
source/patient-disjoint evaluation cohort or an initialization with auditable
separation. Random resplitting or encoder-only loading is not a workaround.

After clearance, freeze a balanced untouched-checkpoint baseline and one bounded
adaptation with the same evaluation. Report all failures and negative-case errors,
selected and terminal checkpoints, and the changed factors. Preserve a genuinely
untouched final cohort. The [next-study draft](UNIVERSAL-SWIN-PROVENANCE-AND-NEXT-STUDY-20261106.md)
is conditional on those requirements, not an authorization to reuse the consumed
four-case permit. This research creates no training run, model promotion or
duplicate training-hours record.
