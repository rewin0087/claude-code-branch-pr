"""ChangeSet: the files the branch changed, with line counts, kinds and where each sits in diff.patch.

  ChangedFile   one file: path (and old path for renames), status, +/- lines, kind, area
  ChangeSet     merge-base -> HEAD (or the working tree) plus untracked files; writes diff.patch
"""
import os

from .filekinds import ORDER, FileKind

STATUS = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed", "C": "copied", "T": "type-changed"}
MAX_UNTRACKED_BYTES = 400000


class ChangedFile(object):
    def __init__(self, path, status, old_path=None):
        self.path, self.status, self.old_path = path, status, old_path
        self.added = self.removed = 0
        self.binary = False
        self.kind, self.area = FileKind.of(path), FileKind.area(path)
        self.diff_line = None          # 1-based line in diff.patch where this file's diff starts

    def as_dict(self):
        d = {"path": self.path, "status": self.status, "kind": self.kind, "area": self.area,
             "added": self.added, "removed": self.removed, "diff_line": self.diff_line}
        if self.old_path:
            d["old_path"] = self.old_path
        if self.binary:
            d["binary"] = True
        return d


class ChangeSet(object):
    def __init__(self, git, since, uncommitted=True):
        self.git, self.since, self.uncommitted = git, since, uncommitted
        self.files = []

    # ---- loading -------------------------------------------------------------------------
    def load(self):
        if self.since:
            self._load_tracked()
        if self.uncommitted:
            known = {f.path for f in self.files}
            for rel in self.git.untracked():
                if rel not in known:
                    self.files.append(self._untracked(rel))
        return self

    def _load_tracked(self):
        rng = self.git.diff_args(self.since, self.uncommitted)
        by_path = {}
        fields = self.git.run(["diff", "-M", "--name-status", "-z"] + rng).split("\0")
        i = 0
        while i < len(fields) and fields[i]:
            code = fields[i][0]
            if code in "RC":
                f = ChangedFile(fields[i + 2], STATUS[code], old_path=fields[i + 1])
                i += 3
            else:
                f = ChangedFile(fields[i + 1], STATUS.get(code, "modified"))
                i += 2
            by_path[f.path] = f
            self.files.append(f)
        fields = self.git.run(["diff", "-M", "--numstat", "-z"] + rng).split("\0")
        i = 0
        while i < len(fields) and fields[i]:
            added, removed, path = fields[i].split("\t", 2)
            if path == "":                       # rename: "a\tb\t" then old, new
                path, i = fields[i + 2], i + 3
            else:
                i += 1
            f = by_path.get(path)
            if f:
                f.binary = added == "-"
                f.added, f.removed = (0, 0) if f.binary else (int(added), int(removed))

    def _untracked(self, rel):
        f = ChangedFile(rel, "added")
        full = os.path.join(self.git.cwd, rel)
        try:
            with open(full, "rb") as fh:
                data = fh.read(MAX_UNTRACKED_BYTES)
            f.binary = b"\0" in data[:8000]
            f.added = 0 if f.binary else data.count(b"\n") + (0 if data.endswith(b"\n") or not data else 1)
        except OSError:
            f.binary = True
        return f

    # ---- the patch -----------------------------------------------------------------------
    def write_patch(self, path):
        """diff.patch: reviewable files first (lockfiles and build output left out), with each file's start line."""
        chunks, line = [], 1
        for f in self.ordered():
            if f.kind == "noise":
                continue
            text = self._file_diff(f)
            if not text:
                continue
            f.diff_line = line
            text = text if text.endswith("\n") else text + "\n"
            chunks.append(text)
            line += text.count("\n")
        with open(path, "w") as fh:
            fh.write("".join(chunks))
        return line - 1

    def _file_diff(self, f):
        if f.binary:
            return "Binary file %s: %s\n" % (f.status, f.path)
        tracked = self.since and not (self.uncommitted and f.path in self._untracked_set())
        if tracked:
            paths = [f.old_path, f.path] if f.old_path else [f.path]
            return self.git.run(["diff", "--no-color", "--no-ext-diff", "-M", "-U5"]
                                + self.git.diff_args(self.since, self.uncommitted) + ["--"] + paths, check=False)
        return self.git.run_diff(["diff", "--no-color", "--no-index", "--", os.devnull, f.path])

    def _untracked_set(self):
        if not hasattr(self, "_untracked_cache"):
            self._untracked_cache = set(self.git.untracked()) if self.uncommitted else set()
        return self._untracked_cache

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
