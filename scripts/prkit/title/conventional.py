"""ConventionalTitle: parses a `<type>(<scope>)!: <description>` title and lists what is wrong with it."""
import re

from .vocabulary import FORMAT, TITLE, TYPES


class ConventionalTitle(object):
    def __init__(self, title):
        self.title = (title or "").strip()
        self.m = TITLE.match(self.title)

    @property
    def breaking(self):
        return bool(self.m and self.m.group("bang"))

    def problems(self):
        """-> (errors, warnings)"""
        if not self.m:
            return (["the title must follow Conventional Commits: %s, e.g. 'feat(refunds): support partial refunds'" % FORMAT], [])
        errors, warnings = [], []
        t, scope, desc = self.m.group("type"), self.m.group("scope"), self.m.group("desc")
        if t not in TYPES:
            errors.append("unknown type '%s': use one of %s" % (t, ", ".join(TYPES)))
        warnings += self._scope_problems(t, scope) + self._description_problems(desc)
        return errors, warnings

    @staticmethod
    def _scope_problems(t, scope):
        if not scope:
            return ["no scope: add the area the change affects, e.g. %s(<area>): ..." % t]
        if scope != scope.lower():
            return ["scope '%s' should be lower-case" % scope]
        return []

    @staticmethod
    def _description_problems(desc):
        out = []
        if desc.endswith("."):
            out.append("the description should not end with a period")
        if desc[:1].isupper() and not re.match(r"^[A-Z]{2,}\b", desc):
            out.append("start the description in lower case: '%s'" % (desc[:1].lower() + desc[1:40]))
        return out
