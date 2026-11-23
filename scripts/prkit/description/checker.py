"""DescriptionChecker: runs the title, section and content checks on a written title + description.

Errors (must fix): a malformed Conventional Commits title, a missing default section (when no repo
template is used), an empty QA list, a description over the platform's size limit, a
secret-looking value. Warnings: no scope, '!' and the breaking-change caveat disagreeing, leftover
placeholders, local file paths, a long description or title.
"""
from .content_check import ContentCheck
from .findings import Findings
from .markdown import MarkdownDoc
from .section_check import SectionCheck
from .title_check import TitleCheck


class DescriptionChecker(object):
    def __init__(self, title, body, limit, uses_template=False):
        self.title, self.doc = (title or "").strip(), MarkdownDoc(body)
        self.limit, self.uses_template = limit, uses_template
        self.findings = Findings()

    def check(self):
        for check in (TitleCheck(self.title, self.doc.text), SectionCheck(self.doc, self.uses_template),
                      ContentCheck(self.title, self.doc, self.limit)):
            check.run(self.findings)
        return self

    @property
    def ok(self):
        return self.findings.ok

    @property
    def errors(self):
        return self.findings.errors

    @property
    def warnings(self):
        return self.findings.warnings

    def stats(self):
        body = self.doc.text
        return {"chars": len(body), "lines": body.count("\n") + 1,
                "qa_items": len(self.doc.list_items(self.doc.qa_section() or "")),
                "headings": self.doc.headings()}
