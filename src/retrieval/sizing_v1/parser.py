"""Sizing-only parser mode for run S, with its memory, expansion and XML guards.

Each sampled file is parsed independently. No cross-file event log, final state or snapshot is
built. Every output row and the per-file manifest carry ``sizing_only: true``, and
``refuse_sizing_only`` is the guard that selection, promotion and export must call.

**XML safety, standard library only (pyexpat):**
- Parameter-entity parsing is ``NEVER``, so an external DTD named in ``DOCTYPE`` is tolerated but
  never read or fetched. No resolver exists, so there is no network path.
- ``ExternalEntityRefHandler`` refuses every external entity reference.
- ``EntityDeclHandler`` refuses **every** entity declaration, internal or external. The finite
  internal-expansion bound is therefore zero user-defined entities: only the five predefined
  entities and character references expand. This also refuses "billion laughs" at its first
  declaration.
- ``SkippedEntityHandler`` refuses references to undeclared entities (fail closed). Declarations
  after an unread parameter-entity reference are ignored by expat and can never expand.
- expat must be at least 2.4.1, whose built-in amplification limits are a second layer.

**Files:** ``parse_stream`` reads and writes only file objects it is given. In a run, the parent
opens the source sample and creates the output exclusively through the fs hook (``fsio``), then
passes the two descriptors to the child (``pass_fds``). The child never receives a path. The
manifest is written by the parent through the hook. ``parse_file`` is a plain-path wrapper for
tests and standalone use only.

**Memory:** the parser runs in a child process. ``run_with_watchdog`` polls its resident set
every ``poll`` seconds and kills it above the cap (Quinton's decision, 2026-10-03). Overshoot is
bounded by the growth within one poll interval, or three if readings are briefly missing. A
monitor failure, or more than two consecutive missing readings while the child is alive, kills it. This is a watchdog cap, not an OS-enforced limit; the tests inject RSS
readings and do not prove an OS-level bound. The same loop runs the 60-second volume and
free-space check during parsing. The child's stdout and stderr are drained concurrently into
bounded memory: 1 MiB accepted per stream, with a 64 KiB stderr tail. Overflow stops the child,
and no diagnostic file is created (``sizing_v1.2``).

**Expansion:** gzip is decompressed as a stream, with at most ``CHUNK`` bytes out per call.
Decompressed bytes above ``expansion_limit`` x compressed size stop the parse
(``stopped_expansion_guard``). Decompressed bytes are streamed, not written. They are still
charged to the scratch allowance, as the plan says they count against the scratch cap (a
conservative reading). Output bytes are charged before they are written.

The output format (``PARTITION_FORMAT``) is the proposed parsed-store partition row, declared
here because ACQUISITION-PLAN says only "events plus parsed fields". P5 must use these same fields
and compression, or re-measure.
"""
import gzip
import io
import json
import os
import pyexpat
import re
import select
import signal
import subprocess
import stat
import sys
import threading
import time
import zlib
from xml.parsers import expat

from src.retrieval.sizing_v1 import (GIB, MIB, SIZING_ONLY_MARKER, CapExceeded, ParserGuard,
                                     SizingOnlyRefused, SizingStop, UnexpectedFile)

PARTITION_FORMAT = 'prowl-parsed-partition-v0-proposed'
GZIP_LEVEL = 6
CHUNK = 1 * MIB
MIN_EXPAT = (2, 4, 1)
MEMORY_CAP = 4 * GIB
EXPANSION_LIMIT = 20
POLL_SECONDS = 0.5
DIAG_STREAM_LIMIT = 1024 * 1024
DIAG_STDERR_TAIL = 64 * 1024
DRAIN_JOIN_SECONDS = 5.0
DRAIN_SELECT_SECONDS = 0.1
_PARENT_PID = None          # set only in the parser child: stop if the watchdog parent disappears
MAX_MISSING_READINGS = 2
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
ARTICLE_FIELDS = ('title', 'abstract', 'journal_title', 'journal_iso', 'pub_year', 'pub_date_raw',
                  'languages', 'publication_types', 'mesh', 'keywords', 'doi', 'pmcid', 'date_revised')

_A = ('PubmedArticle', 'MedlineCitation')
_ART = _A + ('Article',)
_TEXT_PATHS = {
    _A + ('PMID',): 'pmid',
    _ART + ('ArticleTitle',): 'title',
    _ART + ('Abstract', 'AbstractText'): 'abstract',
    _ART + ('Journal', 'Title'): 'journal_title',
    _ART + ('Journal', 'ISOAbbreviation'): 'journal_iso',
    _ART + ('Journal', 'JournalIssue', 'PubDate', 'Year'): 'pub_year',
    _ART + ('Journal', 'JournalIssue', 'PubDate', 'MedlineDate'): 'medline_date',
    _ART + ('Language',): 'languages',
    _ART + ('PublicationTypeList', 'PublicationType'): 'publication_types',
    _A + ('MeshHeadingList', 'MeshHeading', 'DescriptorName'): 'mesh_descriptor',
    _A + ('MeshHeadingList', 'MeshHeading', 'QualifierName'): 'mesh_qualifier',
    _A + ('KeywordList', 'Keyword'): 'keywords',
    _A + ('DateRevised', 'Year'): 'rev_year',
    _A + ('DateRevised', 'Month'): 'rev_month',
    _A + ('DateRevised', 'Day'): 'rev_day',
    ('PubmedArticle', 'PubmedData', 'ArticleIdList', 'ArticleId'): 'article_id',
    ('PubmedBookArticle', 'BookDocument', 'PMID'): 'pmid',
    ('PubmedBookArticle', 'BookDocument', 'ArticleTitle'): 'title',
    ('DeleteCitation', 'PMID'): 'delete_pmid',
}
_RECORD_TAGS = {'PubmedArticle': 'article', 'PubmedBookArticle': 'book'}
_YEAR = re.compile(r'([0-9]{4})')
_YEAR_EXACT = re.compile(r'[0-9]{4}')


def check_expat():
    version = pyexpat.version_info
    if tuple(version) < MIN_EXPAT:
        raise ParserGuard(f'expat {version} is older than 2.4.1', reason='xml_guard')
    return '.'.join(map(str, version))


def refuse_sizing_only(obj):
    """Boundary guard for selection, promotion and export: sizing output is never accepted.

    Fail closed: accepts only a dict, or a list of dicts, each explicitly marked
    ``sizing_only: false``. Anything else (sizing rows, unmarked rows, other types) is refused.
    """
    if isinstance(obj, dict):
        items = [obj]
    elif isinstance(obj, list):
        items = obj
    else:
        raise SizingOnlyRefused(f'consumer input of type {type(obj).__name__} is not checkable')
    for item in items:
        if not isinstance(item, dict) or item.get(SIZING_ONLY_MARKER) is not False:
            raise SizingOnlyRefused('sizing-only output (or unmarked output) offered to a consumer')
    return obj


def load_partition_for_consumer(path):
    """What any selection/promotion reader must do first: read the manifest and refuse sizing output."""
    with open(path + '.manifest.json', encoding='utf-8') as fh:
        manifest = json.load(fh)
    refuse_sizing_only(manifest)
    with gzip.open(path, 'rt', encoding='utf-8') as fh:
        rows = [json.loads(line) for line in fh]
    return refuse_sizing_only(rows)


class _Charged(io.RawIOBase):
    """Write-only file wrapper that charges the scratch allowance before every write."""

    def __init__(self, raw, meter):
        self.raw, self.meter = raw, meter

    def writable(self):
        return True

    def write(self, b):
        self.meter.charge_written(len(b))
        return self.raw.write(b)

    def flush(self):
        self.raw.flush()


class _Meter:
    def __init__(self, allowance, compressed_size, expansion_limit, deadline):
        self.allowance = allowance
        self.compressed_size = compressed_size
        self.expansion_limit = expansion_limit
        self.deadline = deadline
        self.decompressed = 0
        self.written = 0

    def _charge(self, n):
        if self.decompressed + self.written + n > self.allowance:
            raise CapExceeded('scratch allowance reached during parse', reason='scratch_cap')

    def charge_written(self, n):
        self._charge(n)
        self.written += n

    def charge_decompressed(self, n):
        if self.decompressed + n > self.expansion_limit * self.compressed_size:
            raise ParserGuard('decompressed size exceeds the expansion limit', reason='expansion_guard',
                              limit=self.expansion_limit)
        self._charge(n)
        self.decompressed += n

    def check_time(self):
        if time.monotonic() >= self.deadline:
            raise CapExceeded('per-run time cap reached during parse', reason='time_cap')
        if _PARENT_PID is not None and os.getppid() != _PARENT_PID:
            raise ParserGuard('watchdog parent is gone; the child stops', reason='parent_lost')


class _Handler:
    def __init__(self, source_file, emit_row):
        self.source_file = source_file
        self.emit_row = emit_row
        self.stack = []
        self.capture = None     # (field, attrs, [text parts], depth)
        self.record = None
        self.seq = 0
        self.records = 0
        self.deletes = 0
        self.years = {}
        self.root = None
        self.doctype = None

    # -- expat safety callbacks ---------------------------------------------------------------
    def doctype_start(self, name, sysid, pubid, has_internal_subset):
        self.doctype = dict(name=name, system_id=sysid, public_id=pubid, internal_subset=bool(has_internal_subset))

    @staticmethod
    def entity_decl(name, is_param, value, base, sysid, pubid, notation):
        raise ParserGuard('entity declarations are refused', reason='xml_guard', entity=name)

    @staticmethod
    def external_ref(context, base, sysid, pubid):
        raise ParserGuard('external entity references are refused', reason='xml_guard', system_id=sysid)

    @staticmethod
    def skipped(name, is_param):
        raise ParserGuard('undeclared entity reference refused', reason='xml_guard', entity=name)

    # -- content --------------------------------------------------------------------------------
    def start(self, tag, attrs):
        if self.root is None:
            self.root = tag
            if tag != 'PubmedArticleSet':
                raise UnexpectedFile('root element is not PubmedArticleSet', root=tag)
        self.stack.append(tag)
        path = tuple(self.stack[1:])
        if len(path) == 1 and tag in _RECORD_TAGS:
            self.record = dict(kind=_RECORD_TAGS[tag], pmid=None, pmid_version=None, abstract=[],
                               languages=[], publication_types=[], mesh=[], keywords=[], ids={},
                               rev=[None, None, None])
        if self.capture is None and path in _TEXT_PATHS:
            self.capture = (_TEXT_PATHS[path], dict(attrs), [], len(self.stack))

    def text(self, data):
        if self.capture is not None:
            self.capture[2].append(data)

    def end(self, tag):
        if self.capture is not None and self.capture[3] == len(self.stack):
            field, attrs, parts, _ = self.capture
            self.capture = None
            self._store(field, attrs, ' '.join(''.join(parts).split()))
        path = tuple(self.stack[1:])
        self.stack.pop()
        if len(path) == 1 and tag in _RECORD_TAGS:
            self._emit_record()

    def _store(self, field, attrs, value):
        if field == 'delete_pmid':
            self.deletes += 1
            self.emit_row(self._row('delete', value, attrs.get('Version'), None, None))
            return
        rec = self.record
        if rec is None:
            return
        if field == 'pmid':
            if rec['pmid'] is None:
                rec['pmid'], rec['pmid_version'] = value, attrs.get('Version')
        elif field == 'abstract':
            rec['abstract'].append(dict(label=attrs.get('Label'), text=value))
        elif field in ('title', 'journal_title', 'journal_iso'):
            rec[field] = value
        elif field == 'pub_year':
            rec['pub_year'], rec['pub_date_raw'] = (int(value) if _YEAR_EXACT.fullmatch(value) else None), value
        elif field == 'medline_date':
            m = _YEAR.search(value)
            rec.setdefault('pub_year', int(m.group(1)) if m else None)
            rec['pub_date_raw'] = value
        elif field == 'languages':
            rec['languages'].append(value)
        elif field == 'publication_types':
            rec['publication_types'].append(dict(ui=attrs.get('UI'), name=value))
        elif field == 'mesh_descriptor':
            rec['mesh'].append(dict(ui=attrs.get('UI'), name=value, major=attrs.get('MajorTopicYN') == 'Y',
                                    qualifiers=[]))
        elif field == 'mesh_qualifier' and rec['mesh']:
            rec['mesh'][-1]['qualifiers'].append(dict(ui=attrs.get('UI'), name=value,
                                                      major=attrs.get('MajorTopicYN') == 'Y'))
        elif field == 'keywords':
            rec['keywords'].append(value)
        elif field in ('rev_year', 'rev_month', 'rev_day'):
            rec['rev'][('rev_year', 'rev_month', 'rev_day').index(field)] = value
        elif field == 'article_id':
            rec['ids'].setdefault(attrs.get('IdType'), value)

    def _row(self, event, pmid, version, kind, fields):
        row = {SIZING_ONLY_MARKER: True, 'partition_format': PARTITION_FORMAT,
               'source_file': self.source_file, 'seq': self.seq, 'event': event, 'pmid': pmid,
               'pmid_version': version, 'record_kind': kind, 'fields': fields}
        self.seq += 1
        return row

    def _emit_record(self):
        rec, self.record = self.record, None
        if not rec['pmid']:
            raise UnexpectedFile('record without a PMID', source_file=self.source_file, seq=self.seq)
        rev = rec['rev']
        fields = dict(title=rec.get('title'), abstract=rec['abstract'], journal_title=rec.get('journal_title'),
                      journal_iso=rec.get('journal_iso'), pub_year=rec.get('pub_year'),
                      pub_date_raw=rec.get('pub_date_raw'), languages=rec['languages'],
                      publication_types=rec['publication_types'], mesh=rec['mesh'], keywords=rec['keywords'],
                      doi=rec['ids'].get('doi'), pmcid=rec['ids'].get('pmc'),
                      date_revised='-'.join(p for p in rev if p) or None)
        year = fields['pub_year']
        self.years[str(year) if year else 'unknown'] = self.years.get(str(year) if year else 'unknown', 0) + 1
        self.records += 1
        self.emit_row(self._row('add_or_replace', rec['pmid'], rec['pmid_version'], rec['kind'], fields))


def _new_expat(handler):
    p = expat.ParserCreate()
    p.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    p.StartDoctypeDeclHandler = handler.doctype_start
    p.EntityDeclHandler = handler.entity_decl
    p.ExternalEntityRefHandler = handler.external_ref
    p.SkippedEntityHandler = handler.skipped
    p.StartElementHandler = handler.start
    p.EndElementHandler = handler.end
    p.CharacterDataHandler = handler.text
    p.buffer_text = True
    return p


def parse_stream(src, out, *, source_file, compressed_size, scratch_allowance, seconds_left,
                 expansion_limit=EXPANSION_LIMIT, chunk=CHUNK):
    """Parses one gzip PubMed-style stream into a sizing-only partition written to ``out``.

    ``src`` and ``out`` are already-open binary file objects. The caller created ``out``
    exclusively through the fs hook, and this function never opens a path. ``out`` is flushed and
    fsynced but not closed. Returns measurements; ``scratch_charged`` covers decompressed and
    output bytes, and the manifest is the caller's (``manifest_bytes_for``).
    """
    expat_version = check_expat()
    started = time.monotonic()
    meter = _Meter(scratch_allowance, compressed_size, expansion_limit, started + seconds_left)
    sink = _Charged(out, meter)
    gz = gzip.GzipFile(filename='', mode='wb', fileobj=sink, compresslevel=GZIP_LEVEL, mtime=0)

    def emit_row(row):
        gz.write((json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + '\n')
                 .encode('utf-8'))

    handler = _Handler(source_file, emit_row)
    xml = _new_expat(handler)
    d = zlib.decompressobj(31)
    try:
        while True:
            meter.check_time()
            block = src.read(chunk)
            if not block:
                break
            data = block
            while True:
                piece = d.decompress(data, chunk)
                if piece:
                    meter.charge_decompressed(len(piece))
                    xml.Parse(piece, False)
                meter.check_time()
                if d.eof:
                    data = d.unused_data
                    if not data:
                        break
                    d = zlib.decompressobj(31)     # next gzip member
                    continue
                data = d.unconsumed_tail
                if not data and not piece:
                    break                          # input consumed and no pending output
        if not d.eof:
            raise ParserGuard('truncated gzip stream', reason='malformed_xml', source_file=source_file)
        xml.Parse(b'', True)
    except zlib.error as exc:
        raise ParserGuard(f'gzip error: {exc}', reason='malformed_xml', source_file=source_file) from exc
    except expat.ExpatError as exc:
        raise ParserGuard(f'malformed XML: {exc}', reason='malformed_xml', source_file=source_file) from exc
    gz.close()
    out.flush()
    os.fsync(out.fileno())
    output_bytes = meter.written
    return dict(source_file=source_file, compressed_bytes=compressed_size, decompressed_bytes=meter.decompressed,
                output_bytes=output_bytes, parsed_ratio=output_bytes / compressed_size,
                expansion_ratio=meter.decompressed / compressed_size, records=handler.records,
                deletes=handler.deletes, rows=handler.seq, parse_seconds=round(time.monotonic() - started, 3),
                scratch_charged=meter.decompressed + meter.written, scratch_written=meter.written,
                observed_years=handler.years, doctype=handler.doctype, expat_version=expat_version)


def manifest_bytes_for(measurements):
    manifest = {SIZING_ONLY_MARKER: True, 'partition_format': PARTITION_FORMAT,
                'source_file': measurements['source_file'], 'rows': measurements['rows'], 'gzip_level': GZIP_LEVEL,
                'output_bytes': measurements['output_bytes']}
    return json.dumps(manifest, sort_keys=True).encode('utf-8')


def parse_file(src_path, out_path, *, source_file, compressed_size, scratch_allowance, seconds_left,
               expansion_limit=EXPANSION_LIMIT, chunk=CHUNK):
    """Plain-path wrapper (tests and standalone use): exclusive output, then ``<out>.manifest.json``.

    ``run_sizing`` never uses this; it opens files through the fs hook and calls a launcher.
    """
    try:
        raw = open(out_path, 'xb')
    except FileExistsError as exc:
        raise CapExceeded('scratch name collision', reason='scratch_collision', path=out_path) from exc
    with raw, open(src_path, 'rb') as src:
        m = parse_stream(src, raw, source_file=source_file, compressed_size=compressed_size,
                         scratch_allowance=scratch_allowance, seconds_left=seconds_left,
                         expansion_limit=expansion_limit, chunk=chunk)
    manifest = manifest_bytes_for(m)
    if m['scratch_charged'] + len(manifest) > scratch_allowance:
        raise CapExceeded('scratch allowance reached writing the manifest', reason='scratch_cap')
    with open(out_path + '.manifest.json', 'xb') as fh:
        fh.write(manifest)
        fh.flush()
        os.fsync(fh.fileno())
    return dict(m, manifest_bytes=len(manifest), scratch_charged=m['scratch_charged'] + len(manifest),
                output_path=out_path)


# -- child process and watchdog -----------------------------------------------------------------

class InProcessLauncher:
    """Test launcher: parses in this process (no memory watchdog, no periodic checks)."""

    def parse(self, *, src, out, periodic=None, **kwargs):
        src.seek(0)
        return parse_stream(src, out, **kwargs)


class PsMemoryProbe:
    """Resident set size of a child: /proc on Linux, ``ps -o rss=`` elsewhere (KiB). None if gone."""

    def rss_bytes(self, pid):
        status = f'/proc/{pid}/status'
        if os.path.exists(status):
            with open(status, encoding='ascii', errors='replace') as fh:
                for line in fh:
                    if line.startswith('VmRSS:'):
                        return int(line.split()[1]) * 1024
            return None
        out = subprocess.run(['ps', '-o', 'rss=', '-p', str(pid)], capture_output=True, text=True, timeout=5)
        text = out.stdout.strip()
        if out.returncode != 0 or not text:
            return None
        return int(text) * 1024


class _BoundedDrain:
    """Drains one child pipe on a thread into bounded memory (no files).

    The drain owns its descriptor: it duplicates the pipe's descriptor, the caller's file object is
    closed at once, and only the drain thread closes the duplicate, when it reaches end of file or
    is told to stop. No other code can close the descriptor while the thread may read it, so a
    reused descriptor number can never be read by a stale thread.

    At most ``limit`` bytes are accepted. Beyond that the stream is marked ``overflow``, and further
    bytes are still read (so the child never blocks on a full pipe) but not retained. With
    ``tail``, the last ``tail`` bytes of the stream are kept, including after overflow.
    """

    def __init__(self, stream, limit, tail=None):
        self.limit, self.tail = limit, tail
        self.total, self.overflow, self.buf = 0, False, bytearray()
        self.fd = os.dup(stream.fileno())
        stream.close()
        self.stop = threading.Event()
        self.thread = threading.Thread(target=self._run, name='run-s-diag-drain', daemon=True)
        self.thread.start()

    def _run(self):
        try:
            while not self.stop.is_set():
                ready, _, _ = select.select([self.fd], [], [], DRAIN_SELECT_SECONDS)
                if not ready:
                    continue
                try:
                    chunk = os.read(self.fd, 65536)
                except OSError:
                    return
                if not chunk:
                    return
                self.total += len(chunk)
                if self.total > self.limit:
                    self.overflow = True
                if self.tail is not None:
                    self.buf += chunk
                    if len(self.buf) > self.tail:
                        del self.buf[:len(self.buf) - self.tail]
                elif not self.overflow:
                    self.buf += chunk
        finally:
            os.close(self.fd)

    def data(self):
        return bytes(self.buf)


class _GroupAnchor:
    """A tiny, never-reaped-early process that leads the parse's process group.

    The anchor starts in a new process group and simply waits on a pipe from the parent. The parser
    child then joins the anchor's group. While the anchor is unreaped, alive or a zombie, its PID
    pins the group ID. So ``kill()`` (``killpg`` with SIGKILL) can never reach an unrelated
    process, whenever the parser child itself exited or was reaped. This needs no ``os.waitid``,
    which macOS Python lacks.

    ``kill()`` runs at most once. It takes down the parser child, any grandchildren and the anchor.
    Then ``reap()`` collects the anchor. If the parent dies, even by SIGKILL, the anchor's stdin
    reaches end of file and the anchor kills its own group. So no parser or grandchild is left
    running without the memory watchdog.
    """

    CODE = ('import os, signal, sys\n'
            'sys.stdin.buffer.read()\n'                 # returns when the parent closes or dies
            'os.killpg(0, signal.SIGKILL)\n')           # parent gone: take the parser and grandchildren down

    def __init__(self, python):
        kwargs = _group_kwargs(0)
        self.proc = subprocess.Popen([python, '-c', self.CODE], stdin=subprocess.PIPE,
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, **kwargs)
        self.pgid = self.proc.pid
        self.killed = False

    def kill(self):
        if self.killed:
            return
        self.killed = True
        try:
            os.killpg(self.pgid, signal.SIGKILL)   # pgid pinned: the anchor is not yet reaped
        except (ProcessLookupError, PermissionError):
            pass

    def reap(self):
        try:
            self.proc.stdin.close()
        except Exception:   # noqa: BLE001
            pass
        try:
            self.proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            pass


def _group_kwargs(pgid):
    """Popen arguments that put the new process into group ``pgid`` (0 = a new group of its own)."""
    if sys.version_info >= (3, 11):
        return dict(process_group=pgid)
    return dict(preexec_fn=lambda: os.setpgid(0, pgid))


def run_with_watchdog(argv, *, probe, memory_cap=MEMORY_CAP, poll=POLL_SECONDS, seconds_left,
                      sleep=time.sleep, monotonic=time.monotonic, cwd=None, periodic=None,
                      check_interval=60, pass_fds=(), stream_limit=DIAG_STREAM_LIMIT,
                      stderr_tail=DIAG_STDERR_TAIL):
    """Runs ``argv`` as a child and kills it above ``memory_cap`` RSS or past ``seconds_left``.

    Fail closed: a monitor exception, or more than ``MAX_MISSING_READINGS`` consecutive polls with no
    reading while the child is still running, kills it. A child that is exiting briefly has no RSS
    before it can be reaped, so up to that many gaps are tolerated; this extends the overshoot bound
    to at most three poll intervals in that case.

    ``periodic`` (the volume/free-space check) runs every ``check_interval`` seconds; if it raises,
    the child is killed and the exception propagates.

    **Bounded diagnostics (``sizing_v1.2``).** stdout and stderr are pipes drained concurrently by
    two threads into memory, never into a file:
    - at most ``stream_limit`` bytes (1 MiB) are accepted per stream, and only the last
      ``stderr_tail`` bytes (64 KiB) of stderr are kept;
    - more than the limit on either stream stops and reaps the child, with
      ``ParserGuard(reason='diagnostics_overflow')``. The run writes no manifest after a failed parse.
    - The child runs in a process group led by a ``_GroupAnchor``. The anchor is reaped only after
      the group has been killed, so the kill is safe without ``os.waitid`` (absent on macOS). The
      group is killed exactly once on every exit, so a grandchild still holding a pipe cannot
      outlive the parse. If pipes stay open anyway (a grandchild that left the group), the parse
      fails with ``diagnostics_pipe_held``.

    Draining never blocks the child, so the RSS, time and periodic checks keep running under pipe
    pressure. Every exit path kills the child if it is still alive, joins both drains and closes
    both pipes. Returns ``(returncode, stdout, stderr_tail, peak_rss_polled)``.
    """
    anchor = _GroupAnchor(sys.executable)
    try:
        proc = subprocess.Popen(argv, stdout=subprocess.PIPE, stderr=subprocess.PIPE, cwd=cwd,
                                pass_fds=tuple(pass_fds), **_group_kwargs(anchor.pgid))
    except BaseException:
        anchor.kill()
        anchor.reap()
        raise
    drains = []
    try:
        drains.append(_BoundedDrain(proc.stdout, stream_limit))
        drains.append(_BoundedDrain(proc.stderr, stream_limit, stderr_tail))
        start, peak, missing = monotonic(), 0, 0
        next_check = start + check_interval

        def overflowed():
            return any(d.overflow for d in drains)

        while proc.poll() is None:
            if overflowed():
                raise ParserGuard('parser child exceeded the diagnostics limit', reason='diagnostics_overflow',
                                  limit=stream_limit)
            try:
                rss = probe.rss_bytes(proc.pid)
            except Exception as exc:   # noqa: BLE001 - any monitor failure denies
                if proc.poll() is not None:
                    break
                raise ParserGuard(f'memory monitor failed: {exc}', reason='memory_monitor') from exc
            if rss is None:
                if proc.poll() is not None:
                    break
                missing += 1                   # an exiting child briefly has no RSS before it can be reaped
                if missing > MAX_MISSING_READINGS:
                    raise ParserGuard('memory monitor returned no reading for a live child',
                                      reason='memory_monitor')
                sleep(poll)
                continue
            missing = 0
            peak = max(peak, rss)
            if rss > memory_cap:
                raise ParserGuard('parser exceeded the memory cap', reason='memory_cap', rss=rss, cap=memory_cap)
            now = monotonic()
            if now - start > seconds_left:
                raise CapExceeded('per-run time cap reached during parse', reason='time_cap')
            if periodic is not None and now >= next_check:
                periodic()
                next_check = now + check_interval
            sleep(poll)
        proc.wait(timeout=30)
        anchor.kill()                          # the group stays pinned by the anchor: kill leftovers safely
        for d in drains:
            d.thread.join(DRAIN_JOIN_SECONDS)
        if any(d.thread.is_alive() for d in drains):
            raise ParserGuard('parser child pipes are still held open after exit', reason='diagnostics_pipe_held')
        if overflowed():
            raise ParserGuard('parser child exceeded the diagnostics limit', reason='diagnostics_overflow',
                              limit=stream_limit)
        return proc.returncode, drains[0].data(), drains[1].data(), peak
    finally:
        anchor.kill()                          # at most once per run; no-op if already done
        try:
            proc.wait(timeout=30)
        except subprocess.TimeoutExpired:
            pass
        anchor.reap()
        for d in drains:
            d.stop.set()
        for d in drains:
            d.thread.join(DRAIN_JOIN_SECONDS)    # each drain closes only its own descriptor
        for stream in (proc.stdout, proc.stderr):
            if stream is not None and not stream.closed:
                stream.close()               # only a stream no drain took over (drain creation failed)


_REASON_TYPES = {'diagnostics_overflow': ParserGuard, 'diagnostics_pipe_held': ParserGuard, 'memory_cap': ParserGuard, 'expansion_guard': ParserGuard, 'xml_guard': ParserGuard,
                 'malformed_xml': ParserGuard, 'memory_monitor': ParserGuard, 'parser_failed': ParserGuard,
                 'parent_lost': ParserGuard,
                 'unexpected_file': UnexpectedFile, 'scratch_cap': CapExceeded, 'time_cap': CapExceeded,
                 'scratch_collision': CapExceeded}


class WatchdogLauncher:
    """Live launcher: one child per file, with the RSS watchdog.

    The child gets no paths, only the source and output file descriptors the parent opened
    through the fs hook (``pass_fds``), plus numeric parameters.
    """

    def __init__(self, probe=None, memory_cap=MEMORY_CAP, poll=POLL_SECONDS, python=sys.executable):
        self.probe = probe or PsMemoryProbe()
        self.memory_cap = memory_cap
        self.poll = poll
        self.python = python

    def parse(self, *, src, out, periodic=None, **kwargs):
        fds = (src.fileno(), out.fileno())
        args = dict(kwargs, src_fd=fds[0], out_fd=fds[1], parent_pid=os.getpid())
        argv = [self.python, '-m', 'src.retrieval.sizing_v1.parser', '--worker', json.dumps(args)]
        rc, out, err, peak = run_with_watchdog(argv, probe=self.probe, memory_cap=self.memory_cap,
                                               poll=self.poll, seconds_left=kwargs['seconds_left'] + 5,
                                               cwd=REPO_ROOT, periodic=periodic, pass_fds=fds)
        try:
            result = json.loads(out.decode('utf-8').strip().splitlines()[-1])
        except (ValueError, IndexError) as exc:
            raise ParserGuard(f'parser child returned no result (rc={rc}): {err[-500:]!r}',
                              reason='parser_failed', source_file=kwargs.get('source_file'),
                              returncode=rc) from exc
        if not result.get('ok'):
            reason = result.get('reason', 'parser_failed')
            cls = _REASON_TYPES.get(reason, ParserGuard)
            raise cls(result.get('message', 'parser child failed'), reason=reason, **(result.get('detail') or {}))
        result['measurements']['peak_rss_polled'] = peak
        return result['measurements']


def check_handover_fds(src_fd, out_fd):
    """Descriptors from the parent must be regular files; the output must be empty. Rewind the source."""
    src_st, out_st = os.fstat(src_fd), os.fstat(out_fd)
    if not (stat.S_ISREG(src_st.st_mode) and stat.S_ISREG(out_st.st_mode)):
        raise UnexpectedFile('handed-over descriptors must be regular files')
    if out_st.st_size != 0:
        raise UnexpectedFile('handed-over output is not empty')
    if (src_st.st_dev, src_st.st_ino) == (out_st.st_dev, out_st.st_ino):
        raise UnexpectedFile('source and output are the same file')
    os.lseek(src_fd, 0, os.SEEK_SET)        # never trust the shared offset (a hook may have read ahead)
    os.lseek(out_fd, 0, os.SEEK_SET)


def _worker(args_json):
    global _PARENT_PID
    kwargs = json.loads(args_json)
    src_fd, out_fd = kwargs.pop('src_fd'), kwargs.pop('out_fd')
    _PARENT_PID = kwargs.pop('parent_pid', None)
    try:
        check_handover_fds(src_fd, out_fd)
        with os.fdopen(src_fd, 'rb') as src, os.fdopen(out_fd, 'wb') as out:
            result = dict(ok=True, measurements=parse_stream(src, out, **kwargs))
    except SizingStop as exc:
        result = dict(ok=False, reason=exc.reason, message=str(exc),
                      detail=json.loads(json.dumps(exc.detail, default=str)))
    except Exception as exc:   # noqa: BLE001 - report every child failure to the parent
        result = dict(ok=False, reason='parser_failed', message=f'{type(exc).__name__}: {exc}',
                      detail=dict(source_file=kwargs.get('source_file')))
    sys.stdout.write(json.dumps(result, sort_keys=True) + '\n')
    return 0


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == '--worker':
        sys.exit(_worker(sys.argv[2]))
    sys.exit('usage: python -m src.retrieval.sizing_v1.parser --worker <json>')
