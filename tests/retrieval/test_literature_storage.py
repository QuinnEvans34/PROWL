"""The revised internal allocation must not remove the external-volume guard."""
from types import SimpleNamespace

import pytest

from scripts.retrieval import direct_corpus


@pytest.mark.parametrize('internal,external,error', [
    (50_000_000_000, 408*1024**3, None),
    (60_000_000_000, 408*1024**3, None),
    (49_999_999_999, 408*1024**3, 'Internal storage'),
    (60_000_000_000, 408*1024**3-1, 'External storage'),
])
def test_literature_storage_allocation(monkeypatch, internal, external, error):
    monkeypatch.setattr(direct_corpus.shutil, 'disk_usage', lambda path:
                        SimpleNamespace(free=internal if path == '/System/Volumes/Data' else external))
    if error:
        with pytest.raises(OSError, match=error):
            direct_corpus.limits({'mount': '/invented-external'})
    else:
        direct_corpus.limits({'mount': '/invented-external'})
