import importlib.util
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import tempfile
from types import SimpleNamespace

import pytest

spec = importlib.util.spec_from_file_location("volume_probe", Path(__file__).parents[1] /
                                          "scripts/diagnostics/probe_suprem_metadata_volume_v1.py")
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)


@pytest.fixture
def path():
    with tempfile.TemporaryDirectory(prefix="prowl-volume-invented-", dir=Path(tempfile.gettempdir()).resolve()) as s:
        yield Path(s)


def substitute(monkeypatch, code):
    original = subprocess.Popen
    children, commands = [], []
    def spawn(command, **kw):
        commands.append((command, kw))
        child = original([sys.executable, "-I", "-c", code], **kw)
        children.append(child)
        return child
    monkeypatch.setattr(subprocess, "Popen", spawn)
    monkeypatch.setattr(p, "sample", lambda *args: 1048576)
    return children, commands


def check(r):
    assert not r["training_eligible"] and r["execution_authority"] == "none" and r["source_payload_bytes"] == 0
    assert r["resources"]["owned_child_reaped"] and len(json.dumps(r).encode()) <= 65536


def test_valid_plist_filters_unrelated_hardware_fields(path, monkeypatch):
    raw = plistlib.dumps(dict(MountPoint="/invented", VolumeUUID="invented", FilesystemType="apfs", Secret="never report"))
    children, commands = substitute(monkeypatch, "import sys;sys.stdout.buffer.write("+repr(raw)+")")
    r = p.probe_one(path, domain="invented_volume_diagnostic")
    check(r)
    assert r["status"] == "pass" and r["volume"] == dict(mount="/invented",uuid="invented",filesystem="apfs")
    assert "Secret" not in json.dumps(r) and "never report" not in json.dumps(r)
    assert commands[0][0] == ["/usr/sbin/diskutil", "info", "-plist", str(path)]
    assert commands[0][1]["start_new_session"] and commands[0][1]["close_fds"]
    assert all(c.poll() is not None for c in children)


@pytest.mark.parametrize("fault,reason",[("nonzero","command_nonzero"),("badplist","tool_monitor_or_plist_failure"),
    ("missing","plist_volume_fields"),("stdout","stdout_limit"),("stderr","stderr_limit"),
    ("time","command_time_limit"),("rss","aggregate_rss_limit"),("monitor","tool_monitor_or_plist_failure")])
def test_faults_bounded_and_reaped(path,monkeypatch,fault,reason):
    code={"nonzero":"import sys;sys.stderr.write('invented error');sys.exit(4)",
          "badplist":"print('malformed')", "missing":"import plistlib,sys;sys.stdout.buffer.write(plistlib.dumps({}))",
          "stdout":"import sys;sys.stdout.write('x'*70000)","stderr":"import sys;sys.stderr.write('x'*5000)",
          "time":"import time;time.sleep(10)","rss":"import time;time.sleep(10)","monitor":"import time;time.sleep(10)"}[fault]
    children,_=substitute(monkeypatch,code)
    if fault=="time": monkeypatch.setattr(p,"SECONDS",.1)
    elif fault=="rss": monkeypatch.setattr(p,"RSS",1)
    elif fault=="monitor": monkeypatch.setattr(p,"sample",lambda *a: (_ for _ in ()).throw(OSError()))
    r=p.probe_one(path,domain="invented_volume_diagnostic")
    check(r)
    assert r["status"]=="refused" and r["reason"]==reason,r
    assert all(c.poll() is not None for c in children)
    assert len((r["error"] or "").encode())<=4096
    if fault=="nonzero": assert r["command_returncode"]==4 and r["error"]=="invented error"


@pytest.mark.parametrize("domain,locator",[("training","/"),("volume_diagnostic_only","/"),
    ("volume_diagnostic_only",str(p.ROOT/"pretrained_weights/supervised_suprem_segresnet_2100.pth")),
    ("invented_volume_diagnostic",str(p.ALLOWED[0]))])
def test_denial_before_any_process(monkeypatch,domain,locator):
    monkeypatch.setattr(subprocess,"Popen",lambda *a,**k:pytest.fail("process started"))
    with pytest.raises(p.Refusal): p.probe_one(locator,domain=domain)


@pytest.mark.parametrize("stdout,returncode",[("",1),("bad",0),("1 2 -1",0)])
def test_bad_ps_response_refuses(monkeypatch,stdout,returncode):
    monkeypatch.setattr(subprocess,"run",lambda *a,**k:SimpleNamespace(returncode=returncode,stdout=stdout))
    with pytest.raises(p.Refusal,match="monitor_unavailable"):p.sample()


def test_aggregate_parent_and_descendants_not_other_owner(monkeypatch):
    monkeypatch.setattr(os,"getpid",lambda:10)
    monkeypatch.setattr(subprocess,"run",lambda *a,**k:SimpleNamespace(returncode=0,
        stdout="10 1 10\n20 10 20\n30 20 30\n40 1 99999\n"))
    assert p.sample(20)==60*1024


def test_platform_denial_before_process(path,monkeypatch):
    monkeypatch.setattr(sys,"platform","win32")
    monkeypatch.setattr(subprocess,"Popen",lambda *a,**k:pytest.fail("process started"))
    r=p.probe_one(path,domain="invented_volume_diagnostic");check(r)
    assert r["reason"]=="monitor_platform"


def test_invalid_utf8_error_still_has_four_kib_byte_cap(path,monkeypatch):
    substitute(monkeypatch,"import sys;sys.stderr.buffer.write(b'\\xff'*4000);sys.exit(3)")
    r=p.probe_one(path,domain="invented_volume_diagnostic");check(r)
    assert r["reason"]=="command_nonzero" and len(r["error"].encode())<=4096
