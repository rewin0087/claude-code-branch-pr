"""ChangedFile: one file the branch changed: path (and old path for renames), status, +/- lines, kind."""
from .kinds import FileKind

STATUS = {"A": "added", "M": "modified", "D": "deleted", "R": "renamed", "C": "copied", "T": "type-changed"}


class ChangedFile(object):
    def __init__(self, path, status, old_path=None):
        self.path, self.status, self.old_path = path, status, old_path
        self.added = self.removed = 0
        self.binary = False
        self.kind, self.area = FileKind.of(path), FileKind.area(path)
        self.diff_line = None          # 1-based line in diff.patch where this file's diff starts

    @classmethod
    def from_status_code(cls, code, path, old_path=None):
        return cls(path, STATUS.get(code, "modified"), old_path)

    def set_counts(self, added, removed):
        """numstat values; '-' means binary."""
        self.binary = added == "-"
        self.added, self.removed = (0, 0) if self.binary else (int(added), int(removed))

    def as_dict(self):
        d = {"path": self.path, "status": self.status, "kind": self.kind, "area": self.area,
             "added": self.added, "removed": self.removed, "diff_line": self.diff_line}
        if self.old_path:
            d["old_path"] = self.old_path
        if self.binary:
            d["binary"] = True
        return d
