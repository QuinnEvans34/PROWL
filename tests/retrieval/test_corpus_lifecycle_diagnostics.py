"""Lifecycle failures retain useful diagnostics without retrying or initializing a DB."""
import subprocess
from unittest.mock import Mock

import pytest

from scripts.retrieval import direct_corpus


CONFIG = dict(port=55433, data='/invented/data', password_file='/invented/secret')


def test_failed_start_retains_bind_diagnostic_and_never_initializes(monkeypatch, tmp_path):
    config = dict(CONFIG, data=str(tmp_path))
    monkeypatch.setattr(direct_corpus, 'read_config', lambda _: config)
    monkeypatch.setattr(direct_corpus, 'limits', lambda _: None)
    monkeypatch.setattr(direct_corpus.sys, 'argv', ['direct_corpus', '--config', 'invented', 'start'])
    monkeypatch.setattr(direct_corpus.subprocess, 'check_output',
                        lambda args, **_: b'{"MemTotal":10}' if args[0]=='docker' else b'1000')
    run = Mock(side_effect=subprocess.CalledProcessError(
        1, ['docker'], stderr=b'invalid mount config: existing pgdata: not a directory'))
    monkeypatch.setattr(direct_corpus.subprocess, 'run', run)
    connect = Mock()
    monkeypatch.setattr(direct_corpus, 'connect', connect)
    with pytest.raises(direct_corpus.ComposeFailure, match='existing pgdata: not a directory'):
        direct_corpus.main()
    run.assert_called_once()
    connect.assert_not_called()


def test_timeout_reports_unknown_state_without_retry(monkeypatch):
    run = Mock(side_effect=subprocess.TimeoutExpired(['docker'], 90))
    monkeypatch.setattr(direct_corpus.subprocess, 'run', run)
    with pytest.raises(direct_corpus.ComposeFailure, match='state is unknown'):
        direct_corpus.compose(CONFIG, 'stop', '-t', '60')
    run.assert_called_once()


def test_success_preserves_result_and_dedicated_project(monkeypatch):
    result = subprocess.CompletedProcess(['docker'], 0, b'ready', b'')
    run = Mock(return_value=result)
    monkeypatch.setattr(direct_corpus.subprocess, 'run', run)
    assert direct_corpus.compose(CONFIG, 'up', '-d') is result
    args, kwargs = run.call_args
    assert args[0][args[0].index('-p')+1] == 'prowl-literature'
    assert kwargs['env']['PROWL_DB_PORT'] == '55433'
    assert kwargs['timeout'] == 90


@pytest.mark.parametrize('stderr', [None, b'bad\xffdiagnostic', 'x'*5000])
def test_missing_or_non_utf8_diagnostics_remain_bounded(monkeypatch, stderr):
    monkeypatch.setattr(direct_corpus.subprocess, 'run', Mock(
        side_effect=subprocess.CalledProcessError(1, ['docker'], stderr=stderr)))
    with pytest.raises(direct_corpus.ComposeFailure) as exc:
        direct_corpus.compose(CONFIG, 'up', '-d')
    assert len(str(exc.value)) < 4300
