"""DescriptionChecker: checks the written title and description before they are shown or copied.

Errors (must fix): a missing default section (when no repo template is used), an empty QA list,
a description over the platform's size limit, a secret-looking value, an empty title.
Warnings: leftover placeholders, local file paths, a long description or title.
"""
import re

from .conventional import ConventionalTitle
from .signals import SECRET

SECTIONS = (
    ("Overview", re.compile(r"^#{1,6}\s*(overview|summary|what|description)\b", re.I | re.M)),
    ("Changes", re.compile(r"^#{1,6}\s*(changes|list of changes|what changed|what's changed|implementation)\b", re.I | re.M)),
    ("Caveats", re.compile(r"^#{1,6}\s*(caveats?|risks?|notes|known issues|limitations|deployment notes)\b", re.I | re.M)),
    ("QA test scenarios", re.compile(r"^#{1,6}\s*(qa|test|testing|how to test|test plan|test scenarios)\b", re.I | re.M)),
)
PLACEHOLDER = re.compile(r"\{\{[^}]*\}\}|<(describe|add|insert|todo|fill)[^>]*>|\bTBD\b|lorem ipsum|\[(Role|Ticket|Link|TODO)[^\]]*\]", re.I)
LOCAL_PATH = re.compile(r"(/Users/[\w.-]+|/home/[\w.-]+|[A-Z]:\\\\Users\\\\|/private/tmp/|\.branch-pr/)")
BREAKING = re.compile(r"\*\*breaking changes?\*\*\s*:?\s*(?!none\b|n/a\b|no\b)|^BREAKING[ -]CHANGE:", re.I | re.M)
HEADING = re.compile(r"^#{1,6}\s+.+$", re.M)
LIST_ITEM = re.compile(r"^\s*([-*+]|\d+\.)\s+\S", re.M)
LONG_BODY = 6000
LONG_TITLE = 72


class DescriptionChecker(object):
    def __init__(self, title, body, limit, uses_template=False):
        self.title, self.body, self.limit, self.uses_template = (title or "").strip(), body or "", limit, uses_template
        self.errors, self.warnings = [], []

    def check(self):
        self._title()
        self._sections()
        self._content()
        return self

    @property
    def ok(self):
        return not self.errors

    def _title(self):
        if not self.title:
            self.errors.append("the title is empty")
        elif len(self.title) > LONG_TITLE:
            self.warnings.append("the title is %d characters; keep it under %d" % (len(self.title), LONG_TITLE))
        if "\n" in self.title:
            self.errors.append("the title must be one line")
        if self.title:
            ct = ConventionalTitle(self.title)
            errors, warnings = ct.problems()
            self.errors += errors
            self.warnings += warnings
            says_breaking = bool(BREAKING.search(self.body))
            if says_breaking and not ct.breaking:
                self.warnings.append("the description lists a breaking change but the title has no '!' (e.g. feat(api)!: ...)")
            if ct.breaking and not says_breaking:
                self.warnings.append("the title is marked breaking ('!') but the description has no 'Breaking change' caveat")

    def _sections(self):
        if not HEADING.search(self.body):
            self.errors.append("the description has no Markdown headings")
            return
        missing = [name for name, rx in SECTIONS if not rx.search(self.body)]
        if missing:
            (self.warnings if self.uses_template else self.errors).append("missing section(s): " + ", ".join(missing))
        qa = self._qa_section()
        if qa is not None and not LIST_ITEM.search(qa):
            self.errors.append("the QA test scenarios section has no list items")

    def _qa_section(self):
        """The text under the QA heading, up to the next heading of the same or a higher level."""
        m = SECTIONS[3][1].search(self.body)
        if not m:
            return None
        level = len(re.match(r"#+", m.group(0)).group(0))
        rest = self.body[m.end():]
        nxt = re.search(r"^#{1,%d}\s" % level, rest, re.M)
        return rest[:nxt.start()] if nxt else rest

    def _content(self):
        if len(self.body) > self.limit:
            self.errors.append("the description is %d characters; the platform limit is %d" % (len(self.body), self.limit))
        elif len(self.body) > LONG_BODY:
            self.warnings.append("the description is %d characters; aim for a brief one (under ~%d)" % (len(self.body), LONG_BODY))
        for rx, msg, bucket in ((SECRET, "a secret-looking value", self.errors),
                                (PLACEHOLDER, "a leftover placeholder", self.warnings),
                                (LOCAL_PATH, "a local file path", self.warnings)):
            for text in (self.title, self.body):
                m = rx.search(text)
                if m:
                    bucket.append("%s: %r (line %d)" % (msg, m.group(0)[:40], text[:m.start()].count("\n") + 1))
                    break
        if "<!--" in self.body:
            self.warnings.append("HTML comments from the template are still in the description (hidden when rendered)")

    def stats(self):
        return {"chars": len(self.body), "lines": self.body.count("\n") + 1,
                "qa_items": len(LIST_ITEM.findall(self._qa_section() or "")),
                "headings": [h.lstrip("# ").strip() for h in HEADING.findall(self.body)]}
