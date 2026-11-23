"""CollectDigest: the short text collect.py prints, so the agent knows what to read next."""

MAX_FILES = 60


class CollectDigest(object):
    def __init__(self, ctx):
        self.c = ctx

    def format(self):
        c, L = self.c, []
        t = c["totals"]
        where = ("%s ← %s" % (c["branch"], c["base"])) if c["base"] else "%s (uncommitted work only: no base branch)" % c["branch"]
        L.append("BRANCH  %s  @%s%s" % (where, c["head"], "  (+ uncommitted changes)" if c["includes_uncommitted"] else ""))
        L.append("PLATFORM %s (%s)%s" % (c["platform"]["name"], c["platform"]["noun"],
                                         "  " + c["platform"]["web_url"] if c["platform"]["web_url"] else ""))
        L.append("SIZE    %d files (%d reviewable), +%d / -%d lines, diff.patch %d lines"
                 % (t["files"], t["reviewable_files"], t["added"], t["removed"], t["patch_lines"]))
        if c["tickets"]:
            L.append("TICKETS " + ", ".join("%s%s (%s)" % (x["id"], " [closes]" if x["closes"] else "", x["source"]) for x in c["tickets"]))
        if c["commits"]:
            L.append("\nCOMMITS (%d, oldest first)" % len(c["commits"]))
            L.extend("  %s %s" % (x["short"], x["subject"]) for x in c["commits"][:40])
            if len(c["commits"]) > 40:
                L.append("  … %d more in context.json" % (len(c["commits"]) - 40))
        L.append("\nFILES  (kind  status  +/-  diff.patch line  path)")
        for f in c["files"][:MAX_FILES]:
            L.append("  %-10s %-9s +%-5d -%-5d %s  %s%s" % (
                f["kind"], f["status"], f["added"], f["removed"],
                ("L%d" % f["diff_line"]) if f["diff_line"] else "  -  ", f["path"],
                "  (from %s)" % f["old_path"] if f.get("old_path") else ""))
        if len(c["files"]) > MAX_FILES:
            L.append("  … %d more files in context.json" % (len(c["files"]) - MAX_FILES))
        if c["signals"]:
            L.append("\nCAVEAT SIGNALS (verify each against the code before writing it down)")
            for s in c["signals"]:
                L.append("  [%s] %s" % (s["signal"], s["note"]))
                L.extend("      - " + e for e in s["examples"])
                if s["count"] > len(s["examples"]):
                    L.append("      … %d more" % (s["count"] - len(s["examples"])))
        tpl = c["template"]
        L.append("\nTEMPLATE " + ("%s (fill its sections)%s" % (tpl["path"], "; others: " + ", ".join(tpl["others"]) if tpl["others"] else "")
                                  if tpl else "none in the repo: use the default layout"))
        p = c["paths"]
        L.append("\nWRITE   %s\n        %s\nCONTEXT %s\nDIFF    %s" % (p["title"], p["description"], p["context"], p["patch"]))
        return "\n".join(L)
