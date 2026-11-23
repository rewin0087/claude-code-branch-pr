"""CollectDigest: the short text collect.py prints, so the agent knows what to read next."""

MAX_FILES = 60
MAX_COMMITS = 40


class CollectDigest(object):
    def __init__(self, ctx):
        self.c = ctx

    def format(self):
        L = []
        for part in (self._header, self._commits, self._files, self._signals, self._title, self._template, self._paths):
            L += part()
        return "\n".join(L)

    def _header(self):
        c, t, p = self.c, self.c["totals"], self.c["platform"]
        where = ("%s ← %s" % (c["branch"], c["base"])) if c["base"] else "%s (uncommitted work only: no base branch)" % c["branch"]
        L = ["BRANCH  %s  @%s%s" % (where, c["head"], "  (+ uncommitted changes)" if c["includes_uncommitted"] else ""),
             "PLATFORM %s (%s)%s" % (p["name"], p["noun"], "  " + p["web_url"] if p["web_url"] else ""),
             "SIZE    %d files (%d reviewable), +%d / -%d lines, diff.patch %d lines"
             % (t["files"], t["reviewable_files"], t["added"], t["removed"], t["patch_lines"])]
        if c["tickets"]:
            L.append("TICKETS " + ", ".join("%s%s (%s)" % (x["id"], " [closes]" if x["closes"] else "", x["source"])
                                            for x in c["tickets"]))
        return L

    def _commits(self):
        commits = self.c["commits"]
        if not commits:
            return []
        L = ["\nCOMMITS (%d, oldest first)" % len(commits)]
        L += ["  %s %s" % (x["short"], x["subject"]) for x in commits[:MAX_COMMITS]]
        if len(commits) > MAX_COMMITS:
            L.append("  … %d more in context.json" % (len(commits) - MAX_COMMITS))
        return L

    def _files(self):
        files = self.c["files"]
        L = ["\nFILES  (kind  status  +/-  diff.patch line  path)"]
        for f in files[:MAX_FILES]:
            L.append("  %-10s %-9s +%-5d -%-5d %s  %s%s" % (
                f["kind"], f["status"], f["added"], f["removed"],
                ("L%d" % f["diff_line"]) if f["diff_line"] else "  -  ", f["path"],
                "  (from %s)" % f["old_path"] if f.get("old_path") else ""))
        if len(files) > MAX_FILES:
            L.append("  … %d more files in context.json" % (len(files) - MAX_FILES))
        return L

    def _signals(self):
        if not self.c["signals"]:
            return []
        L = ["\nCAVEAT SIGNALS (verify each against the code before writing it down)"]
        for s in self.c["signals"]:
            L.append("  [%s] %s" % (s["signal"], s["note"]))
            L += ["      - " + e for e in s["examples"]]
            if s["count"] > len(s["examples"]):
                L.append("      … %d more" % (s["count"] - len(s["examples"])))
        return L

    def _title(self):
        h = self.c["title_hints"]
        L = ["\nTITLE   Conventional Commits: %s" % h["format"],
             "  type:  %s" % ("%s (from %s)" % (h["suggested_type"], h["type_source"]) if h["suggested_type"]
                             else "decide from the diff: feat (new capability) | fix (bug) | refactor | perf"),
             "  scope: %s" % (", ".join(h["scope_candidates"]) or "pick the area the change affects")]
        if h["breaking_hint"]:
            L.append("  breaking? definitions were removed: if callers outside this repo break, use '!' (feat(x)!: ...)")
        return L

    def _template(self):
        tpl = self.c["template"]
        if not tpl:
            return ["\nTEMPLATE none in the repo: use the default layout"]
        return ["\nTEMPLATE %s (fill its sections)%s" % (tpl["path"], "; others: " + ", ".join(tpl["others"]) if tpl["others"] else "")]

    def _paths(self):
        p = self.c["paths"]
        return ["\nWRITE   %s\n        %s\nCONTEXT %s\nDIFF    %s" % (p["title"], p["description"], p["context"], p["patch"])]
