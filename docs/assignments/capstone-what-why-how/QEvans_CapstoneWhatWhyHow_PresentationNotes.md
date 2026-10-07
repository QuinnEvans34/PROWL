# PROWL presentation notes

Quinton Evans. Capstone What, Why and How. Class presentation: Thursday, October 8, 2026.

Aim for about 2 minutes 30 seconds. Practice aloud with a timer; these timings are a rehearsal guide. The spoken draft has 332 words, excluding source notes.

## Opening (0:00-0:20)

My capstone is PROWL, which stands for Pancreatic Review and Outlining Workflow for Lesions. It is a research prototype for helping a reviewer work through pancreatic CT images. The central task is to propose outlines that a person can inspect and correct.

## What (0:20-0:55)

The planned imaging workflow has two stages. First, a localizer finds the pancreas in the full CT scan. Then a segmenter proposes outlines for the pancreas and suspected lesions. In the viewer, a reviewer will be able to accept, edit or reject the result, and the system will save that decision. A supporting literature assistant will retrieve source passages for the structured findings and show their citations. When the sources do not support an answer, it should decline to answer.

## Why (0:55-1:30)

I chose this project because pancreatic lesion segmentation pushes me to solve a difficult machine learning and computer vision problem. The system has to locate an organ in a three-dimensional scan, then distinguish small lesions and propose useful boundaries. That challenge is compelling to me on its own, but healthcare gives it a purpose I care about. I see healthcare as the most inspiring use of AI, and I want to explore how AI can support a person's review of medical images.

## How (1:30-2:10)

I am using Python with PyTorch and MONAI for the imaging pipeline. The plan is to use PanTS and PANORAMA after validating their labels and keeping patients separate across training and evaluation. FastAPI and React with NiiVue will connect the model outputs to the reviewer interface. I will compare model contours with reference annotations, measure missed lesions and false alarms, and compare automatic localization with the supplied-region condition. The literature path will preserve the connection between retrieved passages and their citations.

## Closing (2:10-2:30)

Both models can already train, export predictions and recover verified checkpoints, but the contours remain poor. The autonomous two-stage workflow and full integration are still ahead. My goal is an evaluated annotation-assist prototype with clear limitations. It supports review and does not diagnose disease or recommend treatment.

## Before class

- Review the wording so it reflects what you want to say, especially the motivation.
- Rehearse once with a timer and adjust your pace to finish between 2 and 3 minutes.
- Upload QEvans_CapstoneWhatWhyHow_v4.png by Thursday, October 8 at 11:59 pm, according to the supplied assignment outline.
- Keep the PPTX available for presenting and further editing. The LMS accepts the image, not the PPTX.

## Sources for the wording

- Sources for project scope and motivation: Evans_Quinton_PROWL_Capstone_Proposal_v3.8.docx, sections 1, 2, 4 and 5; Evans_Quinton_PROWL_Capstone_Technical_Appendix_v3.1.docx, sections A1 and A2.
- Why wording: Quinton Evans, October 6, 2026 revision request, focusing on the machine learning and computer vision challenge and his interest in healthcare AI.
- Current implementation status: docs/capstone/operations/COURSE-START-SUMMARY-2026-10-05.md and docs/capstone/operations/CAP-EXP-014-RESULTS-2026-10-03.md.
- Brand asset: assets/branding/PROWL_CT_wordmark_concept_v2.png, existing project concept wordmark. It is a stylized illustration, not a model prediction or medical scan.
