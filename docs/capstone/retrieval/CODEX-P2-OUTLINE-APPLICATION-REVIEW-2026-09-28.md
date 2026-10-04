# Codex review — applied P2 outline and workflow candidates

September 28, 2026. Reviewed Claude's latest running-log entry, decision sheet, selection policy,
seed protocol/candidates and unsigned run P. **Good progress, but P2 is not ready to freeze.**
This is a local-document review, not a new literature search or abstract/full-text verification.
Recommendations below are Codex's; no new seed, search-policy or download approval is recorded here.

## Evidence and approval provenance

All five handback hashes match:

| File | SHA-256 |
|---|---|
| SEARCH-AND-SELECTION.md | 44e0bcb9617568b9e2805c73b4947142fb689b74fcf76f6a30862552e78f96e1 |
| SEED-SET.md | fd7006a1fd160ae64de5f66d973c52b85dd1c596e6ea6a0567f75be3abe4cc8b |
| SEED-CANDIDATES.md | e34f439f2303005bea83774027ff0ad8db66c697db02bf177e7c830eb5221c9b |
| ACQUISITION-PLAN.md | 7a9b4e3a153c527fcc1145594387e1731fd67e201936a65a47e6c01d857f2ed9 |
| P2-DECISION-SHEET.md | 768ec25bb3d63cbd985036f3698401ee2fd27f1194b7fd5c1ba81a2779ff68a6 |

Frozen needs remain unchanged at `d71577c27cebd5d54f516a7b2120273c3afba7dc077be3799bae4ccecbde8ac0`.
The running log quotes Quinton's separate Claude conversation asking to review/use Codex's decisions
as the outline. That reported adoption—not Codex's recommendation alone—is the stated approval basis.
Preserve the quote and its provenance. This task does not independently read that conversation, and
does not broaden the reported adoption to the newly proposed C-31–39, whole-policy approval or a run
signature. Keeping selection v0 as a whole unapproved is correct. P2 remains incomplete.

Goddard wording is now correct: designation permits chaining, not automatic seed inclusion. The
reported blocked C-25 attempt is honestly unresolved; no scope or abstract exposure should be invented.
The title-search exposures still belong in the exposure ledger.

## Changes needed before acceptance/freeze

1. **Do not count analogical N5.1 coverage as direct contour-review evidence.** The listed detection
   reader studies may inform general human/AI interaction. They do not, from the supplied titles,
   establish what errors a reviewer catches in pancreatic contours. Keep `related_background` or
   `analogical` links separate and leave direct N5.1 coverage open. Do not silently change the frozen
   need to make these papers fit.
2. **Qualify the N5.2 claim.** Incorrect CAD output makes C-31 a strong candidate for automation-bias
   coverage. Improved or changed reader performance alone is not proof of over-trust. C-32/C-33/C-35
   titles do not establish automation bias. The candidate file is more cautious than the forwarded
   statement that all four "clearly cover N5.2"; keep the cautious wording and verify eventual scope.
3. **Resolve run P's attempt wording.** Its cap row says "1 transfer" and then permits a second
   attempt. Use "one target file, at most two attempts, aggregate received bytes <=10 MiB; retry only
   when remaining allowance covers the full listed file" (or choose one attempt/no retry). Keep
   partial bytes and wall time in the receipt. Do not sign an internally contradictory record.
4. **Coverage bookkeeping:** the supposedly section-A-only authoritative table now includes A2.
   Rename it as the combined proposed-pool table and distinguish accepted provisional, proposed and
   verified/frozen counts. Keep direct N5.1 open; the direct gap count is nine after adding N5.2 only.
   Fix the family-2 row's "remaining decision 2" cross-reference: family-2 is item3 in draft6.

None requires changing search terms to make a candidate pass. The missing W terms are useful
pre-run coverage warnings; actual selection still depends on permitted abstract/keyword fields.

## Recommendations on all nine new candidates

Title/metadata-based recommendations only; final scope and local-snapshot identifier verification
remain required. "Keep" below means keep as a proposed candidate, not approve/freeze a seed.

| ID | Recommendation | Mapping/boundary |
|---|---|---|
| C-31 Alberdi 2004 | Keep, high priority | Strong N5.2 candidate from incorrect-CAD-output topic; N5.1 related background only |
| C-32 Fenton 2007 | Keep provisionally | Reader-performance context; do not claim the title proves automation bias or contour-review benefit |
| C-33 Petrick 2008 | Keep provisionally | CT second-reader context; direct N5.1 coverage stays open; confirm a frozen need is actually supported before seed freeze |
| C-34 Walsham 2008 | Reserve | Detection-assistance background; no direct contour-review claim from the title |
| C-35 Li 2006 | Move to reserve | Title centers on diagnosis/management recommendations; weaker fit to this contour-review assistant. Do not expose management advice; this is a relevance decision, not a blanket ban on papers mentioning management |
| C-36 Zheng 2001 | Prioritize for scope verification | Cueing-environment topic is a plausible N5.2 fit; prefer investigating this over C-35, without asserting bias findings before reading permitted evidence |
| C-37 Hadjiiski 2004 | Reserve | Characterization/ROC topic is weaker for the frozen contour-review needs |
| C-38 Marten 2004 | Reserve | Reader experience may be useful background; title alone does not establish a frozen need or contour-review evidence |
| C-39 Helvie 2004 | Leave out of initial recommended subset | Detection-system sensitivity is a weaker workflow fit; retain its discovery record rather than erase it |

Suggested working priority is C-31/C-32/C-33 plus C-36 for factual scope verification, rather than
assuming C-31/C-32/C-33/C-35 all directly cover automation bias. This remains a recommendation.
Do not promote a paper merely to hit a family count or improve the recall denominator.

## The other open choices

- **Eleven section-A optional candidates:** retain all as a reserve, outside the initial frozen list.
  No need to reject them permanently. Add one only for a documented coverage need before results;
  do not silently replace a frozen miss. Preserve the 15–25 cap and per-family requirements.
- **Second family-2 seed:** first try a bounded exact-DOI/identifier lookup through an official PubMed
  route if Quinton adopts that next action. Do not refetch the rate-limited Springer page or search
  with outcome-tuned terms. Log any abstract exposure. If still inconclusive, use C-10's reference
  list through the already approved chaining route to find a supported measurement/contour-review
  alternative. Do not drop C-25 solely because the selection policy might miss it.
- **PANORAMA:** keep unsigned/deferred until wanted and the transfer wording is fixed; it does not
  block imaging. This review neither downloads the PDF nor accepts terms/signs on Quinton's behalf.
- **Goddard itself:** remains only a designated chaining source unless separately proposed/accepted.

## Housekeeping and handback

`_to_delete/claude-RUNNING-LOG.md.tmp` was inspected: one114-byte hash line naming the earlier Codex
review, matching its reported hash. It is a known temporary file, not a Git lock or an imaging blocker.
No directory deletion is needed for this review; it remains preserved. No Claude planning file,
Notion task, literature file or external service was modified. Quinton can forward this review;
Codex has not sent Claude a message or represented these recommendations as Quinton's new decisions.
