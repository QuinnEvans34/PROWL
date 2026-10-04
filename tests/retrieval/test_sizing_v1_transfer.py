"""Counted, capped, exclusive and verified transfers (fake transport; network denied)."""
import hashlib
import os
import socket

import pytest

from src.retrieval.sizing_v1 import (GIB, KIB, CapExceeded, SizingStop, TransferFailed, UnexpectedFile,
                                     VolumeCheckFailed)
from src.retrieval.sizing_v1.fsio import PlainFs
from src.retrieval.sizing_v1.transfer import (HEADER_RESERVE, Budget, HttpResponse, HttpsTransport, Origins,
                                              ScratchDir, TransferContext, content_length, fetch, head_size)

pytestmark = pytest.mark.component
BASE = 'https://nlm.invalid/pubmed/baseline/'
GZ = b'\x1f\x8b' + b'invented-gzip-like-payload-' * 50


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    def deny(*a, **k):
        raise AssertionError('network denied in sizing_v1 tests')
    monkeypatch.setattr(socket.socket, 'connect', deny)
    monkeypatch.setattr(socket, 'create_connection', deny)
    monkeypatch.setattr(socket, 'getaddrinfo', deny)


def sd(path):
    return ScratchDir(PlainFs(scratch_root=str(path)))


class Clock:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


class FakeResp:
    def __init__(self, transport, status=200, body=b'', headers=None, header_bytes=200, length=True,
                 per_read=0.0, timeout_at=None, stall_at=None, interrupt=None):
        self.transport, self.status, self.body = transport, status, body
        self.headers = dict(headers or {})
        if length and 'content-length' not in self.headers:
            self.headers['content-length'] = str(len(body))
        self.header_bytes = header_bytes
        self.per_read, self.timeout_at, self.stall_at = per_read, timeout_at, stall_at
        self.pos, self.stalled, self.closed = 0, False, False

    def read(self, n):
        assert n > 0
        if self.timeout_at is not None and self.pos >= self.timeout_at:
            raise TimeoutError('invented timeout')
        if self.stall_at is not None and self.pos >= self.stall_at and not self.stalled:
            self.transport.clock.t += 301
            self.stalled = True
        data = self.body[self.pos:self.pos + n]
        self.pos += len(data)
        self.transport.clock.t += self.per_read
        self.transport.body_served += len(data)
        return data

    def close(self):
        if not self.closed:
            self.closed = True
            self.transport.open -= 1


class FakeTransport:
    def __init__(self, clock, routes):
        self.clock, self.routes = clock, {k: list(v) for k, v in routes.items()}
        self.calls, self.open, self.max_open = [], 0, 0
        self.body_served = self.header_served = 0

    def request(self, method, url, timeout):
        self.calls.append((method, url))
        spec = self.routes[(method, url)].pop(0)
        if isinstance(spec, BaseException):
            raise spec
        resp = FakeResp(self, **spec)
        self.open += 1
        self.max_open = max(self.max_open, self.open)
        self.header_served += resp.header_bytes
        return resp


def ctx_for(transport, clock, budget=None, deadline=None, checks=None, chunk=64, urls=(BASE,)):
    events = []

    def periodic():
        if checks is not None:
            checks.append(clock())
    ctx = TransferContext(transport=transport, budget=budget or Budget(10 * GIB, 40 * GIB), origins=Origins(urls),
                          clock=clock, deadline=deadline or clock() + 7200,
                          emit=lambda event, **f: events.append((event, f)), periodic_check=periodic,
                          stall_seconds=300, attempts=2, check_interval=60, chunk=chunk)
    ctx.events = events
    return ctx


def test_success_counts_headers_and_body_and_verifies_md5(tmp_path):
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [dict(body=GZ)]})
    ctx = ctx_for(t, clock)
    r = fetch(ctx, BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz', expected_md5=hashlib.md5(GZ).hexdigest())
    assert r['md5_verified'] and r['sha256'] == hashlib.sha256(GZ).hexdigest() and r['bytes'] == len(GZ)
    assert ctx.budget.network_used == t.body_served + t.header_served
    assert ctx.budget.scratch_used == len(GZ) == os.path.getsize(r['path'])
    assert r['path'].endswith('a.xml.gz.attempt1')


def test_absent_published_md5_is_noted(tmp_path):
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'desc.xml'): [dict(body=b'<?xml version="1.0"?><x/>')]})
    r = fetch(ctx_for(t, clock), BASE + 'desc.xml', sd(tmp_path), 'desc.xml')
    assert not r['md5_verified'] and 'SHA-256 only' in r['integrity_note']


def test_network_cap_exact_fit_then_next_byte_overflow(tmp_path):
    body = b'\x1f\x8b' + b'z' * 69998
    for cap, ok in ((200 + len(body), True), (200 + len(body) - 1, False)):
        clock = Clock()
        t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [dict(body=body)]})
        budget = Budget(cap, 40 * GIB, network_reserve=0)
        ctx = ctx_for(t, clock, budget=budget, chunk=4096)
        out = tmp_path / str(cap)
        out.mkdir()
        if ok:
            fetch(ctx, BASE + 'a.xml.gz', sd(out), 'a.xml.gz')
            assert budget.network_used == cap
        else:
            with pytest.raises(CapExceeded) as exc:
                fetch(ctx, BASE + 'a.xml.gz', sd(out), 'a.xml.gz')
            assert exc.value.reason == 'network_cap' and budget.network_used <= cap


def test_default_reserve_is_one_percent_and_header_reserve_blocks_request(tmp_path):
    assert Budget(10 * GIB, 40 * GIB).network_limit == 10 * GIB - (10 * GIB) // 100
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [dict(body=GZ)]})
    budget = Budget(HEADER_RESERVE - 1, 40 * GIB, network_reserve=0)
    with pytest.raises(CapExceeded):
        fetch(ctx_for(t, clock, budget=budget), BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz')
    assert t.calls == []


def test_scratch_cap_exact_fit_then_overflow_writes_only_charged_bytes(tmp_path):
    for cap, ok in ((len(GZ), True), (len(GZ) - 1, False)):
        clock = Clock()
        t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [dict(body=GZ)]})
        budget = Budget(10 * GIB, cap)
        out = tmp_path / str(cap)
        out.mkdir()
        if ok:
            fetch(ctx_for(t, clock, budget=budget), BASE + 'a.xml.gz', sd(out), 'a.xml.gz')
            assert budget.scratch_used == cap
        else:
            with pytest.raises(CapExceeded) as exc:
                fetch(ctx_for(t, clock, budget=budget), BASE + 'a.xml.gz', sd(out), 'a.xml.gz')
            assert exc.value.reason == 'scratch_cap'
            assert os.path.getsize(out / 'a.xml.gz.attempt1') == budget.scratch_used <= cap


def test_inherited_counters_are_not_reset():
    b = Budget(10 * GIB, 40 * GIB, network_used=5 * GIB, scratch_used=7 * GIB)
    assert b.network_used == 5 * GIB and b.scratch_remaining() == 33 * GIB
    with pytest.raises(CapExceeded):
        Budget(10 * GIB, 40 * GIB, scratch_used=41 * GIB)


def test_redirect_within_origin_is_followed_and_counted(tmp_path):
    clock = Clock()
    t = FakeTransport(clock, {
        ('GET', BASE + 'a.xml.gz'): [dict(status=302, body=b'moved', headers={'location': '/mirror/a.xml.gz'})],
        ('GET', 'https://nlm.invalid/mirror/a.xml.gz'): [dict(body=GZ)]})
    ctx = ctx_for(t, clock)
    r = fetch(ctx, BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz')
    assert r['final_url'] == 'https://nlm.invalid/mirror/a.xml.gz' and r['redirects'][0]['status'] == 302
    assert ctx.budget.network_used == t.body_served + t.header_served == 400 + 5 + len(GZ)


def test_redirect_to_a_different_file_is_refused(tmp_path):
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [
        dict(status=302, body=b'', headers={'location': '/pubmed/baseline/b.xml.gz'})]})
    with pytest.raises(UnexpectedFile):
        fetch(ctx_for(t, clock), BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz')


def test_redirect_to_unsigned_host_stops_the_run(tmp_path):
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [
        dict(status=301, body=b'', headers={'location': 'https://elsewhere.invalid/a.xml.gz'})]})
    with pytest.raises(UnexpectedFile):
        fetch(ctx_for(t, clock), BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz')
    assert len(t.calls) == 1


def test_retry_after_partial_keeps_and_counts_partial(tmp_path):
    clock = Clock()
    partial = dict(body=GZ[:100], headers={'content-length': str(len(GZ))})
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [partial, dict(body=GZ)]})
    ctx = ctx_for(t, clock)
    r = fetch(ctx, BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz')
    assert r['attempt'] == 2 and 'truncated' in r['failures'][0]
    assert os.path.getsize(tmp_path / 'a.xml.gz.attempt1') == 100
    assert ctx.budget.scratch_used == 100 + len(GZ)
    assert ctx.budget.network_used == t.body_served + t.header_served


def test_both_attempts_failing_is_terminal_and_bounded(tmp_path):
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [dict(status=500, body=b'x'), dict(status=503, body=b'y'),
                                                           dict(body=GZ)]})
    with pytest.raises(TransferFailed):
        fetch(ctx_for(t, clock), BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz')
    assert len(t.calls) == 2


def test_md5_mismatch_fails_both_attempts_and_is_not_reused(tmp_path):
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [dict(body=GZ), dict(body=GZ)]})
    with pytest.raises(TransferFailed) as exc:
        fetch(ctx_for(t, clock), BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz', expected_md5='0' * 32)
    assert all('MD5 mismatch' in f for f in exc.value.detail['failures'])


def test_stall_and_timeout_consume_attempts(tmp_path):
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [dict(body=GZ, stall_at=64), dict(body=GZ, timeout_at=64)]})
    with pytest.raises(TransferFailed) as exc:
        fetch(ctx_for(t, clock), BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz')
    assert all('stalled' in f for f in exc.value.detail['failures'])


def test_deadline_stops_without_retry(tmp_path):
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [dict(body=GZ, per_read=200.0), dict(body=GZ)]})
    with pytest.raises(CapExceeded) as exc:
        fetch(ctx_for(t, clock, deadline=clock() + 500), BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz')
    assert exc.value.reason == 'time_cap' and len(t.calls) == 1


def test_periodic_volume_check_runs_every_60_seconds_and_can_stop(tmp_path):
    clock = Clock()
    checks = []
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [dict(body=GZ, per_read=25.0)]})
    fetch(ctx_for(t, clock, checks=checks), BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz')
    assert len(checks) >= 2 and all(b - a >= 60 for a, b in zip(checks, checks[1:], strict=False))

    def failing():
        raise VolumeCheckFailed('invented mount change')
    t2 = FakeTransport(clock, {('GET', BASE + 'b.xml.gz'): [dict(body=GZ, per_read=25.0)]})
    ctx = ctx_for(t2, clock)
    ctx.periodic_check = failing
    with pytest.raises(VolumeCheckFailed):
        fetch(ctx, BASE + 'b.xml.gz', sd(tmp_path), 'b.xml.gz')


def test_exclusive_creation_collision_stops(tmp_path):
    (tmp_path / 'a.xml.gz.attempt1').write_bytes(b'existing')
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [dict(body=GZ)]})
    with pytest.raises(SizingStop) as exc:
        fetch(ctx_for(t, clock), BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz')
    assert exc.value.reason == 'scratch_collision'
    assert (tmp_path / 'a.xml.gz.attempt1').read_bytes() == b'existing'


def test_unexpected_type_and_size_allowance_stop(tmp_path):
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [dict(body=b'<html>not gzip</html>')],
                              ('GET', BASE + 'desc.xml'): [dict(body=b'<x>' + b'y' * 500 + b'</x>')]})
    with pytest.raises(UnexpectedFile):
        fetch(ctx_for(t, clock), BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz')
    with pytest.raises(SizingStop) as exc:
        fetch(ctx_for(t, clock), BASE + 'desc.xml', sd(tmp_path), 'desc.xml', max_body=100)
    assert exc.value.reason == 'size_allowance'


def test_head_size_counts_bytes_and_handles_missing_length():
    clock = Clock()
    t = FakeTransport(clock, {('HEAD', BASE + 'desc.xml'): [dict(headers={'content-length': '12345'}, length=False),
                                                            dict(length=False)]})
    ctx = ctx_for(t, clock)
    assert head_size(ctx, BASE + 'desc.xml') == 12345
    assert head_size(ctx, BASE + 'desc.xml') is None
    assert ctx.budget.network_used == 400


def test_one_transfer_at_a_time(tmp_path):
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + f'{i}.xml.gz'): [dict(body=GZ)] for i in range(3)})
    ctx = ctx_for(t, clock)
    for i in range(3):
        fetch(ctx, BASE + f'{i}.xml.gz', sd(tmp_path), f'{i}.xml.gz')
    assert t.max_open == 1 and t.open == 0


def test_live_transport_refuses_unsigned_origin_before_any_socket():
    transport = HttpsTransport(Origins([BASE]), 'PROWL-capstone-sizing/1')
    with pytest.raises(UnexpectedFile):
        transport.request('GET', 'https://elsewhere.invalid/x', 5)
    with pytest.raises(UnexpectedFile):
        transport.request('GET', 'ftp://nlm.invalid/x', 5)


def test_connection_error_consumes_attempt(tmp_path):
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [ConnectionResetError('invented'), dict(body=GZ)]})
    r = fetch(ctx_for(t, clock), BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz')
    assert r['attempt'] == 2


def test_header_reserve_constant():
    assert HEADER_RESERVE == 64 * KIB


def test_bad_content_length_and_http_protocol_errors_consume_attempts(tmp_path):
    import http.client
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [http.client.BadStatusLine('invented'), dict(body=GZ)],
                              ('HEAD', BASE + 'm.xml'): [dict(headers={'content-length': '\u00b2'}, length=False)]})
    ctx = ctx_for(t, clock)
    assert fetch(ctx, BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz')['attempt'] == 2
    assert head_size(ctx, BASE + 'm.xml') is None
    assert content_length({'content-length': ' 12 '}) == 12 and content_length({'content-length': '1e3'}) is None


def test_redirect_body_read_error_consumes_attempt(tmp_path):
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [
        dict(status=302, body=b'xxxx', headers={'location': BASE + 'a.xml.gz'}, timeout_at=0), dict(body=GZ)]})
    assert fetch(ctx_for(t, clock), BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz')['attempt'] == 2


def test_oversized_headers_are_charged_then_stop(tmp_path):
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [dict(body=GZ, header_bytes=HEADER_RESERVE + 1)]})
    ctx = ctx_for(t, clock)
    with pytest.raises(UnexpectedFile):
        fetch(ctx, BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz')
    assert ctx.budget.network_used == HEADER_RESERVE + 1


def test_scratch_write_failure_stops_the_run(tmp_path, monkeypatch):
    import src.retrieval.sizing_v1.transfer as T
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [dict(body=GZ)]})

    def failing_write(fh, data, path):  # noqa: ARG001
        raise SizingStop('invented disk full', reason='scratch_write_failed')
    monkeypatch.setattr(T, '_write', failing_write)
    with pytest.raises(SizingStop) as exc:
        fetch(ctx_for(t, clock), BASE + 'a.xml.gz', sd(tmp_path), 'a.xml.gz')
    assert exc.value.reason == 'scratch_write_failed'


def test_origin_default_port_is_normalised():
    o = Origins([BASE])
    assert o.check('https://nlm.invalid:443/pubmed/x') and o.check('https://NLM.invalid/other/')
    with pytest.raises(UnexpectedFile):
        o.check('https://nlm.invalid:8443/pubmed/x')
    with pytest.raises(UnexpectedFile):
        o.check('https://user:pw@nlm.invalid/pubmed/x')


class _Watch:
    def __init__(self):
        self.arms, self.tripped, self.stopped = 0, False, False

    def arm(self):
        self.arms += 1

    def stop(self):
        self.stopped = True


class _Raw:
    status, reason = 200, 'OK'

    def __init__(self):
        self.read1_calls, self.read_calls = [], 0

    def getheaders(self):
        return [('Content-Length', '3')]

    def read1(self, n):
        self.read1_calls.append(n)
        return b'abc'

    def read(self, n=None):
        self.read_calls += 1
        return b''

    def close(self):
        pass


class _Conn:
    sock = None             # http.client drops conn.sock for Connection: close responses

    def close(self):
        pass


def test_live_response_arms_the_watch_before_every_single_receive_read():
    raw, watch = _Raw(), _Watch()
    resp = HttpResponse(_Conn(), raw, watch)
    assert resp.read(1 << 20) == b'abc' and resp.read(10) == b'abc'
    assert raw.read1_calls == [1 << 20, 10] and raw.read_calls == 0 and watch.arms == 2
    assert resp.header_bytes == len(b'HTTP/1.1 200 OK\r\n') + len('Content-Length') + 1 + 4 + 2
    resp.close()
    assert watch.stopped


def _serve(sock, chunks, gap):
    import threading
    import time as _t

    def run():
        try:
            for c in chunks:
                sock.sendall(c)
                _t.sleep(gap)
        except OSError:
            pass
    th = threading.Thread(target=run, daemon=True)
    th.start()
    return th


def test_socket_watch_bounds_header_phase_trickle_on_a_real_http_response():
    import http.client
    import time as _t
    from src.retrieval.sizing_v1.transfer import SocketWatch
    a, b = socket.socketpair()
    try:
        _serve(b, [b'HTTP/1.1 200 OK\r\n'] + [b'X'] * 200, 0.05)     # header line never completes
        watch = SocketWatch(lambda: 0.4, poll=0.05)
        watch.start(a)
        a.settimeout(None)            # per-receive timeouts alone would not bound this loop
        resp = http.client.HTTPResponse(a)
        t0 = _t.monotonic()
        try:
            resp.begin()          # may raise, or see a premature end of headers after shutdown
        except (OSError, http.client.HTTPException, ValueError):
            pass
        # HttpsTransport.request raises TimeoutError whenever the watch tripped in this phase
        assert watch.tripped and _t.monotonic() - t0 < 6.0      # 0.4 s limit; margin covers CPU load
    finally:
        a.close()
        b.close()


def test_socket_watch_enforces_deadline_on_connection_close_body_trickle():
    import http.client
    import time as _t
    from src.retrieval.sizing_v1.transfer import SocketWatch
    a, b = socket.socketpair()
    try:
        _serve(b, [b'HTTP/1.1 200 OK\r\nConnection: close\r\n\r\n'] + [b'y'] * 400, 0.05)
        deadline = _t.monotonic() + 1.0
        watch = SocketWatch(lambda: max(0.05, deadline - _t.monotonic()), poll=0.05)
        watch.start(a)
        raw = http.client.HTTPResponse(a)
        raw.begin()
        resp = HttpResponse(_Conn(), raw, watch)
        got = 0
        with pytest.raises(TimeoutError):
            while True:
                data = resp.read(1 << 20)
                if not data:
                    break
                got += len(data)
        assert got > 0 and _t.monotonic() < deadline + 5.0     # watch or per-receive timeout; margin covers CPU load
    finally:
        a.close()
        b.close()


def test_context_timeout_is_stall_or_time_left():
    clock = Clock()
    ctx = ctx_for(FakeTransport(clock, {}), clock, deadline=clock() + 100)
    assert ctx.timeout() == 100.0
    clock.t += 99.5
    assert ctx.timeout() == 1.0
    ctx2 = ctx_for(FakeTransport(clock, {}), clock)
    assert ctx2.timeout() == 300.0


class _SlowSocket:
    made = []

    def __init__(self, family, type_, proto):
        self.timeout = None
        _SlowSocket.made.append(self)

    def settimeout(self, value):
        self.timeout = value

    def connect(self, addr):
        import time as _t
        _t.sleep(min(self.timeout, 0.3))
        raise socket.timeout('invented unanswered address')

    def close(self):
        pass


def test_connect_shares_one_budget_across_addresses():
    import time as _t
    _SlowSocket.made = []
    addrs = [(socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.0.2.1', 443)),
             (socket.AF_INET6, socket.SOCK_STREAM, 6, '', ('2001:db8::1', 443, 0, 0)),
             (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.0.2.2', 443))]
    tr = HttpsTransport(Origins([BASE]), 'ua', socket_factory=_SlowSocket, resolver=lambda *a: addrs)
    t0 = _t.monotonic()
    with pytest.raises(TimeoutError):
        tr.connect('nlm.invalid', 443, 0.5)
    assert _t.monotonic() - t0 < 0.9
    assert all(s.timeout <= 0.5 for s in _SlowSocket.made) and len(_SlowSocket.made) <= 2


def test_name_resolution_is_bounded_by_the_budget():
    import time as _t

    def slow_resolver(*a):
        _t.sleep(2)
        return []
    tr = HttpsTransport(Origins([BASE]), 'ua', resolver=slow_resolver)
    t0 = _t.monotonic()
    with pytest.raises(TimeoutError):
        tr.connect('nlm.invalid', 443, 0.2)
    assert _t.monotonic() - t0 < 1.0


def test_watch_never_shuts_down_after_stop():
    from src.retrieval.sizing_v1.transfer import SocketWatch
    a, b = socket.socketpair()
    try:
        watch = SocketWatch(lambda: 0.05, poll=0.01)
        watch.start(a)
        watch.stop()
        import time as _t
        _t.sleep(0.2)
        assert not watch.tripped
        b.sendall(b'ok')
        assert a.recv(2) == b'ok'
    finally:
        a.close()
        b.close()


def test_fetch_refuses_a_plain_path_target(tmp_path):
    clock = Clock()
    t = FakeTransport(clock, {('GET', BASE + 'a.xml.gz'): [dict(body=GZ)]})
    with pytest.raises(TypeError):
        fetch(ctx_for(t, clock), BASE + 'a.xml.gz', str(tmp_path), 'a.xml.gz')
    assert t.calls == []
