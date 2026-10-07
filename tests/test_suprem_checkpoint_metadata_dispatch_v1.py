"""New invented dispatcher controls; never positively access actual candidate."""
from copy import deepcopy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import tempfile
import time
from types import SimpleNamespace

import pytest

SPEC = importlib.util.spec_from_file_location("metadata_dispatch", Path(__file__).parents[1] /
                                             "scripts/diagnostics/run_suprem_checkpoint_metadata_v1.py")
d = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(d)


@pytest.fixture
def area():
    temp = Path(tempfile.gettempdir()).resolve()
    with tempfile.TemporaryDirectory(prefix="prowl-source-invented-", dir=temp) as source, \
         tempfile.TemporaryDirectory(prefix="prowl-dispatch-invented-", dir=temp) as output:
        path = Path(source) / "invented-dispatch.pth"
        path.write_bytes(b"fresh invented malformed archive")
        yield path, Path(output) / "attempt"


def prepared(area):
    source, output = area
    result = d.prepare("invented_dispatch", d.INVENTED_AUTHORIZATION, invented_source=source,
                       invented_output=output, invented_sha=hashlib.sha256(source.read_bytes()).hexdigest())
    return result, json.loads((output / "control.json").read_bytes()), json.loads((output / "approval.json").read_bytes())


def run(result):
    path = Path(result["output"])
    return d.dispatch("invented_dispatch", path / "control.json", path / "approval.json",
                      result["request_sha256"], result["approval_sha256"])


def repin(result, request, approval):
    path = Path(result["output"])
    result["request_sha256"] = d.digest(request)
    approval["request_sha256"] = result["request_sha256"]
    result["approval_sha256"] = d.digest(approval)
    (path / "control.json").write_bytes(d.canonical(request))
    (path / "approval.json").write_bytes(d.canonical(approval))


def fake_pass(request):
    c = request["reader_control"]
    value = d.reader._report(domain=d.reader.DOMAIN)
    value.update(status="pass", reason="complete_metadata_match", identity_verified=True,
                 metadata_compatible=True, control_sha256=d.digest(c), source_sha256=c["source"]["sha256"],
                 source_bytes=c["source"]["bytes"], request_sha256=d.digest(c["request"]),
                 model={str(i): {} for i in range(83)},
                 io=dict(hash_bytes=c["source"]["bytes"], metadata_storage_source_bytes=0,
                         aggregate_requested_bytes=c["source"]["bytes"]))
    return value


def safe_stub(monkeypatch):
    def worker(request, approval, started):
        output = Path(request["output"]["path"])
        assert json.loads((output / "consumption-receipt.json").read_bytes()) == request["receipt"]
        return fake_pass(request), dict(aggregate_sampled_peak_rss_bytes=1024, owned_worker_reaped=True)
    monkeypatch.setattr(d, "_run_reader", worker)


def test_exclusive_preparation_never_opens_source(area, monkeypatch):
    original = os.open
    def guarded(path, flags, *args, **kwargs):
        assert str(path) not in (str(area[0]), area[0].name), "preflight opened source leaf"
        return original(path, flags, *args, **kwargs)
    monkeypatch.setattr(os, "open", guarded)
    result, request, approval = prepared(area)
    output = area[1]
    assert set(p.name for p in output.iterdir()) == {"control.json", "approval.json"}
    assert output.stat().st_mode & 0o777 == 0o700 and not result["consumed"]
    assert request["reader_control"]["request"]["consumption_receipt_sha256"] == d.digest(request["receipt"])
    assert request["receipt"]["scope_sha256"] == d.digest(request["scope"])
    with pytest.raises(d.Refusal, match="output_area_already_exists"):
        prepared(area)
    assert set(p.name for p in output.iterdir()) == {"control.json", "approval.json"}


def test_consumption_before_reader_and_no_replay(area, monkeypatch):
    result, request, approval = prepared(area)
    safe_stub(monkeypatch)
    report = run(result)
    assert report["status"] == "pass" and report["consumed"]
    assert report["execution_authority"] == "none" and not report["training_eligible"] and not report["values_audited"]
    assert set(p.name for p in area[1].iterdir()) == d.MEMBERS
    assert sum(p.stat().st_size for p in area[1].iterdir()) <= 4 * 1024**2
    before = {p.name: p.read_bytes() for p in area[1].iterdir()}
    with pytest.raises(d.Refusal, match="attempt_already_consumed_or_partial"):
        run(result)
    assert before == {p.name: p.read_bytes() for p in area[1].iterdir()}


@pytest.mark.parametrize("fault", ["request_pin", "approval_pin", "unknown_request", "unknown_approval", "version",
    "receipt", "reader_receipt", "namespace", "bounds", "pins", "environment", "authorization", "approval_request",
    "run_id", "output_path", "output_fields", "output_floor", "reader_signature", "reader_extra", "reader_domain"])
def test_control_faults_before_consumption_or_reader(area, monkeypatch, fault):
    result, r, a = prepared(area)
    if fault == "request_pin": result["request_sha256"] = "0" * 64
    elif fault == "approval_pin": result["approval_sha256"] = "0" * 64
    else:
        if fault == "unknown_request": r["extra"] = True
        elif fault == "unknown_approval": a["extra"] = True
        elif fault == "version": r["schema_version"] = "unknown"
        elif fault == "receipt": r["receipt"]["state"] = "planned"
        elif fault == "reader_receipt": r["reader_control"]["request"]["consumption_receipt_sha256"] = "0" * 64
        elif fault == "namespace": r["reader_control"]["namespace"] = "identity"
        elif fault == "bounds": r["scope"]["bounds"]["max_seconds"] = 91
        elif fault == "pins": r["pins"][next(iter(r["pins"]))] = "0" * 64
        elif fault == "environment": r["environment"]["python"] = "other"
        elif fault == "authorization": a["authorization"] = d.AUTHORIZATION
        elif fault == "run_id": r["scope"]["run_id"] = "other"
        elif fault == "output_path": r["output"]["path"] += "-other"
        elif fault == "output_fields": r["output"]["extra"] = True
        elif fault == "output_floor": r["output"]["observed_free_bytes"] = 0
        elif fault == "reader_signature": r["reader_control"]["expected_signature"].pop(next(iter(r["reader_control"]["expected_signature"])))
        elif fault == "reader_extra": r["reader_control"]["extra"] = True
        elif fault == "reader_domain": r["reader_control"]["evidence_domain"] = "real_training"
        repin(result, r, a)
        if fault == "approval_request":
            a["request_sha256"] = "0" * 64
            result["approval_sha256"] = d.digest(a)
            (area[1] / "approval.json").write_bytes(d.canonical(a))
    monkeypatch.setattr(d, "_run_reader", lambda *args: pytest.fail("reader started before denial"))
    with pytest.raises((d.Refusal, KeyError)):
        run(result)
    assert not (area[1] / "consumption-receipt.json").exists()


@pytest.mark.parametrize("auth,run_id", [(None,d.RUN_ID),(d.INVENTED_AUTHORIZATION,d.RUN_ID),
                                        (d.AUTHORIZATION,"other")])
def test_actual_approval_denials_never_observe_candidate(monkeypatch, auth, run_id):
    monkeypatch.setattr(d, "source_metadata", lambda *args: pytest.fail("actual preflight reached"))
    with pytest.raises(d.Refusal):
        d.prepare(run_id, auth)


def test_actual_path_cannot_be_relabelled_invented(area, monkeypatch):
    monkeypatch.setattr(d, "source_metadata", lambda *args: pytest.fail("actual candidate observed"))
    with pytest.raises(d.Refusal, match="invented_source_scope"):
        d.prepare("invented_dispatch", d.INVENTED_AUTHORIZATION, invented_source=d.reader.candidate_locator(),
                  invented_output=area[1], invented_sha="1" * 64)


def actual_envelope(invented):
    """Pure control records: not a real preflight or source observation."""
    r=deepcopy(invented)
    c=r["reader_control"]
    p=d.reader.candidate_locator()
    output=d.ROOT/"outputs/prowl"/("SUPREM-CHECKPOINT-INSPECTION-"+d.RUN_ID)
    c["evidence_domain"]=d.reader.ACTUAL_DOMAIN
    c["source"].update(path=str(p),root=str(p.parent),bytes=56500623,sha256=d.reader.ACTUAL_CANDIDATE_SHA,
        volume=dict(mount="/",uuid="01234567-89AB-CDEF-0123-456789ABCDEF",filesystem="apfs"))
    c["request"]["run_id"]=d.RUN_ID
    r["output"]["path"]=str(output)
    r["scope"]=dict(run_id=d.RUN_ID,domain=d.reader.ACTUAL_DOMAIN,source=c["source"],namespace=c["namespace"],
        output=r["output"],pins=r["pins"],environment=r["environment"],bounds=d.bounds(d.reader.ACTUAL_DOMAIN))
    r["receipt"]=dict(schema_version="checkpoint-metadata-consumption-1",run_id=d.RUN_ID,
                      scope_sha256=d.digest(r["scope"]),state="consumed")
    c["request"]["consumption_receipt_sha256"]=d.digest(r["receipt"])
    a=dict(schema_version=d.APPROVAL_VERSION,authorization=deepcopy(d.AUTHORIZATION),request_sha256=d.digest(r),
           reader_approval=d._reader_approval(c))
    return r,a,output


def test_actual_record_consistency_only_without_source_access(area,monkeypatch):
    _,r,_=prepared(area)
    r,a,output=actual_envelope(r)
    monkeypatch.setattr(d,"source_metadata",lambda *a:pytest.fail("actual source observed"))
    assert d.validate(r,a,d.RUN_ID,d.digest(r),d.digest(a),output)==r["reader_control"]
    assert r["scope"]["bounds"]["max_read_bytes"]==64889231
    assert a["reader_approval"]["consumption_receipt_sha256"]==d.digest(r["receipt"])


@pytest.mark.parametrize("fault",["approval_absent","approval_source","approval_receipt","approval_reader",
                                  "approval_control","human_scope","human_extra","locator","size","hash"])
def test_actual_envelope_mismatch_no_candidate_observation(area,monkeypatch,fault):
    _,r,_=prepared(area)
    r,a,output=actual_envelope(r)
    if fault=="approval_absent": a["reader_approval"]=None
    elif fault.startswith("approval_"):
        field={"source":"source_sha256","receipt":"consumption_receipt_sha256","reader":"reader_sha256",
               "control":"control_sha256"}[fault.removeprefix("approval_")]
        a["reader_approval"][field]="0"*64
    elif fault=="human_scope": a["authorization"]["scope"]="training"
    elif fault=="human_extra": a["authorization"]["training_eligible"]=True
    else:
        if fault=="locator": r["reader_control"]["source"]["path"] += "-other"
        elif fault=="size": r["reader_control"]["source"]["bytes"]+=1
        elif fault=="hash": r["reader_control"]["source"]["sha256"]="0"*64
        # Rebind the envelope to isolate the reader's exact actual-source boundary.
        r["receipt"]["scope_sha256"]=d.digest(r["scope"])
        r["reader_control"]["request"]["consumption_receipt_sha256"]=d.digest(r["receipt"])
        a["reader_approval"]=d._reader_approval(r["reader_control"])
    a["request_sha256"]=d.digest(r)
    monkeypatch.setattr(d,"source_metadata",lambda *a:pytest.fail("actual source observed"))
    with pytest.raises(d.Refusal): d.validate(r,a,d.RUN_ID,d.digest(r),d.digest(a),output)


@pytest.mark.parametrize("fault", ["source_symlink", "source_hardlink", "source_directory", "source_parent_writable",
                                   "output_parent_symlink", "output_parent_writable", "actual_sha"])
def test_preflight_path_denials(area, fault):
    source, output = area
    if fault == "source_symlink":
        alias = source.with_name("invented-alias.pth"); alias.symlink_to(source); source = alias
    elif fault == "source_hardlink": os.link(source, source.with_name("invented-link.pth"))
    elif fault == "source_directory": source = source.with_name("invented-dir.pth"); source.mkdir()
    elif fault == "source_parent_writable": source.parent.chmod(0o777)
    elif fault == "output_parent_symlink":
        alias = output.parent / "alias"; alias.symlink_to(output.parent); output = alias / "attempt"
    elif fault == "output_parent_writable": output.parent.chmod(0o777)
    with pytest.raises((d.Refusal, OSError)):
        d.prepare("invented_dispatch", d.INVENTED_AUTHORIZATION, invented_source=source,
                  invented_output=output, invented_sha=d.reader.ACTUAL_CANDIDATE_SHA if fault == "actual_sha" else "1" * 64)


def test_free_bytes_uses_available_blocks_and_reserves_output(area, monkeypatch):
    monkeypatch.setattr(os, "fstatvfs", lambda fd: SimpleNamespace(f_bavail=10, f_frsize=4096, f_bfree=10**15))
    with pytest.raises(d.Refusal, match="output_headroom_limit"):
        prepared(area)
    assert not area[1].exists()


@pytest.mark.parametrize("fault", ["source_mutated", "output_volume", "headroom", "output_member", "control_symlink", "control_mode"])
def test_current_drift_denied_before_consumption(area, monkeypatch, fault):
    result, request, approval = prepared(area)
    if fault == "source_mutated": area[0].write_bytes(b"replaced")
    elif fault == "output_volume": monkeypatch.setattr(d,"observe_volume",lambda *args: dict(mount="other",uuid="other",filesystem="other"))
    elif fault == "headroom": monkeypatch.setattr(os,"fstatvfs",lambda fd: SimpleNamespace(f_bavail=0,f_frsize=4096))
    elif fault == "output_member": (area[1] / "unapproved.txt").write_text("invented")
    elif fault == "control_symlink":
        p=area[1]/"control.json"; raw=p.read_bytes(); p.unlink(); other=area[1].parent/"outside"; other.write_bytes(raw); p.symlink_to(other)
    elif fault == "control_mode": (area[1]/"control.json").chmod(0o644)
    monkeypatch.setattr(d,"_run_reader",lambda *args: pytest.fail("reader started"))
    with pytest.raises((d.Refusal,OSError)):
        run(result)
    assert not (area[1]/"consumption-receipt.json").exists()


@pytest.mark.parametrize("fault", ["reader_exception", "source_drift_after", "output_volume_after", "report_authority",
                                   "reader_identity", "reader_io", "reader_control"])
def test_consumed_failures_retained_without_replay(area, monkeypatch, fault):
    result, request, approval = prepared(area)
    def worker(r,a,started):
        assert (area[1]/"consumption-receipt.json").exists()
        v=fake_pass(r)
        if fault == "reader_exception": raise d.Refusal("invented_reader_fault")
        elif fault == "source_drift_after": area[0].write_bytes(b"mutated")
        elif fault == "output_volume_after": monkeypatch.setattr(d,"observe_volume",lambda *a: dict(mount="other",uuid="other",filesystem="other"))
        elif fault == "report_authority": v["training_eligible"]=True
        elif fault == "reader_identity": v["identity_verified"]=False
        elif fault == "reader_io": v["io"]["metadata_storage_source_bytes"]=4
        elif fault == "reader_control": v["control_sha256"]="0"*64
        return v,dict(owned_worker_reaped=True)
    monkeypatch.setattr(d,"_run_reader",worker)
    report=run(result)
    assert report["status"] == "refused" and report["consumed"]
    assert set(p.name for p in area[1].iterdir()) == d.MEMBERS
    with pytest.raises(d.Refusal,match="attempt_already_consumed_or_partial"): run(result)


def test_output_budget_no_overwrite_and_no_unapproved_member(area):
    result,_,_=prepared(area)
    fd=d.directory_fd(area[1])
    try:
        for name,raw,reason in [("control.json",b"rewrite","output_member_exists"),
                                ("other",b"x","output_member_refused"),
                                ("attempt.log",b"x"*(4*1024**2),"output_byte_limit")]:
            with pytest.raises(d.Refusal,match=reason): d._write(fd,name,raw)
    finally: os.close(fd)


def test_monitor_aggregate_includes_parent_and_descendants(monkeypatch):
    monkeypatch.setattr(os,"getpid",lambda:10); monkeypatch.setattr(os,"getpgrp",lambda:10)
    rows=[(10,1,10,10),(20,10,20,20),(30,20,30,30),(40,30,30,40),(50,1,50,9999)]
    total,groups=d._aggregate(rows,20)
    assert total==100*1024 and groups=={20,30}


@pytest.mark.parametrize("response", [SimpleNamespace(returncode=1,stdout=""),
    SimpleNamespace(returncode=0,stdout="bad row"), SimpleNamespace(returncode=0,stdout="1 2 3 -1")])
def test_monitor_unavailable_refuses(monkeypatch,response):
    monkeypatch.setattr(subprocess,"run",lambda *a,**k:response)
    with pytest.raises(d.Refusal,match="aggregate_monitor_unavailable"): d._process_rows()


@pytest.mark.parametrize("fault", ["time","rss","monitor","stdout","stderr","exit","schema","authority","post_peak"])
def test_owned_worker_stops_and_reaped(area,monkeypatch,fault):
    result,r,a=prepared(area)
    original=subprocess.Popen
    if fault in ("time","rss","monitor"): code="import sys,time;sys.stdin.buffer.read();time.sleep(10)"
    elif fault=="stdout": code="import sys;sys.stdin.buffer.read();sys.stdout.write('x'*1100000)"
    elif fault=="stderr": code="import sys;sys.stdin.buffer.read();sys.stderr.write('x'*70000)"
    elif fault=="exit": code="import sys;sys.stdin.buffer.read();sys.exit(4)"
    else:
        value=dict(reader=fake_pass(r),peak_rss_bytes=1)
        if fault=="schema": value["extra"]=True
        elif fault=="authority": value["reader"]["training_eligible"]=True
        elif fault=="post_peak": value["peak_rss_bytes"]=d.MAX_RSS+1
        code="import sys;sys.stdin.buffer.read();sys.stdout.write("+repr(json.dumps(value))+")"
    processes=[]
    def spawn(command,**kw):
        p=original([sys.executable,"-I","-c",code],**kw);processes.append(p);return p
    monkeypatch.setattr(subprocess,"Popen",spawn)
    # Keep real ps using the original Popen; subprocess.run otherwise inherits the test adapter.
    def rows():
        p=original(["/bin/ps","-axo","pid=,ppid=,pgid=,rss="],stdout=subprocess.PIPE,text=True)
        out,_=p.communicate(timeout=1);assert p.returncode==0
        return [tuple(map(int,line.split())) for line in out.splitlines() if line.strip()]
    monkeypatch.setattr(d,"_process_rows",rows)
    if fault=="time": monkeypatch.setattr(d,"MAX_SECONDS",.15)
    elif fault=="rss": monkeypatch.setattr(d,"MAX_RSS",1)
    elif fault=="monitor": monkeypatch.setattr(d,"_process_rows",lambda: (_ for _ in ()).throw(d.Refusal("aggregate_monitor_unavailable")))
    value,resources=d._run_reader(r,a,time.monotonic())
    assert value["status"]=="refused",value
    assert resources["termination_reason"] and resources["owned_worker_reaped"]
    assert all(p.poll() is not None for p in processes)


def test_native_full_signature_consumed_and_metadata_only(area):
    import torch
    source,output=area
    net={"module."+k:torch.zeros(tuple(v["shape"]),dtype=torch.float32) for k,v in d.reader.expected_signature().items()}
    torch.save(dict(net=net,optimizer={"betas":(.9,.999)},scheduler={"milestones":(1,4)},epoch=0),source)
    result,r,a=prepared(area)
    before=hashlib.sha256(source.read_bytes()).hexdigest()
    report=run(result)
    assert report["status"]=="pass",report
    v=report["reader"]
    assert len(v["model"])==83 and v["io"]["metadata_storage_source_bytes"]==0
    assert v["io"]["hash_bytes"]==source.stat().st_size and not v["values_audited"]
    assert report["resources"]["owned_worker_reaped"] and report["resources"]["aggregate_sampled_peak_rss_bytes"]>0
    assert report["resources"]["aggregate_sampled_peak_rss_bytes"]<=3*1024**3
    assert hashlib.sha256(source.read_bytes()).hexdigest()==before
    assert d.code_pins() == r["pins"] and d.digest(a)==result["approval_sha256"]
