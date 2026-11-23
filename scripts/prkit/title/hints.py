"""TitleHints: what collect.py tells the writer about the title: format, type, scope, breaking."""
from .scope_hint import ScopeHint
from .type_hint import TypeHint
from .vocabulary import FORMAT, TYPE_MEANING

BREAKING_SIGNALS = ("removed_definitions", "source_deleted")


class TitleHints(object):
    def __init__(self, commits, files, signals):
        self.commits, self.files, self.signals = commits, files, signals

    def build(self):
        types = TypeHint(self.commits, self.files)
        from_commits = types.from_commits()
        return {"format": FORMAT, "types": TYPE_MEANING,
                "suggested_type": from_commits or types.from_files(),
                "type_source": "commits" if from_commits else "file kinds",
                "scope_candidates": ScopeHint(types.commit_prefixes(), self.files).candidates(),
                "breaking_hint": any(s["signal"] in BREAKING_SIGNALS for s in self.signals)}
