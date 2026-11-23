"""Finalizer: checks the written title + description, copies the description, builds the create command."""
import os

from ..collect.outputdir import OutputDir
from ..collect.repository import Repository
from ..core.clipboard import Clipboard
from ..core.jsonio import JsonFile
from ..description.checker import DescriptionChecker
from ..hosting.commands import CreateCommand
from ..hosting.platform import HostingPlatform
from .written import WrittenDescription


class Finalizer(object):
    def __init__(self, options):
        self.opt = options
        out = OutputDir(Repository.open(options.repo).cwd)
        self.ctx = JsonFile.load(out.file("context"), "context.json (run collect.py first)")

    def run(self):
        p, pf = self.ctx["paths"], self.ctx["platform"]
        title, body = WrittenDescription(p["title"], p["description"]).load()
        chk = DescriptionChecker(title, body, pf["limit"], bool(self.ctx.get("template"))).check()
        copied = Clipboard.copy(body) if self.opt.copy and chk.ok else None
        return {"ok": chk.ok, "errors": chk.errors, "warnings": chk.warnings, "stats": chk.stats(), "title": title,
                "copied_with": copied, "copy_requested": self.opt.copy, "create_command": self._create_command(pf),
                "description_path": p["description"], "title_path": p["title"], "platform": pf}

    def _create_command(self, pf):
        if not self.ctx["base"]:
            return None
        return CreateCommand(HostingPlatform.from_dict(pf)).build(
            self.ctx["base"], self.ctx["branch"], OutputDir.relative("description"), OutputDir.relative("title"), self.opt.draft)
