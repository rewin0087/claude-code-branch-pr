"""CaveatSignals: things in the diff a reviewer or deployer must know about (caveat candidates).

It reads diff.patch line by line, file by file, and flags: migrations, dependency changes, new
environment variables, feature flags, route/API changes, removed code that may be public, deleted
tests, TODO/FIXME left in, debug output left in, and secret-looking values. Each signal is a hint
for the writer of the description: it is checked against the code before it becomes a caveat.
"""
import re

from .filekinds import FileKind

ENV_VAR = re.compile(r"ENV\[\s*['\"]([A-Z0-9_]+)|ENV\.fetch\(\s*['\"]([A-Z0-9_]+)|process\.env\.([A-Z0-9_]+)|"
                     r"process\.env\[\s*['\"]([A-Z0-9_]+)|os\.environ(?:\.get)?[\[(]\s*['\"]([A-Z0-9_]+)|"
                     r"os\.getenv\(\s*['\"]([A-Z0-9_]+)|System\.getenv\(\s*\"([A-Z0-9_]+)|import\.meta\.env\.([A-Z0-9_]+)|"
                     r"System\.get_env\(\s*\"([A-Z0-9_]+)|^\+?\s*([A-Z][A-Z0-9_]{2,})\s*=", re.M)
FLAG = re.compile(r"Flipper|LaunchDarkly|ldclient|Unleash|unleash|feature_?flag|featureFlag|isFeatureEnabled|"
                  r"FeatureFlag|Split\.io|growthbook|flagsmith|posthog\.isFeatureEnabled", re.I)
ROUTE = re.compile(r"^\s*(get|post|put|patch|delete|resources?|namespace|scope|match)\s+['\":(]|"
                   r"@(app|router|bp|blueprint)\.(get|post|put|patch|delete|route)\(|"
                   r"\b(router|app|server)\.(get|post|put|patch|delete|use)\(\s*['\"`]/|"
                   r"@(Get|Post|Put|Patch|Delete|Request)Mapping|path\(\s*['\"]|"
                   r"\bfield\s+:\w+|\bmutation\s+\w|type\s+(Query|Mutation)\b|export\s+(async\s+)?function\s+(GET|POST|PUT|PATCH|DELETE)\b")
PUBLIC_DEF = re.compile(r"^\s*(def\s+(?!_)\w+|public\s+[\w<>\[\]]+\s+\w+\s*\(|export\s+(default\s+)?(async\s+)?(function|class|const)\s+\w+|"
                        r"func\s+[A-Z]\w*|class\s+\w+|module\s+\w+)")
TODO = re.compile(r"\b(TODO|FIXME|HACK|XXX)\b")
DEBUG = re.compile(r"\bconsole\.(log|debug)\(|\bbinding\.pry\b|\bbyebug\b|\bdebugger\b|\bpdb\.set_trace\(|\bbreakpoint\(\)|"
                   r"\bdd\(|\bvar_dump\(|\bIO\.inspect\b|\bputs\s+[\"'#]|\bpp\s+\w")
PY_PRINT = re.compile(r"^\s*print\(")
SECRET = re.compile(r"AKIA[0-9A-Z]{16}|-----BEGIN [A-Z ]*PRIVATE KEY-----|xox[abpr]-[0-9A-Za-z-]{10,}|gh[pousr]_[0-9A-Za-z]{30,}|"
                    r"sk-[A-Za-z0-9]{20,}|(password|passwd|secret|api_?key|token)\s*[:=]\s*['\"][^'\"\s]{8,}['\"]", re.I)
MAX_EXAMPLES = 6


class FileHunks(object):
    """diff.patch split per file -> {path: (added lines, removed lines)}."""

    @staticmethod
    def split(patch_text):
        out, cur = {}, None
        for line in patch_text.split("\n"):
            if line.startswith("diff --git "):
                cur = line.rsplit(" b/", 1)[-1]
                out[cur] = ([], [])
            elif cur is None or line.startswith(("+++ ", "--- ")):
                continue
            elif line.startswith("+"):
                out[cur][0].append(line[1:])
            elif line.startswith("-"):
                out[cur][1].append(line[1:])
        return out


class CaveatSignals(object):
    def __init__(self, changeset, patch_text):
        self.cs, self.hunks = changeset, FileHunks.split(patch_text)
        self.signals = []

    def scan(self):
        files = self.cs.files
        self._by_kind(files, "migration", "Database migration: check it is reversible, its run order and lock time on large tables")
        self._by_kind(files, "schema", "Schema / API contract file changed: consumers may need updating")
        self._by_kind(files, "dependency", "Dependencies changed: install/lockfile update needed on deploy")
        self._by_kind(files, "infra", "Infrastructure / container config changed")
        self._by_kind(files, "ci", "CI pipeline changed")
        deleted_tests = [f.path for f in files if f.kind == "test" and f.status == "deleted"]
        if deleted_tests:
            self._add("tests_deleted", "Test files deleted", deleted_tests)
        source = [f for f in files if f.kind == "source"]
        if source and not any(f.kind == "test" for f in files):
            self._add("no_tests", "Source changed but no test files changed", [f.path for f in source][:MAX_EXAMPLES])
        deleted_src = [f.path for f in source if f.status == "deleted"]
        if deleted_src:
            self._add("source_deleted", "Source files deleted: check nothing else still uses them", deleted_src)
        self._scan_lines()
        return self.signals

    def _scan_lines(self):
        env, flags, routes, removed_defs, todos, debug, secrets = {}, [], [], [], [], [], []
        for path, (added, removed) in self.hunks.items():
            kind = FileKind.of(path)
            if kind in ("noise", "docs", "asset"):
                continue
            for text in added:
                for m in ENV_VAR.finditer(text):
                    name = next(g for g in m.groups() if g)
                    if m.group(10) and ".env" not in path.split("/")[-1]:
                        continue          # a bare NAME= only counts in .env-style files
                    env.setdefault(name, path)
                if FLAG.search(text):
                    flags.append("%s: %s" % (path, text.strip()[:100]))
                if TODO.search(text):
                    todos.append("%s: %s" % (path, text.strip()[:100]))
                if kind == "source" and (DEBUG.search(text) or (path.endswith(".py") and PY_PRINT.search(text))):
                    debug.append("%s: %s" % (path, text.strip()[:100]))
                if SECRET.search(text):
                    secrets.append(path)
            if kind in ("source", "config", "schema"):
                routes += ["%s: %s" % (path, t.strip()[:100]) for t in added + removed if ROUTE.search(t)]
            if kind == "source":
                added_set = {a.strip() for a in added}
                removed_defs += ["%s: %s" % (path, r.strip()[:100]) for r in removed
                                 if PUBLIC_DEF.search(r) and r.strip() not in added_set]
        if env:
            self._add("env_vars", "Environment variables referenced in new code: make sure they are set in every environment",
                      ["%s (%s)" % kv for kv in env.items()])
        if flags:
            self._add("feature_flags", "Feature flag code touched: note the flag name and its default", flags)
        if routes:
            self._add("routes", "Routes / API endpoints / GraphQL fields added or changed", routes)
        if removed_defs:
            self._add("removed_definitions", "Definitions removed or renamed: possible breaking change for callers", removed_defs)
        if todos:
            self._add("todos", "TODO / FIXME left in the new code", todos)
        if debug:
            self._add("debug_output", "Possible debug output left in", debug)
        if secrets:
            self._add("secret_like", "Secret-looking value added: make sure it is not a real credential", sorted(set(secrets)))

    def _by_kind(self, files, kind, text):
        paths = [f.path for f in files if f.kind == kind]
        if paths:
            self._add(kind, text, paths)

    def _add(self, key, text, examples):
        self.signals.append({"signal": key, "note": text, "count": len(examples), "examples": examples[:MAX_EXAMPLES]})
