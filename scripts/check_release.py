#!/usr/bin/env python3
"""Release gate: is this release answering, is it the expected release, and is its result correct?

Usage: check_release.py COLOR VERSION [--url URL]   (default URL is the preview port)
Exit 0 on PASS, 1 on FAIL.
"""
import argparse
import json
import sys
import urllib.error
import urllib.request

# Fixed on purpose: never read from the app's configuration, so a bad config cannot also change the expectation.
EXPECTED_TOTAL_CENTS = 1200


def get_json(url):
    try:
        with urllib.request.urlopen(url, timeout=3) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as err:
        return err.code, None
    except (urllib.error.URLError, OSError, ValueError) as err:
        return None, str(err)


def check(base_url, color, version):
    """Return a list of failure reasons; empty means PASS."""
    failures = []
    identity = {"color": color, "version": version}

    status, body = get_json(f"{base_url}/health")
    if status != 200 or not isinstance(body, dict):
        failures.append(f"/health: expected 200 JSON, got {status} {body!r}")
    else:
        if not body.get("ready"):
            failures.append("/health: ready is not true")
        for key, want in identity.items():
            if body.get(key) != want:
                failures.append(f"/health: {key}={body.get(key)!r}, expected {want!r}")

    status, body = get_json(f"{base_url}/quote")
    if status != 200 or not isinstance(body, dict):
        failures.append(f"/quote: expected 200 JSON, got {status} {body!r}")
    else:
        for key, want in identity.items():
            if body.get(key) != want:
                failures.append(f"/quote: {key}={body.get(key)!r}, expected {want!r}")
        total = body.get("total_cents")
        # bool is an int subclass in Python; reject it explicitly.
        if not isinstance(total, int) or isinstance(total, bool) or total != EXPECTED_TOTAL_CENTS:
            failures.append(f"/quote: total_cents={total!r}, expected {EXPECTED_TOTAL_CENTS}")

    return failures


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("color", choices=["blue", "green"])
    parser.add_argument("version")
    parser.add_argument("--url", default="http://127.0.0.1:8081")
    args = parser.parse_args()

    failures = check(args.url.rstrip("/"), args.color, args.version)
    label = f"{args.color} {args.version} at {args.url}"
    if failures:
        print(f"FAIL {label}")
        for reason in failures:
            print(f"  - {reason}")
        return 1
    print(f"PASS {label}: healthy, identity matches, total_cents={EXPECTED_TOTAL_CENTS}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
