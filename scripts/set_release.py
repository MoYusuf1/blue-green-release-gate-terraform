#!/usr/bin/env python3
"""Edit terraform/lab.auto.tfvars.json. Never runs Terraform and never touches the release check's expectation.

Examples:
  set_release.py green --version v2-bad --quote-total 999
  set_release.py green --activate
"""
import argparse
import json
import sys
from pathlib import Path

TFVARS = Path(__file__).resolve().parent.parent / "terraform" / "lab.auto.tfvars.json"


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("color", choices=["blue", "green"])
    parser.add_argument("--version")
    parser.add_argument("--quote-total", type=int)
    parser.add_argument("--ready", choices=["true", "false"])
    parser.add_argument("--activate", action="store_true", help="make this color receive live traffic")
    args = parser.parse_args()

    if not TFVARS.exists():
        sys.exit(f"{TFVARS} not found. Copy lab.auto.tfvars.example.json to it first.")
    if args.quote_total is not None and args.quote_total < 0:
        sys.exit("--quote-total must be zero or more")

    data = json.loads(TFVARS.read_text())
    release = data["releases"][args.color]
    if args.version:
        release["version"] = args.version
    if args.quote_total is not None:
        release["quote_total"] = args.quote_total
    if args.ready:
        release["ready"] = args.ready == "true"
    if args.activate:
        data["active_color"] = args.color

    TFVARS.write_text(json.dumps(data, indent=2) + "\n")
    print(f"active_color={data['active_color']}  {args.color}={json.dumps(release)}")
    print("Next: terraform plan, review it, then apply.")


if __name__ == "__main__":
    main()
