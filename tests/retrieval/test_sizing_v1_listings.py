"""Run S preflight listing resolution (invented listings only; network denied)."""
import socket

import pytest

from src.retrieval.sizing_v1 import MIB, PreflightFailed
from src.retrieval.sizing_v1.listings import (MD5_ALLOWANCE, parse_listing, parse_md5_file, planned_bytes,
                                              resolve_baseline, resolve_updates)

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def deny(*a, **k):
        raise AssertionError('network denied in sizing_v1 tests')
    monkeypatch.setattr(socket.socket, 'connect', deny)
    monkeypatch.setattr(socket, 'create_connection', deny)
    monkeypatch.setattr(socket, 'getaddrinfo', deny)


def row(name, size='22M'):
    tail = f'  2025-12-10 14:15  {size}' if size else '  2025-12-10 14:15'
    return f'<a href="{name}">{name}</a>{tail}\n'


def listing(names, sizes=None, extra=''):
    sizes = sizes or {}
    body = ''.join(row(n, sizes.get(n, '22M' if n.endswith('.gz') else '60')) for n in names)
    return ('<html><body><pre><a href="?C=N;O=D">Name</a>\n<a href="../">Parent Directory</a>\n'
            + body + extra + '</pre></body></html>').encode('utf-8')


def baseline_names(skip=(), dup=()):
    names = []
    for i in range(1, 1335):
        n = f'pubmed26n{i:04d}.xml.gz'
        if n in skip:
            continue
        names += [n, n + '.md5']
        if n in dup:
            names.append(n)
    return names + ['README.txt']


def test_exact_baseline_resolves_samples_and_records_extras():
    out = resolve_baseline(parse_listing(listing(baseline_names())))
    assert [s['name'] for s in out['samples']] == ['pubmed26n0001.xml.gz', 'pubmed26n0667.xml.gz',
                                                   'pubmed26n1334.xml.gz']
    assert out['file_count'] == 1334
    assert out['other_entries'] == ['README.txt']
    assert out['samples'][0]['size_upper'] == 23 * MIB


@pytest.mark.parametrize('mutation', ['missing', 'duplicate', 'ambiguous', 'missing_md5', 'extra_number'])
def test_baseline_refusals(mutation):
    names = baseline_names()
    if mutation == 'missing':
        names = baseline_names(skip={'pubmed26n0500.xml.gz'})
    elif mutation == 'duplicate':
        names = baseline_names(dup={'pubmed26n0667.xml.gz'})
    elif mutation == 'ambiguous':
        names.append('pubmed26n0001.xml.gz.bak')
    elif mutation == 'missing_md5':
        names.remove('pubmed26n0042.xml.gz.md5')
    elif mutation == 'extra_number':
        names += ['pubmed26n1335.xml.gz', 'pubmed26n1335.xml.gz.md5']
    with pytest.raises(PreflightFailed):
        resolve_baseline(parse_listing(listing(names)))


def test_missing_sample_refused_and_sample_without_size_refused():
    with pytest.raises(PreflightFailed):
        resolve_baseline(parse_listing(listing(baseline_names(skip={'pubmed26n1334.xml.gz'}))))
    with pytest.raises(PreflightFailed):
        resolve_baseline(parse_listing(listing(baseline_names(), sizes={'pubmed26n0667.xml.gz': None})))


def test_updates_take_two_highest_valid():
    names = []
    for i in (1335, 1336, 1337, 1338):
        names += [f'pubmed26n{i:04d}.xml.gz', f'pubmed26n{i:04d}.xml.gz.md5']
    names.append('pubmed26n1339.xml.gz')          # no .md5: not valid
    names += ['pubmed26n1200.xml.gz', 'pubmed26n1200.xml.gz.md5']   # below 1335: not valid
    out = resolve_updates(parse_listing(listing(names + ['stats.html'])))
    assert [s['name'] for s in out['samples']] == ['pubmed26n1337.xml.gz', 'pubmed26n1338.xml.gz']
    assert out['file_count'] == 4
    assert 'pubmed26n1339.xml.gz' in out['invalid_names'] and 'pubmed26n1200.xml.gz' in out['invalid_names']
    assert out['other_entries'] == ['stats.html']


@pytest.mark.parametrize('names', [
    ['pubmed26n1335.xml.gz', 'pubmed26n1335.xml.gz.md5'],
    ['pubmed26n1335.xml.gz', 'pubmed26n1335.xml.gz.md5', 'pubmed26n1336.xml.gz'],
    ['pubmed26n1335.xml.gz', 'pubmed26n1335.xml.gz.md5', 'pubmed26n1336.xml.gz', 'pubmed26n1336.xml.gz.md5',
     'pubmed26n1336.xml.gz'],
    ['pubmed26n1335.xml.gz', 'pubmed26n1335.xml.gz.md5', 'pubmed26n1336.xml.gz', 'pubmed26n1336.xml.gz.md5',
     'pubmed26n1336.XML.GZ'],
])
def test_update_refusals(names):
    with pytest.raises(PreflightFailed):
        resolve_updates(parse_listing(listing(names)))


def test_size_parsing_is_an_upper_bound_and_dates_are_not_sizes():
    entries = parse_listing(b'<a href="a.xml.gz">a</a> 2025-12-10 14:15  22M\n'
                            b'<a href="b.xml.gz">b</a> 2025-12-10 14:15  2.5M\n'
                            b'<a href="c.xml.gz">c</a> 2025-12-10 14:15\n'
                            b'<a href="d.xml.gz">d</a> 2025-12-10 14:15  1234\n')
    sizes = {n: u for n, _, u in entries}
    assert sizes['a.xml.gz'] == 23 * MIB
    assert 2.6 * MIB <= sizes['b.xml.gz'] <= 2.6 * MIB + 1
    assert sizes['c.xml.gz'] is None
    assert sizes['d.xml.gz'] == 1235


def test_listing_without_entries_refused():
    with pytest.raises(PreflightFailed):
        parse_listing(b'<html><body>nothing here</body></html>')
    with pytest.raises(PreflightFailed):
        parse_listing(b'\xff\xfe not utf8')


def test_md5_body_parsing():
    hexd = '0123456789abcdef0123456789abcdef'
    assert parse_md5_file(f'MD5(pubmed26n0001.xml.gz)= {hexd}\n'.encode(), 'pubmed26n0001.xml.gz') == hexd
    for bad in (f'MD5(pubmed26n0002.xml.gz)= {hexd}\n', f'MD5(pubmed26n0001.xml.gz)= {hexd}\nextra\n',
                'MD5(pubmed26n0001.xml.gz)= nothex\n', ''):
        with pytest.raises(PreflightFailed):
            parse_md5_file(bad.encode(), 'pubmed26n0001.xml.gz')


def test_planned_bytes_sums_samples_md5_and_mesh():
    base = dict(samples=[dict(size_upper=10), dict(size_upper=20), dict(size_upper=30)])
    upd = dict(samples=[dict(size_upper=1), dict(size_upper=2)])
    assert planned_bytes(base, upd, 1000) == 63 + 5 * MD5_ALLOWANCE + 1000
