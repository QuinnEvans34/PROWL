# SuPreM public provenance review — October 6, 2026

## Phone handback

1. **Finished:** official public-source review and the linked
   [checkpoint-inspection draft](SUPREM-CHECKPOINT-INSPECTION-PACKET-2026-10-06.md).
   The publisher's checkpoint SHA-256 exactly matches our retained D-326 candidate record.
   Current local file identity, serialization and protected-evaluation separation remain open.
2. **Files/checks:** two new Markdown documents and this chat's AGENTS/queue/notebook pointers;
   Trello W01-10 records the review. Static checks and final tracking readback are recorded below.
   No checkpoint file was statted, hashed, downloaded or decoded; successful tests were not repeated.
3. **Decision:** the recommended next coding slice is SUP-02A, an invented-file, metadata-only
   checkpoint inspector. Actual-file inspection is a subsequent exact request. Neither step
   grants initialization, model execution or training permission.
4. **Restart:** review SUP-02A's four-file allowlist, read limits and refusal cases in the packet.
   In parallel planning, resolve the pretraining/model-selection membership relationship to the
   protected PROWL development/test roles before any scientific use of this candidate.

Authority: Quinton said “Great, move to the next” after SUP-01's handback recommended public
provenance/license/pretraining-data review and a bounded actual-file inspection proposal.
This authorizes that review and draft only. Earlier handbacks retain their historical statuses.

## Identity: substantially stronger evidence, still a recorded candidate

The [official SuPreM repository](https://github.com/MrGiovanni/SuPreM) links its SegResNet
2,100-CT release to the publisher's Hugging Face weight repository. Its
[exact file page](https://huggingface.co/MrGiovanni/SuPreM/blob/main/supervised_suprem_segresnet_2100.pth)
publishes:

| Field | Public metadata / retained evidence |
|---|---|
| Publisher / collection | MrGiovanni / SuPreM |
| Artifact | `supervised_suprem_segresnet_2100.pth` |
| File revision shown | `d578cce`, upload of three files; short revision only |
| Published SHA-256 | `2db81dc05cd9ea7234ca75e921e53e32b8716dc4cba88a6710742bfc282589a3` |
| Public display size | 56.5 MB, rounded |
| D-326 recorded size | 56,500,623 bytes; exact local historical record |
| D-326 category / import flag | `third_party_weights_not_approved_for_this_run` / `false` |

The hash matches exactly. This is strong evidence that D-326 recorded the publisher's released
artifact, rather than a prior-project fine-tuned checkpoint. It does not establish present local
file identity. Public Xet hash is a different identifier; the ordinary published SHA-256 above is
the comparison value. The public pickle scanner lists tensor reconstruction, FloatStorage and
OrderedDict imports. Its safety label is not a local resource or serialization qualification.
These observations come from file-page metadata, not a download or binary inspection.

Retained control read:
`outputs/prowl/SEGMENTER-CHECKPOINT-INVENTORY-20261002/result.json`, SHA-256
`994e2a13b99e04c8b1f3d8dee176ef04f7146db77fa5fe6254f851aac4b3fe3d`.
No inventory member was reopened. SUP-01's
[85-check invented audit](SEGMENTER-INITIALIZATION-AUDIT-RESULTS-2026-10-06.md) remains unchanged.

## Terms: distinguish code, weights and datasets

The [weight repository's README metadata](https://huggingface.co/MrGiovanni/SuPreM/blob/main/README.md)
declares `apache-2.0`; it contains no substantive model card. This is a publisher declaration for
the weight collection. The [Apache 2.0 text](https://www.apache.org/licenses/LICENSE-2.0) permits
modification/distribution subject to its conditions, including license/notices and changed-file
attribution. The [SuPreM code LICENSE](https://github.com/MrGiovanni/SuPreM/blob/main/LICENSE)
instead declares CC BY-NC-ND 4.0. The
[Creative Commons deed](https://creativecommons.org/licenses/by-nc-nd/4.0/) distinguishes
noncommercial use from distribution of modified material.

**Assessment:** the two artifacts have different stated terms; this is not automatically proof
that either declaration is invalid. Do not copy upstream code or apply the GitHub license to all
weights by assumption. Record the exact weight declaration and provenance when proposing local
inspection. Checkpoint use and any later distribution need an explicit artifact-specific rights
record; this review does not settle every underlying right or authorize publication. No author
contact is required or sent by this packet. Quinton retains outreach ownership.

The [AbdomenAtlas 1.0 Mini dataset card](https://huggingface.co/datasets/AbdomenAtlas/AbdomenAtlas1.0Mini)
has its own CC BY-NC-SA label and gated academic/research terms, including redistribution
restrictions. It is a different dataset/version from the exact 2,100-case checkpoint training
subset. Its terms cannot be substituted for that subset's complete source-data provenance, and
our review did not accept the gate or access its data. A model's weight license does not grant
dataset acquisition rights.

## Pretraining and evaluation separation

Reference: Wenxuan Li, Alan Yuille and Zongwei Zhou, *How Well Do Supervised 3D Models Transfer to
Medical Imaging Tasks?*, ICLR 2024; reviewed
[arXiv HTML v1, January 20, 2025](https://arxiv.org/html/2501.11253v1).
Section 3.2 / Appendix B.1.2 describe a 2,100-CT benchmark pretraining variant, 32 organ/tumor
outputs and held-out model selection, distinct from a 9,262-CT direct-inference variant. The
paper's main text says 1,310 selection cases; Appendix B.1.2 says 310. The larger AbdomenAtlas
collection combines public sources, including MSD and RSNA trauma; the exact subset and
selection membership are not resolved by those aggregate descriptions.

The [authors' FAQ](https://raw.githubusercontent.com/MrGiovanni/SuPreM/main/document/frequently_asked_questions.md)
states that JHH was unseen during pretraining in their described transfer experiment. That
supports the general-pretraining interpretation, but does not provide a candidate-specific
membership crosswalk to PROWL's protected cases. The
[pancreatic downstream example](https://raw.githubusercontent.com/MrGiovanni/SuPreM/main/target_applications/pancreas_tumor_detection/README.md)
uses the released weights as input and creates a separate downstream model; do not substitute
that downstream model for the original release. Neither a later PanTS release date nor a common
institution proves patient/scan separation.

**Assessment:** no reviewed public record establishes contamination of PROWL's protected cases;
no reviewed record proves complete separation either. The source remains unresolved for scientific
use. Require either a checkpoint-bound training AND model-selection manifest with a reliable
crosswalk, or sufficiently specific publisher evidence establishing separation for the protected
roles. Case-name inequality alone is inadequate across renamed datasets. Keep the original
7,200/1,800/901 roles and all holds. Do not filter or reshuffle cases to make this source appear
clean. Future RSNA evaluation also needs a separate overlap assessment.

## Architecture and serialization expectations

The [public downstream SegResNet code](https://raw.githubusercontent.com/MrGiovanni/SuPreM/main/target_applications/totalsegmentator/train.py)
specifies one input, 16 initial filters, down blocks [1,2,2,4], up blocks [1,1,1] and zero dropout.
Its loader reads `net`, removes a leading namespace and excludes the final task convolution.
That supports our architectural hypothesis; it is not a full local tensor match or a suitable
replacement for our reject-before-load audit.

The [current public pretraining writer](https://raw.githubusercontent.com/MrGiovanni/SuPreM/main/supervised_pretraining/train.py)
saves a container with `net`, `optimizer`, `scheduler`, `epoch`; its distributed path can produce
prefixed model keys. These are expectations from mutable current code, not observations of the
released checkpoint. Inspect and report the actual wrapper; never resume that optimizer/scheduler.
Do not drop unknown model tensors or broaden namespace normalization automatically.

[PyTorch's serialization documentation](https://docs.pytorch.org/docs/main/notes/serialization.html)
describes metadata inspection using FakeTensorMode and restricted `weights_only=True` loading,
while explicitly noting resource/safety limitations. Any future reader must qualify those APIs
against our installed, pinned environment with invented files; no unrestricted fallback or custom
pickle-global additions are proposed. SUP-01 is invented-only and cannot accept actual weights
by relabeling their controls.

## Source-access limits and remaining evidence

Reviewed on October 6, 2026 using public HTML/text. Main-branch pages are mutable; no full upstream
code commit was obtained. The file page supplies the short upload revision and published content
hash. Attempts to fetch full GitHub/Hugging Face commit/API metadata through the web tool failed;
two bounded, read-only JSON requests from the shell also failed DNS resolution. Those requests
wrote no response files and fetched no binary endpoints. Report gaps rather than invent a pin.
No exact checkpoint-bound source membership list or patient crosswalk was verified.

| Gate | Present evidence | Remaining condition |
|---|---|---|
| Recorded released-file origin | Exact published SHA agrees with D-326 | Current local identity check under a fresh scope |
| Weight terms | Publisher Apache 2.0 metadata located | Scoped rights record; attribution/publication decisions when applicable |
| Pretraining/selection separation | Paper and FAQ support general abdominal pretraining | Candidate-bound separation evidence for protected roles |
| Architecture | Local definitions and public constructor agree | Actual complete name/shape/dtype/storage inventory |
| Serialization | Public scanner and writer expectations | Invented reader qualification, then exact local metadata inspection |
| Initialization/recovery | 85 invented in-memory audit checks | Separate real-source auditor and versioned pretrained session/recovery |

**Recommendation:** SUP-02A can advance useful engineering without the drive or a scientific
launch. Keep the varied multiclass/development/verified-negative
[metadata scope](VARIED-MULTICLASS-GAP-INVENTORY-2026-10-06.md) visible while separation is resolved.
The 192-update scratch duration comparison stays a different question. Do not silently combine
pretraining, cohort expansion and duration in a result described as changing one factor.

## Verification and stop

Final static verification passed:16existing source/test/design/contract/control/lock pins match;
159local Markdown link occurrences resolve across both documents and the three pointers. The
protected historical notebook marker-to-end SHA-256 remains
`df37ba7cdec1ae1fb941feb5e60a87ef599f28118d5415a50032397bbe96b997`.
Scoped `git diff --check`, new-document whitespace and newline checks pass. Future reader/test/
contract files remain absent; no successful unit/full suite was repeated. An initial whole-notebook
whitespace assertion encountered preserved historical whitespace; the checker was narrowed to new
documents/changed lines, and historical bytes were left untouched. Existing producer/test/lock
diffs remain empty.

Trello [W01-10](https://trello.com/c/tH4APMtJ/32-w01-10-review-suprem-provenance-and-checkpoint-inspection-scope)
was created in In Progress at review start, updated with findings/remaining gates, moved to Done
and marked complete. Final readback confirmed Done, completion and exact description. There is no
pending tracking-sync issue. This closes the review task, not actual checkpoint/source acceptance.

D-335 remains the imaging
checkpoint. Consumed requests, difficult cases, holds, membership and the fixed whole-backup
ceiling of 18,318,645,873 bytes / registered 20 GiB remain unchanged. This task changes no source,
test, lock, registry or import gate, creates no directory and records no human hours.
Stop after the review handback; subsequent coding and actual-file requests are proposals.
