"""ContentCheck: size limits, secret-looking values, leftover placeholders, local paths, template comments."""
import re

from ..signals.patterns import SECRET

LONG_BODY = 6000
PLACEHOLDER = re.compile(r"\{\{[^}]*\}\}|<(describe|add|insert|todo|fill)[^>]*>|\bTBD\b|lorem ipsum|\[(Role|Ticket|Link|TODO)[^\]]*\]", re.I)
LOCAL_PATH = re.compile(r"(/Users/[\w.-]+|/home/[\w.-]+|[A-Z]:\\\\Users\\\\|/private/tmp/|\.branch-pr/)")
SCANS = (   # pattern, what it is, is it an error
    (SECRET, "a secret-looking value", True),
    (PLACEHOLDER, "a leftover placeholder", False),
    (LOCAL_PATH, "a local file path", False),
)


class ContentCheck(object):
    def __init__(self, title, doc, limit):
        self.title, self.doc, self.limit = title, doc, limit

    def run(self, out):
        body = self.doc.text
        if len(body) > self.limit:
            out.error("the description is %d characters; the platform limit is %d" % (len(body), self.limit))
        elif len(body) > LONG_BODY:
            out.warn("the description is %d characters; aim for a brief one (under ~%d)" % (len(body), LONG_BODY))
        for rx, what, as_error in SCANS:
            hit = self.doc.first_match(rx, self.title) or self.doc.first_match(rx, body)
            if hit:
                out.add("%s: %r (line %d)" % (what, hit[0][:40], hit[1]), as_error)
        if "<!--" in body:
            out.warn("HTML comments from the template are still in the description (hidden when rendered)")
