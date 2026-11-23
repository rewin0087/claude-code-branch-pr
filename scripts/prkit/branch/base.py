"""BaseResolver: which branch the current one will merge into, and the commit to diff from."""
from ..core.errors import PRError

BASE_CANDIDATES = ("main", "master", "develop", "development", "dev", "trunk")


class BaseResolver(object):
    def __init__(self, git, explicit=None, committed_only=False):
        self.git, self.explicit, self.committed_only = git, explicit, committed_only

    def resolve(self, branch):
        """-> (base ref or None, commit to diff from). On the base branch: (None, HEAD) = uncommitted work only."""
        base = self._explicit() if self.explicit else self.detect(branch)
        if not base:
            if self.committed_only:
                raise PRError("'%s' looks like the base branch itself: there are no branch commits to describe. "
                              "Pass the base branch explicitly, or drop --committed-only to describe uncommitted work." % branch)
            return None, "HEAD" if self.git.has_commits() else None
        return base, self.git.merge_base(base)

    def _explicit(self):
        base = self.git.resolve_ref(self.explicit)
        if not base:
            raise PRError("Base branch '%s' not found (locally or on origin)." % self.explicit)
        return base

    def detect(self, current, head="HEAD"):
        """The candidate base whose merge-base is closest to head (fewest commits ahead)."""
        best, seen = None, set()
        for ref in self._candidates():
            if ref in seen or ref in (current, "origin/" + current) or not self.git.ref_exists(ref):
                continue
            seen.add(ref)
            mb = self.git.merge_base(ref, head, check=False)
            if not mb:
                continue
            ahead = self.git.count_commits(mb, head)
            if best is None or ahead < best[1]:
                best = (ref, ahead)
        return best[0] if best else None

    def _candidates(self):
        cands = [self.git.origin_head()] if self.git.origin_head() else []
        for name in BASE_CANDIDATES:
            cands += [name, "origin/" + name]
        return cands
