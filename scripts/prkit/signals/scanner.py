"""CaveatSignals: runs the file rules and the line rules over the change set and its patch.

Each signal is a hint for the writer of the description (migrations, dependencies, env vars,
feature flags, routes, removed definitions, deleted tests, TODOs, debug output, secrets): it is
checked against the code before it becomes a caveat.
"""
from ..branch.kinds import FileKind
from .file_rules import FileSignals
from .hunks import FileHunks
from .line_rules import RULES
from .signal_list import SignalList

SKIPPED_KINDS = ("noise", "docs", "asset")


class CaveatSignals(object):
    def __init__(self, changeset, patch_text):
        self.cs, self.hunks = changeset, FileHunks.split(patch_text)

    def scan(self):
        out = SignalList()
        FileSignals(self.cs.files).collect(out)
        rules = [rule() for rule in RULES]
        for path, (added, removed) in self.hunks.items():
            kind = FileKind.of(path)
            if kind in SKIPPED_KINDS:
                continue
            for rule in rules:
                rule.feed(path, kind, added, removed)
        for rule in rules:
            rule.emit(out)
        return out.items
