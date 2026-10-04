import os
import pytest
from src.operations import segmenter_primary_read_guard_v1 as g

@pytest.mark.parametrize('path',['/Volumes/PROWL-Data','/Volumes/PROWL-Data/artifacts/x','PROWL-Data','./PROWL-Data','../PROWL-Data/x'])
def test_absolute_and_relative_components_refused(path):
    with pytest.raises(ValueError):g.check_path(path)

@pytest.mark.parametrize('path',['x','./x','folder/x'])
def test_primary_directory_fd_refused(monkeypatch,path):
    monkeypatch.setattr(g,'fd_path',lambda fd:'/Volumes/PROWL-Data/artifacts')
    with pytest.raises(ValueError):g.check_path(path,dir_fd=77)

@pytest.mark.parametrize('fd',[3,77])
def test_primary_file_or_list_fd_refused(monkeypatch,fd):
    monkeypatch.setattr(g,'fd_path',lambda _: '/Volumes/PROWL-Data/artifacts/x')
    with pytest.raises(ValueError):g.check_path(fd)

def test_independent_directory_fd_allowed(tmp_path):
    fd=os.open(tmp_path,os.O_RDONLY|os.O_DIRECTORY)
    try:g.check_path('x',dir_fd=fd);g.check_path(fd)
    finally:os.close(fd)

def test_primary_symlink_alias_refused(tmp_path):
    p=tmp_path/'alias';p.symlink_to('/Volumes/PROWL-Data/artifacts')
    with pytest.raises(ValueError):g.check_path(p/'x')

def test_anonymous_subprocess_pipe_allowed():
    r,w=os.pipe()
    try:g.check_path(r);g.check_path(w)
    finally:os.close(r);os.close(w)

def test_closed_descriptor_fails_closed():
    r,w=os.pipe();os.close(r);os.close(w)
    with pytest.raises(OSError):g.check_path(r)
