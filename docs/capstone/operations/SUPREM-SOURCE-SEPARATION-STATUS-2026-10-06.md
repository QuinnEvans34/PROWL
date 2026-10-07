# R02 — SuPreM source separation remains unresolved

October6,2026. Approved public-text follow-up to the
[earlier provenance review](SUPREM-PUBLIC-PROVENANCE-REVIEW-2026-10-06.md).
Tracking: [W01-14](https://trello.com/c/cQQbjeYe).

## Phone handback

**Research finished; scientific source use remains blocked.** A public SuPreM dataset-list trail
exists, but the reviewed list is a9,262-line collection list, not a verified manifest for the exact
2,100-case release or its model-selection set. Public-pool overlap therefore cannot be ruled out
from the earlier JHH-unseen statement. No contamination is proved either.

[Specific publisher questions](SUPREM-PUBLISHER-EVIDENCE-QUESTIONS-2026-10-06.md) are ready for
Quinton's review/use. Nothing was sent. Continue independent integration drafts and the separately
proposed metadata inspection; neither action accepts this source for training.

## Exact question and evidence standard

Candidate: `supervised_suprem_segresnet_2100.pth`, historical56,500,623B, published/recorded SHA256
`2db81dc05cd9ea7234ca75e921e53e32b8716dc4cba88a6710742bfc282589a3`.
Current local identity is still unobserved. We need source training **and model-selection** subjects/
scans bound to this artifact, plus reliable separation from PROWL's protected development/test
roles. PROWL retains7,200train/1,800development/901test parents, its exact6/1pilot and every hold.
A collection-name difference or different numerical aliases cannot prove patient separation.

The acceptance path is a candidate-bound pair of membership manifests with a reliable crosswalk,
or sufficiently specific publisher confirmation for the artifact and protected patient/scan sets.
A manifest must account for phases, repeat scans and renamed copies, not merely unique filenames.
The existing standards remain unchanged; no eligibility/role transition is made here.

## New focused public trail

| Official source reviewed October6 | Observation | Limit |
|---|---|---|
| [SuPreM pretraining dataset tree](https://github.com/MrGiovanni/SuPreM/tree/main/supervised_pretraining/dataset) | Lists dataset_list and dataloader_bdmap.py | Mutable main branch; no checkpoint-specific release binding obtained |
| [Current loader](https://github.com/MrGiovanni/SuPreM/blob/main/supervised_pretraining/dataset/dataloader_bdmap.py) | Reads the named dataset .txt list and assembles image/segmentation paths | Generic current implementation; does not establish which historical list produced this artifact or selected its epoch |
| [AbdomenAtlas1.1.txt](https://raw.githubusercontent.com/MrGiovanni/SuPreM/main/supervised_pretraining/dataset/dataset_list/AbdomenAtlas1.1.txt) | Web reader reports9,262text lines with BDMAP aliases | No2,100subset/selection attribution or PanTS patient crosswalk verified; not copied locally |
| [Pretraining README](https://github.com/MrGiovanni/SuPreM/tree/main/supervised_pretraining) | Current examples use AbdomenAtlas1.1 and25classes | Not the release's32-output/2,100-case training manifest |
| [PanTS paper v1,Section3.2](https://arxiv.org/html/2507.01291v1#S3.SS2) | Describes its training pool as assembled from11public abdominal CT datasets | Does not bind the SuPreM release to particular scans or establish our protected-role separation |
| [PanTS current README](https://github.com/MrGiovanni/PanTS) | Separately describes9,000official training and901in-distribution test cases | Current split description differs from paper-v1 aggregate reporting; our frozen local roles remain authoritative |

**Inference:** a statement that JHH was unseen in a described transfer experiment cannot by itself
settle PanTS protected-case separation. PanTS's public aggregation makes the original public-source
membership and renaming crosswalk relevant. The reviewed text does not resolve which protected
PROWL cases share those source subjects with this particular released artifact.

This follows specific new paths rather than repeating the earlier license/architecture review.
No complete public membership search is claimed. The dataset-list directory and its GitHub contents
API returned cache/fetch errors; the known AbdomenAtlas1.1.txt path from the loader/README was
read successfully. AbdomenAtlas1.0.txt was unavailable. An initial malformed arXiv locator failed;
the correct PanTS2507.01291v1 HTML was then used. Search results unrelated to the publishers were
not used. No binary endpoint, PDF, dataset gate, scan or weight was fetched. No contact occurred.

Revision limits: PanTS HTML is explicitlyv1,July2,2025. Reviewed GitHub/raw URLs are mutable main;
no full code/list revision or raw-byte content hash was verified. The9,262line count is a web
observation, not an independently qualified member count or artifact-specific control pin.
The earlier review's1,310vs310selection discrepancy remains unresolved; no new count was assumed.

## Assessment and effect on the queue

| Item | Assessment | Consequence |
|---|---|---|
| Public release origin | Published SHA agrees with retained candidate record | Useful candidate identity; actual local metadata still R04 |
| Weight-specific terms | Earlier publisher Apache2.0 declaration located | Scoped rights record/attribution still needed; no upstream code copied |
| Exact pretraining membership | Unresolved | Scientific initialization/training not accepted |
| Exact selection membership | Unresolved | Same source-use block; training-only list alone insufficient |
| Protected-role crosswalk | Unresolved | Keep roles/holds unchanged; no case filtering or reshuffle |
| Proven contamination | Not established | Do not label candidate contaminated on this evidence |
| Invented engineering/drafts | Approved in their own finite scopes | May continue without actual source use |

No new source was selected. A scratch duration comparison remains a separate planning route, not
automatically dispatched when pretraining is blocked. Varied data qualification, negatives,
autonomous ROI, PANORAMA, retrieval, orchestration and UI remain visible in the roadmap.

Exact next source-evidence action: Quinton may use the linked questions to obtain a candidate-bound
answer or manifest/crosswalk. Review that response once available; do not repeat these searches
hourly while nothing changes. R02 can be complete as a research/gap task while the source gate and
W01-12 parent remain incomplete. Human hours unknown; agent runtime adds no human-hours entry.
