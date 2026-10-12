# PROWL synthetic PostgreSQL platform — Phase 1 handback

## Phase 2 progress — October 12

Quinton cleaned internal storage; the new admission passed at 136,375,734,272 bytes
(127.0 GiB) free. The historical storage blocker below is resolved.
The pinned image was pulled and the dedicated external synthetic database launched.
PostgreSQL 17.10 / pgvector 0.8.2 passed the synthetic SQL smoke. Clean restart,
deliberate process-crash recovery, and dump/restore into a fresh database in the same instance
preserved the 1,001-row inventory hash. The owned container was stopped and verified after
each run; data and logs remain preserved. No real literature or model embeddings were used.

Evidence: `outputs/prowl/pgvector-phase2-20261012/` (image-pull log, admission,
preparation correction note, smoke and recovery results, runtime metrics and recovery script).
A preparation-only Python API error was corrected before any database creation in that attempt.
The runner now samples during startup, waits for TCP readiness (avoiding the temporary init server),
and verifies actual stopped state. 28 model-free tests pass; Compose validates.

The subsequent [100k trial and separate-instance restore](../../docs/capstone/retrieval/PGVECTOR-PHASE2-RESULTS-2026-10-12.md)
completed. Restrictive-filter HNSW recall failed the 95% bar; exact hybrid search was fast in this
synthetic measurement. Quinton selected exact-first; subsequent client-latency/MPS checks passed
(205 ms broad p95, 211 ms concurrent, 1.73% GPU throughput reduction). Phase 2 engineering is ready
for review. See the linked report for retained failed attempts, exact scope and limitations.
No USB/power-loss claim follows.

Status: configuration and model-free checks ready for review, October 12, 2026.
The sections below retain the Phase 1 setup and historical admission; Phase 2 progress above
supersedes the earlier no-launch state and storage blocker.

## Selected layout

Local client → `127.0.0.1:55432` → Compose project `prowl-retrieval-smoke` → external bind mount
`/Volumes/PROWL-Data/PROWL/scratch/literature/pgvector-smoke-01`.

The drive must match UUID `22750B93-2F3F-499D-87F5-902981BFAB59`. The bind mount never creates
its source directory. Data and failed instances are retained. The unrelated `nw-postgres` is untouched.
A dedicated VM would add storage/runtime management; test this isolated bind mount first.

Image candidate: `pgvector/pgvector:0.8.2-pg17`, pinned to its verified ARM64 manifest
`sha256:88b17bc7a7dd6ef73d46c1b15aaa5936d50acb24e4a78713e134c579bf359e25`.
This is a fixed trial candidate, not a claim to the newest release. Actual PostgreSQL patch/extension
versions are emitted by the SQL trial. Registry metadata was inspected without an image pull.
Compressed layers are approximately 156 MB; extracted image/VM growth is not measured yet.
Docker Compose v5.5.1 accepted the configuration.

Limits: 2 CPUs, 2 GiB memory and equal memory+swap limit, 128 PIDs, 128 MiB shared memory,
20 MB rotated container logs. No automatic restart or implicit image pull. SIGINT fast PostgreSQL
shutdown with 60 seconds grace. The runner always attempts stop and reports its result.
It does not remove the container or data. A host crash/SIGKILL can bypass Python cleanup; verify
actual container state before subsequent work.

## Resource admission and current blocker

- Internal: 100 GiB free floor plus 4 GiB reserved for image/runtime overhead before launch.
- External: 400 GiB free floor plus 8 GiB trial data reservation.
- Trial: 30-minute deadline; data ceiling 8 GiB. Runtime sampling triggers stop on a breach.
  Sampling is not a filesystem quota and may overshoot while a command/stop is completing.
- Docker VM memory must remain <=15% host physical memory; do not change global settings.
- A local exclusive coordinator lock and existing-project check prevent duplicate cooperating runs.

Read-only observation: internal free 110,665,408,512 bytes (~103.1 GiB), external free
2,257,657,192,448 bytes. Port 55432 was available, correct volume/context verified, VM memory
8,317,267,968 bytes within the bar. Preflight refused only the internal reservation requirement.
At least approximately 1 GiB additional internal free space is needed; remeasure before selecting
any storage action. No cleanup or reduction of safeguards was performed.

## Commands

From the repository root, read-only admission (does not require a real password or data directory):

```sh
.venv-prowl/bin/python scripts/retrieval/check_pgvector_platform.py check --config infra/retrieval/platform.example.json
```

After Phase 1 review, Phase 2 must resolve space, separately acquire the pinned image with measured
internal growth, create the fresh external directory and a private password file (mode 600, at least
24 random bytes), and copy the template to an ignored `.env.platform.json` with its real password
file path. Do not put credentials in the JSON or Git. No psycopg installation is needed for this
synthetic stage; it uses container-local psql.

The bounded smoke command, for Phase 2 only:

```sh
.venv-prowl/bin/python scripts/retrieval/check_pgvector_platform.py run --config infra/retrieval/.env.platform.json --output outputs/prowl/pgvector-smoke-01
```

Use the runner rather than a bare `compose up`: admission and supervision live in the runner.
The output directory must be fresh. A later trial requires a new external data directory and a
review of the preserved previous container; do not delete/retry failures automatically.

For manual emergency stop, set the three interpolation variables to the reviewed data path,
password file path and port, then use `docker --context desktop-linux compose -p prowl-retrieval-smoke -f infra/retrieval/compose.yaml stop -t 60`.
This targets only the PROWL project. Inspect actual state after any interrupted supervisor.

## What is tested now / what Phase 2 must demonstrate

23 model-free tests cover path escape/symlink rejection, wrong/missing mount identity, occupied port,
space thresholds, memory-independent stop predicates, blocked launch, preservation of existing data,
and private credential requirements. Compose schema validation passes. No SQL behavior is claimed
from these tests.

`smoke.sql` prepares 1,000 synthetic rows plus one forbidden best-match sentinel. It asserts eligible
counts, exact vector ranking, lexical/empty results, duplicates/dimension rejection and deterministic
rank fusion. The synthetic three-dimensional vectors are not a production encoder decision.

Phase 2 runs this SQL and investigates any failure, then supplies separate restart/crash/dump-restore
and full 100k HNSW/filter/latency/MPS coexistence evidence required by P4a. The smoke runner alone
is not the full P4a acceptance harness. Canonical passage contracts and real embeddings remain later.

References: [phase dashboard](../../docs/capstone/retrieval/PGVECTOR-IMPLEMENTATION-PLAN-2026-10-12.md),
[Docker Compose services](https://docs.docker.com/reference/compose-file/services/),
[pgvector](https://github.com/pgvector/pgvector).
