"""Duration stores and read-only legacy cache access under a fresh exact authority."""
from contextlib import contextmanager
from pathlib import Path
import json
import os
import re
import subprocess
import yaml

from src.data.manifest_records import canonical, digest
from src.data.source_inventory_records import require
from src.operations.artifact_store import ArtifactStore, directory
from src.operations.localizer_run_storage import CappedStore, tree_bytes, mounted_apfs
from scripts.diagnostics.storage_setup import disk_info

GIB = 1024**3
FIELDS = {"schema_version", "operation", "phase", "namespace", "registry_sha256",
          "primary_volume_uuid", "backup_volume_uuid", "backup_baseline_bytes",
          "absolute_backup_ceiling", "maximum_new_backup_bytes", "child_ceiling",
          "phase_ceiling", "minimum_free_bytes", "control_reserve_bytes"}


def pin(value):
    return type(value) is str and len(value) == 64 and all(c in "0123456789abcdef" for c in value)


def validate_capability(raw):
    cap = json.loads(raw)
    require(type(cap) is dict and set(cap) == FIELDS, "Duration capacity fields")
    require(cap["schema_version"] == "1.0.0" and cap["operation"] == "duration_transaction_v1"
            and cap["phase"] in ("rehearsal", "real")
            and type(cap["namespace"]) is str
            and re.fullmatch(r"segmenter-duration-[a-z0-9-]{1,48}", cap["namespace"]),
            "Duration capacity namespace/phase")
    require(pin(cap["registry_sha256"]) and all(type(cap[k]) is str and cap[k]
            for k in ("primary_volume_uuid", "backup_volume_uuid"))
            and cap["primary_volume_uuid"] != cap["backup_volume_uuid"], "Capacity domains/pin")
    fixed = dict(absolute_backup_ceiling=26*GIB, maximum_new_backup_bytes=8*GIB,
                 child_ceiling=2*GIB, phase_ceiling=4*GIB, minimum_free_bytes=100*GIB,
                 control_reserve_bytes=64*1024**2)
    require(all(type(cap[k]) is int and cap[k] == v for k, v in fixed.items())
            and type(cap["backup_baseline_bytes"]) is int
            and 0 < cap["backup_baseline_bytes"] <= cap["absolute_backup_ceiling"]-8*GIB,
            "Duration capacity/aggregate allowance")
    return cap


def validate_storage_authority(capability, approval, trusted_pin):
    require(type(approval) is bytes and pin(trusted_pin) and digest(approval) == trusted_pin,
            "Unreviewed duration storage authority")
    cap = validate_capability(capability)
    a = json.loads(approval)
    require(type(a) is dict and set(a) == {"kind", "author", "user_instruction",
            "capability_sha256", "budget_bytes", "preserve_old_evidence", "launch_authorized"}
            and a["kind"] == "exact_duration_storage_v1" and a["author"] == "Quinton Evans"
            and type(a["user_instruction"]) is str and a["user_instruction"].strip()
            and a["capability_sha256"] == digest(capability)
            and type(a["budget_bytes"]) is int and a["budget_bytes"] == cap["absolute_backup_ceiling"]
            and a["preserve_old_evidence"] is True and a["launch_authorized"] is False,
            "Storage authority differs; budget never grants model work")
    return a


def areas(cap, phase=None):
    stem = cap["namespace"]+"-"+(phase or cap["phase"])
    return dict(primary=stem, keeper=stem+"-keepers", restore=stem+"-restores", controls=stem+"-controls")


class PhaseStore(CappedStore):
    """Global lock and quota plus child, phase and combined two-phase growth guards."""

    def __init__(self, *args, cap, backup_root=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.cap, self.backup_root = cap, backup_root

    def space(self, fd, remaining):
        super().space(fd, remaining)
        require(tree_bytes(self.root)+remaining <= self.cap["child_ceiling"], "Duration child quota")
        if self.backup_root is not None:
            names = areas(self.cap)
            total = sum(tree_bytes(self.backup_root/names[k]) if (self.backup_root/names[k]).exists()
                        else 0 for k in ("keeper", "restore", "controls"))
            require(total+remaining <= self.cap["phase_ceiling"], "Combined phase quota")
            require(tree_bytes(self.backup_root)+remaining <= min(
                self.cap["absolute_backup_ceiling"],
                self.cap["backup_baseline_bytes"]+self.cap["maximum_new_backup_bytes"]),
                "Whole backup/new-growth quota")


class ReadOnlyStore(ArtifactStore):
    @contextmanager
    def writer(self, fd):
        raise ValueError("Read-only qualified cache cannot publish")
        yield


def registry_context(registry_path, cap):
    registry_path = Path(registry_path)
    require(registry_path.is_absolute() and registry_path.resolve(strict=True) == registry_path,
            "Unsafe registry path")
    raw = registry_path.read_bytes()
    require(digest(raw) == cap["registry_sha256"], "Duration registry identity changed")
    reg = yaml.safe_load(raw)
    roots = [reg["roots"][n] for n in ("prowl_artifacts", "prowl_backup")]
    domains = [reg["failure_domains"][r["failure_domain"]] for r in roots]
    require(roots[0]["role"] == "artifact" and roots[1]["role"] == "backup"
            and roots[1]["cap_bytes"] == cap["absolute_backup_ceiling"]
            and roots[1]["minimum_free_bytes"] == cap["minimum_free_bytes"]
            and roots[1]["automatic_deletion"] is False
            and roots[0]["access"]=="setup_only" and roots[1]["access"]=="selected_controls_and_keepers"
            and reg.get("scientific_runs_enabled") is False,
            "Registry allowance/roles differ")
    require([d["volume_uuid"] for d in domains] ==
            [cap["primary_volume_uuid"], cap["backup_volume_uuid"]], "Registered domains differ")
    paths = [Path(r["path"]) for r in roots]

    def check(index):
        require(digest(registry_path.read_bytes()) == cap["registry_sha256"], "Registry drift")
        mount = Path(domains[index]["mount_path"])
        info = disk_info(mount)
        mounted = mount.is_mount() or (index == 1 and info.get("Internal") is True and
            mounted_apfs(info, mount, subprocess.check_output(["/sbin/mount"], text=True, timeout=5)))
        require(mounted and info.get("VolumeUUID") == domains[index]["volume_uuid"]
                and info.get("MountPoint") == str(mount) and info.get("FilesystemType") == "apfs"
                and info.get("WritableVolume") is True, "Unavailable/wrong duration volume")
        fd = directory(paths[index]); os.close(fd)
        require(paths[index].stat().st_dev == mount.stat().st_dev, "Root/device mismatch")
        v = os.statvfs(paths[index])
        require(v.f_bavail*v.f_frsize >= cap["minimum_free_bytes"], "Duration free-space floor")
    return paths, check


def duration_stores(registry_path, capability, *, trusted_capability_sha256,
                    approval, trusted_approval_sha256, create=False, recovery_only=False):
    require(digest(capability) == trusted_capability_sha256, "Unpinned duration capability")
    validate_storage_authority(capability, approval, trusted_approval_sha256)
    cap = validate_capability(capability)
    roots, check = registry_context(registry_path, cap)
    for index in ([1] if recovery_only else [0, 1]): check(index)
    if not recovery_only: require(roots[0].stat().st_dev != roots[1].stat().st_dev, "Independent device required")
    require(tree_bytes(roots[1]) <= min(cap["absolute_backup_ceiling"],
            cap["backup_baseline_bytes"]+cap["maximum_new_backup_bytes"]), "Backup already exceeds budget")
    names = areas(cap)
    if create:
        for index, key in ((0, "primary"), (1, "keeper"), (1, "restore"), (1, "controls")):
            require(not recovery_only, "Cold recovery cannot prepare areas")
            fd = directory(roots[index])
            try: os.mkdir(names[key], 0o700, dir_fd=fd); os.fsync(fd)
            finally: os.close(fd)
    stores = []
    for index, key in ((0, "primary"), (1, "keeper"), (1, "restore")):
        if recovery_only and index == 0: stores.append(None); continue
        path = roots[index]/names[key]
        fd = directory(path); os.close(fd)
        stores.append(PhaseStore(path, cap=cap, backup_root=roots[1] if index else None,
            check_root=lambda index=index: check(index), max_bytes=256*1024**2,
            minimum_free_bytes=cap["minimum_free_bytes"], quota_root=roots[1] if index else path,
            quota_bytes=cap["absolute_backup_ceiling"] if index else cap["child_ceiling"]))
    return tuple(stores)


def qualified_cache_reader(registry_path, capability, *, trusted_capability_sha256, cache_area):
    """Read an already accepted cache under current registry; no legacy hash bypass or writes."""
    require(digest(capability) == trusted_capability_sha256, "Unpinned read capability")
    cap = validate_capability(capability)
    roots, check = registry_context(registry_path, cap)
    require(cache_area in ("segmenter-input-cache","cohorts"), "Unapproved accepted metadata/cache area")
    check(0)
    return ReadOnlyStore(roots[0]/cache_area, check_root=lambda: check(0),
                         max_bytes=512*1024**2, minimum_free_bytes=cap["minimum_free_bytes"])


def replay_descriptors(registry_path, capability, *, trusted_capability_sha256):
    """Replay the unchanged accepted cohort under current read-only storage authority."""
    from src.data import segmenter_geometry_loader_v1 as loader
    from src.data.segmenter_cohort_bundle_v1 import resolve
    from src.data.manifest_records_v3 import manifest_validation_session
    from src.data.source_inventory_records import content_hash
    from scripts.diagnostics import freeze_segmenter_cohort as frozen
    reader=qualified_cache_reader(registry_path,capability,trusted_capability_sha256=trusted_capability_sha256,cache_area="cohorts")
    require(digest(frozen.CAP.read_bytes())==loader.CAPABILITY and digest(frozen.PROVIDER.read_bytes())==frozen.PROVIDER_PIN,"Original cohort/provider qualification changed")
    with manifest_validation_session():
        files,receipt=reader.resolve(frozen.BUNDLE_ID,receipt_sha256=loader.COMPLETION,validate=lambda f:frozen.validate(f,loader.CODES,loader.CAPABILITY))
        derived=json.loads(files['purpose-derived.json']);bases={k:v.encode() for k,v in json.loads(files['purpose-inputs.json'])['membership'].items()}
        _,rows=resolve(derived,bases,json.loads(files['cohorts.json']),frozen.EXPECTED)
        require(content_hash(rows)==loader.DESCRIPTORS==receipt['validation']['descriptor_sha256'],"Independent replayed descriptor identity differs")
    return loader.ResolvedInputs(rows,loader._TOKEN)
