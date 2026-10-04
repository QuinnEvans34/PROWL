"""D-341 bounded S1 setup. Cooperative capability guards, not an OS sandbox.

No acquisition, sizing runner, corpus publisher or database is exposed. NativeVolume
provides S2's observation interface; wiring a live sizing job requires a new adapter.
All external/fallback I/O uses no-follow directory descriptors and one flock lease.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
from pathlib import Path
import plistlib
import re
import stat
import subprocess
import time
from contextlib import contextmanager
from dataclasses import dataclass

import yaml

GiB = 1024 ** 3
MiB = 1024 ** 2
NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\Z")


class StorageRefused(RuntimeError):
    """Identity, scope, capacity or durability cannot be established."""


def require(ok, message):
    if not ok:
        raise StorageRefused(message)


def absolute(path):
    require(isinstance(path, str) and path.startswith("/") and
            str(Path(path)) == path and ".." not in Path(path).parts,
            "non-literal or unsafe absolute path")
    return path


def member(name):
    require(isinstance(name, str) and NAME.fullmatch(name) is not None and
            name not in (".", ".."), "unsafe member name")
    return name


@contextmanager
def directory(path):
    absolute(path)
    fd = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in Path(path).parts[1:]:
            new = os.open(component, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=fd)
            os.close(fd)
            fd = new
        yield fd
    finally:
        os.close(fd)


def read_regular(path):
    with directory(str(Path(path).parent)) as parent:
        fd = os.open(Path(path).name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
        with os.fdopen(fd, "rb") as stream:
            require(stat.S_ISREG(os.fstat(stream.fileno()).st_mode), "not a regular file")
            return stream.read()


def stamp(fd):
    s = os.fstat(fd)
    return s.st_dev, s.st_ino


def device(fd):
    return os.fstat(fd).st_dev


def floor(capacity):
    require(type(capacity) is int and capacity > 0, "invalid capacity reading")
    return max(100 * GiB, (capacity + 9) // 10)


class NativeVolume:
    """Read-only macOS identity and statvfs.f_bavail; never guesses on tool failure."""
    def __init__(self, mount, role):
        self.mount = absolute(mount)
        self.role = role

    def observe(self):
        result = subprocess.run(["/usr/sbin/diskutil", "info", "-plist", self.mount],
                                check=True, capture_output=True, timeout=15)
        info = plistlib.loads(result.stdout)
        with directory(self.mount) as fd:
            s = os.fstatvfs(fd)
            return dict(uuid=info.get("VolumeUUID"), mount=info.get("MountPoint"),
                        filesystem=info.get("FilesystemType"),
                        writable=info.get("WritableVolume") is True, role=self.role,
                        device=os.fstat(fd).st_dev, free_bytes=s.f_bavail * s.f_frsize,
                        capacity_bytes=s.f_blocks * s.f_frsize)


@dataclass(frozen=True)
class Capability:
    version: str
    approval: str
    purpose: str
    writer_id: str
    setup_id: str
    registry_sha256: str
    external_mount: str
    external_uuid: str
    internal_mount: str
    internal_uuid: str
    scratch_root: str
    receipts_dir: str
    fallback_dir: str
    setup_cap_bytes: int
    scratch_cap_bytes: int
    receipts_cap_bytes: int
    fallback_cap_bytes: int
    headroom_floor_bytes: int
    internal_floor_bytes: int

    def validate(self):
        require(self.version == "literature-storage-v1" and self.approval == "D-341" and
                self.purpose == "bounded_setup", "missing or mismatched approval/purpose")
        member(self.writer_id)
        member(self.setup_id)
        require(re.fullmatch(r"[0-9a-f]{64}", self.registry_sha256) is not None,
                "invalid registry pin")
        for p in (self.external_mount, self.internal_mount, self.scratch_root,
                  self.receipts_dir, self.fallback_dir):
            absolute(p)
        for n, maximum in ((self.setup_cap_bytes, MiB), (self.scratch_cap_bytes, 40 * GiB),
                           (self.receipts_cap_bytes, 64 * MiB), (self.fallback_cap_bytes, 64 * MiB)):
            require(type(n) is int and 0 < n <= maximum, "invalid storage ceiling")
        for n in (self.headroom_floor_bytes, self.internal_floor_bytes):
            require(type(n) is int and n >= 100 * GiB, "invalid headroom floor")


def load_capability(path, expected_sha256):
    data = read_regular(path)
    require(hashlib.sha256(data).hexdigest() == expected_sha256, "capability transport mismatch")
    cap = Capability(**json.loads(data))
    cap.validate()
    return cap


class LiteratureStorage:
    def __init__(self, registry_path, cap, *, primary, internal, clock=time.monotonic):
        cap.validate()
        self.registry_path = str(registry_path)
        self.cap = cap
        self.primary, self.internal, self.clock = primary, internal, clock
        self.bound = {}
        self.held_lock = None
        self.last_check = None
        self._registry()

    def _registry(self):
        data = read_regular(self.registry_path)
        require(hashlib.sha256(data).hexdigest() == self.cap.registry_sha256, "registry drift")
        r = yaml.safe_load(data)
        require(r.get("schema_version") == "1.0.0" and r.get("scientific_runs_enabled") is False,
                "registry is not the approved setup-only version")
        roots, domains = r["roots"], r["failure_domains"]
        for alias, role, access, wanted in (
                ("prowl_scratch", "scratch", "acquisition_and_scoped_setup", self.cap.scratch_root),
                ("prowl_artifacts", "artifact", "setup_only", str(Path(self.cap.receipts_dir).parents[1]))):
            v = roots[alias]
            require(v["role"] == role and v["access"] == access and
                    v["failure_domain"] == "external_primary", "wrong root role/access/domain")
            base = absolute(v["path"])
            expected = str(Path(base) / "literature") if role == "scratch" else base
            require(wanted == expected, "capability root does not match registry")
        require(self.cap.receipts_dir == str(Path(roots["prowl_artifacts"]["path"]) /
                                             "literature" / "receipts"), "wrong receipts child")
        for domain, mount, uuid in (("external_primary", self.cap.external_mount, self.cap.external_uuid),
                                    ("internal_backup", self.cap.internal_mount, self.cap.internal_uuid)):
            v = domains[domain]
            require(v["mount_path"] == mount and v["volume_uuid"] == uuid and
                    v["filesystem"] == "apfs" and v["kind"] == "physical_device", "wrong domain")
        require(self.cap.external_uuid != self.cap.internal_uuid and
                self.cap.external_mount != self.cap.internal_mount, "same failure domain")
        areas = (self.cap.scratch_root, self.cap.receipts_dir, self.cap.fallback_dir)
        forbidden = []
        for alias, v in roots.items():
            if v["role"] in ("source", "backup"):
                forbidden.extend(p for p in (v.get("path"), v.get("acquisition_parent")) if p)
        for a in areas:
            for b in (*forbidden, *(x for x in areas if x != a)):
                require(not (Path(a).is_relative_to(b) or Path(b).is_relative_to(a)),
                        "overlapping literature/source/backup areas")
        self.roots = roots

    def _observe(self, probe, *, internal=False, remaining=0):
        obs = probe.observe()
        require(isinstance(obs, dict), "volume observation is not a dict")
        c = self.cap
        mount, uuid, role, minimum = ((c.internal_mount, c.internal_uuid, "fallback", c.internal_floor_bytes)
                                     if internal else
                                     (c.external_mount, c.external_uuid, "literature", c.headroom_floor_bytes))
        require(obs.get("uuid") == uuid and obs.get("mount") == mount and
                obs.get("filesystem") == "apfs" and obs.get("writable") is True and
                obs.get("role") == role, "volume identity/role/writable mismatch")
        require(type(obs.get("device")) is int and type(obs.get("free_bytes")) is int,
                "invalid device/free-space observation")
        minimum = max(minimum, floor(obs.get("capacity_bytes")))
        require(obs["free_bytes"] >= minimum + remaining, "headroom plus remaining allowance unavailable")
        with directory(mount) as fd:
            require(device(fd) == obs["device"], "mount device mismatch")
            self._bind(mount, fd)
        return obs

    def _bind(self, path, fd):
        s = stamp(fd)
        require(path not in self.bound or self.bound[path] == s, "directory/device identity switched")
        self.bound[path] = s

    def _checked_dir(self, path, expected_device):
        @contextmanager
        def opened():
            with directory(path) as fd:
                require(device(fd) == expected_device, "directory on wrong device")
                self._bind(path, fd)
                yield fd
        return opened()

    def verify(self, *, remaining=None):
        self._registry()
        if remaining is None:
            remaining = self.cap.setup_cap_bytes + self.cap.receipts_cap_bytes
        require(type(remaining) is int and remaining >= 0, "invalid remaining allowance")
        p = self._observe(self.primary, remaining=remaining)
        i = self._observe(self.internal, internal=True, remaining=self.cap.fallback_cap_bytes)
        require(p["device"] != i["device"], "primary and fallback are the same device")
        for path in (self.roots["prowl_scratch"]["path"], self.roots["prowl_artifacts"]["path"]):
            with self._checked_dir(path, p["device"]):
                pass
        if self.held_lock is not None:
            with self._checked_dir(self.cap.receipts_dir, p["device"]) as parent:
                current = os.stat(".literature-writer.lock", dir_fd=parent, follow_symlinks=False)
                held = os.fstat(self.held_lock)
                require(stat.S_ISREG(current.st_mode) and current.st_nlink == held.st_nlink == 1 and
                        (current.st_dev, current.st_ino) == stamp(self.held_lock), "writer lock replaced")
        with self._checked_dir(str(Path(self.cap.fallback_dir).parent), i["device"]):
            pass
        self.last_check = self.clock()
        return p, i

    def sizing_start_check(self):
        """Observation only: floor + future 40 GiB; does not authorize run_sizing."""
        return self.verify(remaining=self.cap.scratch_cap_bytes)

    def tick(self, remaining):
        if self.last_check is None or self.clock() - self.last_check >= 60:
            self.verify(remaining=remaining)

    def setup(self):
        p, i = self.verify()
        # These are the entire approved directory-creation set.
        for path, dev in ((self.cap.scratch_root, p["device"]),
                          (str(Path(self.cap.receipts_dir).parent), p["device"]),
                          (self.cap.receipts_dir, p["device"]), (self.cap.fallback_dir, i["device"])):
            self.verify()
            with self._checked_dir(str(Path(path).parent), dev) as parent:
                try:
                    os.mkdir(Path(path).name, 0o700, dir_fd=parent)
                    os.fsync(parent)
                except FileExistsError:
                    pass  # Preserve an existing safe directory, never repair or clear it.
            with self._checked_dir(path, dev):
                pass

    @contextmanager
    def writer(self, writer_id):
        require(writer_id == self.cap.writer_id, "wrong capability writer")
        p, _ = self.verify()
        with self._checked_dir(self.cap.receipts_dir, p["device"]) as parent:
            fd = os.open(".literature-writer.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600,
                         dir_fd=parent)
            try:
                s = os.fstat(fd)
                require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, "unsafe writer lock")
                fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                os.fsync(fd)
                os.fsync(parent)
                self.held_lock = fd
                lease = SetupWriter(self)
                try:
                    yield lease
                finally:
                    lease.active = False
                    self.held_lock = None
            finally:
                os.close(fd)


def tree_bytes(fd):
    total = 0
    for name in os.listdir(fd):
        s = os.stat(name, dir_fd=fd, follow_symlinks=False)
        require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, "unsafe/nonregular receipt member")
        total += s.st_size
    return total


def write_all(fd, data):
    view = memoryview(data)
    while view:
        n = os.write(fd, view)
        require(n > 0, "short write made no progress")
        view = view[n:]
    os.fsync(fd)


class SetupWriter:
    """One bounded invented setup session; no payload fallback or live sizing entry point."""
    def __init__(self, storage):
        self.storage = storage
        self.active = True
        self.started = self.stopped = self.terminal = False
        self.payload_bytes = self.sequence = 0
        self.journals = set()
        self.name = "setup-" + storage.cap.setup_id
        self.journal_name = self.name + ".jsonl"

    def _live(self):
        require(self.active and not self.terminal, "inactive or terminal writer")

    def begin(self):
        self._live()
        require(not self.started, "session already started")
        p, _ = self.storage.verify()
        with self.storage._checked_dir(self.storage.cap.scratch_root, p["device"]) as fd:
            os.mkdir(self.name, 0o700, dir_fd=fd)  # Exclusive; never retries/overwrites.
            os.fsync(fd)
        self.started = True
        self.record("started")

    def _primary_guard(self):
        try:
            return self.storage.verify()
        except Exception:
            self.stopped = True
            raise

    def write_invented(self, name, data):
        self._live()
        require(self.started and not self.stopped, "session not started or stopped")
        member(name)
        require(type(data) is bytes and 0 < len(data) <= self.storage.cap.setup_cap_bytes - self.payload_bytes,
                "setup payload ceiling exceeded")
        p, _ = self._primary_guard()
        path = str(Path(self.storage.cap.scratch_root) / self.name)
        with self.storage._checked_dir(path, p["device"]) as parent:
            fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=parent)
            self.payload_bytes += len(data)  # Charge before writing; failures do not refund.
            try:
                write_all(fd, data)
                os.fsync(parent)
            except Exception:
                self.stopped = True
                raise
            finally:
                os.close(fd)

    def record(self, event):
        self._live()
        require(self.started and event in ("started", "readback_verified", "lock_contention_verified",
                                          "completed", "stopped_primary_failure"), "unscoped journal event")
        require(not self.stopped or event == "stopped_primary_failure", "stopped writer cannot succeed")
        terminal = event in ("completed", "stopped_primary_failure")
        self.sequence += 1
        data = (json.dumps(dict(version="literature-storage-v1", setup_id=self.storage.cap.setup_id,
                                sequence=self.sequence, event=event, payload_bytes=self.payload_bytes),
                           sort_keys=True) + "\n").encode()
        try:
            p, _ = self._primary_guard()
            self._append(self.storage.cap.receipts_dir, p["device"], data, self.storage.cap.receipts_cap_bytes)
        except Exception:
            self.stopped = True
            require(event == "stopped_primary_failure", "primary failure: stop and record terminal fallback")
            self.storage._registry()
            i = self.storage._observe(self.storage.internal, internal=True,
                                      remaining=self.storage.cap.fallback_cap_bytes)
            self._append(self.storage.cap.fallback_dir, i["device"], data, self.storage.cap.fallback_cap_bytes)
        if terminal:
            self.terminal = True

    def _append(self, path, device, data, cap):
        with self.storage._checked_dir(path, device) as parent:
            require(tree_bytes(parent) + len(data) <= cap, "receipt ceiling exceeded")
            flags = os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW
            created = False
            try:
                fd = os.open(self.journal_name, flags | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=parent)
                created = True
                self.journals.add(path)
            except FileExistsError:
                require(path in self.journals, "journal already exists")
                fd = os.open(self.journal_name, flags, dir_fd=parent)
            try:
                if created:
                    os.fsync(parent)
                s = os.fstat(fd)
                require(stat.S_ISREG(s.st_mode) and s.st_nlink == 1, "unsafe journal")
                write_all(fd, data)
                os.fsync(parent)
            finally:
                os.close(fd)
