#!/usr/bin/env python3
"""Local viewer for this repo's implementation_plans/ tree.

Renders each plan's markdown into the styled reading format (see
plan_renderer.py) with a sidebar listing recent plans and a table of
contents. No product/board logic; this only serves rendered plans and raw
static files from the repo root.
"""
from __future__ import annotations

import html
import sys
import urllib.parse
from datetime import date
from http import HTTPStatus
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from plan_renderer import render_plan_html  # noqa: E402


ROOT = Path(__file__).resolve().parent.parent
PLANS_DIR = (ROOT / "implementation_plans").resolve()


class PlanViewerHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        if self.path in ("/", ""):
            self.send_response(HTTPStatus.FOUND)
            self.send_header("Location", "/plans")
            self.end_headers()
            return
        if self.path == "/plans" or self.path == "/plans/":
            self._serve_plan_index()
            return
        if self.path.startswith("/plan/"):
            self._serve_plan(self.path[len("/plan/"):])
            return
        super().do_GET()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    SIDEBAR_RECENT_COUNT = 30

    @staticmethod
    def _collect_plans() -> list[dict]:
        plans = sorted(
            PLANS_DIR.rglob("*.md"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
        out = []
        for path in plans:
            rel = path.relative_to(PLANS_DIR).as_posix()
            out.append({
                "rel": rel,
                "mtime": date.fromtimestamp(path.stat().st_mtime).isoformat(),
                "href": "/plan/" + urllib.parse.quote(rel),
            })
        return out

    def _build_sidebar_html(self, active_rel: str) -> str:
        plans = self._collect_plans()
        recent = plans[: self.SIDEBAR_RECENT_COUNT]
        remaining = len(plans) - len(recent)

        rows = []
        for entry in recent:
            is_active = entry["rel"] == active_rel
            cls = "plan-link active" if is_active else "plan-link"
            aria = ' aria-current="page"' if is_active else ""
            rows.append(
                f'<a class="{cls}" href="{entry["href"]}"{aria}>'
                f'<span class="plan-link-date">{entry["mtime"]}</span>'
                f'<span class="plan-link-name">{html.escape(entry["rel"])}</span>'
                f"</a>"
            )

        more_link = ""
        if remaining > 0:
            more_link = f'<a class="sidebar-more" href="/plans">+{remaining} more &mdash; view all plans</a>'

        return (
            '<div class="sidebar-section"><a class="sidebar-home" href="/plans">All plans</a></div>'
            '<div class="sidebar-section"><div class="sidebar-title">Recent plans</div>'
            f'{"".join(rows)}{more_link}</div>'
        )

    def _serve_plan(self, raw_rel_path: str):
        rel_path = urllib.parse.unquote(raw_rel_path)
        if not rel_path.endswith(".md"):
            self.send_error(HTTPStatus.BAD_REQUEST, "Only .md plan files can be rendered")
            return

        candidate = (PLANS_DIR / rel_path).resolve()
        try:
            candidate.relative_to(PLANS_DIR)
        except ValueError:
            self.send_error(HTTPStatus.FORBIDDEN, "Path escapes implementation_plans directory")
            return

        if not candidate.is_file():
            self.send_error(HTTPStatus.NOT_FOUND, f"No plan at {rel_path}")
            return

        try:
            md_text = candidate.read_text(encoding="utf-8")
            source_label = f"implementation_plans/{rel_path}"
            sidebar_html = self._build_sidebar_html(rel_path)
            body = render_plan_html(md_text, source_label, sidebar_html=sidebar_html).encode("utf-8")
        except Exception as exc:
            self.send_error(HTTPStatus.INTERNAL_SERVER_ERROR, f"Failed to render plan: {exc}")
            return

        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_plan_index(self):
        rows = []
        for entry in self._collect_plans():
            rows.append(
                f'<li><a href="{entry["href"]}">{html.escape(entry["rel"])}</a> '
                f'<span class="d">{entry["mtime"]}</span></li>'
            )
        body = f"""<!doctype html>
<html><head><meta charset="utf-8"><title>Implementation Plans</title>
<style>
body{{font:14px -apple-system,sans-serif;background:#0b100e;color:#e7efea;padding:24px;}}
h1{{font-size:1.3rem;}}
ul{{list-style:none;padding:0;max-width:900px;}}
li{{display:flex;justify-content:space-between;gap:1rem;padding:0.5rem 0;border-bottom:1px solid #22302a;}}
a{{color:#7fe9b7;text-decoration:none;}}
a:hover{{text-decoration:underline;}}
.d{{color:#9cada4;font-family:ui-monospace,monospace;font-size:0.85rem;white-space:nowrap;}}
</style></head><body>
<h1>Implementation plans</h1>
<ul>{''.join(rows)}</ul>
</body></html>"""
        encoded = body.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)


def main() -> int:
    port = 8765
    if len(sys.argv) > 1:
        port = int(sys.argv[1])

    if not PLANS_DIR.is_dir():
        print(f"warning: {PLANS_DIR} does not exist yet; the plan index will be empty", file=sys.stderr)

    server = ThreadingHTTPServer(("127.0.0.1", port), PlanViewerHandler)
    print(f"Implementation plan viewer running at http://127.0.0.1:{port}/plans")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down.")
    finally:
        server.server_close()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
