from pathlib import Path

import pytest

from scripts.train_full_segmenter import tree_bytes


def test_counts_nested_files_and_missing_root(tmp_path):
    (tmp_path / 'sub').mkdir()
    (tmp_path / 'a').write_bytes(b'123')
    (tmp_path / 'sub' / 'b').write_bytes(b'4567')
    assert tree_bytes(tmp_path) == 7
    assert tree_bytes(tmp_path / 'absent') == 0


def test_atomic_rename_rescans_and_counts_replacement(tmp_path, monkeypatch):
    temporary = tmp_path / 'case.tmp'
    temporary.write_bytes(b'12345')
    original = Path.stat
    def racing_stat(path, *args, **kwargs):
        if path == temporary:
            temporary.rename(tmp_path / 'case.npz')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'stat', racing_stat)
    assert tree_bytes(tmp_path) == 5


@pytest.mark.parametrize('error', [PermissionError, OSError, FileNotFoundError])
def test_storage_errors_fail_closed(tmp_path, monkeypatch, error):
    member = tmp_path / 'case.npz'
    member.write_bytes(b'123')
    original = Path.stat
    calls = []
    def failing_stat(path, *args, **kwargs):
        if path == member:
            calls.append(path)
            raise error('storage fault')
        return original(path, *args, **kwargs)
    monkeypatch.setattr(Path, 'stat', failing_stat)
    with pytest.raises(error):
        tree_bytes(tmp_path)
    assert len(calls) == (3 if error is FileNotFoundError else 1)
