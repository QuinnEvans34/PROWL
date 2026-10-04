# Claude S2 handback: run S sizing tool `sizing_v1` (2026-10-03)

**For phone screens:** S2 is implemented and passes its offline tests on invented data:
- 131 sizing tests: 130 passed, 1 skipped as root;
- the full retrieval suite: 312 passed, 1 skipped.

An independent reviewer went over it in three rounds, and every confirmed defect is fixed. **Run S
is not ready to sign.** It still needs:
- S1: the live storage binding, which is Codex's;
- a native run of these tests on Quinton's Mac;
- S3, then S4.

The CLI refuses live execution. Nothing was downloaded, installed, signed or committed, and no
network was used.

## Authority and scope

- **Dispatch:** Quinton, 2026-10-03 ("Approve both": S1 and S2). Also Quinton's memory-cap
  decision, "Watchdog is fine". Both are logged in RUNNING-LOG.
- **Packet:** `docs/capstone/operations/CLAUDE-PLAN07-S2-PACKET-DRAFT-2026-10-03.md`, SHA-256
  `0ac7eb939e9cfaf17d4c0365f0e29aaa439b5aabe4d2b1c10d8a9622635b80ef`.
- **Source authority:** ACQUISITION-PLAN run S, SHA-256 `a2be620c6b03373bc6a84b6cd88bf4f2177313bddc1992da7f3991ca713fc826`.
  No cap or check was weakened. Where the plan left something open, the more conservative reading
  was taken (listed below).
- **Writes:** only the packet's allowlist, plus this handback and the RUNNING-LOG entry. Not
  touched:
  - the P3 producers, schemas or tests;
  - shared decisions, roots, the registry, operations files or dependency manifests.

## Files (all new)

| Path | SHA-256 |
|---|---|
| `src/retrieval/sizing_v1/__init__.py` | `29b70aecaf2a35e3833404fc8ab2396f759ae752bfb29ed8062adab326290928` |
| `src/retrieval/sizing_v1/listings.py` | `ad25719ee617bdbd19d54748fa7ddae0e5330fa15f6a340e104c105b581e3d17` |
| `src/retrieval/sizing_v1/transfer.py` | `a5c35774fb20c988ac42db2ce36e7f6e6392b6576b73bb4138088a471f1e9c90` |
| `src/retrieval/sizing_v1/parser.py` | `81c0da39dad9189c93d2e153e0f96ea8eeaba33ef84934de22ba52a157c03a6a` |
| `src/retrieval/sizing_v1/journal.py` | `07025b2efcb36188b741f70f94453bf9416f8b322b5d9ff3dd50594dfbeae983` |
| `src/retrieval/sizing_v1/runner.py` | `8453ee5b9b6b909c5c6217460300d5296df7f96fd1870cba904342b4580e5025` |
| `scripts/retrieval/run_s_sizing_v1.py` | `e433bf9df28619c46fc82512e2a6ceb46374ea853d8eef7f21df67e2a7b97c15` |
| `tests/retrieval/test_sizing_v1_listings.py` | `6d06cd475085a34298b0ee56a760555ab5de63ae2a72a3ab75297c5cafda53f2` |
| `tests/retrieval/test_sizing_v1_transfer.py` | `ef29c6668c906351b0eaa1834a591dcc346d6a09dc9754c2f24b0c7ea954e8b7` |
| `tests/retrieval/test_sizing_v1_parser.py` | `d62759a67868c12893c8b0ab0a41c05fdeeb5cc1e117581375b0111d1bfd65a0` |
| `tests/retrieval/test_sizing_v1_journal.py` | `9d07c8d285aabcc5220470a93b5b795d5d997284c71fcab0bafd276219e8968f` |
| `tests/retrieval/test_sizing_v1_runner.py` | `ec48d14f13f1d04c4f076cdd7696f7f71a9b2c4ff38fd4dfe5cd94fac9b27584` |
| `tests/retrieval/fixtures/sizing_v1/README.md` | `d5b270d84d3389f8b2b66a6bd2a640448dc845c9aecf10c0b5210d1c019f2a0e` |
| `tests/retrieval/fixtures/sizing_v1/pubmed_style_doctype.xml` | `58970b32ea772e70271fe6fcf6a8342eca9b55289481f349ead568a63651a65e` |
| `tests/retrieval/fixtures/sizing_v1/update_with_deletes.xml` | `3ff5a04c07c3df8d8ffa6c1e3ff1327d76a5a6a5ea37393996691871e58afad1` |
| `tests/retrieval/fixtures/sizing_v1/external_entity.xml` | `d74786196fb74147374eb66dc6b4e582e5f8df7486a9d06d50455d2893083a23` |
| `tests/retrieval/fixtures/sizing_v1/billion_laughs.xml` | `eac14200ca0e171d347e828377ebde8b449a4e5de32b9ff67c1e4dfaba46794b` |
| `tests/retrieval/fixtures/sizing_v1/internal_entity.xml` | `ad8c9527a59d981a1ac089cfe901968ddf2c113c80535d02feb42ee9d5619e86` |
| `tests/retrieval/fixtures/sizing_v1/undeclared_entity.xml` | `b9cb2eefc291022ab626a41094bf4f16480c9bf0fe78c70f1cf348042247263a` |
| `tests/retrieval/fixtures/sizing_v1/malformed.xml` | `43fdc5a22376dc55d6dcd9e2fd66018475919ceabbc4220f3de4e31b897642c3` |
| `tests/retrieval/fixtures/sizing_v1/wrong_root.xml` | `c11a224a5d6926ff7ed442b8765274cd832ea98223cf4b8ad82ff7710709482e` |

**Tool code identity** (`runner.code_identity`: SHA-256 over the seven code files, in a fixed
order): `814b89c5dac055b59df4c28ff14cca008d7831d63ba31b418e380831fad837aa`.

**Fixture provenance:** every fixture was written by hand and is invented: PMIDs 9000000xx, all
titles, abstracts and labels made up. No real PubMed record or abstract was used. Listings, `.md5`
bodies and gzip samples are generated inside the tests.

**Side effect:** a Python 3.10 `py_compile` check on the device created `__pycache__/` folders
under `src/retrieval/sizing_v1/` and `scripts/retrieval/`. They are covered by `.gitignore`
line 48.

## Test evidence

| Where | Python / expat | Command | Result |
|---|---|---|---|
| Claude's cloud workspace (Linux) | 3.11.15 / 2.6.1 | `python3 -m pytest -q tests/retrieval -k sizing_v1` | 130 passed, 1 skipped (the directory-permission case skips as root) |
| Same | same | `python3 -m pytest -q tests/retrieval` | 312 passed, 1 skipped (P3: 182 passed, unchanged) |
| Same, repeated 10x | same | full retrieval suite | 10/10 green after the flaky-assertion fix noted below |
| Cowork device VM | 3.10.12 | `python3 -m py_compile` on all code and tests | compiled (that VM has no pytest) |
| **Quinton's Mac (native)** | 3.12.13 venv | `.venv-prowl/bin/python -m pytest -q tests/retrieval -k sizing_v1` | **Not run yet.** Required before S2 acceptance |

`ruff check --select F,E9,B` is clean. ruff was installed only in Claude's cloud workspace; it is
not a project dependency.

**Network denied in tests:** every sizing test module patches `socket.connect`,
`socket.create_connection` and `getaddrinfo` to fail. The watchdog tests start local child
processes (a sleeper, a noisy writer and the parser worker), and the socket-watch tests use
`socket.socketpair()`. Nothing leaves the machine.

## How the packet's requirements are met (decisions recorded for the signed copy)

1. **Injectable interfaces.** Transport, clock, volume probe, memory probe and parser launcher are
   all injected. No live volume probe or writer exists here (S1).
2. **Network counting** (the packet asks for this to be stated exactly). The counter covers HTTP
   status lines and headers, reconstructed from the parsed response, plus every body byte
   returned. That includes redirects, `HEAD`, listings, `.md5` files, retries and partial or failed
   attempts.
   - Not seen: TLS and TCP framing, chunked-encoding framing, and bytes buffered by a failing read.
   - To cover those, the cap stops at **10 GiB minus a 1% reserve**. This is conservative. The
     signed copy should confirm the reserve.
   - Each request first reserves 64 KiB for headers; oversized headers are charged and then stop
     the run.
   - Counters are checked before bytes are accepted, so they can be reached but never exceeded.
3. **Bounded time.**
   - DNS runs in a thread, and DNS plus connect share one budget: min(5 min stall, time left).
   - The TLS handshake, header lines, chunk-size lines and body reads all run under a
     `SocketWatch` thread, which shuts the socket down when the limit passes. Body reads use
     `read1` with the socket timeout reset before each read.
   - Overshoot past the stall limit or the 2-hour deadline is at most one poll (0.5 s) plus the
     1 s timeout floor.
   - There is one transfer at a time and at most 2 attempts per file.
4. **Never substitute.**
   - Only the literal signed origins are contacted, with default ports normalised and userinfo
     refused.
   - A redirect must keep the last path segment and query.
   - Names are resolved only from the frozen listing bytes. Unexpected types, judged by magic
     bytes, stop the run.
   - A listing without a closing `</html>` is treated as truncated and stops preflight.
5. **Listings.** The parser targets an Apache-style autoindex and fails closed if the format
   differs.
   - Displayed sizes are rounded, so the planning bound is the displayed value plus one step of
     its last digit (`22M` counts as 23 MiB).
   - Each sample is fetched with that bound as `max_body`.
   - The cap pre-check adds 11 header reserves.
6. **Re-runs.** Counters are cumulative per signed-copy hash.
   - A first run starts only after proof that no earlier journal exists, and that no `sizing-*`
     scratch folder lacks a journal.
   - A second run inherits counters from the earlier terminal journal, primary plus fallback.
   - A run is refused if a journal is missing, truncated or ambiguous, or if it would be a third
     run.
   - A per-signed-copy `flock` prevents two runs at once.
   - **Samples are never reused:** a re-run downloads again under the shared caps. The plan allows
     reuse only on a checksum match; not reusing is stricter.
7. **XML safety, standard library only (pyexpat).**
   - expat must be at least 2.4.1, and parameter-entity parsing is set to `NEVER`, so the DTD is
     tolerated but never read.
   - External entity references, every entity declaration and undeclared entity references are
     all refused.
   - **The finite internal-expansion bound is therefore 0 user-defined entities.** Only the five
     predefined entities and character references expand.
   - Malformed XML, a truncated or corrupt gzip, and a wrong root element all fail closed, with
     the file named.
8. **Expansion and scratch.**
   - gzip is decompressed as a stream, with at most 1 MiB out per call. More than 20 times the
     compressed size gives `stopped_expansion_guard`.
   - Decompressed bytes are streamed, not written. They are still **charged to the scratch cap**,
     the conservative reading of the plan.
   - Parser output and manifests are charged before they are written.
   - A failed parse is charged its on-disk output plus 20 times the compressed size (an upper
     bound).
9. **Memory (Quinton's decision).** The parser runs as a child process, and its RSS is polled
   every 0.5 s (`ps -o rss=` on macOS, `/proc` on Linux). The child is killed above 4 GiB
   (`stopped_memory_cap`).
   - A monitor failure, or no reading while the child is alive, kills it (fail closed).
   - The 60-second volume and free-space check also runs in this loop during parsing.
   - Overshoot is bounded by the growth within one poll interval. This is **not** an OS-enforced
     limit, and the injected-RSS tests do not claim one.
10. **Output.**
    - One gzip JSON Lines file per sample (level 6, mtime 0, deterministic), plus a manifest.
    - Every row and the manifest carry `sizing_only: true`.
    - There is no cross-file event log, final state or snapshot.
    - The proposed partition row format is `prowl-parsed-partition-v0-proposed`, with fields
      `title, abstract[label,text], journal_title, journal_iso, pub_year, pub_date_raw, languages,
      publication_types[ui,name], mesh[ui,name,major,qualifiers], keywords, doi, pmcid,
      date_revised`. **P5 must use the same fields and compression or re-measure.**
    - `refuse_sizing_only` is fail-closed: it accepts only rows explicitly marked
      `sizing_only: false`. Any future selection or promotion reader must call it, which is a
      P5/P6 design constraint.
11. **Journal.**
    - Exclusive creation with a directory fsync. Each line is written, flushed and fsynced.
    - The sequence number is reserved before the write, and signals are deferred during it.
    - If the primary fails, only journal events go to the internal fallback, and the run stops.
      Readers accept the failed line whether it landed, was torn or is absent.
    - There is exactly one final status: `completed`, `stopped_<reason>` or `interrupted`. An
      unexpected exception gives `stopped_internal_error`. A missing final status means
      incomplete.
12. **CLI.** `--check` validates a sidecar against the signed Markdown copy and lists every unmet
    requirement. `--execute` always refuses in `sizing_v1`.

## Coverage of the packet's test table

| Row | Covered by |
|---|---|
| Listings | listings tests: exact 1334, extras, missing/duplicate/ambiguous/missing `.md5`, 2 highest valid updates, sizes; runner: listing fetched once (frozen bytes) |
| MeSH/precheck | `HEAD` size counted, 1 GiB fallback, oversize stop, pre-check stops before any sample, names/sizes journaled first |
| Streaming | exact-fit and next-byte overflow (network, scratch), header reserve, redirects, retries, partials, MD5/HEAD counted, collisions, one open transfer, 2 attempts, stall/timeout, deadline (fake and the real 7,200 s via the runner), socket-watch on real `http.client` |
| Reruns | fresh proof, inheritance, missing/truncated/ambiguous/fallback-only refused, third refused, lock, orphan scratch folder; reuse is N/A (never reused) |
| Integrity | valid/invalid MD5, SHA-256, absent MD5 noted, both attempts failing terminal; mismatch re-downloaded in the next run |
| Volume/space | start floor+40 GiB, before-file and 60 s checks, mount change, observation failure, periodic check during parse, no payload on the fallback |
| Parser | records/deletes, ratios, streaming chunk sizes, multi-member gzip, 20x guard boundary, scratch allowance, malformed refusal, memory cap through the runner with the live launcher |
| XML | external-DTD DOCTYPE parses with zero fetches; external, billion-laughs, internal and undeclared entities refused; old expat refused |
| Output | sizing-only rows and manifest, consumer refusal (including unmarked and uncheckable input), deterministic bytes, scratch holds no snapshot or event log |
| Journal | exclusive/durable/ordered, single final, primary loss (landed, torn, absent), fallback failure leaves it incomplete, real SIGTERM, unencodable text, directory fsync failure |
| Representation | file-sequence positions, observed years, largest ratio x 1.5 projection |
| Scope | AST check: the tool imports only the standard library and its own package; no live socket, install, database, MPS or storage-root write |

**Gaps that remain:**
- the "completed only after every file is verified" guard cannot be reached, so it has no
  negative test;
- the "wrong role" volume check belongs to the S1 binding;
- streaming release is shown by design, not by a memory measurement.

## Independent review

A separate Claude subagent reviewed the code in three adversarial rounds, with no network and no
edits.

- **Round 1:** 3 HIGH, 5 MEDIUM and 10 LOW findings. The HIGH ones:
  - unexpected exceptions skipped the final status;
  - blocking reads were not bounded by the deadline;
  - journal sequence breaks on volume loss or a signal blocked a valid re-run.
- **Round 2:** confirmed most fixes. It found that the read bound did nothing for
  `Connection: close` responses (http.client drops `conn.sock`), and three LOW regressions.
- **Round 3:** confirmed the socket-watch and journal fixes, with no CRITICAL or HIGH findings.
  Its last three items were fixed afterwards, each with its own test:
  - the connect phase had no deadline: fixed with the shared DNS and connect budget, plus the
    handshake running under the watch;
  - a race between a trip and close: fixed with a locked stop;
  - an unlink error could mask the refusal: fixed.

  Those post-round-3 fixes were verified by tests, not by a fourth review.

One test assertion was flaky (1 in about 15 runs). It assumed the socket watch, rather than the
per-receive timeout, would fire first; either is correct, and the assertion now accepts both.

## Unmet requirements before run S can be signed

1. **S1 binding (Codex).** A live volume probe (UUID, mount, role, writable, `statvfs` free) and
   the controlled writer for `scratch/literature/sizing-<run>` and
   `artifacts/literature/receipts/`, wired into `run_sizing`. `sizing_v1` exposes the interfaces
   but has no live binding, so execution is refused.
2. **Native qualification on Quinton's Mac.** Run the test command above in `.venv-prowl`, and
   check:
   - `ps`-based RSS readings;
   - `flock` and directory `fsync` on the external APFS volume and on the internal fallback
     folder;
   - real TLS through `SocketWatch`.

   Linux results alone do not satisfy native acceptance.
3. **Listing format.** The autoindex parser was written without fetching a live NLM listing (no
   network, no exposure). At run time it fails closed if the format differs.
4. **Proxy.** The live transport connects directly and ignores `HTTPS_PROXY`. If the Mac needs a
   proxy for NLM, report it before signing.
5. **The signed copy must state** (alongside the run S fields):
   - the watchdog memory method;
   - the 1% network reserve;
   - that decompressed bytes count toward scratch;
   - partition format v0;
   - the tool code identity above.
6. **S3** capacity reading and **S4** Quinton's signature.

**Stop point:** Claude stops here. Nothing further is dispatched, nothing is signed, run S is not
executed, and S1 is not enabled.
