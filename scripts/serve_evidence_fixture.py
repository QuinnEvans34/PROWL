#!/usr/bin/env python3
"""Local, model-free fixture response API. Run explicitly; never starts inference."""
import argparse
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from socketserver import TCPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.retrieval.guided_fixture import ResponseStore, canonical

PREFIX = "/evidence-fixture/responses"


class LocalFixtureServer(ThreadingHTTPServer):
    def server_bind(self):
        # This loopback-only service does not need HTTPServer's reverse DNS lookup.
        TCPServer.server_bind(self)
        self.server_name = "localhost"
        self.server_port = self.server_address[1]


def handler_for(store):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_):
            pass  # Do not log request contents or paths.

        def reply(self, status, payload):
            body = canonical(payload)
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)

        def do_POST(self):
            if self.path != PREFIX:
                return self.reply(404, {"error": "Unknown route."})
            # No cross-origin writes; Vite forwards requests without changing Origin.
            origin = self.headers.get("Origin")
            if origin and origin not in {"http://localhost:5173", "http://127.0.0.1:5173", "http://127.0.0.1:5179"}:
                return self.reply(403, {"error": "Origin not allowed."})
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= 1024 or self.headers.get("Content-Type") != "application/json":
                    return self.reply(400, {"error": "Expected a small JSON request."})
                request = json.loads(self.rfile.read(length))
                result = store.save(request)
            except FileExistsError:
                return self.reply(409, {"error": "Request ID conflicts with an existing response."})
            except (ValueError, TypeError, KeyError, UnicodeError):
                return self.reply(400, {"error": "Request or saved response failed validation."})
            except OSError:
                return self.reply(503, {"error": "Response storage is unavailable; no save is confirmed."})
            self.reply(200, result)

        def do_GET(self):
            if self.path == "/evidence-fixture/health":
                return self.reply(200, {"mode": "synthetic-fixture"})
            if not self.path.startswith(PREFIX + "/"):
                return self.reply(404, {"error": "Unknown route."})
            try:
                result = store.read(self.path[len(PREFIX) + 1:])
            except FileNotFoundError:
                return self.reply(404, {"error": "Response not found."})
            except (ValueError, TypeError, KeyError, OSError):
                return self.reply(503, {"error": "Saved response could not be verified."})
            self.reply(200, result)
    return Handler


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output-dir", type=Path, default=Path("outputs/prowl/evidence-fixture/responses"))
    parser.add_argument("--port", type=int, default=8011)
    args = parser.parse_args()
    server = LocalFixtureServer(("127.0.0.1", args.port), handler_for(ResponseStore(args.output_dir)))
    print(f"Synthetic evidence API on 127.0.0.1:{args.port}; saving to {args.output_dir.resolve()}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
