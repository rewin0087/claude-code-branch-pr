"""UntrackedFile: a new file git doesn't track yet, counted as fully added."""
import os

from .files import ChangedFile

MAX_UNTRACKED_BYTES = 400000


class UntrackedFile(object):
    @staticmethod
    def load(root, rel):
        f = ChangedFile(rel, "added")
        try:
            with open(os.path.join(root, rel), "rb") as fh:
                data = fh.read(MAX_UNTRACKED_BYTES)
            f.binary = b"\0" in data[:8000]
            f.added = 0 if f.binary else data.count(b"\n") + (0 if data.endswith(b"\n") or not data else 1)
        except OSError:
            f.binary = True
        return f
