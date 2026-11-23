"""TypeHint: a suggested Conventional Commits type, from the branch's commits or else its file kinds."""
from .vocabulary import COMMIT_PREFIX, PRECEDENCE, TYPES

ONLY_KIND_TYPES = (("docs", "docs"), ("test", "test"), ("ci", "ci"), ("style", "style"))
BUILD_KINDS = {"dependency", "infra", "ci"}
CODE_KINDS = {"source", "migration", "schema", "style"}


class TypeHint(object):
    def __init__(self, commits, files):
        self.commits, self.files = commits, files

    def commit_prefixes(self):
        """[(type, scope)] of the commits already written as Conventional Commits."""
        out = []
        for c in self.commits:
            m = COMMIT_PREFIX.match(c["subject"])
            if m and m.group("type") in TYPES:
                out.append((m.group("type"), m.group("scope")))
        return out

    def from_commits(self):
        types = {t for t, _ in self.commit_prefixes()}
        return min(types, key=PRECEDENCE.index) if types else None

    def from_files(self):
        kinds = {f["kind"] for f in self.files if f["kind"] != "noise"}
        if not kinds:
            return "chore"
        for only, t in ONLY_KIND_TYPES:
            if kinds <= {only}:
                return t
        if kinds <= BUILD_KINDS:
            return "build"
        if not kinds & CODE_KINDS:
            return "chore"
        return None              # source changed: feat / fix / refactor / perf is a judgement from the diff
