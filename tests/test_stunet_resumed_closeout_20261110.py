"""A continuation supervisor must be waited on, not confused with its parent."""
import json
from pathlib import Path
from types import SimpleNamespace
import pytest

from scripts.diagnostics import close_stunet_margin_resume_20261110_v2 as closeout


def test_live_continuation_is_waited_on_before_reading_resources(tmp_path,monkeypatch):
    (tmp_path/'request.json').write_text(json.dumps(dict(deadline_unix=1000.)))
    (tmp_path/'process.json').write_text(json.dumps(dict(supervisor=123)))
    monkeypatch.setattr(closeout,'OUT',tmp_path)
    monkeypatch.setattr(closeout.time,'time',lambda:0.)
    monkeypatch.setattr(closeout.subprocess,'run',lambda *a,**k:SimpleNamespace(returncode=0,stdout='Tue Nov 10 11:54:52 2026'))
    def command(*args,**kwargs):
        return '/python /repo/scripts/diagnostics/resume_stunet_margin_mac_20261110.py --launch-sha256 '+closeout.sha(tmp_path/'request.json')
    monkeypatch.setattr(closeout.subprocess,'check_output',command)
    class WaitObserved(Exception):pass
    monkeypatch.setattr(closeout.time,'sleep',lambda seconds:(_ for _ in ()).throw(WaitObserved()))
    # The first closeout version fell through and tried missing resources.json.
    with pytest.raises(WaitObserved):
        closeout.close()
