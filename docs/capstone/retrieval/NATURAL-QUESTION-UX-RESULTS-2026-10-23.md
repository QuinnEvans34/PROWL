# Natural question UX: results and user walkthrough

Implemented the companion NATURAL-QUESTION-UX-SPEC-2026-10-23.md using the existing local8B model,
corpus, service and UI. User acceptance is pending. No broad answer-quality or independent-evaluation
success is claimed. Earlier failed composition experiments remain unchanged.

## What changed

The panel presents context, the question and answer first; passages and sources remain separate tabs.
Citation buttons open the exact supporting passage. Optional **Help phrase my question** proposes an
editable technical question. **Use this wording** applies it without submitting; the original remains
available. Ambiguity gets clarification, and rejected rewrites leave the original usable. There is no
conversation memory or silent rewrite. Cancel, elapsed time and stale-response protection remain.

Two demonstrated routing errors were repaired: focal-fat comparisons cannot select inflammatory
comparison records, and questions about volume measurement methods cannot select study mean results.
A follow-up scope correction lets general method questions retrieve passages instead of incorrectly
requiring a scan measurement. Individual-scan requests retain their context boundary.

## Bounded evidence

Twelve public development prompts exercised ordinary wording, uncertainty, modality, negation, vague
size, current-scan context, unresolved follow-up, injection and diagnosis requests. The first prompt
added concepts and changed intent; its failures are preserved. The minimal-edit candidate produced
six acceptable suggestions (including one unchanged question), one rewrite that dropped “might”,
three clarification results and two unsupported results. The final uncertainty guard rejects that
rewrite and keeps the original. Final guard replay used the exact saved model responses, not new
independent trials. Seven warm preview calls had median0.447s/max0.506s; cold behavior is not measured.

| Live answer probe | Observed result | Seconds |
| --- | --- | ---: |
| Tell inflammation from a tumor | Cited local-model answer; named comparisons and limits preserved | 9.51 |
| CT comparison wording | Cited local-model answer; complementary MRCP identified explicitly | 7.32 |
| Focal fat versus tumor | Passages only; unrelated inflammatory answer withheld | 0.37 |
| MRI study mean | 82.6cm³,14-person comparison group,±4.8SEM,matching and applicability limits retained | 6.38 |
| Findings without duct dilation | Clarification; no guessed negation reversal | <0.01 |
| MRI volume methods, after scope correction | Five canonical passages; no mean substituted and no generated answer | 0.51 |

Returned evidence records were compared with the canonical corpus; every generated claim citation
quoted its referenced passage exactly. Manual inspection of the three generated answers checked
terminology, values, exceptions, population and scope against those records. This is a narrow
development check, not comprehensive accuracy. Method/fat questions still lack qualified composition;
source-only results do not establish that retrieval fully answers either question.

Final focused backend suite:250passed. Six UI suites:94passed/2skipped. Production build passed with
the existing bundle-size warning. Browser walkthrough verified editable preview, apply without
submission, original retention, size clarification, actual answer generation, citation navigation
and return to Answer. Screenshot and raw receipts are in outputs/prowl/natural-question-ux-20261023/.
The first shell-background restart did not leave a listener; a detached service restart succeeded,
and the final method HTTP check passed. Live8016 uses --study-answers; imaging/review services unchanged.

## Your short walkthrough

Open http://127.0.0.1:5180/research. Try **Help phrase my question**, edit or accept the wording, then
**Ask question**. You can also ask the original directly. Check whether the proposed wording still
means what you intended and whether the answer reads naturally. Select a citation and return to Answer.

1. How can you tell inflammation from a tumor in the pancreas?
2. What clues on CT help tell pancreatic inflammation from cancer?
3. What mean pancreas volume was reported in the MRI study?
4. How big is a pancreas? — answers directly with the supported whole-pancreas volume study example.
5. How do papers measure pancreas volume on MRI? — passages are available, but no qualified summary yet.

Try your own paraphrases too. Report the original question, any unwanted wording change, and what
felt unclear or missing. No need to supply technical labels. Broader faithful composition, independent
evaluation and measurement qualification remain separate unfinished requirements.


## User feedback: default general size to volume

Quinton requested a direct answer for “How big is the pancreas?” rather than choosing a measurement
first. General whole-pancreas size wording now selects the existing cited MRI study-volume example.
Question help leaves that wording usable without clarification or a model rewrite. Explicit length,
head size, current-scan, population and clinical questions do not inherit this default. No unsupported
length or universal normal range was added. This supersedes the size-clarification walkthrough above;
the earlier probe results remain historical.172 affected backend checks pass.
