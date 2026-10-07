"""Exercise the actual CLI argv forms using exclusively generated checkpoints."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest
import torch

from src.models.segresnet import build_model

SCRIPT = Path(__file__).absolute().parents[1] / "scripts/diagnostics/run_suprem_checkpoint_metadata_v2.py"
SPEC = importlib.util.spec_from_file_location("metadata_cli_qualification", SCRIPT)
d = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d)


@pytest.fixture
def prepared():
    temp = Path(tempfile.gettempdir()).resolve()
    with tempfile.TemporaryDirectory(prefix="prowl-source-invented-", dir=temp) as source, \
         tempfile.TemporaryDirectory(prefix="prowl-dispatch-invented-", dir=temp) as parent:
        path = Path(source) / "invented-full-cli.pth"
        with torch.random.fork_rng(devices=[]), torch.device("cpu"):
            torch.manual_seed(2410)
            model = build_model({"model": d.reader.architecture()})
        expected = {k: dict(shape=list(v.shape), dtype=str(v.dtype)) for k, v in model.state_dict().items()}
        assert len(expected) == 83
        torch.save(dict(net={"module." + k: v for k, v in model.state_dict().items()},
                        optimizer={}, scheduler={"milestones": (1, 2)}, epoch=0), path)
        source_before = path.read_bytes()
        output = Path(parent) / "attempt"
        result = d.prepare("invented_cli", d.INVENTED_AUTHORIZATION, invented_source=path,
            invented_output=output, invented_sha=hashlib.sha256(source_before).hexdigest())
        controls_before = {p.name: p.read_bytes() for p in output.iterdir()}
        yield result, output, Path(parent), path, source_before, controls_before, expected


@pytest.mark.parametrize("style", ["relative", "absolute"])
def test_real_entry_point_path_forms(prepared, style):
    result, output, parent, source, source_before, controls_before, expected = prepared
    request = output / "control.json"; approval = output / "approval.json"
    if style == "relative":
        request = request.relative_to(parent); approval = approval.relative_to(parent)
    command = [sys.executable, str(SCRIPT), "--run-id", "invented_cli", "--request", str(request),
        "--approval", str(approval), "--request-sha256", result["request_sha256"],
        "--approval-sha256", result["approval_sha256"]]
    completed = subprocess.run(command, cwd=parent, capture_output=True, timeout=100, check=False)
    assert len(completed.stdout) <= 1024**2 and len(completed.stderr) <= 65536
    summary = json.loads(completed.stdout)
    assert source.read_bytes() == source_before
    assert all(output.joinpath(n).read_bytes() == raw for n, raw in controls_before.items())
    if style == "relative":
        assert completed.returncode == 1 and summary == dict(status="refused", reason="unsafe_directory_path")
        assert {p.name for p in output.iterdir()} == {"control.json", "approval.json"}
        return
    assert completed.returncode == 0 and summary["status"] == "pass", (summary, completed.stderr)
    assert summary["consumed"] is True and summary["reason"] == "complete_metadata_match"
    assert {p.name for p in output.iterdir()} == d.MEMBERS
    assert sum(p.stat().st_size for p in output.iterdir()) <= 4 * 1024**2
    report = json.loads(output.joinpath("report.json").read_bytes())
    receipt = json.loads(output.joinpath("consumption-receipt.json").read_bytes())
    control = json.loads(controls_before["control.json"])
    assert receipt == control["receipt"] and receipt["state"] == "consumed"
    assert report["consumed"] is True and report["execution_authority"] == "none"
    assert report["values_audited"] is False and report["training_eligible"] is False
    metadata = report["reader"]
    assert metadata["status"] == "pass" and metadata["identity_verified"] and metadata["metadata_compatible"]
    assert metadata["evidence_domain"] == d.reader.DOMAIN
    assert {k: dict(shape=v["shape"], dtype=v["dtype"]) for k, v in metadata["model"].items()} == expected
    assert metadata["source_sha256"] == hashlib.sha256(source_before).hexdigest()
    assert metadata["io"]["hash_bytes"] == len(source_before)
    assert metadata["io"]["metadata_storage_source_bytes"] == 0
    assert metadata["io"]["aggregate_requested_bytes"] <= len(source_before) + 8 * 1024**2
    assert metadata["worker"]["exit_code"] == 0
    assert report["resources"]["owned_worker_reaped"] is True
    assert report["resources"]["aggregate_sampled_peak_rss_bytes"] <= 3 * 1024**3
    assert report["resources"]["elapsed_seconds"] <= 90
