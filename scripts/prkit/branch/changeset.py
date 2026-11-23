"""ChangeSet: the files the branch changed (merge-base -> HEAD or the working tree, plus untracked files)."""
from .diffstat import DiffStatParser
from .kinds import ORDER
from .untracked import UntrackedFile


class ChangeSet(object):
    def __init__(self, git, since, uncommitted=True):
        self.git, self.since, self.uncommitted = git, since, uncommitted
        self.files, self.untracked_paths = [], set()

    def load(self):
        if self.since:
            self._load_tracked()
        if self.uncommitted:
            known, untracked = {f.path for f in self.files}, self.git.untracked()
            self.untracked_paths = set(untracked)
            for rel in untracked:
                if rel not in known:
                    self.files.append(UntrackedFile.load(self.git.cwd, rel))
        return self

    def _load_tracked(self):
        rng = self.git.diff_args(self.since, self.uncommitted)
        self.files = DiffStatParser.name_status(self.git.run(["diff", "-M", "--name-status", "-z"] + rng))
        by_path = {f.path: f for f in self.files}
        for path, added, removed in DiffStatParser.numstat(self.git.run(["diff", "-M", "--numstat", "-z"] + rng)):
            if path in by_path:
                by_path[path].set_counts(added, removed)

    def is_untracked(self, f):
        return f.path in self.untracked_paths

    # ---- views ---------------------------------------------------------------------------
    def ordered(self):
        return sorted(self.files, key=lambda f: (ORDER.index(f.kind), f.area, f.path))

    def totals(self):
        real = [f for f in self.files if f.kind != "noise"]
        return {"files": len(self.files), "reviewable_files": len(real),
                "added": sum(f.added for f in real), "removed": sum(f.removed for f in real)}

    def by_kind(self):
        out = {}
        for f in self.files:
            out.setdefault(f.kind, []).append(f.path)
        return {k: out[k] for k in ORDER if k in out}
