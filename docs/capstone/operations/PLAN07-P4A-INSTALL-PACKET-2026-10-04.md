# P4a-B1 platform install/trial authorization — draft

**Draft only, not approved or dispatched.** D-345 approves preparing this scope after the imaging
queue and running any later approved trial in an idle window. This packet names the first bounded
layout-B trial; it does not declare full P4a complete. Layout-C comparison and Quinton's final
layout decision remain owed by PHASES P4a. No runtime, image layer, database or accelerator trial
was started while preparing this document.

## Observed inventory and exact candidate

Native local reads, October4: `/Applications/Docker.app` is **Docker Desktop4.70.0, build224270**;
CLI `/usr/local/bin/docker` is **29.4.0, build9d7ad9f**. Current context `desktop-linux` points to
`unix:///Users/quintonevans/.docker/run/docker.sock`. That socket and `/var/run/docker.sock` are
absent. The engine was not contacted or started. Container/image/volume inventory is therefore
unknown, not empty. macOS denied reading `settings-store.json` even in the native read; memory,
CPU, disk-image placement/size and sharing settings remain unverified.

Preferred first candidate: reuse this installed Docker Desktop version without updating/reinstalling
it; pull exactly the ARM64 PostgreSQL/pgvector image below after authorization. No second runtime
or source build in B1. The official pgvector Dockerfile derives its image from PostgreSQL and pins
the extension source tag. [pgvector v0.8.6 Dockerfile](https://github.com/pgvector/pgvector/blob/v0.8.6/Dockerfile)

| Image property | Exact observed metadata / proposed pin |
|---|---|
| Repository/tag | `pgvector/pgvector:0.8.6-pg17-trixie` (discovery label only) |
| Multi-arch index | `sha256:724a4041afdb1750446e3f6b5cfa8f3b0ac5a2cf538ddfa6bfee4f94c2fa85c6` |
| Executable image | `pgvector/pgvector@sha256:ced026f3d5bc5d6b46663fc6fb0b213b174fe15278cac4e4c7a80798ffed843c` |
| Platform | `linux/arm64`; require native architecture, no emulation |
| Image config | `sha256:6be6b68f521cb0281db83467e669dcc53783de73f84eb777ba10e8bce09beac4` |
| PostgreSQL | config `PG_VERSION=17.11-1.pgdg13+2`, `PG_MAJOR=17`; verify server version during trial |
| pgvector | expected0.8.6 from tag/source; verify extension control/catalog version before using |
| PGDATA | `/var/lib/postgresql/data` |
| Declared stop | config `SIGINT`; use120-second grace, require clean-shutdown log |
| Compressed layer total | 161,441,471bytes; expanded/runtime footprint not inferred from it |

Pins were obtained from [publisher tag metadata](https://hub.docker.com/v2/repositories/pgvector/pgvector/tags/0.8.6-pg17-trixie)
and the hash-verified ARM64 manifest/config via Docker Registry. Only public metadata was fetched:
manifest+config14,707bytes, **zero image layers**. Local metadata evidence:
`outputs/prowl/PLAN07-S1-SETUP-20261004/p4a-image-metadata.json` and `p4a-image-config.json`.
Tag drift never substitutes an image; a missing digest stops preparation. A later version/security
review can replace the candidate only by a new reviewed pin, never silent latest-tag use.

## Proposed storage and resource envelope

Before approval/activation, finish the existing Docker inventory and show any exact global-setting
diff. Shared settings affect other projects; Docker stores images/containers in its shared VM disk.
[Docker Desktop settings](https://docs.docker.com/desktop/settings-and-maintenance/settings/),
[Mac disk-image storage](https://docs.docker.com/desktop/troubleshoot-and-support/faqs/macfaqs/).
Do not shrink/move/reset/prune its disk or stop unrelated containers. If existing work cannot meet
the proposed caps without interference, return a separately pinned layout-C dedicated-runtime
packet; do not install it automatically.

| Proposed bound | Limit / condition |
|---|---|
| VM | At most6 GiB RAM,2 CPUs; any shared setting change requires displayed inventory and separate explicit approval. Meets proposed15% of64 GiB ceiling, subject to measurement |
| One DB container |4 GiB hard memory,4 GiB combined memory+swap (no extra container swap),2 CPUs,256 PIDs; verify enforcement before load. No GPU/device access |
| Trial area | Fresh `/Volumes/PROWL-Data/PROWL/runtime/literature/p4a-b1-20261004/`; proposed only, not created/registered.16 GiB total new external bound including data, WAL/index/logs, failed original, restore/rebuild and exports |
| Each DB instance |4 GiB data+WAL+indexes/logs; one active instance at a time; preserve stopped original during new-instance recovery |
| Internal runtime increment |4 GiB maximum additional allocated disk footprint including image/cache/runtime growth; record baseline, monitor allocated bytes and free-space delta |
| Independent synthetic recovery | At most512 MiB new under `/Users/quintonevans/PROWL-Backups/p4a-b1-20261004/`, inside the existing fixed18,318,645,873-byte whole-root ceiling and registered20 GiB; fresh whole-root measurement must leave this allowance. No reset/deletion/ceiling increase |
| Free space | External `max(100 GiB,10% usable capacity)` plus remaining16 GiB; internal100 GiB plus remaining runtime/recovery allowance. Fresh readings before approval/start, each phase and every60 seconds |
| Exposure | Invented seed42 data only; no literature, imaging/source mounts, real labels, model downloads or P4b schemas |
| Network | Registry image pull only after approval, bounded512 MiB/15 minutes including retries; trial local127.0.0.1:55432 only, no external service/listener. Credentials ignored local control/Keychain, never logs/Git |
| Time |60 minutes total including pull; at most45 minutes runtime, no automatic rerun/extension. Statement timeout30 seconds; index build≤10 minutes |

Container flags enforce memory/CPU limits; a VM memory limit is a separate Desktop setting and is
not established merely by a container limit. Verify swap-limit support. [Docker resource constraints](https://docs.docker.com/engine/containers/resource_constraints/).
The database trial is outside S1 literature scratch/receipt capabilities; S1 setup grants it no access.

## Proposed once-only trial and stop point

After concrete approval, inventory first; activate only the approved runtime/settings and pinned
image, freeze the exact synthetic request/storage capability and verify image/stop signal/version.
Use a generic table,100,000 invented passages/384-dimensional vectors at most, not P4b contracts.
Measure sequential/random I/O, DB/WAL/index size, internal VM growth and memory. Rehearse clean
stop/start with SIGINT/120s, exactly one process-crash drill, and dump/restore plus rebuild into a
fresh instance with count/content-hash checks. Preserve originals and failures; do not unplug USB
or simulate power loss.

Evaluate exact search plus one HNSW-default configuration, including filtered queries and iterative
scans. Report approximate recall@10 against exact (target≥0.95), top10 hybrid p95 at100k (proposed
≤500ms) and pinned query/sample counts. Any expansion to other index/precision options returns to
the defined PHASES measurement trigger and a fresh scope; no sweep. A bounded synthetic MPS
coexistence comparison may run only during an approved idle window, never beside a real imaging
experiment; proposed throughput loss≤10%. Current task runs none of these workloads.

Stop on time/storage/memory limits, volume/role/UUID drift, failed monitor, unsupported limit,
unclean shutdown, recovery/content mismatch, failed coexistence/latency/recall bar or shared-work
conflict. Gracefully stop only the trial container; preserve evidence and return options. A crash
drill's single intentional SIGKILL is scoped to its disposable synthetic container. No unrelated
process kill or automatic cleanup.

Exit B1 with measured evidence and a proposed layout-C comparison packet. Full P4a still requires
the comparison, final pinned platform record and Quinton's approved layout. P4b additionally requires
accepted P3 contracts and its own psycopg3 dependency permission. No install approval is requested
or implied by writing this draft. Next P4a preparation begins with the unreadable shared settings/
inactive-engine inventory gap; show the concrete settings impact before asking for authorization.
