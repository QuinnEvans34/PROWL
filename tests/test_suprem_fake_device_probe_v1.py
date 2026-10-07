"""Only generated fixtures; no actual checkpoint/control or accepted reader changes."""
from copy import deepcopy
import importlib.util
import io
import json
from pathlib import Path
import subprocess
import sys

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "scripts/diagnostics/probe_suprem_fake_device_v1.py"
spec = importlib.util.spec_from_file_location("device_probe", SCRIPT)
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


@pytest.mark.parametrize("tag", ["cpu", "cuda:0", "cuda:3", "mps:0"])
def test_native_generated_tag_observations_no_payload(tag, record_property):
    result = probe.probe_fixture(tag)
    assert result["status"] == "pass", result
    assert result["evidence_domain"] == "invented_fake_device"
    assert result["actual_source_access"] is False and result["values_audited"] is False
    assert result["execution_authority"] == "none" and result["training_eligible"] is False
    seen = result["observation"]
    assert seen["shape"] == [2, 3] and seen["stride"] == [3, 1]
    assert seen["logical_bytes"] == seen["storage_bytes"] == 24 and seen["dtype"] == "torch.float32"
    assert seen["serialized_storage_tag"] == tag
    assert seen["is_fake_tensor"] is True and seen["tensor_device"] == "cpu" and seen["storage_device"] == "meta"
    assert seen["checks"] == {"source_tag_is_cpu": tag == "cpu", "tensor_is_cpu": True,
                              "storage_is_meta": True, "reader2_guard_would_pass": tag == "cpu"}
    evidence = result["io"]
    assert evidence["metadata_storage_source_bytes"] == 0
    assert evidence["aggregate_requested_bytes"] == sum(evidence[k] for k in
        ("hash_bytes", "metadata_source_bytes", "virtual_zero_bytes"))
    assert 0 < evidence["hash_bytes"] <= 65536
    assert evidence["aggregate_requested_bytes"] <= evidence["hash_bytes"] + 128 * 1024
    resources = result["resources"]
    assert resources["owned_worker_reaped"] and resources["exit_code"] == 0
    assert resources["samples"] > 0 and resources["aggregate_sampled_peak_rss_bytes"] < 3 * 1024**3
    assert resources["elapsed_seconds"] < 15 and resources["stderr_bytes"] == 0
    record_property("device_probe_report", json.dumps(result, sort_keys=True))


@pytest.mark.parametrize("tag", [None, 1, {}, "cuda", "cuda:1", "../pretrained_weights/x.pth", "actual"])
def test_no_source_path_or_unlisted_tag_before_process(tag, monkeypatch):
    monkeypatch.setattr(probe, "sample", lambda *a: pytest.fail("invalid input reached monitor"))
    monkeypatch.setattr(probe.subprocess, "Popen", lambda *a, **k: pytest.fail("invalid input spawned"))
    with pytest.raises(probe.Refusal, match="fixture_tag_refused"):
        probe.probe_fixture(tag)


@pytest.mark.parametrize("inputs,reason", [
    ({"tag": "cpu", "path": "pretrained_weights/anything.pth"}, "worker_input_fields"),
    ({"tag": "cuda:1"}, "fixture_tag_refused"),
    ({"tag": "actual"}, "fixture_tag_refused"),
    ({"path": "actual"}, "worker_input_fields"),
])
def test_worker_rejects_source_inputs_before_generation(inputs, reason, monkeypatch):
    monkeypatch.setattr(probe.sys, "stdin", type("Input", (), {"buffer": io.BytesIO(json.dumps(inputs).encode())})())
    monkeypatch.setattr(probe, "_generate_observations", lambda *a: pytest.fail("invalid worker input generated"))
    with pytest.raises(probe.Refusal, match=reason):
        probe._worker()


def test_worker_input_byte_cap(monkeypatch):
    monkeypatch.setattr(probe.sys, "stdin", type("Input", (), {"buffer": io.BytesIO(b"x" * 257)})())
    with pytest.raises(probe.Refusal, match="worker_input_limit"):
        probe._worker()


@pytest.mark.parametrize("reason", ["monitor_unavailable", "aggregate_rss_limit"])
def test_monitor_and_rss_preflight_refuse_before_child(reason, monkeypatch):
    def sample(*a):
        if reason == "monitor_unavailable":
            raise probe.Refusal(reason)
        return probe.RSS + 1
    monkeypatch.setattr(probe, "sample", sample)
    monkeypatch.setattr(probe.subprocess, "Popen", lambda *a, **k: pytest.fail("preflight spawned"))
    result = probe.probe_fixture("cpu")
    assert result["status"] == "refused" and result["reason"] == reason
    assert result["observation"] is None and result["resources"]["owned_worker_reaped"]
    assert result["resources"]["exit_code"] is None


@pytest.mark.parametrize("code,reason", [
    ("import time; time.sleep(3)", "worker_time_limit"),
    ("import sys; sys.stdout.write('x'*9000);sys.stdout.flush()", "worker_output_limit"),
    ("import sys; sys.stderr.write('x'*5000);sys.stderr.flush()", "worker_stderr_limit"),
    ("import sys; sys.stdout.write('{}')", "worker_report_fields"),
    ("import sys; sys.exit(7)", "worker_exit_failure"),
])
def test_native_faults_terminate_only_owned_worker(code, reason, monkeypatch):
    original = subprocess.Popen
    owned = []
    def spawn(args, **kwargs):
        if args[0] == "/bin/ps":
            return original(args, **kwargs)
        assert args[-1] == "--owned-worker" and kwargs["start_new_session"] is True
        child = original([sys.executable, "-I", "-c", code], **kwargs)
        owned.append(child)
        return child
    monkeypatch.setattr(probe.subprocess, "Popen", spawn)
    if reason == "worker_time_limit":
        monkeypatch.setattr(probe, "SECONDS", .02)
    result = probe.probe_fixture("cpu")
    assert result["status"] == "refused" and result["reason"] == reason, result
    assert result["observation"] is None and result["io"] is None
    assert result["resources"]["owned_worker_reaped"] is True
    assert len(owned) == 1 and owned[0].poll() is not None
    assert all(stream.closed for stream in (owned[0].stdin, owned[0].stdout, owned[0].stderr))


def valid_report():
    value = probe.report("cpu")
    value.update(status="pass", reason="invented_device_observations_complete",
        observation=dict(shape=[2, 3], dtype="torch.float32", stride=[3, 1], logical_bytes=24,
            serialized_storage_tag="cpu", tensor_device="cpu", storage_device="meta", is_fake_tensor=True,
            storage_file_offset=512, storage_bytes=24,
            checks=dict(source_tag_is_cpu=True, tensor_is_cpu=True, storage_is_meta=True,
                        reader2_guard_would_pass=True)),
        io=dict(aggregate_requested_bytes=3000, hash_bytes=2000, metadata_source_bytes=1000,
                metadata_storage_source_bytes=0, virtual_zero_bytes=0))
    return value


@pytest.mark.parametrize("field,value,reason", [
    ("training_eligible", True, "worker_report_authority"),
    ("actual_source_access", True, "worker_report_authority"),
    ("fixture_tag", "cuda:0", "worker_report_binding"),
    ("schema_version", "other", "worker_report_binding"),
    ("resources", {}, "worker_report_status"),
])
def test_parent_refuses_wrong_authority_and_bindings(field, value, reason):
    data = valid_report();data[field] = value
    with pytest.raises(probe.Refusal, match=reason):
        probe.validate_report(data, "cpu")


@pytest.mark.parametrize("field,value,reason", [
    ("is_fake_tensor", False, "fixture_metadata_mismatch"),
    ("logical_bytes", 25, "fixture_metadata_mismatch"),
    ("serialized_storage_tag", "cuda:0", "fixture_device_mismatch"),
    ("checks", {"source_tag_is_cpu": True}, "check_fields"),
])
def test_parent_refuses_forged_metadata(field, value, reason):
    data = valid_report();data["observation"][field] = value
    with pytest.raises(probe.Refusal, match=reason):
        probe.validate_report(data, "cpu")


def test_storage_payload_read_in_report_refused():
    data = valid_report();data["io"]["metadata_storage_source_bytes"] = 1
    with pytest.raises(probe.Refusal, match="io_binding"):
        probe.validate_report(data, "cpu")


def test_false_conjunction_is_not_a_successful_guard():
    data = valid_report();data["observation"]["storage_device"] = "cpu"
    data["observation"]["checks"].update(storage_is_meta=False, reader2_guard_would_pass=False)
    assert probe.validate_report(data, "cpu")["observation"]["checks"]["reader2_guard_would_pass"] is False
    data["observation"]["checks"]["reader2_guard_would_pass"] = True
    with pytest.raises(probe.Refusal, match="check_binding"):
        probe.validate_report(data, "cpu")


def test_actual_path_cli_arguments_refused_before_fixture():
    result = subprocess.run([sys.executable, "-I", str(SCRIPT), "--path", "pretrained_weights/anything.pth"],
                            capture_output=True, timeout=3)
    assert result.returncode != 0 and b"invented_invocation_required" in result.stderr


def test_fixture_save_registry_cpu_and_rng_isolation():
    import torch
    before = list(torch.serialization._package_registry), torch.get_rng_state().clone()
    raw = probe._fixture_bytes(torch, "cuda:0")
    assert b"cuda:0" in raw and len(raw) < 65536
    assert torch.serialization._package_registry == before[0] and torch.equal(torch.get_rng_state(), before[1])
