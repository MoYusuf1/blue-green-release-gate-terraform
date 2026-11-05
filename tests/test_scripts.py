"""Self-test for the release check and probe against a stub server. Run: python3 tests/test_scripts.py"""
import json
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import check_release  # noqa: E402
import probe  # noqa: E402
import reload_proxy  # noqa: E402

STATE = {"version": "v2", "total": 1200, "health": 200}


class Stub(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            code, body = STATE["health"], {"color": "green", "version": STATE["version"], "ready": True}
        else:
            code, body = 200, {"color": "green", "version": STATE["version"], "total_cents": STATE["total"]}
        self.send_response(code)
        self.end_headers()
        self.wfile.write(json.dumps(body).encode())

    def log_message(self, *_):
        pass


server = HTTPServer(("127.0.0.1", 0), Stub)
threading.Thread(target=server.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{server.server_port}"

assert check_release.check(url, "green", "v2") == []
STATE["total"] = 999  # healthy but wrong
fails = check_release.check(url, "green", "v2")
assert len(fails) == 1 and "total_cents=999" in fails[0], fails
assert check_release.check(url, "blue", "v2")  # wrong identity
STATE.update(total=1200, health=503)
assert check_release.check(url, "green", "v2")
assert check_release.check("http://127.0.0.1:1", "green", "v2")  # nothing listening

STATE.update(health=200, total=999)
bad = probe.sample(f"{url}/quote", 1200)
assert not bad["ok"] and bad["reason"] == "wrong_total", bad
STATE["total"] = 1200
good = probe.sample(f"{url}/quote", 1200)
dead = probe.sample("http://127.0.0.1:1/quote", 1200)
s = probe.summarize([good, bad, dead])
assert (s["samples"], s["failed"], s["wrong_total"], s["http_or_connection"]) == (3, 2, 1, 1), s

# The reload waits until live traffic serves the configured color, and reports the color it saw if it never does.
naps = []
assert reload_proxy.wait_for_color(url, "green", sleep=naps.append) == "green" and naps == []
assert reload_proxy.wait_for_color(url, "blue", seconds=2, sleep=naps.append) == "green" and len(naps) == 4
assert reload_proxy.wait_for_color("http://127.0.0.1:1/", "blue", seconds=1, sleep=naps.append) is None

server.shutdown()
print("all script checks passed")
