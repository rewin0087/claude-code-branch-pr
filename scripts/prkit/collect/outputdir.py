"""OutputDir: the .branch-pr/ folder in the repo: its file paths, created and kept out of git."""
import os

NAME = ".branch-pr"
FILES = {"context": "context.json", "patch": "diff.patch", "description": "PR_DESCRIPTION.md", "title": "PR_TITLE.txt"}


class OutputDir(object):
    def __init__(self, root):
        self.root, self.path = root, os.path.join(root, NAME)

    def file(self, key):
        return os.path.join(self.path, FILES[key])

    @staticmethod
    def relative(key):
        """The path from the repo root, for commands the user runs there."""
        return NAME + "/" + FILES[key]

    def paths(self):
        return dict({"out": self.path}, **{k: self.file(k) for k in ("context", "patch", "description", "title")})

    def create(self, git):
        os.makedirs(self.path, exist_ok=True)
        self._ignore(git)
        return self

    def _ignore(self, git):
        """Add the folder to .git/info/exclude, so the tracked .gitignore is never touched."""
        git_dir = git.git_dir()
        if not git_dir:
            return
        exclude = os.path.join(git_dir if os.path.isabs(git_dir) else os.path.join(git.cwd, git_dir), "info", "exclude")
        entry = NAME + "/"
        try:
            os.makedirs(os.path.dirname(exclude), exist_ok=True)
            existing = open(exclude).read() if os.path.exists(exclude) else ""
            if entry not in existing.split("\n"):
                with open(exclude, "a") as fh:
                    fh.write(("" if existing.endswith("\n") or not existing else "\n") + entry + "\n")
        except OSError:
            pass
