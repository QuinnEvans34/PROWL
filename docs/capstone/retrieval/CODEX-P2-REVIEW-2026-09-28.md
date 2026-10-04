# Codex review of Claude's P2 handback

September 28, 2026. **Verdict: revisions requested before P2 acceptance or seed freeze.**
This is Codex's review/recommendation, not Quinton's approval of new policy, candidates, downloads,
or tool implementation. Claude's four draft files were not edited. P3 acceptance remains unchanged.

## Verified review inputs

All four SHA-256 values agree with Claude's handback:

| File under `planning/` | SHA-256 |
|---|---|
| SEARCH-AND-SELECTION.md | be5edc3781f0216581c5ea5c07aab2a5c6a136e7bf523be74b9b63005f1382f1 |
| SEED-SET.md | 91fabc6cddd4393bf8a96037644c0369c14feb186ade1b82fd05e9c6fef51276 |
| SEED-CANDIDATES.md | e60b7fc0754839b1b51e053884497373b019c3ff111b0d2248579bc5a4ca5850 |
| ACQUISITION-PLAN.md | 1e0612f7a177201234a44a9fb8e4037e4a45cf9335fe07667d495d493a390b1c |

Reviewed the execution rules, examples, seed protocol/list, run S envelope and running-log handback.
These are specifications, not executed selection tests. No code changed; the last native full-suite
baseline remains 893 passes, not a new P2 test result.

## Required revisions

### R1 — seed eligibility cannot depend on matching the selection policy

SEED-SET rule 10 makes recall membership conditional on a P- or W-term match in the title.
That undermines rule 1's independence: relevant works with different wording disappear from the
recall denominator before the policy gets tested. A title-only classifier also cannot establish that
an abstract/MeSH-based policy was never intended to reach a work.

Replace it with a topic/use scope fixed from INFORMATION-NEEDS: pancreas CT annotation/segmentation
and general imaging-AI review/workflow evidence when it directly supports an approved need. Quinton
judges expected usefulness and scope without requiring any policy term. Preserve title-only branches
as a diagnostic column, never the eligibility criterion. Truly out-of-scope methods may remain probes
with a substantive reason. Do not automatically promote all eight probes; reassess each individually.

If N5.5's dataset-method literature is deliberately outside Tier 1, state that coverage limitation
against the frozen needs. Do not hide it by redefining a known relevant miss as a probe. The 90% bar
and provisional selection terms need not change to correct the denominator.

### R2 — correct S-01 and recompute coverage before approving the list

The live [NLM PMID 33840636 record](https://pubmed.ncbi.nlm.nih.gov/33840636/) identifies:
Suman et al., **Quality gaps in public pancreas imaging datasets: Implications & challenges for AI
applications**, *Pancreatology* 2021;21(5):1001–1008, DOI **10.1016/j.pan.2021.03.016**.
It does not match the appendix's title. This is a confirmed citation conflict, not merely an
unsuccessful Crossref lookup. Retain the original citation and correction provenance; do not edit the
approved appendix in place or silently substitute the live record in P5.

Recommend retaining the corrected work as a candidate for dataset quality/review needs, subject to
Quinton's correction approval and final-snapshot resolution. Reassess N5.4/N5.5/N5.6 and any family-2
assignment; the old N1.1/N2.1 mapping cannot simply be carried over. This may help the family-5 gap,
but does not resolve WORKFLOW coverage.

SEED-SET's concluding list says nine uncovered needs whereas SEED-CANDIDATES says eleven. Recompute
one authoritative coverage table after corrections and R1. All 25 needs do not each require a unique
seed; the agreed requirement is 15–25 seeds and at least two per family, with meaningful coverage.
Do not choose set size merely to make the one-miss/two-miss threshold easier.

### R3 — tighten run S into a bounded execution contract

The frozen-copy signature, exact baseline samples and two update-file rule are good. Before signing:

- Freeze listing snapshots and resolved update filenames at preflight; require at least two distinct
  valid update files and exactly the required baseline identities. Refuse incomplete/ambiguous
  listings instead of substituting samples. MeSH name and URLs must be literal values in the signed copy.
- Specify that the 10 GiB network cap includes retries, partials and auxiliary transfers. Enforce
  caps while streaming, not only every 60 seconds. Space/volume periodic checks supplement those caps.
- Give the sizing parser an explicit memory cap and bounded XML/decompression behavior in its tool
  packet (no external entity/DTD network resolution, no uncontrolled expansion). Record what makes
  sample parse output representative of the proposed store. The 1.5 factor is a projection, not proof
  that the store fits; keep runtime phase caps and stop conditions.
- Define failure/interrupt receipts and their durable destination, even when a volume disappears;
  no successful completion marker on partial work. Keep no-overwrite behavior.

These are operational definitions, not permission to build or execute the tool. S2 still requires the
separate Group C dispatch. Do not mark S ready to sign until actual code, aliases, capacity and checks
are available.

## Answers to Claude's policy questions

Recommend **yes to all three**, as explicit pre-run changes based on obvious language variants:

| Question | Recommended exact rule |
|---|---|
| Bare AI | Add case-sensitive whole-token `AI` to A, using the same original-case normalized token view as CT; no substring match and no lowercase `ai` alias |
| Intra-observer | Add listed `intra-observer` alongside `intraobserver`, following the existing hyphen rule |
| Reader studies | Add explicit `reader studies` to W; no general stemming. Treat singular/plural as one W concept for cap scoring, so repeating both does not earn an extra distinct-concept point |

The last recommendation requires corresponding clarification of W scoring/examples. Preserve E5b's
old expectation as historical, and add/update tests for the newly approved policy: uppercase/lowercase
AI, AI substring rejection, intra-observer variants, singular/plural reader study and cap ordering.
No term changes have been applied. Record the revised policy identity before its first run; do not
rewrite a previously run/frozen policy. These recommendations arise from execution semantics, not a
post-result attempt to rescue seeds.

## Seven interpretations at the top of SEARCH-AND-SELECTION

| # | Codex recommendation |
|---|---|
| 1 Snapshot upper date bound | Keep. The snapshot determines availability; future issue-year flags must remain visible. No claim of excluding every publication dated after cutoff |
| 2 Omit OtherAbstract/VernacularTitle | Keep as an explicit v0 field limitation; store their presence. Do not call it equivalent to matching every abstract or a language guarantee |
| 3 Six publication exclusions only | Keep. All other types remain observable; relevance is assessed separately |
| 4 Deleted PMIDs in reconciliation | Keep. They belong in accounting, never in live candidate/recall membership |
| 5 Stage-1 seed recall | Keep. Report stage-2 usable-text coverage separately; selected metadata is not delivered evidence |
| 6 Post-sample qualifier subgroups | Keep. Insufficient subgroup counts mean no trigger; report uncertainty and avoid a causal claim. State whether another branch can still admit a record after a CORE-only revision |
| 7 Stage-2 rights allowlist before execution | Keep. Unknown/conflicting rights remain unavailable for full-text use; selection does not confer display/index rights |

These are reviewer recommendations for Quinton's v0 approval, not seven newly recorded decisions.

## Candidate-by-candidate recommendation

All are provisional bibliography judgments, not final-snapshot verification or evidence-quality ratings.
No original candidate is rejected merely because its title has no branch match.

| Candidates | Recommendation |
|---|---|
| S-01 | **Edit**, corrected citation and needs above; keep its original conflict in the log |
| S-02 | Keep as broad AI-background candidate |
| C-01 | Keep as general visibility/background candidate |
| C-02, C-03, C-04 | Keep available but optional for final trimming: substantial overlap in early/pre-diagnostic context; do not let them crowd out measurement/workflow |
| C-05 | Keep; visibility/false-negative context |
| C-06 | Keep, but **edit** N1.3 assignment: mimics are not automatically isoattenuating-lesion evidence; N3.1 is the clearer title-supported mapping |
| C-07 | Keep; anatomy/appearance candidate, with needs assignments provisional |
| C-08, C-09 | Keep optional as drafted |
| C-10 | High-priority keep: strongest title-supported bridge across contour agreement, efficiency and segmentation |
| C-11, C-12 | Keep: segmentation/localization rather than detection alone |
| C-13, C-14, C-15, C-16, C-17 | Keep as candidates; choose a balanced subset rather than over-weighting detection. No subtype/diagnostic questions are authorized by including these papers |
| C-18, C-19, C-20 | Keep optional as drafted |
| P-01, P-03, P-04, P-05, P-06, P-07, P-08 | Reassess under R1 for measurement, annotation or dataset-provenance usefulness; title wording alone is not grounds to exclude from recall |
| P-02 | General-method probe is reasonable unless a concrete approved reviewer need establishes intended Tier-1 usefulness |
| NEG-01–03 | Keep optional controls with independently stated out-of-scope rationale; a surprising selection is a finding, not grounds to discard the control |

A 17-seed set permits one miss at 90%; that arithmetic is correct. The final count must follow scope,
coverage and verification, not be used to soften the bar. Do not freeze the current recommendation yet.

## Additional chaining source and exposure disclosure

A proposed **new chaining source**, subject to Quinton's acceptance, is Goddard, Roudsari and Wyatt,
[Automation bias: a systematic review of frequency, effect mediators, and mitigators](https://pubmed.ncbi.nlm.nih.gov/21685142/),
*JAMIA* 2012;19(1):121–127, DOI 10.1136/amiajnl-2011-000089. Use its references to find imaging-related
human-review work; the review itself is not automatically an eligible Tier-1 seed.

Transparency: Codex used a live web search for `site.pubmed.ncbi.nlm.nih.gov "automation bias"
radiology systematic review` while reviewing this gap. This is **search-suggested**, not a source
Quinton said he had read and not a citation-chained candidate under existing rule 1. Do not quietly add
search results to the seed set. Ask Quinton to designate the source, or explicitly revise discovery
rules before using it. No frozen selection results were inspected.

The web tool exposed search snippets, including abstract-derived material, and NLM's S-01 page
returned abstract and MeSH text while verifying the citation. This review therefore cannot claim
metadata-only exposure. Results included PMIDs 21685142, 21335679, 27516495, 38635456, 42436051,
42446358 and 42565207, and the mammography article DOI 10.1148/radiol.222176. Transfer these exposures
into the inspection ledger before sampling; conservatively keep exposed records out of independent
confirmation. No abstract text was copied into project files, and no relevance labels were assigned.
Preserve the query/date in the running log; do not describe these results as independently discovered
seeds. Do not use any snippet's apparent date as final-snapshot evidence.

## Codex-owned reconciliation and operational status

- The PubMed route wording is **already reconciled**: `CORPUS-AND-RIGHTS.md` approved channels and
  Plan 07 P07-05 both specify baseline + ordered updates, with E-utilities for bounded checks.
  SCOPE section 10 and ACQUISITION prerequisites should distinguish completed wording from unsigned runs.
- Read-only filesystem observations today: registered scratch and artifacts directories exist and are
  not symlinks; `artifacts/literature/` and `artifacts/literature/receipts/` do not exist. No directories
  were created. Existing registry access remains setup-only/scoped acquisition; no literature writer
  or source alias is enabled. Latest metadata job verified the registered volume, but S needs its own
  current identity/capacity checks and tested writer. S1 is not complete.
- `.git/index.lock` is absent. The reported stale marker exists and is zero bytes; left untouched.
  This review used Git with optional locks disabled. No Git reset, commit, push or cleanup occurred.
- Recommend allowing the single PANORAMA protocol PDF for reference-list inspection, **if Quinton
  approves it**. The [Zenodo record](https://zenodo.org/records/10599559) lists the named PDF at 6.3 MB
  and MD5 `3c89347570dc4bb327924abfd7f001c0`. A bounded packet should allow only that file, cap it at
  10 MiB, verify the published MD5 plus local SHA-256, preserve a receipt, and not ingest/index it.
  This review fetched the landing page only; it did not download the PDF or accept terms.

## Handback to Claude

Revise R1–R3 and reconcile coverage/status prose. Preserve the frozen needs and existing bars.
Prepare the S-01 correction and policy variants for Quinton's approval; mark recommendations as
recommendations. Update the running log with this review and its exposure disclosure. Do not freeze
seeds, execute sizing/downloads, build the sizing tool or begin another phase on this review alone.
Return changed-file hashes and a concise response to each finding for Codex's check.
