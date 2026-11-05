#!/usr/bin/env python3
"""Activate the proxy config Terraform wrote: syntax check, graceful reload, then wait until live traffic
actually reaches the configured color.

A reload is asynchronous: NGINX starts new workers while old ones finish, so a request sent right after
the reload can still reach the previous release. This waits (up to 15 s) instead of reporting success early.
It still does not replace the release check: run check_release.py against the live URL afterwards.
"""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

CONTAINER = "mo-bg-proxy"
LIVE = "http://127.0.0.1:8080/"
TFVARS = Path(__file__).resolve().parent.parent / "terraform" / "lab.auto.tfvars.json"


def run(*cmd):
    result = subprocess.run(["docker", "exec", CONTAINER, *cmd], capture_output=True, text=True)
    print((result.stdout + result.stderr).strip())
    return result.returncode


def live_color(url):
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            return json.loads(resp.read()).get("color")
    except (OSError, ValueError):
        return None


def wait_for_color(url, color, seconds=15, sleep=time.sleep):
    """Return the color live traffic reached: `color` once it is served, else the last color seen."""
    seen = None
    for _ in range(seconds * 2):
        seen = live_color(url)
        if seen == color:
            return seen
        sleep(0.5)
    return seen


def main():
    expected = json.loads(TFVARS.read_text())["active_color"]
    if run("nginx", "-t") != 0:
        sys.exit("Config test failed; NGINX is still running its previous config. Not reloading.")
    if run("nginx", "-s", "reload") != 0:
        sys.exit("Reload failed. Check: docker logs mo-bg-proxy")
    seen = wait_for_color(LIVE, expected)
    if seen != expected:
        sys.exit(f"Live traffic still reaches {seen!r}, not {expected!r}, after 15 s. Check: docker logs mo-bg-proxy")
    print(f"Live traffic now reaches {expected}. Verify it with check_release.py --url http://127.0.0.1:8080")


if __name__ == "__main__":
    main()
