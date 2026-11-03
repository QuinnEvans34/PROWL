import json
from pathlib import Path
import pytest
from scripts.diagnostics import handoff_autonomous70_20261103 as h

@pytest.mark.parametrize('fail',[False,True])
def test_durable_chain_stops_on_failure_without_retry(tmp_path,monkeypatch,fail):
    out=tmp_path/'prepared';out.mkdir();sources=tmp_path/'sources';base=tmp_path/'outputs';backup=tmp_path/'backup';backup.mkdir();evidencebackup=tmp_path/'evidencebackup';evidencebackup.mkdir()
    monkeypatch.setattr(h.run.prep,'OUT',out);monkeypatch.setattr(h.run.prep,'SOURCES',sources);monkeypatch.setattr(h.run,'BASE',base);monkeypatch.setattr(h.run,'BACKUP',backup);backup.rmdir();monkeypatch.setattr(h,'BACKUP',evidencebackup)
    cases=[dict(case_id=str(i),needs_restoration=True,preflight_failure=None,identity=dict(source_sha256={'ct':str(i)})) for i in range(64)]
    r=dict(cases=cases,limits=dict(restore_seconds=7200,restore_rss_bytes=2, total_evaluation_seconds=42000,rss_bytes=12))
    (out/'handoff-request.json').write_text(json.dumps(dict(pins={})))
    pin=h.q.sha(out/'handoff-request.json');monkeypatch.setattr(h.run,'request',lambda p:r);monkeypatch.setattr(h.run,'admission',lambda *a:None);monkeypatch.setattr(h.run,'gate',lambda *a:None)
    calls=[]
    def stage(flag,pin,log,seconds,rss,r):
        calls.append(flag)
        if fail:raise RuntimeError('simulated integrity failure')
        if flag=='--restore-sha256':
            sources.mkdir();(sources/'restoration.json').write_text(json.dumps(dict(request_sha256=h.PIN,cases={str(i):str(i) for i in range(64)})))
            (out/'restore.resources.json').write_text(json.dumps(dict(success=True,workers_reaped=True,exit_code=0)))
        elif flag=='--admit-sources-sha256':
            (out/'source-admission.resources.json').write_text(json.dumps(dict(success=True,workers_reaped=True,exit_code=0)))
            (out/'ready.json').write_text(json.dumps(dict(request_sha256=h.PIN,evidence=[{}]*70)))
        else:
            base.mkdir();backup.mkdir();data=json.dumps(dict(total_cases=70,successful_cases=69,failed=['PanTS_00005592']))
            (base/'completion.json').write_text(data);(backup/'completion.json').write_text(data)
    monkeypatch.setattr(h,'execute_stage',stage)
    if fail:
        with pytest.raises(RuntimeError,match='integrity'):h.main(pin)
        assert calls==['--restore-sha256'] and (out/'handoff-failure.json').exists()
    else:
        h.main(pin);assert calls==['--restore-sha256','--admit-sources-sha256','--launch-ready-sha256']
    assert (out/'handoff.jsonl').read_bytes()==(evidencebackup/'handoff.jsonl').read_bytes()
    with pytest.raises(FileExistsError):h.main(pin)

def test_resource_completion_requires_reaped_success(tmp_path):
    p=tmp_path/'resources.json';p.write_text(json.dumps(dict(success=True,workers_reaped=False,exit_code=0)))
    with pytest.raises(ValueError,match='reap'):h.verify_resources(p)
