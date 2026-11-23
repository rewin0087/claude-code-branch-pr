"""Repository: finds the git repository root for a directory, or explains why there is none."""
import os

from ..core.errors import PRError
from ..core.gitcmd import Git


class Repository(object):
    @staticmethod
    def open(directory):
        """-> Git rooted at the repository that contains directory."""
        root = Git(os.path.abspath(directory)).root()
        if not root:
            raise PRError("%s is not inside a git repository" % os.path.abspath(directory))
        return Git(root)
