"""FinalizeDigest: the short text finalize.py prints: verdict, problems, clipboard, title, file, command."""


class FinalizeDigest(object):
    def __init__(self, result):
        self.r = result

    def format(self):
        r, s = self.r, self.r["stats"]
        L = ["%s  %s: %d chars, %d lines, %d QA scenarios, sections: %s" % (
            "OK  " if r["ok"] else "FAIL", r["platform"]["short"], s["chars"], s["lines"], s["qa_items"], " | ".join(s["headings"]))]
        L += ["  ✗ " + e for e in r["errors"]] + ["  ! " + w for w in r["warnings"]]
        if r["copy_requested"]:
            L.append(self._copied())
        L += ["TITLE   " + r["title"], "FILE    " + r["description_path"]]
        if r["create_command"]:
            L.append("CREATE  (from the repo root) " + r["create_command"])
        return "\n".join(L)

    def _copied(self):
        r = self.r
        if r["copied_with"]:
            return "COPIED  description copied to the clipboard (%s)" % r["copied_with"]
        return "COPIED  no (%s)" % ("fix the errors first" if not r["ok"] else "no clipboard tool found")
