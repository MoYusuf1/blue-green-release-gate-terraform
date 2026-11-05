#!/usr/bin/env python3
"""Sample a quote URL about once per second. HTTP failures AND wrong totals both count as failed.

stdout: one JSON line per sample, then a final {"summary": ...} line (redirect it to evidence/run.jsonl).
stderr: a short live line per sample, so you can watch it.
Stop early with Ctrl+C; the summary is still written.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone


def sample(url, expected):
    record = {"ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds")}
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            body = json.loads(resp.read())
            record.update(status=resp.status, version=body.get("version"), total_cents=body.get("total_cents"))
            record["ok"] = resp.status == 200 and body.get("total_cents") == expected
            if not record["ok"]:
                record["reason"] = "wrong_total"
    except urllib.error.HTTPError as err:
        record.update(status=err.code, ok=False, reason="http_error")
    except (urllib.error.URLError, OSError, ValueError) as err:
        record.update(status=None, ok=False, reason=f"error: {err}")
    return record


def summarize(records):
    failed = [r for r in records if not r["ok"]]
    return {
        "summary": True,
        "samples": len(records),
        "failed": len(failed),
        "wrong_total": sum(r.get("reason") == "wrong_total" for r in failed),
        "http_or_connection": sum(r.get("reason") != "wrong_total" for r in failed),
        "first_failure": failed[0]["ts"] if failed else None,
        "last_failure": failed[-1]["ts"] if failed else None,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("url")
    parser.add_argument("--seconds", type=int, default=600)
    parser.add_argument("--expected-total", type=int, default=1200)
    args = parser.parse_args()

    records = []
    deadline = time.monotonic() + args.seconds
    try:
        while time.monotonic() < deadline:
            r = sample(args.url, args.expected_total)
            records.append(r)
            print(json.dumps(r), flush=True)
            mark = "ok  " if r["ok"] else "FAIL"
            print(f"{r['ts'][11:23]} {mark} {r.get('status')} {r.get('version')} {r.get('total_cents')}", file=sys.stderr)
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    summary = summarize(records)
    print(json.dumps(summary), flush=True)
    print(f"SUMMARY {json.dumps(summary)}", file=sys.stderr)


if __name__ == "__main__":
    main()
