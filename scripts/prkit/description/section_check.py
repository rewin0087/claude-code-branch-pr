"""SectionCheck: headings present, the default sections (errors without a repo template), QA items listed."""


class SectionCheck(object):
    def __init__(self, doc, uses_template):
        self.doc, self.uses_template = doc, uses_template

    def run(self, out):
        if not self.doc.has_headings():
            out.error("the description has no Markdown headings")
            return
        missing = self.doc.missing_sections()
        if missing:
            out.add("missing section(s): " + ", ".join(missing), as_error=not self.uses_template)
        qa = self.doc.qa_section()
        if qa is not None and not self.doc.list_items(qa):
            out.error("the QA test scenarios section has no list items")
