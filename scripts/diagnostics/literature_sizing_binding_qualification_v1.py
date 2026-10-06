"""Prepare/execute one frozen invented N4 rehearsal; no live Run S branch."""
from __future__ import annotations

import argparse
from dataclasses import asdict
import gzip
import fcntl
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import time
import threading

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from src.operations import literature_storage_v1 as s1
from src.operations import literature_sizing_binding_v1 as b
from src.retrieval.sizing_v1.parser import WatchdogLauncher
from src.retrieval.sizing_v1.journal import read_events, plan_run, fallback_name, primary_name
from scripts.diagnostics.literature_storage_setup_v1 import imaging_idle, FaultProbe


def invented_transport():
    body = gzip.compress((REPO / "tests/fixtures/literature_sizing_binding_v1/invented.xml").read_bytes(),
                         mtime=0)
    samples = ("pubmed26n0001.xml.gz", "pubmed26n0667.xml.gz", "pubmed26n1334.xml.gz")
    updates = ("pubmed26n1340.xml.gz", "pubmed26n1341.xml.gz")

    def listing(names):
        lines = []
        for name in names:
            lines.extend((f'<a href="{name}">{name}</a> 2026-01-01 00:00 {len(body)}',
                          f'<a href="{name}.md5">{name}.md5</a> 2026-01-01 00:00 60'))
        return ("<html><pre>\n" + "\n".join(lines) + "\n</pre></html>").encode()

    routes = {("GET", b.BASE): listing([f"pubmed26n{i:04d}.xml.gz" for i in range(1, 1335)]),
              ("GET", b.UPDATE): listing([f"pubmed26n{i:04d}.xml.gz" for i in range(1335, 1342)])}
    mesh = b"<?xml version=\"1.0\"?><DescriptorRecordSet><Invented/></DescriptorRecordSet>"
    routes[("GET", b.MESH)] = routes[("HEAD", b.MESH)] = mesh
    for base, names in ((b.BASE, samples), (b.UPDATE, updates)):
        for name in names:
            routes[("GET", base + name)] = body
            routes[("GET", base + name + ".md5")] = f"MD5({name})= {hashlib.md5(body).hexdigest()}\n".encode()
    return b.InventedTransport(routes)


def config_for(cap, fs):
    roots = cap.roots()
    obs = fs.observe()
    return dict(signed_copy_sha256=cap.signed_copy_sha256, baseline_url=b.BASE,
                update_url=b.UPDATE, mesh_url=b.MESH, mesh_name="invented.xml",
                scratch_root=roots["scratch"], receipts_dir=roots["receipts"],
                fallback_dir=roots["fallback"], executor=cap.executor, tool_code_hash=cap.s2_identity,
                user_agent="PROWL-invented-binding-only/1", memory_cap_bytes=4 * s1.GiB,
                expansion_limit=20, headroom_floor_bytes=max(cap.s1.headroom_floor_bytes,
                                                           s1.floor(obs["capacity_bytes"])),
                volume_uuid=cap.s1.external_uuid, volume_mount=cap.s1.external_mount)


def exclusive_json(path, value):
    with open(path, "x", encoding="utf-8") as fh:
        json.dump(value, fh, indent=2, sort_keys=True)
        fh.write("\n")
        fh.flush()
        os.fsync(fh.fileno())


def descriptor_inventory():
    result = {}
    for fd in range(512):
        try:
            st = os.fstat(fd)
            result[fd] = (st.st_dev, st.st_ino, st.st_mode)
        except OSError:
            pass
    return result


def prepare(args):
    # Local controls only. No qualification children or literature content writes here.
    out = Path(args.controls).resolve()
    s1.require(out.is_relative_to(REPO / "outputs/prowl"), "invented qualification requirement failed")
    out.mkdir(parents=True, exist_ok=False)
    raw = s1.read_regular(str(Path(args.s1_capability).resolve()))
    s1.require(hashlib.sha256(raw).hexdigest() == args.s1_capability_sha256, "invented qualification requirement failed")
    old = s1.Capability(**json.loads(raw))
    primary = s1.NativeVolume(old.external_mount, "literature")
    internal = s1.NativeVolume(old.internal_mount, "fallback")
    store = s1.LiteratureStorage(args.registry, old, primary=primary, internal=internal)
    p, i = store.verify(remaining=40 * s1.GiB)
    world = invented_transport()
    cap = b.QualificationCapability("literature-sizing-binding-v1", "offline_invented_qualification",
                                   "D-346/D-350", args.id, "codex-binding-qualifier",
                                   (args.id + "-success", args.id + "-failure"),
                                   b.digest(dict(invented=True, qualification=args.id)), b.S2_IDENTITY,
                                   world.identity, b.runtime_pins(REPO), old, p["device"], i["device"])
    cap.validate(REPO)
    exclusive_json(out / "capability.json", asdict(cap))
    payload = (out / "capability.json").read_bytes()
    exclusive_json(out / "request.json", dict(capability_sha256=hashlib.sha256(payload).hexdigest(),
                                             purpose=cap.purpose, run_ids=cap.run_ids, roots=cap.roots(),
                                             scenarios=["success", "invented_primary_observation_failure"],
                                             sentinels="exclusive denied-scope.txt in each child; bytes must match",
                                             locks="exclusive empty qualification-lock-probe in primary/fallback children",
                                             seconds=120, payload_cap_bytes=cap.payload_cap_bytes,
                                             receipts_cap_bytes=cap.journal_cap_bytes,
                                             fallback_cap_bytes=cap.journal_cap_bytes,
                                             imaging_idle_required=True, network=False, run_s=False))
    print(json.dumps(dict(controls=str(out), capability_sha256=hashlib.sha256(payload).hexdigest(),
                         request_sha256=hashlib.sha256((out / "request.json").read_bytes()).hexdigest(),
                         external_writes=False)))


def execute(args):
    # The one-shot marker is created before external writes; it is never removed/reset.
    cap = b.load_capability(args.capability, args.capability_sha256)
    cap.validate(REPO)
    controls = Path(args.capability).resolve().parent
    s1.require(controls.is_relative_to(REPO / "outputs/prowl"), "invented qualification requirement failed")
    request_raw = s1.read_regular(str(controls / "request.json"))
    s1.require(hashlib.sha256(request_raw).hexdigest() == args.request_sha256, "invented qualification requirement failed")
    request = json.loads(request_raw)
    s1.require(request["capability_sha256"] == args.capability_sha256 and request["roots"] == cap.roots(), "invented qualification requirement failed")
    idle = imaging_idle()
    exclusive_json(controls / "consumed.json", dict(capability_sha256=args.capability_sha256,
                                                   started=time.time(), imaging_idle=idle))
    start = time.monotonic()
    primary = FaultProbe(s1.NativeVolume(cap.s1.external_mount, "literature"))
    internal = s1.NativeVolume(cap.s1.internal_mount, "fallback")
    storage = s1.LiteratureStorage(args.registry, cap.s1, primary=primary, internal=internal)
    before = storage.verify(remaining=40 * s1.GiB)
    before_fds = descriptor_inventory()
    before_threads = {t.ident for t in threading.enumerate()}
    children = []
    old_popen = subprocess.Popen

    class TrackedPopen(old_popen):
        def __init__(self, *a, **kw):
            super().__init__(*a, **kw)
            children.append(self)
    subprocess.Popen = TrackedPopen

    def deny(*a, **kw):
        raise AssertionError("network forbidden in invented binding qualifier")
    original = (socket.socket.connect, socket.create_connection, socket.getaddrinfo)
    socket.socket.connect = socket.create_connection = socket.getaddrinfo = deny
    try:
        with storage.writer(cap.s1.writer_id) as lease:
            fs = b.GuardedSizingFs(storage, lease, cap, REPO)
            fs.prepare_areas()
            # Explicitly predeclared sentinel creation; fs create/write can never reach this name.
            sentinels = {}
            lock_checks = {}
            for area, root in fs.roots().items():
                dev = cap.internal_device if area == "fallback" else cap.primary_device
                with storage._checked_dir(root, dev) as fd:
                    sentinel = os.open("denied-scope.txt", os.O_CREAT | os.O_EXCL | os.O_WRONLY |
                                       os.O_NOFOLLOW, 0o600, dir_fd=fd)
                    try:
                        s1.write_all(sentinel, b"invented sentinel; never a payload or journal\n")
                    finally:
                        os.close(sentinel)
                    os.fsync(fd)
                sentinels[area] = hashlib.sha256(s1.read_regular(str(Path(root) / "denied-scope.txt"))).hexdigest()
                if area != "scratch":
                    with storage._checked_dir(root, dev) as fd:
                        first = os.open("qualification-lock-probe", os.O_CREAT | os.O_EXCL |
                                        os.O_RDWR | os.O_NOFOLLOW, 0o600, dir_fd=fd)
                        second = None
                        try:
                            fcntl.flock(first, fcntl.LOCK_EX | fcntl.LOCK_NB)
                            os.fsync(first)
                            os.fsync(fd)
                            second = os.open("qualification-lock-probe", os.O_RDWR | os.O_NOFOLLOW,
                                             dir_fd=fd)
                            try:
                                fcntl.flock(second, fcntl.LOCK_EX | fcntl.LOCK_NB)
                            except BlockingIOError:
                                lock_checks[area] = "competing descriptor refused"
                            else:
                                raise AssertionError("APFS qualification lock did not exclude")
                        finally:
                            if second is not None:
                                os.close(second)
                            os.close(first)
            cfg = config_for(cap, fs)
            success = fs.run(cfg, transport=invented_transport(), launcher=WatchdogLauncher(poll=0.05),
                             run_id=cap.run_ids[0])
            s1.require(success == "completed", "invented qualification requirement failed")
            index, inherited, prior = plan_run(fs, cap.signed_copy_sha256)
            s1.require(index == 2 and inherited["network_used"] > 0 and inherited["scratch_used"] > 0, "invented qualification requirement failed")
            world = invented_transport()

            def fault(method, url):
                if (method, url) == ("GET", b.BASE):
                    primary.failed = True
            world.on_request = fault
            failure = fs.run(cfg, transport=world, launcher=WatchdogLauncher(poll=0.05),
                             run_id=cap.run_ids[1])
            s1.require(failure == "stopped_internal_error", "invented qualification requirement failed")
            primary.failed = False
            events = read_events(fs, "receipts", primary_name(cap.run_ids[0]))
            fallback = read_events(fs, "fallback", fallback_name(cap.run_ids[1]))
            s1.require(events[-1]["status"] == "completed" and fallback[-1]["status"] == failure, "invented qualification requirement failed")
            s1.require(fallback[0]["event"] == "primary_lost", "invented qualification requirement failed")
            s1.require(all(fallback[-1]["counters"][k] >= v for k, v in inherited.items()), "invented qualification requirement failed")
            s1.require(len(lock_checks) == 2, "invented qualification requirement failed")
            for area, root in fs.roots().items():
                s1.require(hashlib.sha256(s1.read_regular(str(Path(root) / "denied-scope.txt"))).hexdigest() == sentinels[area], "invented qualification requirement failed")
            usage = {area: fs._usage(area) for area in fs.roots()}
            s1.require(usage["scratch"][0] <= cap.payload_cap_bytes, "invented qualification requirement failed")
            s1.require(usage["receipts"][0] <= cap.journal_cap_bytes, "invented qualification requirement failed")
            s1.require(usage["fallback"][0] <= cap.journal_cap_bytes, "invented qualification requirement failed")
            result = dict(status="invented_binding_qualification_passed", before=before,
                          success=success, failure=failure, inherited=inherited, prior=prior,
                          primary_events=events, fallback_events=fallback, sentinels=sentinels,
                          lock_checks=lock_checks,
                          area_bytes_and_cumulative=usage, charged=fs.charged,
                          s2_identity=cap.s2_identity, roots=fs.roots(), imaging_idle=idle,
                          registry_sha256=cap.s1.registry_sha256,
                          seconds=time.monotonic() - start, native_parser=True, network=False, run_s=False)
        s1.require(result["seconds"] <= 120, "invented qualification requirement failed")
        extra = {fd: identity for fd, identity in descriptor_inventory().items()
                 if fd not in before_fds or before_fds[fd] != identity}
        live_children = [p.pid for p in children if p.poll() is None]
        live_threads = [t.name for t in threading.enumerate()
                        if t.ident not in before_threads and t.is_alive()]
        s1.require(not extra and not live_children and not live_threads, "invented qualification requirement failed")
        result["cleanup"] = dict(tracked_children=len(children), live_children=live_children,
                                  extra_descriptors=extra, live_threads=live_threads)
        exclusive_json(controls / "result.json", result)
        print(json.dumps({k: result[k] for k in ("status", "success", "failure", "seconds", "run_s")}))
    finally:
        subprocess.Popen = old_popen
        socket.socket.connect, socket.create_connection, socket.getaddrinfo = original


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("prepare", "execute"))
    p.add_argument("--registry", required=True)
    p.add_argument("--controls")
    p.add_argument("--id")
    p.add_argument("--s1-capability")
    p.add_argument("--s1-capability-sha256")
    p.add_argument("--capability")
    p.add_argument("--capability-sha256")
    p.add_argument("--request-sha256")
    args = p.parse_args()
    (prepare if args.mode == "prepare" else execute)(args)


if __name__ == "__main__":
    main()
