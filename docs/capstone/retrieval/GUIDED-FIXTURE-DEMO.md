# Guided evidence fixture demonstration

Quinton selected this first AI expert implementation on October 9, 2026: guided reviewer
questions, one saved response per request, and transparent evidence/scope/failure messages.
Tracking: [W01-30](https://trello.com/c/3qTiK9p4).

This is a working synthetic adapter, not a qualified literature expert. The approved grounded-response
and interface plans remain the production target. No live search, generation, medical source claims,
patient interpretation, or training is performed. The fixture is deliberately sparse: unanswered
topics remain unanswered rather than acquiring invented clinical content.

## Run locally

From the repository root, start the isolated response service:

```sh
.venv-prowl/bin/python scripts/serve_evidence_fixture.py
```

Then run the existing UI (`npm --prefix ui run dev`) and open **Guided evidence questions** in the
review workspace. The Vite development server proxies `/evidence-fixture` to loopback port 8011.
The legacy model server is not required. The panel sends only a random request ID and a predefined
question ID; no case ID, CT, prediction, measurement, reference mask, or free text is submitted.

The service writes to `outputs/prowl/evidence-fixture/responses` by default. Use `--output-dir`
to choose another local destination. The API binds only to 127.0.0.1; it is a development service,
not a production deployment or authenticated multiuser writer. The static production build has no
fixture writer attached and reports service unavailable when a request cannot be completed.

## Visible paths

- **Supported by the selected fixture:** one exact quotation from the synthetic workflow passage,
  plus its title, locator, authorship/rights notice and source text. No invented publication metadata.
- **Not enough evidence:** contour, measurements, anatomy and model limitations have no supporting
  passages in this fixture set. No claims/citations are supplied. Missing evidence does not prove
  that evidence does not exist.
- **Outside PROWL's scope:** the diagnosis boundary demonstration refuses patient diagnosis,
  malignancy, stage, prognosis and treatment.
- **Unavailable/unconfirmed:** transport, save, or response-validation failure produces an alert,
  no evidence conclusion and no claim of a confirmed save. Retrying keeps the same request ID.
  Unavailable is a client operation state; no fictitious saved response is fabricated during outage.

Partial answers and conflicting evidence remain defined in the broader contract but are not exercised
by this first slice. The UI provides no general-purpose prompt field or clinical conversation history.

## Saved-response rules

The version `prowl-guided-fixture-response-v1` identifies a deliberately narrow demo artifact,
not the final Plan 07 response schema. It includes request/question identity, response state/message,
atomic extractive claims, full citations, limitations, fixture digest, adapter version, null model/index,
completion time and a canonical content SHA-256. The backend revalidates hashes and exact fixture
content on read. The browser checks response/request identity, fixed state/message, claims and citation
contents before rendering; it does not independently certify clinical truth or cryptographic provenance.

Each unique request ID yields one JSON artifact. A retry returns that existing artifact; reusing its ID
for another question fails. Publication uses a flushed temporary file and an exclusive atomic link,
so a concurrent retry cannot overwrite an existing response or expose a partial file. Disk failures
never return a successful save acknowledgment. Files survive browser refresh and process restart;
the download/read endpoint resolves them by response ID. They are local artifacts, not backups.

The panel shows only one response at a time. Changing question clears the displayed result. Changing
case remounts the panel and aborts/fences pending results; the service may still complete a previously
submitted save, but it never associates that generic response with the new case. Case-package evidence
attachment and browsing saved response history remain future integration work.

## Verification

- `tests/test_guided_evidence_fixture.py`: fixed routes, exact support, concurrent retry, cold store
  reload, request conflicts, unsafe/unknown input, tampering and failed disk publication.
- `ui/tests/GuidedEvidencePanel.test.jsx`: supported/refused/insufficient paths, unconfirmed save,
  identical retry, case-switch cancellation, altered responses and service errors.
- `ui/tests/browser/guided-evidence.spec.js`: real local API, file reload/retry, supported and refusal
  rendering, unavailable isolation and responsive screenshots using the synthetic viewer.

Use Node 24 for the installed UI test dependencies; the machine's Node 20 runtime fails before test
collection in the installed jsdom/undici combination. No dependency installation was needed.

## Next implementation choice

Review the wording and interaction together, then connect the retrieval owner's validated passage
contract to this flow. Live generation follows explicit citation/support and refusal checks. A source
supporting a statement is evidence, not a guarantee that the statement is clinically true for a patient.
