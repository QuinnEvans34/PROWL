"""Frozen-listing resolution for run S (preflight steps 2, 3 and 5).

All resolution uses only the raw listing bytes saved at run start. The listing parser targets an
Apache-style HTML autoindex (anchor ``href`` names, optionally followed by a date and a size). It
fails closed: no parsable names, a missing sample, duplicates or ambiguous names stop the run.

Listing sizes are human-readable (for example ``22M``) and therefore approximate. Displayed values
may be rounded to the nearest last digit, so for the cap pre-check each size is taken as the
displayed value **plus one step of its last digit** (``22M`` -> 23 MiB; ``2.5M`` -> 2.6 MiB). The
planned bytes are therefore an upper bound. Actual sample bytes are recorded beside the listed text.
"""
import math
import re

from src.retrieval.sizing_v1 import KIB, PreflightFailed

YEAR_PREFIX = 'pubmed26n'
BASELINE_COUNT = 1334
SAMPLE_BASELINE = ('pubmed26n0001.xml.gz', 'pubmed26n0667.xml.gz', 'pubmed26n1334.xml.gz')
FIRST_UPDATE_NUMBER = BASELINE_COUNT + 1
MD5_ALLOWANCE = 4 * KIB          # planned bytes for one .md5 file (body; headers are reserved separately)

_ANCHOR = re.compile(r'<a\s+[^>]*href="([^"]+)"[^>]*>[^<]*</a>([^\n<]*)', re.IGNORECASE)
_SIZE = re.compile(r'^(\d+(?:\.\d+)?)([KMGT]?)$')
_UNITS = {'': 1, 'K': 1024, 'M': 1024 ** 2, 'G': 1024 ** 3, 'T': 1024 ** 4}
_DATA = re.compile(r'^pubmed26n(\d{4})\.xml\.gz$')
_MD5 = re.compile(r'^pubmed26n(\d{4})\.xml\.gz\.md5$')
_MD5_BODY = re.compile(r'^\s*MD5\s*\(([^)]+)\)\s*=\s*([0-9a-fA-F]{32})\s*$')


def parse_listing(raw):
    """Returns ``[(name, size_text_or_None, size_upper_bytes_or_None)]`` in listing order."""
    try:
        text = raw.decode('utf-8')
    except UnicodeDecodeError as exc:
        raise PreflightFailed('listing is not UTF-8') from exc
    entries = []
    for href, tail in _ANCHOR.findall(text):
        if href.startswith(('?', '/', '#')) or '://' in href or href in ('../', './'):
            continue
        size_text, upper = None, None
        tokens = tail.split()
        m = _SIZE.match(tokens[-1]) if tokens else None
        if m:
            size_text = tokens[-1]
            value, unit = float(m.group(1)), m.group(2)
            decimals = len(m.group(1).split('.')[1]) if '.' in m.group(1) else 0
            step = 10.0 ** -decimals    # displayed sizes may be rounded to the nearest last digit
            upper = int(math.ceil((value + step) * _UNITS[unit]))
        entries.append((href, size_text, upper))
    if not entries:
        raise PreflightFailed('listing has no parsable entries')
    return entries


def _index(entries):
    seen, duplicates = {}, set()
    for name, size_text, upper in entries:
        if name in seen:
            duplicates.add(name)
        seen[name] = (size_text, upper)
    return seen, duplicates


def _classify(name):
    if _DATA.match(name):
        return 'data'
    if _MD5.match(name):
        return 'md5'
    if name.lower().startswith(YEAR_PREFIX):
        return 'ambiguous'
    return 'other'


def resolve_baseline(entries):
    """Preflight step 2. Exactly the 1334 baseline names, once each, each with a matching .md5."""
    seen, duplicates = _index(entries)
    pubmed = [n for n in seen if _classify(n) in ('data', 'md5', 'ambiguous')]
    if duplicates & set(pubmed):
        raise PreflightFailed('baseline listing has duplicate names', names=sorted(duplicates))
    ambiguous = sorted(n for n in pubmed if _classify(n) == 'ambiguous')
    if ambiguous:
        raise PreflightFailed('baseline listing has ambiguous pubmed26n names', names=ambiguous)
    expected = {f'pubmed26n{i:04d}.xml.gz' for i in range(1, BASELINE_COUNT + 1)}
    data = {n for n in pubmed if _classify(n) == 'data'}
    md5 = {n[:-4] for n in pubmed if _classify(n) == 'md5'}
    if data != expected:
        raise PreflightFailed('baseline data names are not exactly pubmed26n0001..1334',
                              missing=sorted(expected - data)[:10], extra=sorted(data - expected)[:10])
    if md5 != expected:
        raise PreflightFailed('baseline .md5 names do not match the data names one to one',
                              missing=sorted(expected - md5)[:10], extra=sorted(md5 - expected)[:10])
    for name in SAMPLE_BASELINE:
        if seen[name][1] is None:
            raise PreflightFailed('sample has no listed size', name=name)
    others = sorted(n for n in seen if _classify(n) == 'other')
    total = sum(seen[n][1] or 0 for n in expected)
    return dict(samples=[dict(name=n, size_text=seen[n][0], size_upper=seen[n][1]) for n in SAMPLE_BASELINE],
                file_count=len(expected), listed_bytes_upper=total,
                unlisted_size_count=sum(1 for n in expected if seen[n][1] is None), other_entries=others)


def resolve_updates(entries):
    """Preflight step 3. The two highest-numbered valid update files (>= 1335, once, with .md5)."""
    seen, duplicates = _index(entries)
    pubmed = [n for n in seen if _classify(n) in ('data', 'md5', 'ambiguous')]
    if duplicates & set(pubmed):
        raise PreflightFailed('update listing has duplicate names', names=sorted(duplicates))
    ambiguous = sorted(n for n in pubmed if _classify(n) == 'ambiguous')
    if ambiguous:
        raise PreflightFailed('update listing has ambiguous pubmed26n names', names=ambiguous)
    md5 = {n[:-4] for n in pubmed if _classify(n) == 'md5'}
    valid, invalid = [], []
    for name in pubmed:
        m = _DATA.match(name)
        if not m:
            continue
        number = int(m.group(1))
        if number >= FIRST_UPDATE_NUMBER and name in md5:
            valid.append((number, name))
        else:
            invalid.append(name)
    valid.sort()
    if len(valid) < 2:
        raise PreflightFailed('fewer than two valid update files in the frozen listing', valid=len(valid))
    chosen = [name for _, name in valid[-2:]]
    for name in chosen:
        if seen[name][1] is None:
            raise PreflightFailed('update sample has no listed size', name=name)
    others = sorted(n for n in seen if _classify(n) == 'other')
    return dict(samples=[dict(name=n, size_text=seen[n][0], size_upper=seen[n][1]) for n in chosen],
                file_count=len(valid), listed_bytes_upper=sum(seen[n][1] or 0 for _, n in valid),
                invalid_names=sorted(invalid), other_entries=others)


def parse_md5_file(raw, expected_name):
    """NLM ``MD5(<name>)= <hex>`` body. The named file must be the expected one."""
    try:
        text = raw.decode('ascii')
    except UnicodeDecodeError as exc:
        raise PreflightFailed('md5 file is not ASCII', name=expected_name) from exc
    lines = [line for line in text.splitlines() if line.strip()]
    if len(lines) != 1:
        raise PreflightFailed('md5 file must contain exactly one line', name=expected_name)
    m = _MD5_BODY.match(lines[0])
    if not m or m.group(1).strip() != expected_name:
        raise PreflightFailed('md5 file does not name the expected file', name=expected_name)
    return m.group(2).lower()


def planned_bytes(baseline, updates, mesh_allowance):
    """Preflight step 5: upper bound of all planned sample transfers, .md5 files and MeSH."""
    samples = baseline['samples'] + updates['samples']
    return sum(s['size_upper'] for s in samples) + len(samples) * MD5_ALLOWANCE + mesh_allowance
