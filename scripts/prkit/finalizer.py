"""Finalizer: reads the written title + description, checks them, optionally copies the description.

  FinalizeOptions   the CLI flags
  Finalizer         loads context.json and the two files, runs DescriptionChecker, copies, reports
"""
import os

from .checker import DescriptionChecker
from .clipboard import Clipboard
from .collector import OUT_DIR
from .errors import PRError
from .gitcmd import Git
from .jsonio import JsonFile
from .platform import HostingPlatform


class FinalizeOptions(object):
    def __init__(self, repo=".", copy=False, draft=False):
        self.repo, self.copy, self.draft = repo, copy, draft


class Finalizer(object):
    def __init__(self, options):
        self.opt = options
        root = Git(os.path.abspath(options.repo)).root()
        if not root:
            raise PRError("%s is not inside a git repository" % os.path.abspath(options.repo))
        self.ctx = JsonFile.load(os.path.join(root, OUT_DIR, "context.json"), "context.json (run collect.py first)")

    def run(self):
        p = self.ctx["paths"]
        body = self._read(p["description"], "PR_DESCRIPTION.md")
        title = self._read(p["title"], "PR_TITLE.txt").strip()
        body = body.strip() + "\n"
        with open(p["description"], "w") as fh:          # normalised: no leading/trailing blank lines
            fh.write(body)
        chk = DescriptionChecker(title, body, self.ctx["platform"]["limit"], bool(self.ctx.get("template"))).check()
        copied = Clipboard.copy(body) if self.opt.copy and chk.ok else None
        pf = self.ctx["platform"]
        plat = HostingPlatform(pf["name"], pf["noun"], pf["short"], pf["limit"], pf["web_url"])
        cmd = plat.create_command(self.ctx["base"], self.ctx["branch"], OUT_DIR + "/PR_DESCRIPTION.md",
                                  OUT_DIR + "/PR_TITLE.txt", self.opt.draft) if self.ctx["base"] else None
        return {"ok": chk.ok, "errors": chk.errors, "warnings": chk.warnings, "stats": chk.stats(), "title": title,
                "copied_with": copied, "copy_requested": self.opt.copy, "create_command": cmd,
                "description_path": p["description"], "title_path": p["title"], "platform": pf}

    @staticmethod
    def _read(path, label):
        if not os.path.exists(path):
            raise PRError("%s not found at %s: write it first" % (label, path))
        with open(path, errors="replace") as fh:
            return fh.read()


class FinalizeDigest(object):
    def __init__(self, result):
        self.r = result

    def format(self):
        r, L = self.r, []
        s = r["stats"]
        L.append("%s  %s: %d chars, %d lines, %d QA scenarios, sections: %s" % (
            "OK  " if r["ok"] else "FAIL", r["platform"]["short"], s["chars"], s["lines"], s["qa_items"], " | ".join(s["headings"])))
        L.extend("  ✗ " + e for e in r["errors"])
        L.extend("  ! " + w for w in r["warnings"])
        if r["copy_requested"]:
            L.append("COPIED  description copied to the clipboard (%s)" % r["copied_with"] if r["copied_with"]
                     else "COPIED  no (%s)" % ("fix the errors first" if not r["ok"] else "no clipboard tool found"))
        L.append("TITLE   " + r["title"])
        L.append("FILE    " + r["description_path"])
        if r["create_command"]:
            L.append("CREATE  (from the repo root) " + r["create_command"])
        return "\n".join(L)
