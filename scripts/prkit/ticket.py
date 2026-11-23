"""TicketRefs: ticket / issue ids mentioned by the branch name and the commit messages."""
import re

JIRA = re.compile(r"\b([A-Z][A-Z0-9]{1,9}-\d{1,6})\b")
HASH = re.compile(r"(?<![\w&/])#(\d{1,7})\b")
BRANCH_NUM = re.compile(r"(?:^|/)(?:[a-z]+[-_])?(\d{2,7})(?:[-_]|$)")
CLOSING = re.compile(r"\b(close[sd]?|fix(e[sd])?|resolve[sd]?)\s+(#\d+|[A-Z][A-Z0-9]+-\d+)", re.I)


class TicketRefs(object):
    @staticmethod
    def find(branch, commits):
        """-> [{"id", "source", "closes"}] in first-seen order."""
        seen, out = set(), []

        def add(tid, source, closes=False):
            if tid not in seen:
                seen.add(tid)
                out.append({"id": tid, "source": source, "closes": closes})
            elif closes:
                next(x for x in out if x["id"] == tid)["closes"] = True

        for m in JIRA.finditer(branch.upper()):
            add(m.group(1), "branch")
        m = BRANCH_NUM.search(branch)
        if m and not out:
            add("#" + m.group(1), "branch (number)")
        for c in commits:
            text = c["subject"] + "\n" + c.get("body", "")
            for m in JIRA.finditer(text):
                add(m.group(1), "commit " + c["short"])
            for m in HASH.finditer(text):
                add("#" + m.group(1), "commit " + c["short"])
            for m in CLOSING.finditer(text):
                add(m.group(3), "commit " + c["short"], closes=True)
        return out
