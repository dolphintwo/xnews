import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
from core.config import CACHE_DIR

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
HOUR_RE = re.compile(r"^\d{2}$")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
HTML_PATH = os.path.join(BASE_DIR, "view_reports.html")


def load_index_html():
    with open(HTML_PATH, "r", encoding="utf-8") as f:
        return f.read()

def _safe_report_paths(date: str, hour: str):
    if not DATE_RE.match(date):
        return None, None
    if not HOUR_RE.match(hour):
        return None, None

    day_dir = os.path.join(CACHE_DIR, date)
    json_path = os.path.join(day_dir, f"{hour}.json")
    md_path = os.path.join(day_dir, f"{hour}.md")
    return json_path, md_path


def list_reports():
    reports = []
    if not os.path.exists(CACHE_DIR):
        return reports

    for day in os.listdir(CACHE_DIR):
        day_dir = os.path.join(CACHE_DIR, day)
        if not os.path.isdir(day_dir):
            continue
        if not DATE_RE.match(day):
            continue

        hour_map = {}
        for name in os.listdir(day_dir):
            if not (name.endswith(".json") or name.endswith(".md")):
                continue
            stem, ext = os.path.splitext(name)
            if not HOUR_RE.match(stem):
                continue
            info = hour_map.setdefault(stem, {"date": day, "hour": stem, "has_json": False, "has_md": False})
            if ext == ".json":
                info["has_json"] = True
            elif ext == ".md":
                info["has_md"] = True

        reports.extend(hour_map.values())

    reports.sort(key=lambda x: (x["date"], x["hour"]), reverse=True)
    return reports


def load_report(date: str, hour: str):
    json_path, md_path = _safe_report_paths(date, hour)
    if not json_path:
        return {"error": "invalid params"}

    json_data = None
    markdown = ""

    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            json_data = json.load(f)

    if os.path.exists(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            markdown = f.read()

    return {
        "date": date,
        "hour": hour,
        "json_data": json_data,
        "markdown": markdown
    }


class ReportHandler(BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _send_html(self, html: str, status=200):
        body = html.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/":
            self._send_html(load_index_html())
            return

        if parsed.path == "/api/reports":
            self._send_json({"reports": list_reports()})
            return

        if parsed.path == "/api/report":
            params = parse_qs(parsed.query)
            date = (params.get("date") or [""])[0]
            hour = (params.get("hour") or [""])[0]
            payload = load_report(date, hour)
            if payload.get("error"):
                self._send_json(payload, status=400)
                return
            self._send_json(payload)
            return

        self._send_json({"error": "not found"}, status=404)

    def log_message(self, format, *args):
        return


def run_server(port: int = 8000):
    server = ThreadingHTTPServer(("127.0.0.1", port), ReportHandler)
    print(f"Report viewer running at http://127.0.0.1:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    run_server(8000)
