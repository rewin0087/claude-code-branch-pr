"""Collector: everything /branch-pr needs to write the description, gathered into .branch-pr/.

  context.json   branch, base, commits, ticket ids, files (kind, +/-, diff.patch line), caveat
                 signals, title hints, the repo's PR/MR template, the hosting platform
  diff.patch     the branch diff, reviewable files first, lockfiles left out
"""
import os

from ..branch.base import BaseResolver
from ..branch.changeset import ChangeSet
from ..branch.patch import PatchWriter
from ..branch.tickets import TicketRefs
from ..core.errors import PRError
from ..core.jsonio import JsonFile
from ..hosting.platform import HostingPlatform
from ..hosting.templates import TemplateFinder
from ..signals.scanner import CaveatSignals
from ..title.hints import TitleHints
from .outputdir import OutputDir
from .repository import Repository


class Collector(object):
    def __init__(self, options):
        self.opt = options
        self.git = Repository.open(options.repo)
        self.root = self.git.cwd
        self.out = OutputDir(self.root)

    def run(self):
        git = self.git
        branch = git.branch() or "HEAD"
        base, since = BaseResolver(git, self.opt.base, self.opt.committed_only).resolve(branch)
        uncommitted = not self.opt.committed_only
        commits = git.commits(since) if since and base else []
        cs = ChangeSet(git, since, uncommitted).load()
        if not cs.files:
            raise PRError("No changes found on '%s'%s. Nothing to describe." % (
                branch, " compared with %s" % base if base else ""))
        self.out.create(git)
        patch_lines = PatchWriter(cs).write(self.out.file("patch"))
        signals = self._signals(cs)
        ctx = {
            "repo": os.path.basename(self.root), "branch": branch, "head": git.head_sha(),
            "base": base, "merge_base": since if base else None,
            "includes_uncommitted": uncommitted and git.is_dirty(), "on_base_branch": base is None,
            "commits": commits, "tickets": TicketRefs.find(branch, commits),
            "totals": dict(cs.totals(), patch_lines=patch_lines),
            "files": [f.as_dict() for f in cs.ordered()], "by_kind": cs.by_kind(),
            "signals": signals, "title_hints": TitleHints(commits, [f.as_dict() for f in cs.files], signals).build(),
            "platform": HostingPlatform.from_remote(git.remote_url(), self.opt.platform).as_dict(),
            "template": None if self.opt.no_template else TemplateFinder(self.root).find(self.opt.template),
            "paths": self.out.paths(),
        }
        JsonFile.write(self.out.file("context"), ctx)
        return ctx

    def _signals(self, cs):
        with open(self.out.file("patch"), errors="replace") as fh:
            return CaveatSignals(cs, fh.read()).scan()
