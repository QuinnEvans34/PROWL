# 01 — Product brief and decisions

> Approval update, October 18: Quinton approved Concept 01 and requested the Claude implementation handoff. O01 (logo), the visual direction, and the first implementation sequence are settled. See 08–10 for operational details. Unresolved backend dependencies remain explicitly open.


## Confirmed by Quinton, October 18

- Primary user: radiologist, or hospital professional reviewing pancreatic CT studies.
- Desired flow: acquire a CT outside PROWL, bring the study into PROWL, inspect model-proposed
  pancreas and possible lesion contours in 2D and 3D, consult the expert, and retain human judgment.
- Reference masks may or may not exist. Reviewing a study without them is a complete normal flow.
- The expert should answer pancreatic questions using the project's literature corpus and, later,
  receive structured scan facts. It assists the reviewer; it does not make a definitive diagnosis.
- Current expert has no scan context. Explicit static examples are acceptable while integration evolves.
- Initial import design must include DICOM, in addition to preserving existing prepared-case access.
- The first completion artifact should be a draft review summary that the radiologist can edit.
- Use the existing prowling black panther logo. Its sleek, minimal character should guide the design.
  The supplied asset is now available at repository root: `PROWL_LOGO.png`. User dislikes the current palette; designer may propose.
- Review visual drafts iteratively. User prefers reacting to concrete designs over choosing abstract styles.
- Create `codex/prowl-ui-redesign` and clear Markdown specs, then eventually a Claude implementation prompt.
- Planning and prototype review are complete. Quinton now requests the Claude implementation handoff.

## Product thesis — proposed

PROWL is a focused pancreatic imaging review workbench. A study remains the center of the experience.
Imaging, model proposals, measurements, evidence, and an editable summary share its context.
The application is a research prototype designed around radiologist tasks; this UI project does not
establish clinical deployment readiness or hospital integration.

## Five-minute journey — experience target, not inference SLA

1. Select/import the relevant CT series and confirm its identity.
2. Open the CT, see analysis status, and inspect available pancreas/lesion predictions.
3. Move between slices and 3D without losing the active study or selected finding.
4. Inspect available measurements; ask a literature question with cited support.
5. Review and edit a structured summary; save/export only through supported capabilities.

Import, conversion, or inference can take longer than five minutes. Never fake completion to meet this target.

## Open decisions

| ID | Question | Working proposal |
|---|---|---|
| O01 resolved | Panther asset | Repository root `PROWL_LOGO.png`; preserve the original |
| O02 | DICOM ingestion/service readiness | Audit existing support before committing implementation scope |
| O03 | Summary destination and persistence | Editable in-app draft; exact save/export contract still to decide |
| O04 | Summary scope | Research review: observations, measurements, limitations, reviewer notes; no invented diagnosis |
| O05 | First supported desktop size | Start at 1440×900; verify 1280×720, 1024 wide, and 200% zoom |
| O06 | Contour correction | Preserve existing external correction boundary; browser editing is not implied |
| O07 | Assistant naming | PROWL Assistant for now; user can rename after visual review |
| O08 | DICOM series/folder/ZIP support | Specify folder/series UX first; accept only formats the ingestion adapter validates |

## Decisions to avoid by accident

No PACS connection, scanner control, patient registration system, multi-user roles, clinical sign-off,
browser contour editor, or new AI model is implied by this redesign. Discuss these separately if needed.
RAG and workflow/DAG implementation remains in its owning backend lane. UI states must reflect its actual API.
