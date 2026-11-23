"""WrittenDescription: the title and description files the agent wrote, read and normalised."""
import os

from ..core.errors import PRError


class WrittenDescription(object):
    def __init__(self, title_path, body_path):
        self.title_path, self.body_path = title_path, body_path

    def load(self):
        """-> (title, body). The body is saved back without leading/trailing blank lines."""
        body = self._read(self.body_path, "PR_DESCRIPTION.md").strip() + "\n"
        title = self._read(self.title_path, "PR_TITLE.txt").strip()
        with open(self.body_path, "w") as fh:
            fh.write(body)
        return title, body

    @staticmethod
    def _read(path, label):
        if not os.path.exists(path):
            raise PRError("%s not found at %s: write it first" % (label, path))
        with open(path, errors="replace") as fh:
            return fh.read()
