"""TemplateFinder: the repository's own PR / MR description template, if it has one."""
import glob
import os

PATTERNS = (
    ".github/pull_request_template.md", ".github/PULL_REQUEST_TEMPLATE.md", "pull_request_template.md",
    "PULL_REQUEST_TEMPLATE.md", "docs/pull_request_template.md", "docs/PULL_REQUEST_TEMPLATE.md",
    ".github/PULL_REQUEST_TEMPLATE/*.md", ".gitlab/merge_request_templates/Default.md",
    ".gitlab/merge_request_templates/*.md", ".bitbucket/pull_request_template.md", ".azuredevops/pull_request_template.md",
)
MAX_CHARS = 8000


class TemplateFinder(object):
    def __init__(self, root):
        self.root = root

    def find(self, explicit=None):
        """-> {"path", "text", "others"} or None. An explicit path wins over the repo's templates."""
        if explicit:
            path = explicit if os.path.isabs(explicit) else os.path.join(self.root, explicit)
            return self._load(path, [])
        found, seen = [], set()
        for pat in PATTERNS:
            for p in sorted(glob.glob(os.path.join(self.root, pat))):
                key = self._identity(p)
                if key and key not in seen:          # case-insensitive filesystems match one file twice
                    seen.add(key)
                    found.append(p)
        if not found:
            return None
        return self._load(found[0], [os.path.relpath(p, self.root) for p in found[1:]])

    @staticmethod
    def _identity(path):
        try:
            st = os.stat(path)
        except OSError:
            return None
        return (st.st_dev, st.st_ino) if os.path.isfile(path) else None

    def _load(self, path, others):
        try:
            with open(path, errors="replace") as fh:
                text = fh.read(MAX_CHARS)
        except OSError:
            return None
        return {"path": os.path.relpath(path, self.root), "text": text, "others": others}
