# General source-based answers: implementation and test record

Quinton requested continued autonomous work until a useful general fallback could be tested.
The failed free-composition candidate remains unpromoted. This is an explicit interim implementation:
select directly responsive research sentences and present them as quotations with source links.
It does not satisfy the remaining goal of fluent plain-language synthesis. User acceptance is pending.

## Runtime behavior

Existing reviewed disease, volume and study answers keep precedence. Eligible unmatched literature
questions use the same five retrieved passages and local8B model. It selects sentence IDs, then audits
selection against the original question and full passages. The application copies text; the model
cannot supply the displayed factual wording. At most6sentences,2calls,90seconds combined. Bad IDs,
inconsistent coverage and timeouts keep the passages available. No runtime evaluation labels or
question-answer list is read. Refusals, scan requests and existing clarifications bypass this fallback.

General whole-pancreas location questions now search literature; scan-localization requests retain
their boundary. No case images or predictions are added to the literature prompt.

The optional service flag is --study-answers --general-extracts. UI uses a distinct envelope with
exact text/quote/source checks and displays “Source-based answer” rather than claiming model-written
prose. Source selection is still a model judgment: exact copying does not prove relevance or complete
coverage. No broad reliability, clinical safety or independent evaluation acceptance is claimed.

## Controlled comparisons

All receipts are under outputs/prowl/general-spans-20261023/. Original failed attempts are retained.
The initial existing span selector missed a function paraphrase and included unrelated AIP evidence
for focal fat. A sentence selector plus audit in non-thinking mode still selected the AIP sentence.
The same selector/audit in reasoning mode removed that unrelated disease and selected direct evidence.

| Fixed public question | Reasoning selection | Selection time |
| --- | --- | ---: |
| What does a pancreas do? | Digestive/exocrine/endocrine roles and their source context;5sentences |25.66s|
| What jobs does the pancreas have? | Digestive enzymes/hormones and exocrine/endocrine roles;3sentences |37.53s|
| How do papers measure pancreas volume on MRI? | Source method and integration across sections;2sentences |18.43s|
| How can fat in the pancreas head look different from a tumor on CT? | Direct CT focal-fat/PDAC comparison;1sentence; unrelated AIP removed |45.49s|
| What is the normal pancreatic stiffness range in kilopascals? | No answer selected; no substituted volume values |14.53s|

All11selected quotations bind exactly to canonical retrieved text. Manual inspection checked entity,
modality, scope and source context. Function quotations still include some background and technical
terms; MRI quotation includes acquisition details. They are useful source extracts, not polished
plain-language answers. The paraphrase packet does not contain the glucose-regulation passage present
in the first function packet; retrieval sensitivity remains a limitation. No insulin claim is invented.

## Verification and walkthrough

Focused backend checks initially164pass; sentence-span checks20pass. UI86pass/1skip across general,
volume, study and panel tests; build passes with existing bundle warning. Tests cover exact citation
binding, unknown IDs, review removing irrelevant sentences, gap results, preserved reviewed answers,
refusals and clarifications, timeout fallback, rendered provenance and source navigation. Final public
regression and live browser results follow below.

Try in Research:

1. What does a pancreas do?
2. What jobs does the pancreas have?
3. Where is the pancreas located?
4. How do papers measure pancreas volume on MRI?
5. How can fat in the pancreas head look different from a tumor on CT?

Check whether selected text answers your intent and whether source links are easy to inspect. It may
take tens of seconds because selection uses reasoning. Existing reviewed questions still use their
faster composition path. Source wording can contain jargon and original paper reference numbers;
our clickable source buttons identify the actual passages. Polished synthesis remains future work.

The regression matrix used here is configs/evidence/week3-quality-matrix-v1.json (20supported,
10boundaries). It does not replace the broader exposed former-evaluation set, whose previous failures
remain recorded. This release is a user-testable source-extract preview, not acceptance of general
free-written answers. Mechanical citation checks and source copying cannot replace semantic review.

## Final qualification and live preview

The public30-case matrix completed:20/20existing supported questions retained their expected reviewed
records and canonical citations (median6.70s,max13.04s).10/10boundary questions returned no answer
claims. One normal-volume-range boundary timed out at90.73s; child-volume and combined volume/treatment
requests also unnecessarily entered selection. Their original volume-scope boundaries are now
preserved before fallback. Final real HTTP rechecks for those three requests return no answer/model
call in0.38/0.36/0.43s. Original slow receipts remain unchanged. Acute-pancreatitis comparison withheld
with no claims; no boundary failure was relabeled as a supported answer.

Additional candidate HTTP checks: general location returned the exact posterior-wall/behind-stomach
sentence in49.21s; function returned a supported source extract in30.54s; stiffness gap withheld in
14.46s. Exact records and quotation bindings verified in every HTTP receipt. These are development
results and not a claim of fresh independent accuracy.

Final backend affected suite165pass; UI86pass/1skip, plus8pass after adding the prompt identity check.
Final build passes. Browser on the normal5180Research page visibly answers the function question,
labels source-copy provenance, opens the correct passage at citation1, and returns to Answer.
Screenshot: outputs/prowl/general-spans-20261023/live-answer.jpg. The live8016service now uses the
optional general-extract flag; temporary8020candidate service stopped. No imaging/review service,
model weights, training or private evaluation data changed.

Interpretation of completion: ready for user feedback as an interim source-extract preview. It does
not meet the complete plain-language composition goal. Existing reviewed prose still works; new
questions receive selected source wording when admitted. Long quotations, jargon, retrieval sensitivity,
selection latency and semantic selection errors outside the tested set remain limitations.
