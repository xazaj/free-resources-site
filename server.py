#!/usr/bin/env python3
"""Static file server for the free-resources site. Stdlib only.

Serves public/ on 0.0.0.0:$PORT (default 8000). No database, no template
rendering per request, no external network calls: every request is a
plain file read, which is the cheapest possible shape for the Uppcoder
Spark free tier (500 CPU-seconds/day/stack).
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
    port = int(os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("0.0.0.0", port), Handler)
    print(f"free-resources site serving {PUBLIC} on 0.0.0.0:{port}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()
