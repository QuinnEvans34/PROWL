# SUP-01 implementation handback — October6,2026

## Phone handback

1. **Finished:** the approved four-file invented initialization auditor. **85targeted native checks
   pass**, no failures/skips. The resource-qualified run completed in1.449988seconds, peak RSS
   **428,605,440bytes (about0.40GiB)**, below5minutes/3GiB. It used invented CPU tensors only.
2. **Files/checks:** new module, tests, exact contract and this results file; routine packet/queue/
   AGENTS/notebook pointers updated. All11reviewed existing source/test/design pins and the
   protected historical notebook tail remain unchanged. No current full-suite claim.
3. **Decision needed:** no unfinished SUP-01 implementation decision. The next actual-source
   preparation needs a bounded public provenance/license/overlap review, followed by an exact
   checkpoint/serialization/read-budget proposal. That follow-on work is not dispatched here.
4. **Restart:** review this handback, then the
   [packet's later source/integration steps](SUPREM-INITIALIZATION-QUALIFICATION-PACKET-2026-10-06.md).
   SUP-01's complete tests need no repeat. Do not open/import the actual checkpoint or alter a
   scratch consumer on the strength of this invented result.

Authority: Quinton's “Great, move onto the next” after the T06 preparation handback. This approval
covers SUP-01's in-memory invented four-file slice, routine repair/checks and a handback stop.
Trello W01-09 records implementation separately from the completed W01-08 drafting task.

## What changed and what it proves

[The new auditor](../../../src/models/segmenter_initialization_audit_v1.py) takes supplied bounded
CPU tensor mappings and pinned invented candidate/policy/inventory controls. It validates exact
schemas/types/domain, provenance-assessment placeholders, candidate identity and historical hash
refusal before inspecting tensors. It validates complete inventory, namespace, shape/dtype/finite
content and source/fresh content bindings before cloning. Unknown/missing/malformed inputs return
an explicit refusal with no replacement state. There is no partial load or silent scratch fallback.

On pass it returns the complete detached cloned destination state, loading every non-head tensor
and preserving exactly `conv_final.2.conv.bias`/`conv_final.2.conv.weight` from the bound fresh state.
Final-block normalization is loaded. State/report ordering is deterministic; output tensors cannot
mutate either input. Controls and CPU RNG are unchanged. Reports always state
`execution_authority='none'` and `evidence_domain='invented_weights_only'`.

The full-network test constructed fresh32-output and seed42 three-output SegResNets through the
existing factory, without a forward/backward. Distinct invented source values verified every
backbone tensor and both retained heads. The complete returned state strict-loaded into a fresh
disposable destination; its content hash matched the report. The fresh destination hash remained
`3ee49a533f03db4c2cea5c9cdec512004c7f904873149fa04002781980640add`.

Negative tests cover missing/extra backbone and normalization keys, absent/wrong heads, dtype,
NaN/Infinity, non-tensors, sparse/meta/noncontiguous/quantized/negative-view inputs, namespace
mixing/collisions/repetition, invalid keys, altered pins/content, class/seed/policy changes, prior/
capstone/unknown hashes, renamed forbidden hashes, unresolved rights/overlap, real evidence,
control/tensor limits and malformed schemas. Failure tests prohibit cloning before refusal and
check unchanged caller state. An oversized logical view is rejected before content scan/allocation.
Guarded tests prohibit file open, deserialization/save, socket, forward/backward and optimizer calls.

This establishes component mechanics with invented controls. It does not establish authentic
source/rights/overlap evidence, original serialized-file/tensor linkage, quality of pretrained
features, seed-generation history or a real checkpoint's compatibility. Factory completeness relies
on the caller's independently reviewed pinned full signature, exercised by the full invented test.
The exact [contract](../imaging/SEGMENTER-INITIALIZATION-AUDIT-CONTRACT-V1.md) states these limits.

## Four new files and pins

| File | SHA-256 |
|---|---|
| `src/models/segmenter_initialization_audit_v1.py` | `3c20657349a0f6ca923de9dc2d8b633968ead2af1b56be399ec8c43873ce9530` |
| `tests/test_segmenter_initialization_audit_v1.py` | `ca7632cad0cdaa7fc8ac80df2fb8653384e7fc07a0a15063d3339c0931b78c91` |
| `docs/capstone/imaging/SEGMENTER-INITIALIZATION-AUDIT-CONTRACT-V1.md` | `5bfe1554c10352004a7274ad56e903347d284a9eca5c2315243aa5797a18759a` |
| This results file | Current handback; no self-referential hash |

Runtime imports are `collections`, `copy`, `hashlib`, `json`, `math` and already installed `torch`.
It imports no existing training session, source reader or historical loader. Tests reuse the model
factory for invented construction only. No dependency or new directory was introduced.
Current source pins were checked against the
[T06 review inventory](SUPREM-INITIALIZATION-REVIEW-2026-10-06.md), not substituted into D-335.

## Targeted verification and retained reporter failure

First check:

```text
PYTHONDONTWRITEBYTECODE=1 /usr/bin/time -l .venv-prowl/bin/python -m pytest -q tests/test_segmenter_initialization_audit_v1.py -p no:cacheprovider
75 passed, 3 warnings in2.14s
2.62 real /1.64 user /0.39 sys
time: sysctl kern.clockrate: Operation not permitted
```

Pytest passed; `/usr/bin/time -l` then failed its sandboxed resource query, returning overall exit1
and no accepted RSS evidence. This diagnostic-reporter failure is retained here. It was not a model,
source-read or experiment failure, and consumed no scientific request.

Review subsequently added explicit negative-view refusal and ten total additional checks, including
paired backbone omission, autograd isolation, malformed top-level controls, each rights reference
and strict boolean import flags. Final targeted invocation used the same pytest arguments via
`pytest.main` under a native Python wrapper. `signal.alarm(300)` bounded duration; a plugin checked
`resource.getrusage(RUSAGE_SELF).ru_maxrss` at test setup/teardown against3GiB and exited on excess.
It checked the final wall/RSS envelope as well. RSS checks occur at test boundaries, not as an
operating-system memory hard limit; the measured peak is safely below the envelope.

```text
85 passed, 3 warnings in1.31s
exit_code:0
wall_seconds:1.449988
peak_rss_bytes:428605440
rss_limit_bytes:3221225472
seconds_limit:300
within_envelope:true
```

Exact final wrapper, executable from the verified root:

```python
import json, resource, signal, time
started = time.monotonic()
import pytest
seconds_limit, rss_limit = 300, 3 * 1024**3
class Budget:
    def check(self):
        if (time.monotonic() - started > seconds_limit or
                resource.getrusage(resource.RUSAGE_SELF).ru_maxrss > rss_limit):
            pytest.exit('SUP-01 CPU test envelope exceeded', returncode=1)
    def pytest_runtest_setup(self, item): self.check()
    def pytest_runtest_teardown(self, item, nextitem): self.check()
signal.alarm(seconds_limit)
code = pytest.main(['-q', 'tests/test_segmenter_initialization_audit_v1.py',
                   '-p', 'no:cacheprovider'], plugins=[Budget()])
signal.alarm(0)
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
elapsed = time.monotonic() - started
print(json.dumps(dict(exit_code=int(code), wall_seconds=elapsed, peak_rss_bytes=rss,
                     within_envelope=rss <= rss_limit and elapsed <= seconds_limit)))
raise SystemExit(int(code) if rss <= rss_limit and elapsed <= seconds_limit else 1)
```

Run with `.venv-prowl/bin/python`, `PYTHONDONTWRITEBYTECODE=1`; bytecode and pytest cache writes
were disabled. The3warnings comprise two installed PyTorch `torch.jit.interface` deprecations and
one deprecation from constructing the invented quantized tensor that the auditor rejects. No
failure or skip occurred. No previous successful suites or model qualification were repeated.
Syntax/import inspection passed; document/source-pin/whitespace checks and Trello readback are
recorded after the final handback reconciliation below.

Native context readback: Python3.12.13, Darwin/arm64, PyTorch2.13.0 and MONAI1.6.0. Existing
`requirements/locks/macos-arm64-py312.txt` SHA-256 is
`525f827150da4bfbc727e317c6646c80bd00f464ac604f9e9d4e128828ffedfb`.
These values identify this targeted check; no dependency update or new full installed-inventory
qualification was performed.

**Final static/tracking checks:** all3new source/test/contract hashes above match; all11reviewed
old source/test/design hashes match. Syntax and the runtime import allowlist pass.170local Markdown
link occurrences resolve across the four new files and four maintained pointers. Scoped whitespace
checks pass. Existing producer/test/lock diffs are empty. The marker-to-end historical notebook
SHA-256 remains `df37ba7cdec1ae1fb941feb5e60a87ef599f28118d5415a50032397bbe96b997`.
Trello [W01-09](https://trello.com/c/mDAd9N7t/31-w01-09-implement-invented-suprem-initialization-audit)
was updated, moved to Done and marked complete; final readback verified its exact description,
list and completion flag. No pending tracking-sync blocker remains. Routine pointers comprise
AGENTS, the live queue, the approved packet and the current notebook section; the hours log and
other lanes' shared records were not edited.

## Exact remaining boundary

No real checkpoint bytes, images/reference/cache arrays, model forwards/backwards/updates,
accelerator calls, source stat/header/hash job, acquisition, literature sizing/signature,
installation/database work, external writes, deletion, Git commit/push or experiment registration
occurred. No existing source/test file changed. Existing scratch import gates, initialized hash,
session/checkpoint/recovery producers and consumed requests remain closed and unchanged.
No source inventory, data permission, cohort/hold or fixed18,318,645,873-byte backup ceiling changed.
D-335 is still the latest completed imaging experiment. Retrieval/N4 retain their existing owner.

Next preparation: public metadata review of the recorded SuPreM artifact's revision/license/
pretraining-data relationship, then a concrete actual-file/serialization/read-budget proposal.
After actual-source acceptance, a separate versioned pretrained session and cold recovery slice
is still necessary. Varied multiclass/development/verified-negative metadata selection remains
visible. Changing initialization creates a new comparison; the192-update duration-only planning
choice retains its scratch initialization. None of those follow-ons is automatically dispatched.
Human hours remain unknown; unattended agent time is excluded and no hours were credited.
