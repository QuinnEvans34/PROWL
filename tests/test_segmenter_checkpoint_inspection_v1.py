"""SUP-02A invented serialization only. No actual file/model execution."""
from collections import OrderedDict
from contextlib import nullcontext
from copy import deepcopy
import hashlib
import io
import json
from pathlib import Path
import socket
import struct
import tempfile
import zipfile

import pytest
import torch

from src.models import segmenter_checkpoint_inspection_v1 as inspector
from src.models.segresnet import build_model


def control(path, namespace="identity"):
    return dict(schema_version=inspector.CONTROL_VERSION, evidence_domain=inspector.DOMAIN,
                source=dict(root=str(path.parent), path=str(path), bytes=path.stat().st_size,
                            sha256=hashlib.sha256(path.read_bytes()).hexdigest()),
                architecture=inspector.architecture(), expected_signature=inspector.expected_signature(),
                namespace=namespace, wrapper="net_optimizer_scheduler_epoch", limits=inspector.limits())


def run(path, c, native=False):
    pin = inspector.control_sha256(c)
    if native:
        return inspector.inspect_checkpoint(path, pinned_control=c, expected_control_sha256=pin)
    return inspector._inspect_local(path, c, pin)


def assert_refused(report, reason=None):
    assert report["status"] == "refused", report
    assert report["execution_authority"] == "none" and report["training_eligible"] is False
    assert report["values_audited"] is False
    if reason:
        assert report["reason"] == reason, report["reason"]
    assert len(json.dumps(report, allow_nan=False).encode()) < 1024**2


@pytest.fixture(autouse=True)
def restore_test_globals():
    # Unit tests enter the private worker implementation; public API isolation is tested separately.
    before = torch.serialization.get_safe_globals()
    rng = torch.get_rng_state().clone()
    yield
    torch.serialization.clear_safe_globals()
    torch.serialization.add_safe_globals(before)
    torch.set_rng_state(rng)


@pytest.fixture(scope="module")
def factory():
    with torch.random.fork_rng(devices=[]):
        torch.manual_seed(812)
        model = build_model({"model": inspector.architecture()})
    return model.state_dict()


@pytest.fixture
def area():
    with tempfile.TemporaryDirectory(prefix="prowl-invented-checkpoint-",
                                     dir=Path(tempfile.gettempdir()).resolve()) as name:
        yield Path(name)


@pytest.fixture
def fixture(area, factory):
    path = area / "invented-full.pth"
    blob = {"net": factory, "optimizer": {"state": {0: {"step": torch.tensor(1.)}},
                                         "param_groups": [{"params": [0], "lr": .0003}]},
            "scheduler": {"last_epoch": 0}, "epoch": 0}
    torch.save(blob, path)
    return path, control(path), blob


def rewrite(path, blob, namespace="identity"):
    torch.save(blob, path)
    return control(path, namespace)


def independent_archive(path):
    result = {}
    with zipfile.ZipFile(path) as archive, path.open("rb") as stream:
        for member in archive.infolist():
            stream.seek(member.header_offset)
            raw = struct.unpack("<4s5H3I2H", stream.read(30))
            offset = member.header_offset + 30 + raw[-2] + raw[-1]
            result[member.filename.partition("/")[2]] = (offset, member.file_size)
    return result


def test_fixed_complete_signature_matches_independent_factory(factory):
    expected = {k: {"shape": list(v.shape), "dtype": str(v.dtype)} for k, v in factory.items()}
    assert expected == inspector.expected_signature()
    assert len(expected) == 83
    assert sum(v.numel() * v.element_size() for v in factory.values()) == 18805696


def test_native_complete_inventory_and_no_payload_read(fixture, monkeypatch):
    path, c, _ = fixture
    before = path.read_bytes(), deepcopy(c), torch.get_rng_state().clone()
    globals_before = torch.serialization.get_safe_globals()
    monkeypatch.setattr(socket, "socket", lambda *a, **k: pytest.fail("Network used"))
    monkeypatch.setattr(torch.nn.Module, "__call__", lambda *a, **k: pytest.fail("Model executed"))
    result = run(path, c, native=True)
    assert result["status"] == "pass", result
    assert len(result["model"]) == 83 and result["identity_verified"]
    assert result["metadata_compatible"] and not result["training_eligible"]
    assert not result["values_audited"] and result["execution_authority"] == "none"
    assert result["io"]["hash_bytes"] == c["source"]["bytes"]
    assert result["io"]["virtual_zero_bytes"] >= 0
    assert result["io"]["metadata_storage_source_bytes"] == 0
    assert result["io"]["aggregate_requested_bytes"] == sum(result["io"][k] for k in
           ("hash_bytes", "metadata_source_bytes", "virtual_zero_bytes"))
    offsets = independent_archive(path)
    for row in result["model"].values():
        assert (row["storage_file_offset"], row["storage_bytes"]) == offsets[row["storage_member"]]
        assert row["source_device"] == "cpu"
    assert result["worker"]["sampled_peak_rss_bytes"] > 0
    assert result["worker"]["child_peak_rss_bytes"] > 0
    assert result["worker"]["sampling_seconds"] == .05
    assert result["worker"]["elapsed_seconds"] < 60 and result["worker"]["exit_code"] == 0
    assert path.read_bytes() == before[0] and c == before[1]
    assert torch.equal(torch.get_rng_state(), before[2])
    assert torch.serialization.get_safe_globals() == globals_before


def test_metadata_only_descriptor_calls_exclude_storages(fixture, monkeypatch):
    path, c, _ = fixture
    original = inspector.os.pread
    ranges = []
    def observed(fd, count, offset):
        ranges.append((offset, offset + count))
        return original(fd, count, offset)
    monkeypatch.setattr(inspector.os, "pread", observed)
    result = run(path, c)
    assert result["status"] == "pass", result
    # The first ceil(file/1MiB) calls are the explicitly allowed identity hash pass.
    metadata = ranges[(c["source"]["bytes"] + 1024**2 - 1) // 1024**2:]
    storage_spans = [(a, a + size) for name, (a, size) in independent_archive(path).items()
                     if name.startswith("data/")]
    assert all(max(a, x) >= min(b, y) for a, b in metadata for x, y in storage_spans)


def test_deterministic_semantic_report(fixture):
    path, c, _ = fixture
    a, b = run(path, c), run(path, c)
    assert a == b and a["status"] == "pass"


@pytest.mark.parametrize("namespace", ["identity", "uniform_module"])
def test_uniform_namespace_and_alias_inventory(fixture, namespace):
    path, _, blob = fixture
    # Alias one equal-shaped pair: a real shared storage, not merely equal contents.
    net = dict(blob["net"])
    net["conv_final.0.bias"] = net["conv_final.0.weight"]
    if namespace == "uniform_module":
        net = {"module." + k: v for k, v in net.items()}
    blob["net"] = net
    c = rewrite(path, blob, namespace)
    result = run(path, c)
    assert result["status"] == "pass", result
    assert sorted(["net/conv_final.0.bias", "net/conv_final.0.weight"]) in \
        result["auxiliary"]["aliases"].values()


@pytest.mark.parametrize("change,reason", [
    ("domain", "actual_domain_refused"), ("version", "control_version"),
    ("extra", "control_fields"), ("architecture", "architecture_mismatch"),
    ("signature", "incomplete_expected_signature"), ("namespace", "namespace_policy"),
    ("wrapper", "wrapper_policy"), ("actual_hash", "actual_candidate_refused"),
    ("traversal", "unsafe_source_path"), ("outside_root", "non_test_root_refused"),
    ("filename", "source_path_mismatch"), ("size", "file_byte_limit"),
    ("boolean_limit", "invalid_limit"), ("large_limit", "invalid_limit"),
    ("extra_limit", "limit_fields"), ("small_control", "control_byte_limit"),
    ("model_count", "model_tensor_limit"), ("model_bytes", "model_byte_limit"),
])
def test_control_rejects_before_source_open(fixture, monkeypatch, change, reason):
    path, c, _ = fixture
    if change == "domain": c["evidence_domain"] = "actual_checkpoint"
    elif change == "version": c["schema_version"] = "unknown"
    elif change == "extra": c["run_authorized"] = True
    elif change == "architecture": c["architecture"]["out_channels"] = 3
    elif change == "signature": c["expected_signature"].pop("convInit.conv.weight")
    elif change == "namespace": c["namespace"] = "strip_anything"
    elif change == "wrapper": c["wrapper"] = "guess"
    elif change == "actual_hash": c["source"]["sha256"] = inspector.ACTUAL_CANDIDATE_SHA
    elif change == "traversal": c["source"]["path"] = str(path.parent) + "/../" + path.name
    elif change == "outside_root": c["source"]["root"] = "/"
    elif change == "filename": c["source"]["path"] = str(path.parent / "supervised_suprem.pth")
    elif change == "size": c["source"]["bytes"] = 64 * 1024**2 + 1
    elif change == "boolean_limit": c["limits"]["max_members"] = True
    elif change == "large_limit": c["limits"]["max_members"] = 4097
    elif change == "extra_limit": c["limits"]["actual_read_allowed"] = 1
    elif change == "small_control": c["limits"]["max_control_bytes"] = 1
    elif change == "model_count": c["limits"]["max_model_tensors"] = 82
    elif change == "model_bytes": c["limits"]["max_model_bytes"] = 18805695
    pin = inspector.control_sha256(c)
    monkeypatch.setattr(inspector.os, "open", lambda *a, **k: pytest.fail("Source opened"))
    result = inspector.inspect_checkpoint(path, pinned_control=c, expected_control_sha256=pin)
    assert_refused(result, reason)


def test_control_pin_and_nonfinite_refusal(fixture, monkeypatch):
    path, c, _ = fixture
    pin = inspector.control_sha256(c)
    c["source"]["bytes"] -= 1
    monkeypatch.setattr(inspector.os, "open", lambda *a, **k: pytest.fail("Source opened"))
    assert_refused(inspector.inspect_checkpoint(path, pinned_control=c,
                                              expected_control_sha256=pin), "control_pin_mismatch")
    c["limits"]["max_worker_seconds"] = float("nan")
    assert_refused(inspector.inspect_checkpoint(path, pinned_control=c,
                                              expected_control_sha256=pin), "nonfinite_json")


@pytest.mark.parametrize("kind,reason", [
    ("symlink", "symlink_refused"), ("parent_symlink", "symlink_refused"),
    ("hardlink", "non_regular_or_hardlinked_source"),
    ("directory", "non_regular_or_hardlinked_source"),
    ("private_mode", "non_private_test_root"), ("size", "file_size_mismatch"),
    ("hash", "file_hash_mismatch"),
])
def test_source_identity_refusals(fixture, kind, reason):
    path, c, _ = fixture
    if kind == "symlink":
        moved = path.with_name("invented-original.pth")
        path.rename(moved); path.symlink_to(moved)
    elif kind == "parent_symlink":
        # Canonical source root still contains a symlink component.
        alias = path.parent / "prowl-invented-checkpoint-alias"
        alias.symlink_to(path.parent, target_is_directory=True)
        c["source"]["root"] = str(alias); c["source"]["path"] = str(alias / path.name)
        path = alias / path.name
    elif kind == "hardlink":
        path.with_name("invented-alias.pth").hardlink_to(path)
    elif kind == "directory":
        path.unlink(); path.mkdir()
    elif kind == "private_mode":
        path.parent.chmod(0o755)
    elif kind == "size":
        c["source"]["bytes"] -= 1
    elif kind == "hash":
        c["source"]["sha256"] = "0" * 64
    result = run(path, c)
    assert_refused(result, reason)
    assert result["model"] is None


@pytest.mark.parametrize("change", ["replace", "mutate"])
def test_descriptor_detects_mid_read_changes(fixture, monkeypatch, change):
    path, c, _ = fixture
    original = inspector.os.pread
    done = False
    def changing(fd, count, offset):
        nonlocal done
        data = original(fd, count, offset)
        if not done:
            done = True
            if change == "replace":
                new = path.with_name("invented-replacement.pth")
                new.write_bytes(path.read_bytes()); new.replace(path)
            else:
                with path.open("r+b") as writer:
                    writer.seek(0); writer.write(b"NOPE")
        return data
    monkeypatch.setattr(inspector.os, "pread", changing)
    assert_refused(run(path, c), "source_mutated_or_replaced")


@pytest.mark.parametrize("change,reason", [
    ("missing", "model_key_mismatch"), ("extra", "model_key_mismatch"),
    ("wrong_head", "model_shape_or_dtype_mismatch"), ("wrong_dtype", "model_shape_or_dtype_mismatch"),
    ("mixed_prefix", "namespace_mismatch"), ("repeated_prefix", "namespace_mismatch"),
    ("wrong_wrapper", "wrapper_mismatch"), ("extra_wrapper", "wrapper_mismatch"),
    ("nonfinite", "nonfinite_primitive"), ("tuple", "container_value_type"),
    ("negative_epoch", "auxiliary_wrapper_type"), ("out_of_storage", "view_out_of_storage"),
])
def test_model_and_container_refusals(fixture, change, reason):
    path, _, blob = fixture
    blob = dict(blob); blob["net"] = dict(blob["net"])
    namespace = "identity"
    if change == "missing": blob["net"].pop("convInit.conv.weight")
    elif change == "extra": blob["net"]["unknown"] = torch.ones(1)
    elif change == "wrong_head": blob["net"]["conv_final.2.conv.bias"] = torch.ones(3)
    elif change == "wrong_dtype": blob["net"]["conv_final.0.weight"] = torch.ones(16, dtype=torch.float64)
    elif change == "mixed_prefix":
        value = blob["net"].pop("convInit.conv.weight"); blob["net"]["module.convInit.conv.weight"] = value
    elif change == "repeated_prefix":
        blob["net"] = {"module.module." + k: v for k, v in blob["net"].items()}
        namespace = "uniform_module"
    elif change == "wrong_wrapper": blob = blob["net"]
    elif change == "extra_wrapper": blob["extra"] = 1
    elif change == "nonfinite": blob["optimizer"]["lr"] = float("inf")
    elif change == "tuple": blob["optimizer"]["betas"] = (.9, .999)
    elif change == "negative_epoch": blob["epoch"] = -1
    elif change == "out_of_storage":
        # A stride-zero 16-element logical view over one float has a valid span, but
        # is unsupported because logical repetition is not a contiguous state tensor.
        blob["net"]["conv_final.0.weight"] = torch.ones(1).expand(16)
        reason = "unsupported_tensor_view"
    c = rewrite(path, blob, namespace)
    assert_refused(run(path, c), reason)


def test_legacy_format_refuses_before_torch_load(fixture, monkeypatch):
    path, _, blob = fixture
    torch.save(blob, path, _use_new_zipfile_serialization=False)
    c = control(path)
    monkeypatch.setattr(torch, "load", lambda *a, **k: pytest.fail("Legacy decoding attempted"))
    assert_refused(run(path, c), "zip_footer_or_comment")


def test_raw_view_cannot_expose_descriptor_or_unmetered_read(fixture):
    path, c, _ = fixture
    with inspector._Source(c) as source:
        source.hash()
        inspector._archive(source)
        view = inspector._View(source)
        with pytest.raises(io.UnsupportedOperation):
            view.fileno()
        assert not hasattr(view, "name")
        with pytest.raises(inspector.Refusal, match="seek_out_of_file"):
            view.seek(-1)
        c["limits"]["max_metadata_read_bytes"] = source.requested - source.hash_bytes
        with pytest.raises(inspector.Refusal, match="metadata_read_limit"):
            view.read(1)


@pytest.mark.parametrize("cap,reason", [
    ("max_directory_bytes", "directory_byte_limit"),
    ("max_pickle_bytes", "metadata_member_byte_limit"),
    ("max_members", "member_count_limit"), ("max_storages", "storage_count_limit"),
    ("max_storage_bytes", "storage_byte_limit"),
    ("max_metadata_read_bytes", "metadata_read_limit"),
    ("max_text_bytes", "text_limit"), ("max_depth", "container_structure_limit"),
    ("max_items", "container_structure_limit"),
])
def test_structure_and_read_caps(fixture, cap, reason):
    path, c, _ = fixture
    if cap == "max_text_bytes":
        # Path is valid; a long auxiliary key crosses this same UTF-8 cap.
        _, _, blob = fixture
        blob["optimizer"]["x" * 200] = 1
        c = rewrite(path, blob); c["limits"][cap] = max(len(str(path).encode()), 128)
    elif cap == "max_items":
        # More auxiliary items than archive read calls, so this tests inventory cap.
        _, _, blob = fixture
        blob["optimizer"]["many"] = list(range(4096))
        c = rewrite(path, blob); c["limits"][cap] = 2048
    else:
        c["limits"][cap] = 1
    assert_refused(run(path, c), reason)


class SideEffect:
    def __init__(self, marker):
        self.marker = marker
    def __reduce__(self):
        return eval, (f"open({str(self.marker)!r}, 'w').write('executed')",)


def test_unsafe_global_never_executes_even_if_parent_allowlists_it(fixture):
    path, _, blob = fixture
    marker = path.parent / "must-not-exist"
    blob["optimizer"]["attack"] = SideEffect(marker)
    c = rewrite(path, blob)
    with torch.serialization.safe_globals([eval]):
        before = torch.serialization.get_safe_globals()
        report = run(path, c, native=True)
        assert torch.serialization.get_safe_globals() == before
    assert_refused(report, "restricted_decode_refused")
    assert not marker.exists()


@pytest.mark.parametrize("cap,reason,value", [
    ("max_worker_seconds", "worker_time_limit", .05),
    ("max_worker_rss_bytes", "worker_rss_limit", 1),
    ("max_report_bytes", "report_byte_limit", 2048),
])
def test_native_worker_stops_and_reaps(fixture, cap, reason, value):
    path, c, _ = fixture
    c["limits"][cap] = value
    report = run(path, c, native=True)
    assert_refused(report, reason)
    if report["worker"]:
        assert report["worker"]["exit_code"] is not None


def test_unavailable_monitor_refuses_without_source_open(fixture, monkeypatch):
    path, c, _ = fixture
    def unavailable(pid):
        raise inspector.Refusal("rss_monitor_unavailable")
    monkeypatch.setattr(inspector, "_sample_rss", unavailable)
    report = run(path, c, native=True)
    assert_refused(report, "rss_monitor_unavailable")
    assert not report["identity_verified"] and report["worker"]["exit_code"] is not None


def repack(path, transform, compression=zipfile.ZIP_STORED):
    # Read/copy only this freshly invented archive. No actual source is opened.
    with zipfile.ZipFile(path) as archive:
        entries = [(m.filename, archive.read(m)) for m in archive.infolist()]
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=compression) as archive:
        for name, data in transform(entries):
            archive.writestr(name, data)
    path.write_bytes(buffer.getvalue())
    return control(path)


@pytest.mark.parametrize("kind,reason", [
    ("compressed", "compressed_member_refused"), ("duplicate", "duplicate_member"),
    ("traversal", "unsafe_member_name"), ("absolute", "unsafe_member_name"),
    ("backslash", "unsafe_member_name"), ("unknown", "unknown_archive_member"),
    ("mixed_root", "mixed_archive_root"), ("missing_pickle", "missing_metadata_member"),
    ("no_storages", "missing_storage_members"),
])
def test_archive_layout_refuses_before_decoder(fixture, monkeypatch, kind, reason):
    path, _, _ = fixture
    def transform(entries):
        if kind == "duplicate": return entries + [entries[0]]
        if kind == "missing_pickle": return [(n, d) for n, d in entries if not n.endswith("/data.pkl")]
        if kind == "no_storages": return [(n, d) for n, d in entries if "/data/" not in n]
        if kind in ("traversal", "absolute", "backslash", "unknown", "mixed_root"):
            name, data = entries[0]
            root = name.partition("/")[0]
            bad = {"traversal": root + "/../data.pkl", "absolute": "/" + name,
                   "backslash": root + "\\data.pkl", "unknown": root + "/surprise",
                   "mixed_root": "other/.data/serialization_id"}[kind]
            if kind == "mixed_root":
                return entries + [(bad, b"0")]
            return [(bad, data)] + entries[1:]
        return entries
    with pytest.warns(UserWarning, match="Duplicate name") if kind == "duplicate" else nullcontext():
        c = repack(path, transform, zipfile.ZIP_DEFLATED if kind == "compressed" else zipfile.ZIP_STORED)
    monkeypatch.setattr(torch, "load", lambda *a, **k: pytest.fail("Invalid ZIP decoded"))
    assert_refused(run(path, c), reason)


@pytest.mark.parametrize("kind,reason", [
    ("encrypted", "encrypted_or_unsupported_flags"),
    ("local_name", "local_name_disagreement"),
    ("local_size", "local_size_disagreement"),
    ("local_offset", "overlapping_or_bad_header"),
    ("footer_comment", "zip_footer_or_comment"),
    ("multivolume", "multivolume_zip"),
    ("directory_size", "directory_byte_limit"),
    ("directory_offset", "directory_out_of_file"),
    ("zip64_locator", "invalid_zip64_locator"),
    ("zip64_count", "member_count_limit"),
])
def test_forged_archive_headers(fixture, monkeypatch, kind, reason):
    path, _, _ = fixture
    data = bytearray(path.read_bytes())
    footer = len(data) - 22
    directory = struct.unpack_from("<I", data, footer + 16)[0]
    zip64 = struct.unpack_from("<Q", data, len(data) - 42 + 8)[0]
    if kind == "encrypted":
        flags = struct.unpack_from("<H", data, directory + 8)[0]
        struct.pack_into("<H", data, directory + 8, flags | 1)
    elif kind == "local_name":
        data[30] = ord("X")
    elif kind == "local_size":
        struct.pack_into("<I", data, 18, 123)
    elif kind == "local_offset":
        struct.pack_into("<I", data, directory + 42, len(data))
    elif kind == "footer_comment":
        struct.pack_into("<H", data, footer + 20, 1)
    elif kind == "multivolume":
        struct.pack_into("<H", data, footer + 4, 1)
    elif kind == "directory_size":
        struct.pack_into("<I", data, footer + 12, 1024**2 + 1)
        struct.pack_into("<Q", data, zip64 + 40, 1024**2 + 1)
    elif kind == "directory_offset":
        struct.pack_into("<I", data, footer + 16, len(data))
        struct.pack_into("<Q", data, zip64 + 48, len(data))
    elif kind == "zip64_locator":
        struct.pack_into("<Q", data, len(data) - 42 + 8, len(data))
    elif kind == "zip64_count":
        struct.pack_into("<2H", data, footer + 8, 4097, 4097)
        struct.pack_into("<2Q", data, zip64 + 24, 4097, 4097)
    path.write_bytes(data)
    c = control(path)
    monkeypatch.setattr(torch, "load", lambda *a, **k: pytest.fail("Forged ZIP decoded"))
    assert_refused(run(path, c), reason)


def test_restricted_load_arguments_and_no_materialized_tensors(fixture, monkeypatch):
    path, c, _ = fixture
    original = torch.load
    calls = []
    def observed(view, **kwargs):
        calls.append(kwargs)
        assert isinstance(view, inspector._View)
        blob = original(view, **kwargs)
        assert all(v.untyped_storage().device.type == "meta" for v in blob["net"].values())
        return blob
    monkeypatch.setattr(torch, "load", observed)
    assert run(path, c)["status"] == "pass"
    assert calls == [{"weights_only": True, "map_location": "cpu", "mmap": False}]


def test_report_cap_refuses_large_inventory(fixture):
    path, c, _ = fixture
    c["limits"]["max_report_bytes"] = 2048
    assert_refused(run(path, c, native=True), "report_byte_limit")


def test_native_full_model_with_small_index_masks_tail_storage(fixture):
    path, _, blob = fixture
    # Independent packed-storage construction: all 83 complete tensors are
    # contiguous views into one invented buffer. The tiny ZIP index forces
    # PyTorch's footer read to cross actual storage intervals.
    items = list(blob["net"].items())
    packed = torch.cat([value.flatten() for _, value in items])
    offset, net = 0, {}
    for key, value in items:
        net[key] = packed[offset:offset + value.numel()].view(value.shape)
        offset += value.numel()
    blob["net"] = net
    c = rewrite(path, blob)
    report = run(path, c, native=True)
    assert report["status"] == "pass", report
    assert len(report["model"]) == 83 and report["archive"]["storage_count"] == 2
    assert report["io"]["virtual_zero_bytes"] > 0
    assert report["io"]["metadata_storage_source_bytes"] == 0
    assert any(len(keys) == 83 for keys in report["auxiliary"]["aliases"].values())
    for key, row in report["model"].items():
        assert row["shape"] == list(net[key].shape)
        assert row["stride"] == list(net[key].stride())
        assert row["storage_offset"] == net[key].storage_offset()


@pytest.mark.parametrize("kind,reason", [
    ("net", "model_attributes_refused"), ("auxiliary", "container_attributes_refused"),
    ("version_nonfinite", "nonfinite_primitive"),
])
def test_serialized_dictionary_attributes_are_not_ignored(fixture, kind, reason):
    path, _, blob = fixture
    blob["net"] = OrderedDict(blob["net"])
    if kind == "net":
        blob["net"].unreviewed = {"surprise": 1}
    elif kind == "auxiliary":
        blob["optimizer"]["state"] = OrderedDict(blob["optimizer"]["state"])
        blob["optimizer"]["state"].unreviewed = 1
    else:
        blob["net"]._metadata = {"invented": {"version": float("inf")}}
    c = rewrite(path, blob)
    assert_refused(run(path, c), reason)


def test_value_finiteness_is_explicitly_unaudited(fixture):
    path, _, blob = fixture
    blob["net"] = dict(blob["net"])
    blob["net"]["conv_final.0.weight"] = torch.full((16,), float("nan"))
    report = run(path, rewrite(path, blob))
    assert report["status"] == "pass"
    assert report["values_audited"] is False and report["training_eligible"] is False


@pytest.mark.parametrize("kind", ["complex", "sparse", "requires_grad", "transposed"])
def test_auxiliary_unsupported_tensor_policies(fixture, kind):
    path, _, blob = fixture
    value = torch.ones((2, 2))
    if kind == "complex": value = value.to(torch.complex64)
    elif kind == "sparse": value = value.to_sparse()
    elif kind == "requires_grad": value.requires_grad_(True)
    elif kind == "transposed": value = value.t()
    blob["optimizer"]["unsupported"] = value
    report = run(path, rewrite(path, blob))
    assert_refused(report)
    assert report["reason"] in ("unsupported_tensor_type_or_layout", "unsupported_tensor_view",
                                "format_or_restricted_decode_refused", "restricted_decode_refused")


def test_original_accelerator_location_is_refused_without_allocation(fixture):
    path, _, _ = fixture
    def transform(entries):
        result = []
        for name, data in entries:
            # The qualified older ZIP layout computes offsets directly. Removing
            # the newer format hint prevents miniz alignment arithmetic on repacked files.
            if name.endswith("/.format_version"):
                continue
            if name.endswith("/data.pkl"):
                token = b"X\x03\x00\x00\x00cpu"
                assert token in data
                data = data.replace(token, b"X\x06\x00\x00\x00cuda:0")
            result.append((name, data))
        return result
    c = repack(path, transform)
    assert_refused(run(path, c), "non_cpu_or_materialized_storage")


def test_child_reported_peak_closes_sampling_gap(fixture, monkeypatch):
    path, c, _ = fixture
    # Simulate a polling gap: the child reports its independent real peak after
    # a complete invented inspection, even though samples under-report it.
    monkeypatch.setattr(inspector, "_sample_rss", lambda pid: 1)
    c["limits"]["max_worker_rss_bytes"] = 32 * 1024**2
    report = run(path, c, native=True)
    assert_refused(report, "worker_peak_rss_limit")
    assert report["metadata_compatible"] is False
    assert report["worker"]["termination_reason"] == "worker_peak_rss_limit"
    assert report["worker"]["sampled_peak_rss_bytes"] == 1
    assert report["worker"]["child_peak_rss_bytes"] > c["limits"]["max_worker_rss_bytes"]
    assert report["worker"]["exit_code"] == 0
