"""Downloader subset for run S: counted, capped, exclusive, verified transfers.

**What the network counter measures (stated, not assumed).** For every HTTP response, including
redirects, HEAD requests, listings, ``.md5`` files, partial and failed attempts, it counts:
- the status line and header bytes, reconstructed from the parsed response; and
- every body byte the transport hands back.

It does **not** see:
- TLS record overhead, TCP/IP framing or chunked-encoding framing;
- bytes a failing read had buffered internally but never returned (for example a truncated chunked
  body or a timed-out partial read);
- unread socket buffers.

To keep the signed 10 GiB "every byte" cap conservative, the counter stops at
``network_cap - network_reserve``. The default reserve is 1% of the cap, an engineering allowance
for that unmeasured overhead (the native review should confirm it). The figure is recorded in the
journal. Payload ``Content-Length`` is never used as the count.

Enforcement happens **before** bytes are accepted:
- each read asks for at most the remaining network allowance;
- each request first reserves ``HEADER_RESERVE`` for its status line and headers;
- each chunk is charged to the scratch counter before it is written.

Counters are therefore never exceeded, only reached.

**Blocking reads.** The live transport keeps its own reference to the connected socket, because
``http.client`` drops ``conn.sock`` after reading the headers of a ``Connection: close`` response.
Three things then bound every phase, including the header and chunk-size lines that
``http.client`` reads in loops:
- body reads return after at most one underlying receive (``read1``);
- before every read the socket timeout is reset to ``min(stall limit, time left before the run
  deadline)``;
- a ``SocketWatch`` thread shuts the socket down once that limit passes without the next read
  being re-armed.

Name resolution (run in a thread, as Python's resolver has no timeout) and connecting share one
budget of that same limit. The TLS handshake runs under the watch. So no server can hold a request
past the stall limit or the run deadline by more than one watch poll (0.5 s), plus the 1-second
timeout floor. The 60-second checks keep running. There is exactly one transfer at a time, and
at most ``attempts`` per file.

**Never substitute.** A redirect may change scheme, host or directory within the signed origins,
but the target's last path segment and query must equal the requested ones.
"""
import hashlib
import http.client
import os
import posixpath
import re
import socket
import ssl
import threading
import time
from urllib.parse import urljoin, urlsplit

from src.retrieval.sizing_v1 import (KIB, MIB, CapExceeded, SizingStop, TransferFailed,
                                     UnexpectedFile)

HEADER_RESERVE = 64 * KIB
REDIRECT_BODY_LIMIT = 64 * KIB
MAX_REDIRECTS = 3
CHUNK = 1 * MIB
REDIRECT_STATUSES = (301, 302, 303, 307, 308)
_DIGITS = re.compile(r'[0-9]{1,15}')
_DEFAULT_PORT = {'https': 443, 'http': 80}
_MAGIC = {
    'gzip': lambda b: b[:2] == b'\x1f\x8b',
    'md5': lambda b: b.lstrip()[:3] == b'MD5',
    'listing': lambda b: b'<' in b[:4096],
    'xml': lambda b: b.lstrip(b'\xef\xbb\xbf \t\r\n')[:1] == b'<',
}
_TRANSPORT_ERRORS = (socket.timeout, TimeoutError, OSError, http.client.HTTPException, ValueError)


def kind_for_name(name):
    if name.endswith('.gz'):
        return 'gzip'
    if name.endswith('.md5'):
        return 'md5'
    if name.endswith('.xml'):
        return 'xml'
    raise UnexpectedFile('unexpected file type', name=name)


def content_length(headers):
    """ASCII-digit ``Content-Length`` or None (anything else is treated as absent)."""
    value = headers.get('content-length')
    if value is not None and _DIGITS.fullmatch(value.strip()):
        return int(value.strip())
    return None


def _tail(url):
    parts = urlsplit(url)
    path = parts.path or '/'
    return posixpath.basename(path.rstrip('/')), path.endswith('/'), parts.query


class Budget:
    """Cumulative counters for one signed copy (both runs share them)."""

    def __init__(self, network_cap, scratch_cap, network_reserve=None, network_used=0, scratch_used=0):
        self.network_cap = network_cap
        self.network_reserve = network_cap // 100 if network_reserve is None else network_reserve
        self.scratch_cap = scratch_cap
        self.network_used = network_used
        self.scratch_used = scratch_used
        if network_used > self.network_limit or scratch_used > scratch_cap:
            raise CapExceeded('inherited counters already exceed the caps', reason='network_cap'
                              if network_used > self.network_limit else 'scratch_cap')

    @property
    def network_limit(self):
        return self.network_cap - self.network_reserve

    def network_remaining(self):
        return self.network_limit - self.network_used

    def scratch_remaining(self):
        return self.scratch_cap - self.scratch_used

    def charge_network(self, n):
        if n < 0 or self.network_used + n > self.network_limit:
            raise CapExceeded('network cap reached', reason='network_cap', used=self.network_used, asked=n)
        self.network_used += n

    def charge_scratch(self, n):
        if n < 0 or self.scratch_used + n > self.scratch_cap:
            raise CapExceeded('scratch cap reached', reason='scratch_cap', used=self.scratch_used, asked=n)
        self.scratch_used += n

    def require_header_reserve(self):
        if self.network_remaining() < HEADER_RESERVE:
            raise CapExceeded('network allowance below one header reserve', reason='network_cap',
                              used=self.network_used)

    def snapshot(self):
        return dict(network_used=self.network_used, network_cap=self.network_cap,
                    network_reserve=self.network_reserve, scratch_used=self.scratch_used,
                    scratch_cap=self.scratch_cap)


class Origins:
    """The literal (scheme, host, port) origins from the signed copy. Nothing else is contacted."""

    def __init__(self, urls):
        self.allowed = {self._key(u) for u in urls}

    @staticmethod
    def _key(url):
        try:
            parts = urlsplit(url)
            port = parts.port
        except ValueError as exc:
            raise UnexpectedFile('unparsable URL', url=url) from exc
        if parts.scheme not in _DEFAULT_PORT or not parts.hostname or parts.username or parts.password:
            raise UnexpectedFile('unsupported URL', url=url)
        return parts.scheme, parts.hostname.lower(), port or _DEFAULT_PORT[parts.scheme]

    def check(self, url):
        if self._key(url) not in self.allowed:
            raise UnexpectedFile('URL origin is not in the signed copy', url=url)
        return url


class SocketWatch:
    """Shuts a socket down when ``timeout_fn()`` seconds pass after the last ``arm()``.

    It covers phases that a per-receive socket timeout cannot bound (header lines and chunk-size
    lines read in loops).
    """

    def __init__(self, timeout_fn, poll=0.5, monotonic=time.monotonic):
        self.timeout_fn, self.poll, self.monotonic = timeout_fn, poll, monotonic
        self.sock = None
        self.tripped = False
        self.limit = monotonic() + timeout_fn()
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread = threading.Thread(target=self._run, name='run-s-socket-watch', daemon=True)

    def start(self, sock):
        self.sock = sock
        self.arm()
        self._thread.start()

    def arm(self):
        allowed = self.timeout_fn()
        self.limit = self.monotonic() + allowed
        if self.sock is not None:
            try:
                self.sock.settimeout(allowed)
            except OSError:
                pass

    def _run(self):
        while not self._stop.wait(self.poll):
            if self.monotonic() > self.limit:
                with self._lock:                 # never shut down a socket after stop()/close
                    if self._stop.is_set():
                        return
                    self.tripped = True
                    try:
                        self.sock.shutdown(socket.SHUT_RDWR)
                    except OSError:
                        pass
                return

    def stop(self):
        with self._lock:
            self._stop.set()


class HttpsTransport:
    """Live transport (http.client). Refuses any origin outside ``origins`` before connecting.

    It opens one connection per request with ``Connection: close`` and
    ``Accept-Encoding: identity``, and sends a project User-Agent and no other headers (no
    personal data). ``timeout`` may be a number or a callable, which is re-evaluated before every
    read. The offline tests cover origin refusal and the read/timeout discipline; the native
    review covers real sockets.
    """

    def __init__(self, origins, user_agent, socket_factory=socket.socket, resolver=socket.getaddrinfo):
        self.origins = origins
        self.user_agent = user_agent
        self.socket_factory = socket_factory
        self.resolver = resolver

    def connect(self, host, port, budget):
        """Resolve and connect within one time budget (DNS has no timeout of its own in Python)."""
        start = time.monotonic()
        result = {}

        def resolve():
            try:
                result['addrs'] = self.resolver(host, port, 0, socket.SOCK_STREAM)
            except Exception as exc:   # noqa: BLE001
                result['error'] = exc
        th = threading.Thread(target=resolve, name='run-s-resolve', daemon=True)
        th.start()
        th.join(budget)
        if th.is_alive():
            raise TimeoutError('name resolution exceeded the time budget')
        if 'error' in result:
            raise result['error']
        last = None
        for family, type_, proto, _, addr in result['addrs']:
            left = budget - (time.monotonic() - start)
            if left <= 0:
                break
            sock = self.socket_factory(family, type_, proto)
            try:
                sock.settimeout(left)
                sock.connect(addr)
                return sock
            except OSError as exc:
                last = exc
                sock.close()
        raise TimeoutError(f'connect exceeded the time budget or failed: {last}')

    def request(self, method, url, timeout):
        self.origins.check(url)
        timeout_fn = timeout if callable(timeout) else (lambda: timeout)
        parts = urlsplit(url)
        path = parts.path or '/'
        if parts.query:
            path += '?' + parts.query
        port = parts.port or (443 if parts.scheme == 'https' else 80)
        conn = (http.client.HTTPSConnection if parts.scheme == 'https' else http.client.HTTPConnection)(
            parts.hostname, port, timeout=timeout_fn())
        watch = SocketWatch(timeout_fn)
        try:
            raw = self.connect(parts.hostname, port, timeout_fn())
            if parts.scheme == 'https':
                tls = ssl.create_default_context().wrap_socket(raw, server_hostname=parts.hostname,
                                                               do_handshake_on_connect=False)
                watch.start(tls)
                tls.do_handshake()               # bounded by the socket timeout and the watch
                conn.sock = tls
            else:
                watch.start(raw)
                conn.sock = raw
            conn.request(method, path, headers={'User-Agent': self.user_agent, 'Accept-Encoding': 'identity',
                                                'Connection': 'close'})
            resp = conn.getresponse()
        except BaseException as exc:
            watch.stop()
            conn.close()
            if watch.tripped and isinstance(exc, (OSError, http.client.HTTPException, ValueError)):
                raise TimeoutError('socket watch tripped before the response headers completed') from exc
            raise
        if watch.tripped:
            # shutdown() can turn a stalled header phase into an apparent end of headers
            watch.stop()
            conn.close()
            raise TimeoutError('socket watch tripped before the response headers completed')
        return HttpResponse(conn, resp, watch)


class HttpResponse:
    def __init__(self, conn, resp, watch):
        self._conn, self._resp, self._watch = conn, resp, watch
        self.status = resp.status
        self.headers = {k.lower(): v for k, v in resp.getheaders()}
        self.header_bytes = (len(f'HTTP/1.1 {resp.status} {resp.reason}\r\n'.encode('latin-1', 'replace'))
                             + sum(len(k.encode('latin-1', 'replace')) + len(v.encode('latin-1', 'replace')) + 4
                                   for k, v in resp.getheaders()) + 2)

    def read(self, n):
        self._watch.arm()
        try:
            data = self._resp.read1(n)
        except (OSError, http.client.HTTPException, ValueError) as exc:
            if self._watch.tripped:
                raise TimeoutError('socket watch tripped (stall limit or run deadline)') from exc
            raise
        if not data and self._watch.tripped:
            # shutdown() turns the stalled read into an EOF; never mistake that for a complete body
            raise TimeoutError('socket watch tripped (stall limit or run deadline)')
        return data

    def close(self):
        self._watch.stop()
        self._resp.close()
        self._conn.close()


class TransferContext:
    def __init__(self, *, transport, budget, origins, clock, deadline, emit, periodic_check,
                 stall_seconds=300, attempts=2, check_interval=60, chunk=CHUNK):
        self.transport = transport
        self.budget = budget
        self.origins = origins
        self.clock = clock
        self.deadline = deadline
        self.emit = emit
        self.periodic_check = periodic_check
        self.stall_seconds = stall_seconds
        self.attempts = attempts
        self.check_interval = check_interval
        self.chunk = chunk
        self.next_check = clock() + check_interval

    def check_time(self):
        now = self.clock()
        if now >= self.deadline:
            raise CapExceeded('per-run time cap reached', reason='time_cap')
        if now >= self.next_check:
            self.periodic_check()
            self.next_check = now + self.check_interval
        return now

    def timeout(self):
        return max(1.0, min(float(self.stall_seconds), self.deadline - self.clock()))


class _AttemptFailed(Exception):
    pass


def _drain(ctx, resp, limit):
    got = 0
    length = content_length(resp.headers)
    while True:
        if length is not None and got >= length:
            return got
        ctx.check_time()
        n = min(ctx.chunk, ctx.budget.network_remaining(), limit - got + 1)
        if n <= 0:
            raise CapExceeded('network cap reached', reason='network_cap')
        try:
            data = resp.read(n)
        except _TRANSPORT_ERRORS as exc:
            raise _AttemptFailed(f'redirect body read error: {exc}') from exc
        if not data:
            return got
        ctx.budget.charge_network(len(data))
        got += len(data)
        if got > limit:
            raise _AttemptFailed('redirect body too large')


def _open(ctx, method, url):
    """Issues the request and follows at most MAX_REDIRECTS redirects within the signed origins."""
    hops = []
    want = _tail(url)
    for _ in range(MAX_REDIRECTS + 1):
        ctx.check_time()
        ctx.origins.check(url)
        ctx.budget.require_header_reserve()
        try:
            resp = ctx.transport.request(method, url, ctx.timeout)
        except _TRANSPORT_ERRORS as exc:
            raise _AttemptFailed(f'request failed: {type(exc).__name__}: {exc}') from exc
        if resp.header_bytes > HEADER_RESERVE:
            ctx.budget.charge_network(min(resp.header_bytes, ctx.budget.network_remaining()))
            resp.close()
            raise UnexpectedFile('response headers exceed the header reserve', url=url)
        ctx.budget.charge_network(resp.header_bytes)
        if resp.status in REDIRECT_STATUSES:
            location = resp.headers.get('location')
            try:
                if method != 'HEAD':
                    _drain(ctx, resp, REDIRECT_BODY_LIMIT)
            finally:
                resp.close()
            if not location:
                raise _AttemptFailed('redirect without location')
            target = urljoin(url, location)
            ctx.origins.check(target)                  # unexpected redirect origin stops the run
            if _tail(target) != want:
                raise UnexpectedFile('redirect would substitute a different file', url=url, target=target)
            hops.append(dict(status=resp.status, to=target))
            url = target
            continue
        return resp, url, hops
    raise _AttemptFailed('too many redirects')


def head_size(ctx, url):
    """Preflight step 4 helper: ``Content-Length`` from a HEAD request, or None. Bytes are counted."""
    try:
        resp, final_url, hops = _open(ctx, 'HEAD', url)
    except _AttemptFailed as exc:
        ctx.emit('head_failed', url=url, error=str(exc))
        return None
    try:
        if resp.status != 200:
            ctx.emit('head_failed', url=url, status=resp.status)
            return None
        size = content_length(resp.headers)
        ctx.emit('head', url=url, final_url=final_url, redirects=hops, content_length=size)
        return size
    finally:
        resp.close()


class ScratchDir:
    """Where attempt files go: ``scratch`` area, optional ``sizing-<run_id>`` subdirectory, via the fs hook."""

    def __init__(self, fs, subdir=''):
        self.fs, self.subdir = fs, subdir

    def rel(self, name):
        return f'{self.subdir}/{name}' if self.subdir else name

    def create(self, name):
        return self.fs.create_exclusive('scratch', self.rel(name))

    def display(self, name):
        return self.fs.display('scratch', self.rel(name))


def _as_dir(target):
    if not isinstance(target, ScratchDir):
        raise TypeError('fetch target must be a ScratchDir (all writes go through the fs hook)')
    return target


def fetch(ctx, url, target, name, *, max_body=None, expected_md5=None, keep_bytes=False,
          kind=None):
    """Downloads ``url`` into ``<target>/<name>.attempt<k>`` (exclusive create through the fs hook).

    ``target`` is a ``ScratchDir`` over the run's fs hook.

    Returns a receipt dict, plus ``data`` when ``keep_bytes``. Run-stopping conditions (caps, time,
    volume, unexpected file/redirect, size allowance, scratch collision or write failure) propagate
    at once; other failures consume an attempt. Two failed attempts raise TransferFailed. Partial
    files are kept and stay charged to the scratch counter.
    """
    kind = kind or kind_for_name(name)
    failures = []
    for attempt in range(1, ctx.attempts + 1):
        sdir = _as_dir(target)
        fname = f'{name}.attempt{attempt}'
        path = sdir.display(fname)
        ctx.emit('file_start', name=name, url=url, attempt=attempt, path=path)
        started = ctx.clock()
        try:
            receipt = _attempt(ctx, url, sdir, fname, path, name, kind, max_body, expected_md5, keep_bytes)
        except _AttemptFailed as exc:
            failures.append(str(exc))
            ctx.emit('file_attempt_failed', name=name, attempt=attempt, error=str(exc),
                     counters=ctx.budget.snapshot())
            continue
        receipt.update(name=name, attempt=attempt, seconds=round(ctx.clock() - started, 3),
                       failures=failures)
        ctx.emit('file_end', **{k: v for k, v in receipt.items() if k != 'data'},
                 counters=ctx.budget.snapshot())
        return receipt
    raise TransferFailed('file failed both attempts', name=name, failures=failures)


def _write(fh, data, path):
    try:
        fh.write(data)
    except OSError as exc:
        raise SizingStop(f'scratch write failed: {exc}', reason='scratch_write_failed', path=path) from exc


def _attempt(ctx, url, sdir, fname, path, name, kind, max_body, expected_md5, keep_bytes):
    resp, final_url, hops = _open(ctx, 'GET', url)
    try:
        if resp.status != 200:
            raise _AttemptFailed(f'HTTP {resp.status}')
        try:
            fh = sdir.create(fname)
        except FileExistsError as exc:
            raise SizingStop('scratch name collision', reason='scratch_collision', path=path) from exc
        except (OSError, ValueError) as exc:
            raise SizingStop(f'scratch file cannot be created: {exc}', reason='scratch_write_failed',
                             path=path) from exc
        md5, sha = hashlib.md5(usedforsecurity=False), hashlib.sha256()
        got, buf, first = 0, [], True
        length = content_length(resp.headers)
        last_progress = ctx.clock()
        with fh:
            while True:
                if length is not None and got >= length:
                    break                      # complete per Content-Length; no extra read needed
                ctx.check_time()
                n = min(ctx.chunk, ctx.budget.network_remaining())
                if max_body is not None:
                    n = min(n, max_body - got + 1)
                if n <= 0:
                    raise CapExceeded('network cap reached', reason='network_cap')
                try:
                    data = resp.read(n)
                except (socket.timeout, TimeoutError) as exc:
                    raise _AttemptFailed('stalled (no progress within the stall limit)') from exc
                except _TRANSPORT_ERRORS as exc:
                    raise _AttemptFailed(f'read error: {type(exc).__name__}: {exc}') from exc
                now = ctx.clock()
                if data:
                    ctx.budget.charge_network(len(data))
                if now - last_progress > ctx.stall_seconds:
                    raise _AttemptFailed('stalled (no progress within the stall limit)')
                if not data:
                    break
                if max_body is not None and got + len(data) > max_body:
                    raise SizingStop('transfer exceeds its size allowance', reason='size_allowance',
                                     name=name, allowance=max_body)
                if first:
                    if not _MAGIC[kind](data):
                        raise UnexpectedFile('content does not match the expected file type', name=name,
                                             kind=kind)
                    first = False
                ctx.budget.charge_scratch(len(data))
                _write(fh, data, path)
                md5.update(data)
                sha.update(data)
                if keep_bytes:
                    buf.append(data)
                got += len(data)
                last_progress = now
            try:
                fh.flush()
                os.fsync(fh.fileno())
            except OSError as exc:
                raise SizingStop(f'scratch flush failed: {exc}', reason='scratch_write_failed', path=path) from exc
        if length is not None and length != got:
            raise _AttemptFailed(f'truncated: {got} of {length} bytes')
        if got == 0:
            raise _AttemptFailed('empty body')
        md5_hex = md5.hexdigest()
        if expected_md5 is not None and md5_hex != expected_md5:
            raise _AttemptFailed('published MD5 mismatch')
        receipt = dict(path=path, rel=sdir.rel(fname), url=url, final_url=final_url, redirects=hops, bytes=got,
                       md5=md5_hex, sha256=sha.hexdigest(),
                       md5_verified=expected_md5 is not None,
                       integrity_note=None if expected_md5 is not None else 'no published MD5; SHA-256 only')
        if keep_bytes:
            receipt['data'] = b''.join(buf)
        return receipt
    finally:
        resp.close()
