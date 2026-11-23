"""TitleCheck: one line, not too long, Conventional Commits, and '!' agreeing with the breaking-change caveat."""
import re

from ..title.conventional import ConventionalTitle

LONG_TITLE = 72
BREAKING = re.compile(r"\*\*breaking changes?\*\*\s*:?\s*(?!none\b|n/a\b|no\b)|^BREAKING[ -]CHANGE:", re.I | re.M)


class TitleCheck(object):
    def __init__(self, title, body):
        self.title, self.body = title, body

    def run(self, out):
        if not self.title:
            out.error("the title is empty")
        elif len(self.title) > LONG_TITLE:
            out.warn("the title is %d characters; keep it under %d" % (len(self.title), LONG_TITLE))
        if "\n" in self.title:
            out.error("the title must be one line")
        if self.title:
            self._conventional(out)

    def _conventional(self, out):
        ct = ConventionalTitle(self.title)
        errors, warnings = ct.problems()
        for e in errors:
            out.error(e)
        for w in warnings:
            out.warn(w)
        says_breaking = bool(BREAKING.search(self.body))
        if says_breaking and not ct.breaking:
            out.warn("the description lists a breaking change but the title has no '!' (e.g. feat(api)!: ...)")
        if ct.breaking and not says_breaking:
            out.warn("the title is marked breaking ('!') but the description has no 'Breaking change' caveat")
