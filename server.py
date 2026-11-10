#!/usr/bin/env python3
"""Static file server for the free-resources site. Stdlib only.

Serves public/ on 127.0.0.1:8000 — the address Uppcoder's proxy forwards to
(see the Flask guide: apps start as `python app.py` and listen on
127.0.0.1:8000). No database, no template rendering per request, no external
network calls: every request is a plain file read, which is the cheapest
possible shape for the Uppcoder Spark free tier (500 CPU-seconds/day/stack).
"""
import os
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

ROOT = os.path.dirname(os.path.abspath(__file__))
PUBLIC = os.path.join(ROOT, "public")


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PUBLIC, **kwargs)

    def log_message(self, fmt, *args):  # keep logs quiet
        pass

    def end_headers(self):
        # Short cache for HTML (data refreshes daily), longer for assets.
        if self.path.endswith((".css", ".js")):
            self.send_header("Cache-Control", "public, max-age=3600")
        else:
            self.send_header("Cache-Control", "public, max-age=300")
        super().end_headers()


def main():
    # Uppcoder's documented contract for Python apps (Flask guide):
    # the app is started as `python app.py` and must listen on
    # 127.0.0.1:8000 — the platform proxy forwards to that address.
    # Do NOT bind 0.0.0.0:$PORT: the proxy does not read $PORT, and the
    # Flask starter hardcodes 127.0.0.1:8000 the same way.
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print(f"free-resources site serving {PUBLIC} on 127.0.0.1:8000", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
