"""Explicitly invoked, short-lived HTTPS intake for one hash-pinned checkpoint.

Private JSON configuration contains bind/peer IP, port, token_sha256, expected
bytes/sha256, certificate/key paths, a fresh destination and receipt path.
The sender alone retains the bearer token. No tokens or HTTP headers are logged.
"""
import hashlib
import hmac
from http.server import BaseHTTPRequestHandler, HTTPServer
import ipaddress
import json
import os
from pathlib import Path
import re
import socket
import ssl
import threading
import time


def receive(config):
    c = config
    for key in ('bind', 'peer'):
        address = ipaddress.ip_address(c[key])
        if not address.is_private or address.is_unspecified:
            raise ValueError('Explicit private interface and peer required')
    for key in ('sha256', 'token_sha256'):
        if not re.fullmatch('[0-9a-f]{64}', c[key]):
            raise ValueError('Invalid digest')
    ttl = c.get('ttl_seconds', 300)
    if not 1 <= ttl <= 300 or not 1 <= c['bytes'] <= 256 * 1024**2:
        raise ValueError('Invalid transfer bounds')
    dest, receipt = Path(c['destination']), Path(c['receipt'])
    part = dest.with_name(dest.name + '.receiving')
    if any(p.exists() or p.is_symlink() for p in (dest, part, receipt)):
        raise ValueError('Fresh destination and receipt required')
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.minimum_version = ssl.TLSVersion.TLSv1_2
    context.load_cert_chain(c['certificate'], c['key'])
    deadline = time.monotonic() + ttl
    state = dict(status='expired', accepted_bytes=0, rejected_requests=0)
    active = set()
    lock = threading.Lock()

    class Server(HTTPServer):
        def get_request(self):
            raw, address = self.socket.accept()
            if address[0] != c['peer']:
                raw.close()
                raise OSError('Unadmitted peer')
            raw.settimeout(min(10, max(.01, deadline-time.monotonic())))
            wrapped = context.wrap_socket(raw, server_side=True, do_handshake_on_connect=False)
            with lock:
                active.add(wrapped)
            try:
                wrapped.do_handshake()
                return wrapped, address
            except BaseException:
                self.close_request(wrapped)
                raise

        def close_request(self, request):
            with lock:
                active.discard(request)
            super().close_request(request)

        def handle_error(self, request, client_address):
            state['rejected_requests'] += 1

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            auth = self.headers.get_all('Authorization', [])
            lengths = self.headers.get_all('Content-Length', [])
            valid_auth = (len(auth) == 1 and auth[0].startswith('Bearer ')
                          and hmac.compare_digest(hashlib.sha256(auth[0][7:].encode()).hexdigest(), c['token_sha256']))
            if (self.path != '/checkpoint' or not valid_auth or lengths != [str(c['bytes'])]
                    or self.headers.get('Transfer-Encoding') or time.monotonic() >= deadline):
                state['rejected_requests'] += 1
                self.send_error(403, 'Transfer rejected')
                return
            state['status'] = 'failed'
            h = hashlib.sha256()
            try:
                with part.open('xb') as f:
                    os.chmod(part, 0o600)
                    remaining = c['bytes']
                    while remaining:
                        self.connection.settimeout(min(10, max(.01, deadline-time.monotonic())))
                        if time.monotonic() >= deadline:
                            raise TimeoutError('Transfer expired')
                        chunk = self.rfile.read(min(1024**2, remaining))
                        if not chunk:
                            raise ValueError('Incomplete transfer')
                        f.write(chunk)
                        h.update(chunk)
                        remaining -= len(chunk)
                        state['accepted_bytes'] += len(chunk)
                    f.flush()
                    os.fsync(f.fileno())
                if not hmac.compare_digest(h.hexdigest(), c['sha256']):
                    raise ValueError('Checkpoint digest differs')
                os.link(part, dest)  # Atomic, fails rather than overwriting an existing file.
                state.update(status='verified', sha256=h.hexdigest())
                self.send_response(201)
                self.send_header('Content-Length', '0')
                self.end_headers()
            finally:
                # Only this receiver's fresh temporary file can be removed.
                if part.exists():
                    part.unlink()

    server = Server((c['bind'], c['port']), Handler)
    server.timeout = .25

    def expire():
        server.server_close()
        with lock:
            for conn in list(active):
                try:
                    conn.shutdown(socket.SHUT_RDWR)
                except OSError:
                    pass
                conn.close()

    timer = threading.Timer(ttl, expire)
    timer.daemon = True
    timer.start()
    started = time.monotonic()
    print('One-file TLS receiver ready; credentials are not logged.', flush=True)
    try:
        while state['status'] == 'expired' and time.monotonic() < deadline:
            try:
                server.handle_request()
            except (OSError, ValueError):
                if time.monotonic() < deadline:
                    raise
    finally:
        timer.cancel()
        expire()
        state['elapsed_seconds'] = time.monotonic() - started
        receipt.write_text(json.dumps(state, indent=2)+'\n')
    return state


if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', type=Path, required=True)
    result = receive(json.loads(p.parse_args().config.read_text()))
    print(json.dumps(result))
    raise SystemExit(0 if result['status'] == 'verified' else 1)
