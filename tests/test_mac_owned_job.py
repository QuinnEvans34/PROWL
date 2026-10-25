from pathlib import Path
import sys
import pytest
from scripts.diagnostics.launch_mac_owned_job import definition

def test_one_shot_has_no_restart_or_timer(tmp_path):
    p=definition('com.prowl.synthetic',[sys.executable,'probe.py'],tmp_path,tmp_path,{'HOME':str(tmp_path)})
    assert p['RunAtLoad'] is True and p['KeepAlive'] is False
    assert not {'StartInterval','StartCalendarInterval','WatchPaths','QueueDirectories'}&p.keys()
    assert p['ProgramArguments']==[sys.executable,'probe.py']

def test_rejects_unscoped_job(tmp_path):
    with pytest.raises(ValueError):definition('com.apple.other',[sys.executable],tmp_path,tmp_path,{})

def test_rejects_relative_executable(tmp_path):
    with pytest.raises(ValueError):definition('com.prowl.synthetic',['python'],tmp_path,tmp_path,{})
