# Independent evaluation: next steps for Quinton

## Current status — expanded disease evaluation

The [reconciliation checkpoint](EVALUATION-RECONCILIATION-2026-10-17.md) supersedes the execution
instructions below. The public inventory now includes 136 distinct normalized wordings and the
current target is 14 sources / 1,179 passages. The final revised development set and independent
labeling arrangement are pending. **Do not start private authoring or use the old templates yet.**
Quinton supplies natural questions; he is not being assigned article search, JSON or offset work.

The only current command is public and reads no protected content:

```sh
.venv-retrieval/bin/python -m src.retrieval.private_evaluation --public-preflight
```

Normal validation/`--prepare` now stop before requesting any private path. The lower-level validator
is retained for invented tests; a future admission/schema version must match the actual frozen scope
and reviewer roles. Earlier approvals remain valid for their ten-source scope.

## Historical ten-source instructions — not current execution steps

> **October17 workflow revision:** Quinton will supply natural questions but will not search papers,
> choose evidence spans or enter technical labels. The instructions below describe the earlier
> authoring arrangement and are retained as a technical reference. Do not ask him to execute them.
> First reconcile the scan-centered capability contract and an independent engineering-supported
> labeling process against the [disease-reference update](DISEASE-REFERENCE-CORPUS-2026-10-17.md).
> Existing private tooling may be reused by that process; it does not establish completed review.

The 30 development questions are accepted, including evidence and the full consistency pass.
You do not need to review them again. Step 5 now needs the separate **30-question private test set**.
This measures performance on questions the development agent has not helped write or seen.

## 1. Prepare private storage

Follow [protected authoring](PROTECTED-EVALUATION-AUTHORING.md) before writing questions. Confirm
the current shared storage allocation and independent encrypted-backup capacity; this checkpoint
creates neither an encrypted image nor a storage allocation. Do not assume an older capacity limit
in a historical document is the current approval. Keep private content outside the repository,
agent-connected folders, cloud documents, chat and Trello. Work with agents idle and unmount the
image afterward. A mounted image is accessible to processes running as your OS user.

## 2. Read sources and author independently

The local [source-reading pack](../../../outputs/prowl/evaluation-private-preparation-20261017/source-reading/README.md)
contains all 947 frozen passages from the ten-source corpus, with article attribution, representation
identities and normalized character offsets. It contains no suggested test questions or gold labels.
Overlapping passages are not independent evidence. Full source text remains local, outside Git.

Copy these public blank templates into your private workspace:

- [Suite template](../../../configs/evidence/evaluation/private-authoring-template-v1.json): fill the authorship/review description and add 30 cases to `cases`.
- [Case template](../../../configs/evidence/evaluation/private-case-template-v1.json): copy once per question, use distinct `q:heldout-01` through `q:heldout-30` identities and matching label question IDs.
- [Closed format reference](../contracts/retrieval/private-evaluation-v1.schema.json): allowed fields and values.

These templates deliberately fail validation until completed. The template status names a validation
stage, not acceptance. Keep their public corpus/development hashes unchanged. Leave content hashes
blank during drafting; the explicit `--prepare` command below computes them in a separate copy.

Write **20 answerable questions and 10 unsupported/refused questions**. Cover all five answerable
families (`appearance`, `measurement`, `anatomy`, `ai_limits`, `review`) and all four difficulty
categories (`easy`, `paraphrase`, `multi_passage`, `limiting`). Choose actual frozen information needs
from [needs v2](planning/INFORMATION-NEEDS-V2.md) and its inherited base. Do not manufacture supported
answers to meet the counts. Avoid one paper being the sole gold support for more than 10 of the
20 answerable questions; multiple genuinely supporting papers are allowed.

For each answerable case, record required concepts, exact direct/partial/limiting spans and a judgment
for every retained source. Use normalized Unicode character offsets `[start, end)`, not HTML byte
offsets. Each direct span must fit completely inside a frozen passage. Representation ID/hash and
offset fields follow the [span contract](../contracts/retrieval/span-label.schema.json). Every required
concept must have direct support. Unsupported/refused cases have no gold spans, concepts or source
judgments; record the reason and boundary in their expected behavior and review notes.

## 3. Complete your semantic review and second pass

Check whether the evidence actually supports the expected meaning, including population, modality,
units and limitations. Then separately check consistency across the set. Record the actual reviewer,
ISO date/time, reasoning and both completed review stages. Set the three suite-level review flags
only after doing those reviews.

Compare intended facts and paraphrases with all exposed development versions, the old regression
and demo questions listed in [public exposure inventory](../../../configs/evidence/evaluation/public-exposure-v1.json).
The inventory has 142 records / 64 distinct wordings / 31 intent groups. It is a known repository
inventory, not proof that all past conversation exposure has been captured. Review that history too.
Different wording alone does not make a question independent. If a development revision is needed,
tell this chat only what public development material needs changing; keep the protected question private.

## 4. Run the checker privately

Use Terminal.app outside an agent-connected terminal, while agents are idle. From the repository:

```sh
.venv-retrieval/bin/python -m src.retrieval.private_evaluation --prepare
```

Confirm the private session and enter your private JSON path at the hidden prompt. Do not put it in
the command line or send it to this chat. The input must be an ordinary, non-symlink JSON file outside
the repository, at most 2 MiB. The tool cannot establish whether the location is encrypted or whether
other agents can access it; those remain your responsibility. A terminal check is not a security sandbox.

The checker verifies the closed format, corpus versions, exact evidence offsets, concept coverage,
counts, family/difficulty coverage and exact exposed wording/intent reuse. It does not judge entailment
or detect all paraphrases. Review assertions remain human attestations.

Successful output goes beside your input into a new `<input-stem>.validated` directory containing
`validated-set.json` and `validation.json`, with owner-only permissions. The input is unchanged and
existing outputs are never overwritten. For revisions, keep prior evidence and use a new draft name.
A failed write can leave an incomplete output directory; no atomic or power-loss guarantee is claimed.
Without `--prepare`, existing content hashes are checked instead of recalculated. Do not paste private
files, paths or content-bearing diagnostics here. The tool's fixed failure message can be shared.

## 5. Finish the protected freeze

Mechanical success is not the final freeze. Preserve authoring history, build the private content
manifest, freeze the encrypted image, verify the independent encrypted backup and unmount it as
described in the authoring worksheet. These storage/freeze operations are not automated by this checker.
Only then complete the closed, content-free public receipt with genuine hashes, counts and attestations.
The validation report's suite hash is not a substitute for the separately required content-manifest hash.

Current state: the public protected receipt remains `not_created`, and retrieval comparisons remain
gated. No actual protected questions or labels have been authored, opened or validated by this task.
Once the real protected freeze receipt is complete, the next engineering step is the development
retrieval comparison, followed by readable cited summaries and viewer integration.

## Delivered checks

28 invented-input private-validator tests and 36 public-checkpoint tests pass. Public corpus loading
verifies ten sources / 947 passages and the exposure inventory. Tests are engineering checks, not
held-out performance results. The prior development validator still refuses private-set records.
