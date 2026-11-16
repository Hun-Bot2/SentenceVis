"""Local-only labeling tool for a SentenScope sample (private judgment text).

AI-assisted: written with Claude (Anthropic) in Claude Code, 2026-11-16.
See docs/records/ATTRIBUTION.md.

Usage:
    python3 scripts/annotate/label_server.py data/private/labeling/<sample> [--port 8765]
Then open http://127.0.0.1:8765/ . Binds to 127.0.0.1 only; never publish.
Labels are appended to <sample>/labels.jsonl (latest label per item wins);
nothing is overwritten. The reviewer name is entered in the page.
"""
from __future__ import annotations

import argparse
import json
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

PAGE = Path(__file__).with_name("label_tool.html")


def make_handler(sample: Path):
    items = [json.loads(x) for x in (sample / "items.jsonl").read_text().splitlines() if x.strip()]
    ids = {x["item_id"] for x in items}
    labels_path = sample / "labels.jsonl"

    class H(BaseHTTPRequestHandler):
        def _send(self, code: int, body: bytes, ctype: str) -> None:
            self.send_response(code)
            self.send_header("Content-Type", ctype)
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):  # noqa: N802
            if self.path == "/":
                self._send(200, PAGE.read_bytes(), "text/html; charset=utf-8")
            elif self.path == "/api/items":
                self._send(200, json.dumps(items, ensure_ascii=False).encode(), "application/json")
            elif self.path == "/api/labels":
                latest = {}
                if labels_path.exists():
                    for line in labels_path.read_text().splitlines():
                        rec = json.loads(line)
                        latest[rec["item_id"]] = rec
                self._send(200, json.dumps(latest, ensure_ascii=False).encode(), "application/json")
            else:
                self._send(404, b"not found", "text/plain")

        def do_POST(self):  # noqa: N802
            if self.path != "/api/label":
                return self._send(404, b"not found", "text/plain")
            rec = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            if rec.get("item_id") not in ids or not str(rec.get("reviewer", "")).strip():
                return self._send(400, b"unknown item or missing reviewer", "text/plain")
            rec["saved_at"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
            with labels_path.open("a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
            self._send(200, b'{"ok":true}', "application/json")

        def log_message(self, *args):
            pass

    return H


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("sample")
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()
    srv = ThreadingHTTPServer(("127.0.0.1", a.port), make_handler(Path(a.sample)))
    print(f"labeling http://127.0.0.1:{a.port}/  (Ctrl+C to stop)")
    srv.serve_forever()


if __name__ == "__main__":
    main()
