"""P03-I: versioned invented metadata checks, recorded tags and strict placement."""
from collections import OrderedDict, namedtuple
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path
import socket
import struct
import tempfile
import zipfile

import pytest
import torch

from src.models import segmenter_checkpoint_source_inspection_v3 as reader
from src.models.segresnet import build_model


# Independent frozen stat oracle, rather than the reader's identity helper.
def stat_record(path, root=False):
    info = os.stat(path, follow_symlinks=False)
    result = dict(device=info.st_dev, inode=info.st_ino, mode=info.st_mode, owner=info.st_uid)
    if not root:
        result.update(links=info.st_nlink, mtime_ns=info.st_mtime_ns, ctime_ns=info.st_ctime_ns)
    return result


def control(path, namespace="identity"):
    return dict(schema_version=reader.CONTROL_VERSION, evidence_domain=reader.DOMAIN,
                source=dict(root=str(path.parent), path=str(path), bytes=path.stat().st_size,
                            sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                            identity=stat_record(path), root_identity=stat_record(path.parent, True),
                            volume=dict(mount="invented", uuid="invented", filesystem="invented",
                                        device=path.stat().st_dev, fsid=[0, 0], method="invented")),
                architecture=reader.architecture(), expected_signature=reader.expected_signature(),
                namespace=namespace, wrapper="net_optimizer_scheduler_epoch", device_policy=reader.device_policy(),
                limits=reader.limits(),
                request=dict(run_id="invented_r01", reader_sha256=reader.reader_sha256(),
                             consumption_receipt_sha256=hashlib.sha256(b"invented consumed receipt").hexdigest()))


def run(path, c, native=False, approval=None, approval_pin=None):
    pin = reader.control_sha256(c)
    if native:
        return reader.inspect_source_checkpoint(path, pinned_control=c, expected_control_sha256=pin,
                                                approval=approval, expected_approval_sha256=approval_pin)
    return reader._inspect_local(path, c, pin, approval, approval_pin)


def refused(result, reason=None):
    assert result["status"] == "refused", result
    if reason:
        assert result["reason"] == reason, result
    assert result["scope"] == "checkpoint_metadata_only"
    assert result["execution_authority"] == "none"
    assert result["training_eligible"] is False and result["values_audited"] is False
    assert len(json.dumps(result, allow_nan=False).encode()) < 1024**2


@pytest.fixture(autouse=True)
def restore_globals():
    before = torch.serialization.get_safe_globals()
    rng = torch.get_rng_state().clone()
    yield
    torch.serialization.clear_safe_globals()
    torch.serialization.add_safe_globals(before)
    torch.set_rng_state(rng)


@pytest.fixture(scope="module")
def factory():
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(3418)
        model = build_model({"model": reader.architecture()})
    return model.state_dict()


@pytest.fixture
def area():
    with tempfile.TemporaryDirectory(prefix="prowl-source-invented-",
                                     dir=Path(tempfile.gettempdir()).resolve()) as name:
        yield Path(name)


@pytest.fixture
def fixture(area, factory):
    path = area / "invented-full.pth"
    # Fresh optimizer metadata, including ordinary Adam betas and nested tuples.
    blob = dict(net=OrderedDict(factory), optimizer={
        "state": {0: {"step": torch.tensor(1.)}},
        "param_groups": [{"params": [0], "lr": .0003, "betas": (.9, .999)}],
        "nested": ([], {"schedule": (None, 1, True)})},
        scheduler={"last_epoch": 0, "milestones": (1, 4, (8, 16))}, epoch=0)
    blob["net"]._metadata = {"": {"version": 1}}
    torch.save(blob, path)
    return path, control(path), blob


def rewrite(path, blob, namespace="identity"):
    torch.save(blob, path)
    return control(path, namespace)


def tagged_rewrite(path, blob, tag, namespace="identity", mixed=False):
    registry = list(torch.serialization._package_registry)
    try:
        torch.serialization.register_package(0,
            lambda storage: ("cpu" if mixed and storage.nbytes() == 4 else tag)
                if storage.device.type == "cpu" else None,
            lambda storage, location: None)
        torch.save(blob, path)
    finally:
        torch.serialization._package_registry[:] = registry
    return control(path, namespace)


def archive_offsets(path):
    result = {}
    with zipfile.ZipFile(path) as archive, path.open("rb") as stream:
        for row in archive.infolist():
            stream.seek(row.header_offset)
            header = struct.unpack("<4s5H3I2H", stream.read(30))
            result[row.filename.partition("/")[2]] = (
                row.header_offset + 30 + header[-2] + header[-1], row.file_size)
    return result


def actual_control(c):
    # Pure strings and invented identity fields. Never stat or open this locator.
    result = deepcopy(c)
    path = reader.candidate_locator()
    result["evidence_domain"] = reader.ACTUAL_DOMAIN
    result["source"].update(root=str(path.parent), path=str(path), bytes=56500623,
                            sha256=reader.ACTUAL_CANDIDATE_SHA,
                            volume={"filesystem": "apfs", "mount": "/",
                                    "uuid": "01234567-89AB-CDEF-0123-456789ABCDEF",
                                    "device": c["source"]["identity"]["device"], "fsid": [1, 2],
                                    "method": "darwin_fstatfs_diskutil"})
    return result


def approval(c):
    request = c["request"]
    return dict(schema_version="checkpoint-metadata-approval-3", approved_by="Quinton Evans",
                operation="single_checkpoint_metadata", run_id=request["run_id"],
                control_sha256=reader.control_sha256(c), reader_sha256=request["reader_sha256"],
                consumption_receipt_sha256=request["consumption_receipt_sha256"],
                source_sha256=c["source"]["sha256"])


def test_independent_full_signature(factory):
    expected = {k: dict(shape=list(v.shape), dtype=str(v.dtype)) for k, v in factory.items()}
    assert reader.expected_signature() == expected and len(expected) == 83
    assert sum(v.numel() * v.element_size() for v in factory.values()) == 18805696


@pytest.mark.parametrize("tag", ["cpu", "mps:0", "cuda:0", "cuda:3", "cuda:1023"])
def test_exact_source_tag_grammar_accepts_only_declared_forms(tag):
    assert reader._source_tag_allowed(tag) is True


@pytest.mark.parametrize("tag", [None, 0, True, "cuda", "cuda:-1", "cuda:+1", "cuda:01", "cuda:1024",
                                "cuda:99999", " cuda:0", "cuda:0 ", "cuda:0:1", "cuda:١", "mps", "mps:1",
                                "meta", "xpu:0", "cpu:0", "cpu\n"])
def test_unknown_or_ambiguous_serialization_tags_refused(tag):
    assert reader._source_tag_allowed(tag) is False


@pytest.mark.parametrize("tag,namespace", [("cuda:0", "uniform_module"), ("cuda:1023", "identity"),
                                          ("mps:0", "identity")])
def test_native_full83_original_tags_cpu_fake_meta_zero_values(fixture, tag, namespace, record_property):
    path, _, blob = fixture
    if namespace == "uniform_module":
        blob["net"] = {"module." + k: v for k, v in blob["net"].items()}
    c = tagged_rewrite(path, blob, tag, namespace)
    before = path.read_bytes(), deepcopy(c), torch.get_rng_state().clone()
    result = run(path, c, native=True)
    assert result["status"] == "pass", result
    assert result["device_policy"] == reader.device_policy() and result["device_failure"] is None
    assert len(result["model"]) == 83 and set(result["model"]) == set(reader.expected_signature())
    offsets = archive_offsets(path)
    for key, row in result["model"].items():
        assert row["shape"] == reader.expected_signature()[key]["shape"]
        assert row["dtype"] == "torch.float32" and row["source_device"] == tag
        assert row["tensor_device"] == "cpu" and row["storage_device"] == "meta"
        assert (row["storage_file_offset"], row["storage_bytes"]) == offsets[row["storage_member"]]
    assert result["io"]["hash_bytes"] == c["source"]["bytes"]
    assert result["io"]["metadata_storage_source_bytes"] == 0
    assert not result["values_audited"] and not result["training_eligible"] and result["execution_authority"] == "none"
    assert path.read_bytes() == before[0] and c == before[1] and torch.equal(torch.get_rng_state(), before[2])
    assert result["worker"]["exit_code"] == 0
    record_property("reader3_tagged_fixture", json.dumps({"tag": tag, "namespace": namespace,
        "tensor_count": len(result["model"]), "io": result["io"], "worker": result["worker"]}, sort_keys=True))


def test_mixed_original_devices_and_auxiliary_storage_aliases(fixture):
    path, _, blob = fixture
    blob["optimizer"]["alias"] = blob["net"]["conv_final.0.weight"]
    result = run(path, tagged_rewrite(path, blob, "cuda:3", mixed=True))
    assert result["status"] == "pass", result
    assert {row["source_device"] for row in result["model"].values()} == {"cuda:3"}
    tensors = []
    def walk(value):
        if type(value) is dict:
            if "tensor" in value:
                tensors.append(value["tensor"])
            for v in value.values(): walk(v)
        elif type(value) is list:
            for v in value: walk(v)
    walk(result["auxiliary"])
    assert {row["source_device"] for row in tensors} == {"cpu", "cuda:3"}
    assert all(row["tensor_device"] == "cpu" and row["storage_device"] == "meta" for row in tensors)
    assert any(paths == ["net/conv_final.0.weight", "optimizer/alias"]
               for paths in result["auxiliary"]["aliases"].values())


@pytest.mark.parametrize("tag", ["cuda:01", "cuda:1024", "mps:1", "xpu:0"])
def test_serialized_bad_tags_refuse_with_exact_tensor_predicates(fixture, tag):
    path, _, blob = fixture
    result = run(path, tagged_rewrite(path, blob, tag))
    refused(result, "unsupported_serialized_device_tag")
    failure = result["device_failure"]
    assert failure == dict(tensor_path="net/convInit.conv.weight", tensor_path_truncated=False,
        serialized_storage_tag=tag, serialized_tag_truncated=False, source_tag_allowed=False,
        tensor_device="cpu", tensor_is_cpu=True, storage_device="meta", storage_is_meta=True)
    assert result["model"] is None and result["metadata_compatible"] is False
    assert result["io"]["metadata_storage_source_bytes"] == 0


@pytest.mark.parametrize("tag,cpu,meta", [("cpu", False, True), ("cuda:0", True, False),
                                       ("cuda:0", False, False), ("xpu:0", False, False)])
def test_each_loaded_placement_refuses_independently(tag, cpu, meta):
    from types import SimpleNamespace
    value = SimpleNamespace(device=torch.device("cpu" if cpu else "cuda:0"))
    storage = SimpleNamespace(device=torch.device("meta" if meta else "cpu"), _fake_device=tag)
    reason = "non_cpu_or_materialized_storage" if tag != "xpu:0" else "unsupported_serialized_device_tag"
    with pytest.raises(reader.Refusal, match=reason) as exc:
        reader._check_devices(value, storage, "net/invented.weight")
    seen = exc.value.device_failure
    assert seen["tensor_is_cpu"] is cpu and seen["storage_is_meta"] is meta
    assert seen["source_tag_allowed"] is (tag != "xpu:0") and seen["tensor_path"] == "net/invented.weight"


def test_bounded_failure_strings_never_repr_unknown_objects():
    from types import SimpleNamespace
    class NoRepr:
        def __repr__(self): pytest.fail("untrusted tag repr used")
    for tag in [NoRepr(), "unknown:" + "é" * 600, "cpu\n"]:
        value = SimpleNamespace(device=torch.device("cpu"))
        storage = SimpleNamespace(device=torch.device("meta"), _fake_device=tag)
        with pytest.raises(reader.Refusal) as exc:
            reader._check_devices(value, storage, "net/" + "é" * 600)
        detail = exc.value.device_failure
        assert len(detail["tensor_path"].encode()) <= 512 and detail["tensor_path_truncated"]
        if detail["serialized_storage_tag"] is not None:
            assert len(detail["serialized_storage_tag"].encode()) <= 512 and detail["serialized_tag_truncated"]
        assert len(reader._json_bytes(detail)) < 4096


@pytest.mark.parametrize("change,reason", [("missing", "control_fields"), ("rule", "device_policy_mismatch"),
                                         ("extra", "device_policy_mismatch"), ("version2", "control_version")])
def test_missing_or_mutable_device_policy_before_worker(fixture, change, reason, monkeypatch):
    path, c, _ = fixture
    if change == "missing": del c["device_policy"]
    elif change == "rule": c["device_policy"]["loaded_tensor_device"] = "cuda"
    elif change == "extra": c["device_policy"]["accept_any"] = True
    else: c["schema_version"] = "segmenter-checkpoint-source-control-2"
    monkeypatch.setattr(reader, "_worker_run", lambda *a: pytest.fail("invalid policy worker"))
    refused(run(path, c, native=True), reason)


def test_real_tensor_still_refused_before_device_metadata(fixture, monkeypatch):
    path, _, blob = fixture
    c = control(path)
    monkeypatch.setattr(torch, "load", lambda *a, **k: blob)
    result = run(path, c)
    refused(result, "unsupported_tensor_type_or_layout")
    assert result["device_failure"] is None and result["model"] is None


def test_native_inventory_tuples_accounting_and_parent_isolation(fixture, monkeypatch):
    path, c, _ = fixture
    before = path.read_bytes(), deepcopy(c), torch.get_rng_state().clone()
    ambient = torch.serialization.get_safe_globals()
    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("network used"))
    monkeypatch.setattr(torch.nn.Module, "__call__", lambda *a, **k: pytest.fail("model executed"))
    result = run(path, c, native=True)
    assert result["status"] == "pass", result
    assert result["schema_version"] == "segmenter-checkpoint-source-inspection-report-3"
    assert result["evidence_domain"] == reader.DOMAIN
    assert result["scope"] == "checkpoint_metadata_only"
    assert result["identity_verified"] and result["metadata_compatible"]
    assert not result["values_audited"] and not result["training_eligible"]
    assert result["request_sha256"] == reader.control_sha256(c["request"])
    assert result["device_policy"] == reader.device_policy() and result["device_failure"] is None
    assert result["observed_volume"] is None
    assert len(result["model"]) == 83
    assert '"tuple"' in json.dumps(result["auxiliary"])
    expected = archive_offsets(path)
    for row in result["model"].values():
        assert (row["storage_file_offset"], row["storage_bytes"]) == expected[row["storage_member"]]
        assert row["source_device"] == "cpu"
        assert row["tensor_device"] == "cpu" and row["storage_device"] == "meta"
    counts = result["io"]
    assert counts["hash_bytes"] == c["source"]["bytes"]
    assert counts["metadata_storage_source_bytes"] == 0
    assert counts["aggregate_requested_bytes"] == sum(counts[k] for k in
        ("hash_bytes", "metadata_source_bytes", "virtual_zero_bytes"))
    assert counts["aggregate_requested_bytes"] <= c["source"]["bytes"] + 8 * 1024**2
    assert result["worker"]["exit_code"] == 0
    assert result["worker"]["child_peak_rss_bytes"] > 0
    assert result["worker"]["sampled_peak_rss_bytes"] > 0
    assert result["worker"]["elapsed_seconds"] < 60
    assert path.read_bytes() == before[0] and c == before[1]
    assert torch.equal(torch.get_rng_state(), before[2])
    assert torch.serialization.get_safe_globals() == ambient


def test_descriptor_reads_exclude_storage_after_hash(fixture, monkeypatch):
    path, c, _ = fixture
    original, calls = os.pread, []
    def observed(fd, count, offset):
        calls.append((offset, offset + count))
        return original(fd, count, offset)
    monkeypatch.setattr(reader.os, "pread", observed)
    result = run(path, c)
    assert result["status"] == "pass", result
    later = calls[(c["source"]["bytes"] + 1024**2 - 1) // 1024**2:]
    spans = [(a, a + n) for key, (a, n) in archive_offsets(path).items() if key.startswith("data/")]
    assert all(max(a, x) >= min(b, y) for a, b in later for x, y in spans)


@pytest.mark.parametrize("field", ["device", "inode", "mode", "owner", "links", "mtime_ns", "ctime_ns"])
def test_frozen_source_identity_refuses_before_read(fixture, monkeypatch, field):
    path, c, _ = fixture
    c["source"]["identity"][field] += 1
    if field == "device":
        c["source"]["root_identity"][field] += 1
        c["source"]["volume"][field] += 1
    monkeypatch.setattr(reader.os, "pread", lambda *a: pytest.fail("mismatched identity read"))
    refused(run(path, c), "root_identity_mismatch" if field == "device" else "source_identity_mismatch")


@pytest.mark.parametrize("field", ["inode", "mode", "owner"])
def test_frozen_root_identity_refuses_before_read(fixture, monkeypatch, field):
    path, c, _ = fixture
    c["source"]["root_identity"][field] += 1
    monkeypatch.setattr(reader.os, "pread", lambda *a: pytest.fail("mismatched root read"))
    refused(run(path, c), "root_identity_mismatch")


@pytest.mark.parametrize("mode,reason", [(0o755, "non_private_test_root"), (0o777, "unsafe_source_root")])
def test_root_permissions_enforced(fixture, mode, reason):
    path, _, _ = fixture
    path.parent.chmod(mode)
    c = control(path)
    refused(run(path, c), reason)
    path.parent.chmod(0o700)


def test_hardlink_and_symlink_refused(fixture):
    path, _, _ = fixture
    hard = path.parent / "invented-hard.pth"
    os.link(path, hard)
    refused(run(path, control(path)), "non_regular_or_hardlinked_source")
    soft = path.parent / "invented-symlink.pth"
    soft.symlink_to(path)
    refused(run(soft, control(soft)), "symlink_refused")


@pytest.mark.parametrize("replace", [False, True])
def test_mutation_or_replacement_during_read(fixture, monkeypatch, replace):
    path, c, _ = fixture
    original, called = os.pread, [False]
    def disturbed(fd, count, offset):
        data = original(fd, count, offset)
        if not called[0]:
            called[0] = True
            if replace:
                replacement = path.parent / "invented-replacement.pth"
                replacement.write_bytes(path.read_bytes())
                os.replace(replacement, path)
            else:
                with path.open("r+b") as stream:
                    stream.seek(-1, 2); stream.write(b"x")
        return data
    monkeypatch.setattr(reader.os, "pread", disturbed)
    refused(run(path, c), "source_mutated_or_replaced")


def test_hash_mismatch_and_no_decode(fixture, monkeypatch):
    path, c, _ = fixture
    c["source"]["sha256"] = "0" * 64
    monkeypatch.setattr(torch, "load", lambda *a, **k: pytest.fail("hash mismatch decoded"))
    refused(run(path, c), "file_hash_mismatch")


@pytest.mark.parametrize("change,reason", [
    ("extra", "control_fields"), ("domain", "source_domain_refused"),
    ("runid", "unsafe_run_id"), ("reader", "reader_pin_mismatch"),
    ("receipt", "invalid_sha256"), ("arch", "architecture_mismatch"),
    ("signature", "incomplete_expected_signature"), ("namespace", "namespace_policy"),
    ("identity_bool", "identity_type"), ("volume", "invented_volume_mismatch"),
    ("actual_sha", "actual_candidate_refused"), ("limit", "invalid_limit"),
    ("source_extra", "source_fields"), ("device", "source_root_device_mismatch"),
])
def test_closed_control_refuses_before_worker(fixture, monkeypatch, change, reason):
    path, c, _ = fixture
    if change == "extra": c["training_permission"] = True
    elif change == "domain": c["evidence_domain"] = "training"
    elif change == "runid": c["request"]["run_id"] = "../../escape"
    elif change == "reader": c["request"]["reader_sha256"] = "0" * 64
    elif change == "receipt": c["request"]["consumption_receipt_sha256"] = "invalid"
    elif change == "arch": c["architecture"]["out_channels"] = 3
    elif change == "signature": c["expected_signature"].pop("convInit.conv.weight")
    elif change == "namespace": c["namespace"] = "auto"
    elif change == "identity_bool": c["source"]["identity"]["inode"] = True
    elif change == "volume": c["source"]["volume"]["uuid"] = "actual"
    elif change == "actual_sha": c["source"]["sha256"] = reader.ACTUAL_CANDIDATE_SHA
    elif change == "limit": c["limits"]["max_file_bytes"] *= 2
    elif change == "source_extra": c["source"]["accept_rights"] = True
    elif change == "device": c["source"]["identity"]["device"] += 1
    monkeypatch.setattr(reader, "_worker_run", lambda *a: pytest.fail("invalid control dispatched"))
    refused(run(path, c, native=True), reason)


def test_control_pin_and_invented_approval_refused(fixture, monkeypatch):
    path, c, _ = fixture
    monkeypatch.setattr(reader, "_worker_run", lambda *a: pytest.fail("dispatched"))
    refused(reader.inspect_source_checkpoint(path, pinned_control=c, expected_control_sha256="0"*64),
            "control_pin_mismatch")
    refused(run(path, c, native=True, approval={}, approval_pin="0"*64), "invented_approval_refused")


def test_actual_missing_approval_refuses_without_source_or_worker(fixture, monkeypatch):
    _, c, _ = fixture
    c = actual_control(c)
    monkeypatch.setattr(reader.os, "open", lambda *a, **k: pytest.fail("actual descriptor opened"))
    monkeypatch.setattr(reader, "_observe_volume", lambda *a: pytest.fail("actual volume probed"))
    monkeypatch.setattr(reader, "_worker_run", lambda *a: pytest.fail("actual worker dispatched"))
    refused(run(c["source"]["path"], c, native=True), "actual_approval_missing")


@pytest.mark.parametrize("field", ["schema_version", "approved_by", "operation", "run_id",
                                    "control_sha256", "reader_sha256", "consumption_receipt_sha256", "source_sha256"])
def test_actual_approval_binding_refuses_without_access(fixture, monkeypatch, field):
    _, c, _ = fixture
    c = actual_control(c)
    a = approval(c); a[field] = "wrong"
    monkeypatch.setattr(reader, "_worker_run", lambda *args: pytest.fail("actual worker dispatched"))
    monkeypatch.setattr(reader.os, "open", lambda *args, **kw: pytest.fail("source opened"))
    refused(run(c["source"]["path"], c, native=True, approval=a, approval_pin=reader.control_sha256(a)),
            "approval_binding_mismatch")


@pytest.mark.parametrize("change,reason", [
    ("locator", "actual_locator_mismatch"), ("bytes", "actual_identity_mismatch"),
    ("hash", "actual_identity_mismatch"), ("filesystem", "actual_volume_policy"),
    ("uuid", "actual_volume_policy"), ("mount", "actual_volume_policy"),
    ("approval_extra", "approval_fields"), ("approval_pin", "approval_pin_mismatch"),
])
def test_actual_closed_policy_denials_only(fixture, monkeypatch, change, reason):
    _, c, _ = fixture
    c = actual_control(c)
    if change == "locator": c["source"]["path"] = str(Path(c["source"]["root"]) / "alternate.pth")
    elif change == "bytes": c["source"]["bytes"] -= 1
    elif change == "hash": c["source"]["sha256"] = "0" * 64
    elif change in ("filesystem", "uuid", "mount"): c["source"]["volume"][change] = "wrong"
    a = approval(c)
    if change == "approval_extra": a["training_eligible"] = True
    pin = "0" * 64 if change == "approval_pin" else reader.control_sha256(a)
    monkeypatch.setattr(reader, "_worker_run", lambda *args: pytest.fail("actual worker dispatched"))
    refused(run(c["source"]["path"], c, native=True, approval=a, approval_pin=pin), reason)


@pytest.mark.parametrize("kind,reason", [
    ("metadata_tuple", "tuple_outside_auxiliary"), ("cycle", "container_cycle"),
    ("nonfinite", "nonfinite_primitive"), ("deep_tuple", "container_structure_limit"),
    ("extra_wrapper", "wrapper_mismatch"), ("missing_key", "model_key_mismatch"),
    ("head_shape", "model_shape_or_dtype_mismatch"), ("dtype", "model_shape_or_dtype_mismatch"),
    ("mixed_prefix", "namespace_mismatch"), ("repeat_prefix", "namespace_mismatch"),
    ("noncontiguous", "unsupported_tensor_view"),
])
def test_semantic_tuple_and_model_denials(fixture, kind, reason):
    path, _, blob = fixture
    namespace = "identity"
    if kind == "metadata_tuple": blob["net"]._metadata = {"": {"v": (1, 2)}}
    elif kind == "cycle":
        cycle = []; cycle.append(cycle); blob["optimizer"]["cycle"] = cycle
    elif kind == "nonfinite": blob["scheduler"]["rate"] = float("nan")
    elif kind == "deep_tuple":
        value = 1
        for _ in range(20): value = (value,)
        blob["optimizer"]["deep"] = value
    elif kind == "extra_wrapper": blob["extra"] = True
    elif kind == "missing_key": blob["net"].pop("convInit.conv.weight")
    elif kind == "head_shape": blob["net"]["conv_final.2.conv.bias"] = torch.zeros(3)
    elif kind == "dtype": blob["net"]["conv_final.0.weight"] = torch.zeros(16, dtype=torch.float64)
    elif kind == "mixed_prefix":
        blob["net"]["module.convInit.conv.weight"] = blob["net"].pop("convInit.conv.weight")
    elif kind == "repeat_prefix":
        blob["net"] = {"module.module."+k: v for k, v in blob["net"].items()}; namespace = "uniform_module"
    elif kind == "noncontiguous": blob["net"]["conv_final.0.weight"] = torch.ones(1).expand(16)
    refused(run(path, rewrite(path, blob, namespace)), reason)


def test_uniform_module_and_shared_tuple_accounting(fixture):
    path, _, blob = fixture
    shared = (.9, .999)
    blob["optimizer"]["a"] = shared; blob["scheduler"]["b"] = shared
    blob["net"] = {"module."+k: v for k, v in blob["net"].items()}
    result = run(path, rewrite(path, blob, "uniform_module"))
    assert result["status"] == "pass", result
    assert set(result["model"]) == set(reader.expected_signature())
    fields = result["auxiliary"]["fields"]
    assert next(r["value"] for r in fields["optimizer"]["mapping"] if r["key"] == "a") == {
        "tuple": [{"primitive": .9}, {"primitive": .999}]}


class SideEffect:
    def __init__(self, marker): self.marker = marker
    def __reduce__(self):
        return eval, (f"open({str(self.marker)!r}, 'w').write('executed')",)


def test_restricted_child_refuses_parent_safe_global(fixture):
    path, _, blob = fixture
    marker = path.parent / "must-not-exist"
    blob["optimizer"]["attack"] = SideEffect(marker)
    c = rewrite(path, blob)
    with torch.serialization.safe_globals([eval]):
        before = torch.serialization.get_safe_globals()
        result = run(path, c, native=True)
        assert torch.serialization.get_safe_globals() == before
    refused(result, "restricted_decode_refused")
    assert not marker.exists()


TupleSubclass = namedtuple("TupleSubclass", "value")


def test_tuple_subclass_not_allowlisted(fixture):
    path, _, blob = fixture
    blob["optimizer"]["bad"] = TupleSubclass(1)
    refused(run(path, rewrite(path, blob)), "restricted_decode_refused")


@pytest.mark.parametrize("cap,value,reason", [
    ("max_worker_seconds", .05, "worker_time_limit"),
    ("max_worker_rss_bytes", 1, "worker_rss_limit"),
    ("max_report_bytes", 2048, "report_byte_limit"),
])
def test_native_stops_reap_owned_child(fixture, monkeypatch, cap, value, reason):
    path, c, _ = fixture
    c["limits"][cap] = value
    original, children = reader.subprocess.Popen, []
    def tracked(*args, **kwargs):
        child = original(*args, **kwargs)
        if "--worker" in args[0]: children.append(child)
        return child
    monkeypatch.setattr(reader.subprocess, "Popen", tracked)
    result = run(path, c, native=True)
    refused(result, reason)
    assert children and all(child.poll() is not None for child in children)
    if result["worker"]: assert result["worker"]["exit_code"] is not None


def test_unavailable_monitor_stops_before_source(fixture, monkeypatch):
    path, c, _ = fixture
    def unavailable(pid): raise reader.Refusal("rss_monitor_unavailable")
    monkeypatch.setattr(reader, "_sample_rss", unavailable)
    result = run(path, c, native=True)
    refused(result, "rss_monitor_unavailable")
    assert result["worker"]["exit_code"] is not None and not result["identity_verified"]


def test_bounded_view_no_descriptor(fixture):
    _, c, _ = fixture
    with reader._Source(c) as source:
        source.hash(); reader._archive(source)
        view = reader._View(source)
        with pytest.raises(io.UnsupportedOperation): view.fileno()
        with pytest.raises(reader.Refusal, match="seek_out_of_file"): view.seek(-1)
        c["limits"]["max_metadata_read_bytes"] = source.requested - source.hash_bytes
        with pytest.raises(reader.Refusal, match="metadata_read_limit"): view.read(1)


@pytest.mark.parametrize("cap,reason", [
    ("max_directory_bytes", "directory_byte_limit"),
    ("max_pickle_bytes", "metadata_member_byte_limit"),
    ("max_members", "member_count_limit"), ("max_storages", "storage_count_limit"),
    ("max_storage_bytes", "storage_byte_limit"),
    ("max_metadata_read_bytes", "metadata_read_limit"),
])
def test_metered_archive_limits(fixture, cap, reason):
    path, c, _ = fixture
    c["limits"][cap] = 1
    refused(run(path, c), reason)


def test_legacy_refuses_before_decoder(fixture, monkeypatch):
    path, _, blob = fixture
    torch.save(blob, path, _use_new_zipfile_serialization=False)
    monkeypatch.setattr(torch, "load", lambda *a, **k: pytest.fail("legacy decoder"))
    refused(run(path, control(path)), "zip_footer_or_comment")


def test_old_inspector_guard_and_pins_unchanged(fixture):
    from src.models import segmenter_checkpoint_inspection_v1 as old
    path, c, _ = fixture
    refused_old = old.inspect_checkpoint(path, pinned_control=c, expected_control_sha256=old.control_sha256(c))
    assert refused_old["status"] == "refused" and not refused_old["identity_verified"]
    root = Path(__file__).absolute().parents[1]
    pins = {
        "src/models/segmenter_checkpoint_inspection_v1.py": "6ccdd1e7ac84ead10c87774d61aa8cc70a5de2593bce506358c386020cda6043",
        "tests/test_segmenter_checkpoint_inspection_v1.py": "19d907e1daaa5232764368641b531994dd148c8906bf06ac5061009c2126e18e",
        "docs/capstone/imaging/SEGMENTER-CHECKPOINT-INSPECTION-CONTRACT-V1.md": "db57aee7d17cf0010a25e49649916018dd4a56d8d1c375ceb6dd4894f82fc8e3"}
    assert all(hashlib.sha256((root / path).read_bytes()).hexdigest() == pin for path, pin in pins.items())


def test_actual_denial_report_does_not_claim_invented_domain(fixture):
    _, c, _ = fixture
    c = actual_control(c)
    result = run(c["source"]["path"], c, native=True)
    refused(result, "actual_approval_missing")
    assert result["evidence_domain"] == reader.ACTUAL_DOMAIN
    assert result["identity_verified"] is False


def test_root_permission_mutation_during_read(fixture, monkeypatch):
    path, c, _ = fixture
    original, changed = os.pread, [False]
    def observed(fd, count, offset):
        data = original(fd, count, offset)
        if not changed[0]:
            changed[0] = True; path.parent.chmod(0o755)
        return data
    monkeypatch.setattr(reader.os, "pread", observed)
    refused(run(path, c), "root_identity_mismatch")
    path.parent.chmod(0o700)


def test_pinned_snapshot_independent_from_caller(fixture):
    path, c, _ = fixture
    frozen = reader._validate_control(path, c, reader.control_sha256(c))
    c["source"]["identity"]["inode"] += 1
    assert frozen["source"]["identity"] == stat_record(path)


@pytest.mark.parametrize("kind,reason", [
    ("out", "worker_output_limit"), ("err", "worker_log_limit"),
    ("bad_json", "worker_or_monitor_unavailable"),
    ("schema", "worker_report_schema"), ("authority", "worker_report_authority"),
    ("post_peak", "worker_peak_rss_limit"),
])
def test_worker_transport_limits_and_post_exit_peak(fixture, monkeypatch, kind, reason):
    path, c, _ = fixture
    original, children = reader.subprocess.Popen, []
    # A test-owned child exercises transport limits; never invokes source reader.
    code = {
        "out": "import sys; sys.stdin.read(); sys.stdout.write('x'*1100000)",
        "err": "import sys; sys.stdin.read(); sys.stderr.write('x'*70000)",
        "bad_json": "import sys; sys.stdin.read(); print('broken json')",
        "schema": "import sys; sys.stdin.read(); print('{}')",
    }.get(kind)
    if kind in ("authority", "post_peak"):
        fake = reader._report()
        if kind == "authority": fake["training_eligible"] = True
        else: fake["worker"] = {"child_peak_rss_bytes": 3 * 1024**3 + 1}
        code = "import sys; sys.stdin.read(); print(" + repr(json.dumps(fake)) + ")"
    def substitute(args, **kwargs):
        if "--worker" in args:
            child = original([reader.sys.executable, "-I", "-c", code], **kwargs)
            children.append(child); return child
        return original(args, **kwargs)
    monkeypatch.setattr(reader.subprocess, "Popen", substitute)
    refused(run(path, c, native=True), reason)
    assert children and all(child.poll() is not None for child in children)


def test_unqualified_monitor_platform_no_worker(fixture, monkeypatch):
    path, c, _ = fixture
    monkeypatch.setattr(reader.sys, "platform", "win32")
    monkeypatch.setattr(reader.subprocess, "Popen", lambda *a, **k: pytest.fail("unqualified worker started"))
    refused(run(path, c, native=True), "monitor_platform_unqualified")


def test_descriptor_volume_observer_firmlink_policy(area, monkeypatch):
    kernel = dict(mount=str(area), filesystem="apfs", device=area.stat().st_dev, fsid=[1, 2])
    calls = []
    monkeypatch.setattr(reader, "_kernel_volume", lambda fd: kernel)
    def tool(mount):
        calls.append(mount)
        return dict(MountPoint=mount, VolumeUUID="01234567-89AB-CDEF-0123-456789ABCDEF", FilesystemType="APFS")
    monkeypatch.setattr(reader, "_volume_tool", tool)
    assert reader._observe_volume(area) == dict(kernel, uuid="01234567-89AB-CDEF-0123-456789ABCDEF",
                                              method="darwin_fstatfs_diskutil")
    assert calls == [str(area)]


@pytest.mark.parametrize("fault", ["device", "fsid", "mount", "filesystem", "uuid", "drift", "symlink"])
def test_descriptor_volume_mismatches_refuse(area, monkeypatch, fault):
    kernel = dict(mount=str(area), filesystem="apfs", device=area.stat().st_dev, fsid=[1, 2])
    count = [0]
    def observed(fd):
        count[0] += 1
        value = dict(kernel)
        if count[0] == 2 and fault in ("device", "fsid"):
            value[fault] = value[fault] + 1 if fault == "device" else [3, 4]
        if count[0] == 3 and fault == "drift": value["fsid"] = [3, 4]
        return value
    monkeypatch.setattr(reader, "_kernel_volume", observed)
    fields = dict(MountPoint=str(area), VolumeUUID="01234567-89AB-CDEF-0123-456789ABCDEF", FilesystemType="apfs")
    if fault == "mount": fields["MountPoint"] = "/other"
    elif fault == "filesystem": fields["FilesystemType"] = "other"
    elif fault == "uuid": fields["VolumeUUID"] = "other"
    monkeypatch.setattr(reader, "_volume_tool", lambda mount: fields)
    target = area
    if fault == "symlink":
        target = area / "alias"; target.symlink_to(area)
    with pytest.raises((reader.Refusal, OSError)): reader._observe_volume(target)


def test_volume_actual_control_physical_mount_needs_descriptor_record(fixture):
    path, c, _ = fixture
    c = actual_control(c)
    c["source"]["volume"]["mount"] = "/System/Volumes/Data"
    a = approval(c)
    # Pure consistency; actual directory/volume/source are never opened here.
    assert reader._validate_control(c["source"]["path"], c, reader.control_sha256(c), a,
                                    reader.control_sha256(a)) == c
    c["source"]["volume"]["device"] += 1
    a = approval(c)
    with pytest.raises(reader.Refusal, match="volume_descriptor_type"):
        reader._validate_control(c["source"]["path"], c, reader.control_sha256(c), a, reader.control_sha256(a))


def test_native_descriptor_volume_on_invented_directory(area):
    import ctypes
    assert ctypes.sizeof(reader._DarwinStatFS) == 2168 and ctypes.alignment(reader._DarwinStatFS) == 8
    value = reader._observe_volume(area)
    assert value["filesystem"] == "apfs" and value["device"] == area.stat().st_dev
    assert value["device"] == Path(value["mount"]).stat().st_dev
    assert len(value["fsid"]) == 2 and value["method"] == "darwin_fstatfs_diskutil"
    assert reader.re.fullmatch(r"[0-9A-Fa-f]{8}(-[0-9A-Fa-f]{4}){3}-[0-9A-Fa-f]{12}", value["uuid"])


@pytest.mark.parametrize("fault,reason",[("nonzero","volume_tool_nonzero:invented error"),
    ("stdout","volume_output_limit"),("stderr","volume_output_limit"),("time","volume_time_limit"),
    ("rss","volume_rss_limit"),("monitor","rss_monitor_unavailable"),("plist","volume_plist_fields")])
def test_volume_tool_bounded_transport_and_error(monkeypatch, fault, reason):
    import plistlib
    original = reader.subprocess.Popen
    children = []
    codes = {"nonzero":"import sys;sys.stdout.buffer.write("+repr(plistlib.dumps({"ErrorMessage":"invented error"}))+ ");sys.exit(1)",
        "stdout":"import sys;sys.stdout.write('x'*70000)","stderr":"import sys;sys.stderr.write('x'*5000)",
        "time":"import time;time.sleep(10)","rss":"import time;time.sleep(10)",
        "monitor":"import time;time.sleep(10)","plist":"import sys;sys.stdout.buffer.write("+repr(plistlib.dumps([]))+")"}
    def fake(command, **kwargs):
        assert command == ["/usr/sbin/diskutil", "info", "-plist", "/invented"]
        p = original([reader.sys.executable, "-I", "-c", codes[fault]], **kwargs)
        children.append(p); return p
    monkeypatch.setattr(reader.subprocess,"Popen",fake)
    monkeypatch.setattr(reader,"_sample_rss",lambda pid: 1)
    if fault == "time":
        original_time = reader.time.monotonic; calls = [0]
        def clock():
            calls[0] += 1
            return original_time() + (4 if calls[0] > 1 else 0)
        monkeypatch.setattr(reader.time,"monotonic",clock)
    elif fault == "rss": monkeypatch.setattr(reader,"_sample_rss",lambda pid: 4*1024**3)
    elif fault == "monitor": monkeypatch.setattr(reader,"_sample_rss",lambda pid: (_ for _ in ()).throw(reader.Refusal("rss_monitor_unavailable")))
    with pytest.raises(reader.Refusal,match=reason): reader._volume_tool("/invented")
    assert all(p.poll() is not None for p in children)
