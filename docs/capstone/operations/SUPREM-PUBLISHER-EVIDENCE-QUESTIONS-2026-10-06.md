# SuPreM publisher evidence questions — draft for Quinton

October6,2026. **Prepared only; no message sent.** Quinton owns publisher outreach.
Supporting [R02 evidence-gap record](SUPREM-SOURCE-SEPARATION-STATUS-2026-10-06.md).
These questions seek artifact-specific provenance without asking for identifiable patient data.

## Candidate and intended use

Released `MrGiovanni/SuPreM/supervised_suprem_segresnet_2100.pth`, SHA256
`2db81dc05cd9ea7234ca75e921e53e32b8716dc4cba88a6710742bfc282589a3`.
Our historical local record is56,500,623B; current local identity is not yet inspected.
Proposed use: initialize only the SegResNet backbone for an undergraduate research pilot, replacing
the32-output task convolution with a fresh3-class head. We would create a new optimizer/session,
retain original PanTS roles and keep all held cases. No clinical deployment or publication is
being authorized by this draft.

PROWL's protected parent roles are7,200training/1,800development/901test from the original
9,901-case public PanTS pool. The immediate pilot contains six training cases and one report-only
development case; source separation must cover protected roles, not just these seven cases.
Do not send local patient metadata or an unapproved subject manifest with an inquiry.

## Questions to resolve

1. Can you bind the named SHA256 release to its exact pretraining run, source dataset versions,
   full training subject/scan membership and checkpoint-selection membership? Is the public
   AbdomenAtlas1.1.txt9,262-case list related to this2,100-case release, and if so which subset?
2. What data were used to select the released epoch or tune its pretraining recipe? Can you
   clarify the paper's1,310vs310selection counts for this particular release, including any
   additional development/selection sets beyond the optimizer-training list?
3. Can you provide deidentified stable source IDs or a reliable crosswalk to the public
   PanTS9,901-case pool, including its901in-distribution test cases? How are renamed datasets,
   multiple contrast phases and repeat scans of the same patient accounted for?
4. If manifests cannot be shared, can you explicitly confirm whether any subjects/scans from
   those protected PanTS cases were used in optimizer pretraining, checkpoint selection or
   hyperparameter selection for this artifact, and state the evidence supporting that answer?
   A general JHH-unseen or different-release-date statement will not settle renamed public scans.
5. Which weight-specific license/terms apply to this exact artifact and academic backbone
   fine-tuning? Are there additional restrictions/notices relevant to using or later sharing
   derived weights? The Hugging Face collection and GitHub code carry different declarations;
   we intend to use our own local implementation.
6. Separately, if we later evaluate RSNA abdominal-trauma data, which RSNA subjects/scans were
   present in this release's training or selection sets? This is a future evaluation dependency,
   not a request to acquire data or change the current pilot.

## What would close the issue

An answer must identify the exact artifact and both training/selection provenance. A reliable
scan-and-subject crosswalk permitting a role-separation check, or sufficiently explicit and
supported publisher separation confirmation, can be reviewed for acceptance. Case-name inequality,
dates, institution names and broad dataset descriptions alone remain insufficient.

Record response date, author, exact artifact identity, supporting references/manifests and limits.
If evidence establishes overlap, preserve the original roles and report the limitation; do not
filter cases or claim this source clean. If the response remains ambiguous, keep source use
unaccepted and discuss the separate scratch route with Quinton. No response is fabricated here.
