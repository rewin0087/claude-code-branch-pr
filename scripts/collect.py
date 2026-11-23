#!/usr/bin/env python3
"""Collect the current branch's changes for /branch-pr: writes .branch-pr/context.json and diff.patch.

  python3 collect.py [--repo DIR] [--base BRANCH] [--committed-only] [--template FILE | --no-template]
                     [--platform github|gitlab|bitbucket|azure] [--json]
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prkit.collect.collector import Collector  # noqa: E402
from prkit.collect.digest import CollectDigest  # noqa: E402
from prkit.collect.options import CollectOptions  # noqa: E402
from prkit.core.errors import PRError  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--repo", default=".", help="repository directory (default: current)")
    ap.add_argument("--base", help="base branch (default: auto-detected main/master/develop/...)")
    ap.add_argument("--committed-only", action="store_true", help="ignore uncommitted and untracked changes")
    ap.add_argument("--template", help="PR/MR template file to fill (default: the repo's own, if any)")
    ap.add_argument("--no-template", action="store_true", help="ignore the repo's template; use the default layout")
    ap.add_argument("--platform", choices=["github", "gitlab", "bitbucket", "azure"], help="override the detected host")
    ap.add_argument("--json", action="store_true", help="print context.json instead of the digest")
    a = ap.parse_args()
    try:
        ctx = Collector(CollectOptions(a.repo, a.base, a.committed_only, a.template, a.no_template, a.platform)).run()
    except PRError as e:
        print("ERROR: %s" % e, file=sys.stderr)
        return 2
    print(json.dumps(ctx, indent=1) if a.json else CollectDigest(ctx).format())
    return 0


if __name__ == "__main__":
    sys.exit(main())
