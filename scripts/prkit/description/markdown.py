"""MarkdownDoc: the parts of a Markdown description the checks need (headings, sections, list items)."""
import re

SECTIONS = (    # the default layout: (name, heading pattern), in order
    ("Overview", re.compile(r"^#{1,6}\s*(overview|summary|what|description)\b", re.I | re.M)),
    ("Changes", re.compile(r"^#{1,6}\s*(changes|list of changes|what changed|what's changed|implementation)\b", re.I | re.M)),
    ("Caveats", re.compile(r"^#{1,6}\s*(caveats?|risks?|notes|known issues|limitations|deployment notes)\b", re.I | re.M)),
    ("QA test scenarios", re.compile(r"^#{1,6}\s*(qa|test|testing|how to test|test plan|test scenarios)\b", re.I | re.M)),
)
QA_SECTION = SECTIONS[3][1]
HEADING = re.compile(r"^#{1,6}\s+.+$", re.M)
LIST_ITEM = re.compile(r"^\s*([-*+]|\d+\.)\s+\S", re.M)


class MarkdownDoc(object):
    def __init__(self, text):
        self.text = text or ""

    def headings(self):
        return [h.lstrip("# ").strip() for h in HEADING.findall(self.text)]

    def has_headings(self):
        return bool(HEADING.search(self.text))

    def missing_sections(self):
        return [name for name, rx in SECTIONS if not rx.search(self.text)]

    def section(self, heading_rx):
        """The text under the first heading matching heading_rx, up to the next heading of the same or a higher level."""
        m = heading_rx.search(self.text)
        if not m:
            return None
        level = len(re.match(r"#+", m.group(0)).group(0))
        rest = self.text[m.end():]
        nxt = re.search(r"^#{1,%d}\s" % level, rest, re.M)
        return rest[:nxt.start()] if nxt else rest

    def qa_section(self):
        return self.section(QA_SECTION)

    @staticmethod
    def list_items(text):
        return LIST_ITEM.findall(text or "")

    @staticmethod
    def first_match(rx, text):
        """-> (matched text, 1-based line) or None."""
        m = rx.search(text)
        return (m.group(0), text[:m.start()].count("\n") + 1) if m else None
