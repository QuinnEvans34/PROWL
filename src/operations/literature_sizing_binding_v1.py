"""Offline N4 qualification binding. Cooperative guards; no live acquisition entry point.

The separate qualification capability authorizes invented child areas only. S1's
unchanged setup capability supplies identity checks and the shared writer lease;
its SetupWriter is never begun or used to authorize a sizing job. Parser children
write delegated descriptors directly. Closing a handle only closes its descriptor.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import asdict, dataclass
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import sys
import time

from src.operations import literature_storage_v1 as s1
from src.retrieval.sizing_v1.fsio import LockHeld, LockUnsupported, check_rel
from src.retrieval.sizing_v1.runner import CODE_FILES, code_identity, run_sizing
from src.retrieval.sizing_v1.parser import WatchdogLauncher, InProcessLauncher, PsMemoryProbe, POLL_SECONDS

S2_IDENTITY = "791be77ffc96c17aaaf23a8b588c52bf8db1a82ddaa959d41ad217da318f4d53"
BASE = "https://binding.invalid/pubmed/baseline/"
UPDATE = "https://binding.invalid/pubmed/updatefiles/"
MESH = "https://binding.invalid/mesh/invented.xml"
RUNTIME_FILES = (*CODE_FILES, "src/operations/literature_storage_v1.py",
                 "src/operations/literature_sizing_binding_v1.py",
                 "scripts/diagnostics/literature_sizing_binding_qualification_v1.py",
                 "scripts/diagnostics/literature_storage_setup_v1.py",
                 "tests/test_literature_sizing_binding_v1.py",
                 "tests/fixtures/literature_sizing_binding_v1/README.md",
                 "tests/fixtures/literature_sizing_binding_v1/invented.xml")


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def runtime_pins(repo):
    return tuple((name, hashlib.sha256(s1.read_regular(str(Path(repo) / name))).hexdigest())
                 for name in RUNTIME_FILES)


@dataclass(frozen=True)
class QualificationCapability:
    version: str
    purpose: str
    approval: str
    qualification_id: str
    executor: str
    run_ids: tuple[str, ...]
    signed_copy_sha256: str  # Invented configuration identity, never a Run S signature.
    s2_identity: str
    source_sha256: str
    code_pins: tuple[tuple[str, str], ...]
    s1: s1.Capability
    primary_device: int
    internal_device: int
    payload_cap_bytes: int = s1.MiB
    journal_cap_bytes: int = 64 * 1024
    seconds: int = 120

    def validate(self, repo):
        s1.require(self.version == "literature-sizing-binding-v1" and
                   self.purpose == "offline_invented_qualification" and
                   self.approval == "D-346/D-350", "unapproved binding capability")
        self.s1.validate()
        s1.member(self.qualification_id)
        s1.member(self.executor)
        s1.require(1 <= len(self.run_ids) <= 2 and len(set(self.run_ids)) == len(self.run_ids),
                   "invalid bounded run inventory")
        for name in self.run_ids:
            s1.member(name)
        for pin in (self.signed_copy_sha256, self.source_sha256):
            s1.require(isinstance(pin, str) and len(pin) == 64 and
                       all(c in "0123456789abcdef" for c in pin), "invalid control pin")
        s1.require(self.s2_identity == S2_IDENTITY and code_identity(repo) == self.s2_identity,
                   "S2 identity drift")
        s1.require(self.code_pins == runtime_pins(repo), "binding/S1/runtime code drift")
        for value, maximum in ((self.payload_cap_bytes, s1.MiB),
                               (self.journal_cap_bytes, 64 * 1024), (self.seconds, 120)):
            s1.require(type(value) is int and 0 < value <= maximum, "qualification limit invalid")
        s1.require(type(self.primary_device) is int and type(self.internal_device) is int and
                   self.primary_device != self.internal_device, "invalid device inventory")

    def roots(self):
        name = "binding-qualification-" + self.qualification_id
        return {area: str(Path(root) / name) for area, root in
                (("scratch", self.s1.scratch_root), ("receipts", self.s1.receipts_dir),
                 ("fallback", self.s1.fallback_dir))}


def load_capability(path, expected_sha256):
    data = s1.read_regular(str(path))
    s1.require(hashlib.sha256(data).hexdigest() == expected_sha256, "capability transport mismatch")
    value = json.loads(data)
    value["s1"] = s1.Capability(**value["s1"])
    value["run_ids"] = tuple(value["run_ids"])
    value["code_pins"] = tuple(tuple(p) for p in value["code_pins"])
    return QualificationCapability(**value)


def recursive_bytes(fd, expected_device):
    """Stat only the named literature area; no symlink/hardlink or device crossing."""
    total = 0
    for name in os.listdir(fd):
        s1.require(name not in (".", ".."), "unsafe directory member")
        named = os.stat(name, dir_fd=fd, follow_symlinks=False)
        if stat.S_ISDIR(named.st_mode):
            child = os.open(name, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            try:
                s1.require(s1.device(child) == expected_device and s1.stamp(child) ==
                           (named.st_dev, named.st_ino), "directory switched or device crossed")
                total += recursive_bytes(child, expected_device)
            finally:
                os.close(child)
        else:
            s1.require(stat.S_ISREG(named.st_mode) and named.st_nlink == 1,
                       "unsafe/nonregular literature member")
            total += named.st_size
    return total


class GuardedFile:
    def __init__(self, fs, area, rel, fd, mode):
        self.fs, self.area, self.rel = fs, area, rel
        self.stream = io.FileIO(fd, mode, closefd=True)
        self.identity = s1.stamp(fd)

    def _check(self):
        self.fs._guard(self.area)
        with self.fs._parent(self.area, self.rel) as (parent, name):
            named = os.stat(name, dir_fd=parent, follow_symlinks=False)
            held = os.fstat(self.stream.fileno())
            s1.require(stat.S_ISREG(named.st_mode) and named.st_nlink == held.st_nlink == 1 and
                       self.identity == s1.stamp(self.stream.fileno()) ==
                       (named.st_dev, named.st_ino), "file path substituted")

    def write(self, data):
        self._check()
        self.fs._reserve(self.area, len(data))
        written = self.stream.write(data)  # Charge before writes; never refund a failed/short write.
        if written != len(data):
            raise OSError("short guarded write; partial bytes retained and charged")
        return written

    def read(self, size=-1):
        self._check()
        return self.stream.read(size)

    def seek(self, *args):
        self._check()
        return self.stream.seek(*args)

    def flush(self):
        self._check()
        self.stream.flush()

    def fileno(self):
        self._check()
        return self.stream.fileno()

    def close(self):
        self.stream.close()  # No named commit, truncation, rename, deletion or guard on cleanup.

    @property
    def closed(self):
        return self.stream.closed

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


class DescriptorLock:
    def __init__(self, fd):
        self.fd = fd

    def release(self):
        if self.fd is not None:
            os.close(self.fd)
            self.fd = None


class GuardedSizingFs:
    def __init__(self, storage, lease, cap, repo, *, clock=time.monotonic):
        cap.validate(repo)
        s1.require(storage.cap == cap.s1 and lease.storage is storage and lease.active and
                   storage.held_lock is not None, "wrong or inactive S1 lease")
        self.storage, self.lease, self.cap, self.repo, self.clock = storage, lease, cap, str(repo), clock
        self.seal = digest(asdict(cap))
        self.started = clock()
        self.active_run = None
        self.charged = dict(scratch=0, receipts=0, fallback=0)
        self.locks = {}
        self._roots = cap.roots()

    def _lease_check(self):
        s1.require(self.lease.active and self.storage.held_lock is not None and
                   self.lease.storage is self.storage, "closed/wrong writer lease")
        s1.require(digest(asdict(self.cap)) == self.seal, "capability changed")
        s1.require(self.clock() - self.started <= self.cap.seconds, "qualification wall cap")
        held = os.fstat(self.storage.held_lock)
        s1.require(stat.S_ISREG(held.st_mode) and held.st_nlink == 1, "unsafe held writer lease")

    def _guard(self, area):
        s1.require(area in self._roots, "wrong filesystem area")
        self._lease_check()
        self.storage._registry()
        if area == "fallback":
            obs = self.storage._observe(self.storage.internal, internal=True,
                                        remaining=self.cap.journal_cap_bytes)
            expected = self.cap.internal_device
        else:
            obs, internal = self.storage.verify(remaining=40 * s1.GiB)
            expected = self.cap.primary_device
            s1.require(internal["device"] == self.cap.internal_device, "internal device drift")
        s1.require(obs["device"] == expected, "pinned device drift")
        with self.storage._checked_dir(self._roots[area], expected):
            pass
        for (locked_area, name), lock in self.locks.items():
            if lock.fd is not None and locked_area == area:
                with self.storage._checked_dir(self._roots[area], expected) as fd:
                    named = os.stat(name, dir_fd=fd, follow_symlinks=False)
                    s1.require(stat.S_ISREG(named.st_mode) and named.st_nlink == 1 and
                               (named.st_dev, named.st_ino) == s1.stamp(lock.fd), "signed lock replaced")
        return expected

    def observe(self):
        self._guard("scratch")
        primary, _ = self.storage.verify(remaining=40 * s1.GiB)
        return primary

    def roots(self):
        self._lease_check()
        return dict(self._roots)

    def display(self, area, rel):
        s1.require(area in self._roots, "wrong area")
        return str(Path(self._roots[area]).joinpath(*check_rel(rel)))

    def prepare_areas(self):
        """Exclusive, capability-scoped qualification children, never live sizing-* roots."""
        self._lease_check()
        primary, internal = self.storage.verify(remaining=40 * s1.GiB)
        s1.require(primary["device"] == self.cap.primary_device and
                   internal["device"] == self.cap.internal_device, "pinned device drift")
        for area, root in self._roots.items():
            expected = self.cap.internal_device if area == "fallback" else self.cap.primary_device
            with self.storage._checked_dir(str(Path(root).parent), expected) as fd:
                os.mkdir(Path(root).name, 0o700, dir_fd=fd)
                os.fsync(fd)
            with self.storage._checked_dir(root, expected):
                pass

    @contextmanager
    def _parent(self, area, rel):
        parts = check_rel(rel)
        s1.require(area == "scratch" or len(parts) == 1, "nested journal path")
        expected = self.cap.internal_device if area == "fallback" else self.cap.primary_device
        with self.storage._checked_dir(self._roots[area], expected) as root:
            if len(parts) == 1:
                yield root, parts[0]
            else:
                path = str(Path(self._roots[area]) / parts[0])
                with self.storage._checked_dir(path, expected) as child:
                    yield child, parts[1]

    def _usage(self, area):
        expected = self.cap.internal_device if area == "fallback" else self.cap.primary_device
        with self.storage._checked_dir(self._roots[area], expected) as fd:
            current = recursive_bytes(fd, expected)
        base = {"scratch": self.cap.s1.scratch_root, "receipts": self.cap.s1.receipts_dir,
                "fallback": self.cap.s1.fallback_dir}[area]
        with self.storage._checked_dir(base, expected) as fd:
            cumulative = recursive_bytes(fd, expected)
        return current, cumulative

    def _reserve(self, area, count):
        current, cumulative = self._usage(area)
        limit = self.cap.payload_cap_bytes if area == "scratch" else self.cap.journal_cap_bytes
        global_limit = 40 * s1.GiB if area == "scratch" else 64 * s1.MiB
        used = max(current, self.charged[area])
        s1.require(used + count <= limit and cumulative + count <= global_limit,
                   "cumulative area quota exceeded")
        self.charged[area] = used + count

    def mkdir_exclusive(self, area, rel):
        self._guard(area)
        s1.require(area == "scratch" and rel == "sizing-" + str(self.active_run),
                   "unscoped scratch directory")
        with self._parent(area, rel) as (fd, name):
            os.mkdir(name, 0o700, dir_fd=fd)
            os.fsync(fd)
        self._guard(area)

    def create_exclusive(self, area, rel):
        self._guard(area)
        parts = check_rel(rel)
        if area == "scratch":
            s1.require(len(parts) == 2 and parts[0] == "sizing-" + str(self.active_run),
                       "unscoped payload path")
        else:
            suffix = ".fallback.jsonl" if area == "fallback" else ".jsonl"
            s1.require(rel == "run-S-" + str(self.active_run) + suffix, "unscoped journal path")
        self._reserve(area, 0)
        with self._parent(area, rel) as (fd, name):
            out = os.open(name, os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=fd)
            try:
                s1.require(stat.S_ISREG(os.fstat(out).st_mode) and os.fstat(out).st_nlink == 1,
                           "unsafe created file")
                os.fsync(fd)
                return GuardedFile(self, area, rel, out, "wb")
            except BaseException:
                os.close(out)
                raise

    def open_read(self, area, rel):
        self._guard(area)
        with self._parent(area, rel) as (fd, name):
            out = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
            try:
                held = os.fstat(out)
                s1.require(stat.S_ISREG(held.st_mode) and held.st_nlink == 1, "unsafe read file")
                return GuardedFile(self, area, rel, out, "rb")
            except BaseException:
                os.close(out)
                raise

    def list(self, area, prefix="", suffix=""):
        expected = self._guard(area)
        with self.storage._checked_dir(self._roots[area], expected) as fd:
            names = os.listdir(fd)
            for name in names:
                check_rel(name)
                named = os.stat(name, dir_fd=fd, follow_symlinks=False)
                s1.require(stat.S_ISDIR(named.st_mode) or
                           (stat.S_ISREG(named.st_mode) and named.st_nlink == 1), "unsafe listed member")
            return sorted(n for n in names if n.startswith(prefix) and n.endswith(suffix))

    def fsync_dir(self, area, subdir=""):
        expected = self._guard(area)
        if subdir:
            s1.require(area == "scratch" and len(check_rel(subdir)) == 1, "unsafe subdir fsync")
        with self.storage._checked_dir(str(Path(self._roots[area]) / subdir), expected) as fd:
            os.fsync(fd)

    def lock(self, area, rel):
        self._guard(area)
        s1.require(area == "receipts" and rel == "run-S-" + self.cap.signed_copy_sha256[:16] + ".lock",
                   "unscoped signed-copy lock")
        with self._parent(area, rel) as (parent, name):
            fd = os.open(name, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600, dir_fd=parent)
            try:
                held = os.fstat(fd)
                s1.require(stat.S_ISREG(held.st_mode) and held.st_nlink == 1, "unsafe lock file")
                try:
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError as exc:
                    raise LockHeld("signed-copy lock held") from exc
                except OSError as exc:
                    raise LockUnsupported("signed-copy locking unsupported") from exc
                os.fsync(fd)
                os.fsync(parent)
                lock = DescriptorLock(fd)
                self.locks[(area, rel)] = lock
                return lock
            except BaseException:
                os.close(fd)
                raise

    def remove_own_empty(self, area, rel, fh):
        fh._check()
        s1.require(os.fstat(fh.fileno()).st_size == 0, "not an owned empty file")
        raise s1.StorageRefused("no-delete preservation: empty journal retained for review")

    def run(self, config, *, transport, launcher, run_id, clock=time.monotonic, wall=lambda: "invented"):
        self.cap.validate(self.repo)
        s1.require(type(transport) is InventedTransport and transport.identity == self.cap.source_sha256,
                   "only frozen invented transport is authorized")
        s1.require(type(launcher) in (WatchdogLauncher, InProcessLauncher), "unqualified parser launcher")
        if type(launcher) is WatchdogLauncher:
            s1.require(launcher.memory_cap == 4 * s1.GiB and
                       type(launcher.probe) is PsMemoryProbe and launcher.python == sys.executable and
                       isinstance(launcher.poll, (int, float)) and 0 < launcher.poll <= POLL_SECONDS,
                       "watchdog executable/monitor/bounds differ from qualification")
        s1.require(run_id in self.cap.run_ids and self.active_run is None, "wrong/nested run")
        roots = self.roots()
        for area, field in (("scratch", "scratch_root"), ("receipts", "receipts_dir"),
                            ("fallback", "fallback_dir")):
            s1.require(config[field] == roots[area], "config path mismatch")
        s1.require(config["signed_copy_sha256"] == self.cap.signed_copy_sha256 and
                   config["executor"] == self.cap.executor and
                   config["tool_code_hash"] == self.cap.s2_identity and
                   config["volume_uuid"] == self.cap.s1.external_uuid and
                   config["volume_mount"] == self.cap.s1.external_mount and
                   config["headroom_floor_bytes"] == max(self.cap.s1.headroom_floor_bytes,
                                                        s1.floor(self.observe()["capacity_bytes"])) and
                   (config["baseline_url"], config["update_url"], config["mesh_url"]) ==
                   (BASE, UPDATE, MESH), "config identity/floor/source mismatch")
        self.active_run = run_id
        try:
            fs = self

            class QualificationLauncher:
                def parse(self, **kwargs):
                    fs._guard("scratch")
                    current, _ = fs._usage("scratch")
                    kwargs["scratch_allowance"] = min(kwargs["scratch_allowance"],
                                                       fs.cap.payload_cap_bytes - current)
                    kwargs["seconds_left"] = min(kwargs["seconds_left"],
                                                 max(0, fs.cap.seconds - (fs.clock() - fs.started) - 5))
                    old_periodic = kwargs.get("periodic")

                    def periodic():
                        fs._guard("scratch")
                        fs._reserve("scratch", 0)
                        if old_periodic:
                            old_periodic()
                    kwargs["periodic"] = periodic
                    return launcher.parse(**kwargs)

            return run_sizing(config, transport=transport, clock=clock, wall=wall, volume=self,
                              fs=self, launcher=QualificationLauncher(), run_id=run_id,
                              code_hash=self.cap.s2_identity)
        finally:
            self.active_run = None


class InventedResponse:
    def __init__(self, body, *, head=False):
        self.body, self.offset = body, 0
        self.status, self.headers, self.header_bytes = 200, {"content-length": str(len(body))}, 180
        self.head = head

    def read(self, count):
        value = self.body[self.offset:self.offset + count]
        self.offset += len(value)
        return value

    def close(self):
        pass


class InventedTransport:
    """In-memory, frozen invented responses; cannot contact DNS, TLS or a socket."""
    def __init__(self, routes):
        self.routes = dict(routes)
        self.identity = digest({" ".join(k): hashlib.sha256(v).hexdigest()
                                for k, v in sorted(self.routes.items())})
        self.calls = []
        self.on_request = None

    def request(self, method, url, timeout):
        s1.require(url.startswith("https://binding.invalid/"), "non-invented origin")
        s1.require(self.identity == digest({" ".join(k): hashlib.sha256(v).hexdigest()
                                          for k, v in sorted(self.routes.items())}), "invented source drift")
        self.calls.append((method, url))
        if self.on_request:
            self.on_request(method, url)
        return InventedResponse(self.routes[(method, url)], head=method == "HEAD")
