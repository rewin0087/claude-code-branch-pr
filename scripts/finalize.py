#!/usr/bin/env python3
"""Check the written .branch-pr/PR_TITLE.txt + PR_DESCRIPTION.md and optionally copy the description.

  python3 finalize.py [--repo DIR] [--copy] [--draft] [--json]

Exit code 1 when the description has errors (missing sections, secret-looking values, too long).
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prkit.errors import PRError  # noqa: E402
from prkit.finalizer import FinalizeDigest, FinalizeOptions, Finalizer  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="repository directory (default: current)")
    ap.add_argument("--copy", action="store_true", help="copy the description to the clipboard when it passes")
    ap.add_argument("--no-copy", dest="copy", action="store_false", help="don't copy (the default)")
    ap.add_argument("--draft", action="store_true", help="make the suggested create command open a draft")
    ap.add_argument("--json", action="store_true", help="print the result as JSON")
    a = ap.parse_args()
    try:
        r = Finalizer(FinalizeOptions(a.repo, a.copy, a.draft)).run()
    except PRError as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2
    print(json.dumps(r, indent=1) if a.json else FinalizeDigest(r).format())
    return 0 if r["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
