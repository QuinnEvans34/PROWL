# S2 v1.1 native verification — N2 handback, October 4, 2026

**Complete:** native sizing tests144passed, full retrieval326passed; no failures or skips.
All22handback pins and code identity match before and after testing. No Claude file changed.

**Ownership settled by Quinton in this chat:** “Keep N4/N5 in the other chat; this chat verifies
N2 and hands back”. The other chat retains the binding and local commit. D-346–D-348 and the N3
shared-contract implementation already existed when this task began; they were not overwritten,
reimplemented or duplicated here. This N2 handback is the stop point, not a follow-on dispatch.

## Native results

Quinton's Mac, existing `.venv-prowl`: Python3.12.13, expat2.7.4. Both commands exited0.
The environment disabled bytecode and pytest cache writes; test-created invented files/child
processes used their normal disposable test areas. Sizing tests deny network. Native execution
was needed for the watchdog's process observations; no real volume binding or sizing job ran.

| Command | Native result |
|---|---|
| `.venv-prowl/bin/python -m pytest -q tests/retrieval -k sizing_v1` |144passed,182deselected in4.03s; no skips|
| `.venv-prowl/bin/python -m pytest -q tests/retrieval` |326passed in4.64s; no skips|

Exact command environment for both: `PYTHONDONTWRITEBYTECODE=1` and
`PYTEST_ADDOPTS='-p no:cacheprovider'`. The144selected sizing tests plus182other retrieval tests
reconcile to326. Claude's Linux root-only skip is not present natively. There are no failures to
relay verbatim. These results do not establish an S1-bound live writer, signed Run S, S3 capacity,
N4 acceptance, full-project test acceptance or acquisition permission.

## Exact input verification

Tool code identity before and after:
`df585e2b10a69f55e24db8cc0f96822151a43d52be15ad5bb4917bd9a0a24d4e`.
Computed using the tool's `runner.code_identity` over its eight fixed path/NUL/byte/NUL members.
All22pins match [Claude's v1.1 handback](../retrieval/CLAUDE-S2-V1.1-HANDBACK-2026-10-04.md):
13explicit code/test rows plus9unchanged fixture pins carried from
[the original handback](../retrieval/CLAUDE-S2-HANDBACK-2026-10-03.md).
V1.1 handback SHA-256:
`3d00e92aac6f12ae4a052c70988a630522bd5af3ad210e40cc846d8a1f13b2c6`.
No old814b89c5identity or21pin qualification was substituted for this revision.

| Path | Verified SHA-256 |
|---|---|
| `src/retrieval/sizing_v1/__init__.py` | `3eec5d35e8cf5470af53bbea177f11024dd5db801a25a0291cefbbe73311789d` |
| `src/retrieval/sizing_v1/fsio.py` | `d2c6db413c72b4b54169a316410036aab8fa58218081f16814a89d8557714705` |
| `src/retrieval/sizing_v1/journal.py` | `90b52ab491a8cea11eb87d99129eabbd561847a8c8475f0d7dc8db8abe270cd5` |
| `src/retrieval/sizing_v1/parser.py` | `a2081337d8a9516090acdfb722c1e9ee47e7509d9d5243ea568ed4adeeb317f8` |
| `src/retrieval/sizing_v1/runner.py` | `8f42f526164a2a412859a104ca9a19d8bf0af12286914d2791a57cde6df782bf` |
| `src/retrieval/sizing_v1/transfer.py` | `fb8c159abd6fada2f1c9160c85e72c61a602c329090900f1a33656d13ff2cb1a` |
| `src/retrieval/sizing_v1/listings.py` | `ad25719ee617bdbd19d54748fa7ddae0e5330fa15f6a340e104c105b581e3d17` |
| `scripts/retrieval/run_s_sizing_v1.py` | `e433bf9df28619c46fc82512e2a6ceb46374ea853d8eef7f21df67e2a7b97c15` |
| `tests/retrieval/test_sizing_v1_journal.py` | `3c4c2218b528016f5253594e7ed494333af87e6544bb7207dfb97fa0be384e29` |
| `tests/retrieval/test_sizing_v1_listings.py` | `6d06cd475085a34298b0ee56a760555ab5de63ae2a72a3ab75297c5cafda53f2` |
| `tests/retrieval/test_sizing_v1_parser.py` | `b181314332e0f3479ccb64018dbcea8d9c0d6b4c5a84363e4d09c83edf6a9c33` |
| `tests/retrieval/test_sizing_v1_runner.py` | `cad03a1036390d7a22679d4f4684cff3eead9ec0c4b49ca7683837d251503424` |
| `tests/retrieval/test_sizing_v1_transfer.py` | `b1de4cf728cf6ca978d372c42b6bcfb1a5c622d4e98b70cba0118cd258037dca` |
| `tests/retrieval/fixtures/sizing_v1/README.md` | `d5b270d84d3389f8b2b66a6bd2a640448dc845c9aecf10c0b5210d1c019f2a0e` |
| `tests/retrieval/fixtures/sizing_v1/pubmed_style_doctype.xml` | `58970b32ea772e70271fe6fcf6a8342eca9b55289481f349ead568a63651a65e` |
| `tests/retrieval/fixtures/sizing_v1/update_with_deletes.xml` | `3ff5a04c07c3df8d8ffa6c1e3ff1327d76a5a6a5ea37393996691871e58afad1` |
| `tests/retrieval/fixtures/sizing_v1/external_entity.xml` | `d74786196fb74147374eb66dc6b4e582e5f8df7486a9d06d50455d2893083a23` |
| `tests/retrieval/fixtures/sizing_v1/billion_laughs.xml` | `eac14200ca0e171d347e828377ebde8b449a4e5de32b9ff67c1e4dfaba46794b` |
| `tests/retrieval/fixtures/sizing_v1/internal_entity.xml` | `ad8c9527a59d981a1ac089cfe901968ddf2c113c80535d02feb42ee9d5619e86` |
| `tests/retrieval/fixtures/sizing_v1/undeclared_entity.xml` | `b9cb2eefc291022ab626a41094bf4f16480c9bf0fe78c70f1cf348042247263a` |
| `tests/retrieval/fixtures/sizing_v1/malformed.xml` | `43fdc5a22376dc55d6dcd9e2fd66018475919ceabbc4220f3de4e31b897642c3` |
| `tests/retrieval/fixtures/sizing_v1/wrong_root.xml` | `c11a224a5d6926ff7ed442b8765274cd832ea98223cf4b8ad82ff7710709482e` |

## Files, decisions and exact next starting point

This chat created only this review document in the repository. It changed no implementation,
fixtures, planning log, shared decisions, registry, occupied contract files or checkpoint scope.
No commit/push, download, signature, S3, install, database, D-085 producer migration, imaging run,
real scratch `sizing-*` child or follow-on dispatch occurred. No new permission decision is needed
for the completed N2 verification; Quinton has already assigned N4/N5 to the other chat.

The other chat starts from this native result and
[the approved binding packet](PLAN07-S1-S2-BINDING-PACKET-2026-10-04.md), using the actual
v1.1 fsio contract and unchanged S1 lease. It verifies exclusive file ownership and imaging-idle
status before any invented binding rehearsal, then finishes N4 or lists its unmet requirements.
It owns the refreshed exact checkpoint and the approved one local commit/no push under N5.
Include this review with the v1.1 handback/hook proposal and latest pins; do not modify Claude's
files or turn the CLI refusal into launch permission. Report unresolved interface requirements
instead of patching another lane. Stop after that chat's requested handback.
