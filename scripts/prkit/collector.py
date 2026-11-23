"""Collector: everything /branch-pr needs to write the description, gathered into the output folder.

  .branch-pr/context.json   branch, base, commits, ticket ids, files (kind, +/-, diff.patch line),
                            caveat signals, the repo's PR/MR template, the hosting platform
  .branch-pr/diff.patch     the branch diff, reviewable files first, lockfiles left out

  CollectOptions   the CLI flags
  Collector        runs git, builds the ChangeSet and signals, writes both files
"""
import os

from .changeset import ChangeSet
from .conventional import TitleHints
from .errors import PRError
from .gitcmd import Git
from .jsonio import JsonFile
from .platform import HostingPlatform
from .signals import CaveatSignals
from .templates import TemplateFinder
from .ticket import TicketRefs

OUT_DIR = ".branch-pr"


class CollectOptions(object):
    def __init__(self, repo=".", base=None, committed_only=False, template=None, no_template=False, platform=None):
        self.repo, self.base, self.committed_only = repo, base, committed_only
        self.template, self.no_template, self.platform = template, no_template, platform


class Collector(object):
    def __init__(self, options):
        self.opt = options
        self.git = Git(os.path.abspath(options.repo))
        root = self.git.root()
        if not root:
            raise PRError("%s is not inside a git repository" % os.path.abspath(options.repo))
        self.git = Git(root)
        self.root, self.out = root, os.path.join(root, OUT_DIR)

    def run(self):
        git = self.git
        branch = git.branch() or "HEAD"
        base, since = self._base(branch)
        uncommitted = not self.opt.committed_only
        commits = git.commits(since) if since and base else []
        cs = ChangeSet(git, since, uncommitted).load()
        if not cs.files:
            raise PRError("No changes found on '%s'%s. Nothing to describe." % (
                branch, " compared with %s" % base if base else ""))
        os.makedirs(self.out, exist_ok=True)
        git.ensure_ignored(OUT_DIR + "/")
        patch_path = os.path.join(self.out, "diff.patch")
        patch_lines = cs.write_patch(patch_path)
        with open(patch_path, errors="replace") as fh:
            signals = CaveatSignals(cs, fh.read()).scan()
        platform = HostingPlatform.from_remote(git.remote_url(), self.opt.platform)
        template = None if self.opt.no_template else TemplateFinder(self.root).find(self.opt.template)
        dirty = bool(git.run(["status", "--porcelain"], check=False).strip())
        ctx = {
            "repo": os.path.basename(self.root), "branch": branch, "head": git.head_sha(),
            "base": base, "merge_base": since if base else None,
            "includes_uncommitted": uncommitted and dirty, "on_base_branch": base is None,
            "commits": commits, "tickets": TicketRefs.find(branch, commits),
            "totals": dict(cs.totals(), patch_lines=patch_lines),
            "files": [f.as_dict() for f in cs.ordered()], "by_kind": cs.by_kind(),
            "signals": signals, "title_hints": TitleHints(commits, [f.as_dict() for f in cs.files], signals).build(),
            "platform": platform.as_dict(), "template": template,
            "paths": {"out": self.out, "context": os.path.join(self.out, "context.json"), "patch": patch_path,
                      "description": os.path.join(self.out, "PR_DESCRIPTION.md"),
                      "title": os.path.join(self.out, "PR_TITLE.txt")},
        }
        JsonFile.write(ctx["paths"]["context"], ctx)
        return ctx

    def _base(self, branch):
        """-> (base ref or None, commit to diff from). On the base branch: (None, HEAD) = uncommitted work only."""
        if self.opt.base:
            base = self.git.resolve_ref(self.opt.base)
            if not base:
                raise PRError("Base branch '%s' not found (locally or on origin)." % self.opt.base)
        else:
            base = self.git.detect_base(branch)
        if not base:
            if self.opt.committed_only:
                raise PRError("'%s' looks like the base branch itself: there are no branch commits to describe. "
                              "Pass the base branch explicitly, or drop --committed-only to describe uncommitted work." % branch)
            return None, "HEAD" if self.git.has_commits() else None
        return base, self.git.merge_base(base)
