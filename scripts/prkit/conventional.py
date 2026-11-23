"""Conventional Commits titles (https://www.conventionalcommits.org/en/v1.0.0/).

  <type>(<scope>)!: <description>      e.g.  feat(refunds): support partial refunds

  ConventionalTitle   parses and checks a title
  TitleHints          suggests a type and scope candidates from the commits and the changed files
"""
import re
from collections import Counter

TYPES = ("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert")
TYPE_MEANING = {
    "feat": "a new feature or user-visible capability", "fix": "a bug fix", "docs": "documentation only",
    "style": "formatting only, no code meaning change", "refactor": "restructuring without behaviour change",
    "perf": "a performance improvement", "test": "tests only", "build": "build system or dependencies",
    "ci": "CI configuration", "chore": "maintenance that touches no source or tests", "revert": "reverts earlier work",
}
TITLE = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^()\s]+)\))?(?P<bang>!)?: (?P<desc>\S.*)$")
COMMIT = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^()\s]+)\))?(?P<bang>!)?:\s")
PRECEDENCE = ("revert", "feat", "fix", "perf", "refactor", "build", "ci", "test", "docs", "style", "chore")
GENERIC_DIRS = {"app", "src", "lib", "pkg", "internal", "packages", "services", "models", "controllers", "views",
                "components", "helpers", "utils", "api", "spec", "tests", "test", "config", "db", "migrate", "(root)"}


class ConventionalTitle(object):
    def __init__(self, title):
        self.title = (title or "").strip()
        self.m = TITLE.match(self.title)

    def problems(self):
        """-> (errors, warnings)"""
        if not self.m:
            return (["the title must follow Conventional Commits: <type>(<scope>): <description>, "
                     "e.g. 'feat(refunds): support partial refunds'"], [])
        errors, warnings = [], []
        t, scope, desc = self.m.group("type"), self.m.group("scope"), self.m.group("desc")
        if t not in TYPES:
            errors.append("unknown type '%s': use one of %s" % (t, ", ".join(TYPES)))
        if not scope:
            warnings.append("no scope: add the area the change affects, e.g. %s(<area>): ..." % t)
        elif scope != scope.lower():
            warnings.append("scope '%s' should be lower-case" % scope)
        if desc.endswith("."):
            warnings.append("the description should not end with a period")
        if desc[:1].isupper() and not re.match(r"^[A-Z]{2,}\b", desc):
            warnings.append("start the description in lower case: '%s'" % (desc[:1].lower() + desc[1:40]))
        return errors, warnings

    @property
    def breaking(self):
        return bool(self.m and self.m.group("bang"))


class TitleHints(object):
    def __init__(self, commits, files, signals):
        self.commits, self.files, self.signals = commits, files, signals

    def build(self):
        ctype, cscopes = self._from_commits()
        return {"format": "<type>(<scope>): <description>", "types": TYPE_MEANING,
                "suggested_type": ctype or self._from_files(),
                "type_source": "commits" if ctype else "file kinds",
                "scope_candidates": (cscopes + [s for s in self._from_paths() if s not in cscopes])[:5],
                "breaking_hint": any(s["signal"] in ("removed_definitions", "source_deleted") for s in self.signals)}

    def _from_commits(self):
        types, scopes = [], Counter()
        for c in self.commits:
            m = COMMIT.match(c["subject"])
            if m and m.group("type") in TYPES:
                types.append(m.group("type"))
                if m.group("scope"):
                    scopes[m.group("scope")] += 1
        if not types:
            return None, []
        best = min(set(types), key=PRECEDENCE.index)
        return best, [s for s, _ in scopes.most_common(3)]

    def _from_files(self):
        kinds = {f["kind"] for f in self.files if f["kind"] != "noise"}
        if not kinds:
            return "chore"
        for only, t in ((("docs",), "docs"), (("test",), "test"), (("ci",), "ci"), (("style",), "style")):
            if kinds <= set(only):
                return t
        if kinds <= {"dependency", "infra", "ci"}:
            return "build"
        if not kinds & {"source", "migration", "schema", "style"}:
            return "chore"
        return None              # source changed: feat / fix / refactor / perf is a judgement from the diff

    def _from_paths(self):
        """Domain-ish folder or file names under the most-changed source files, generic folders skipped."""
        weight = Counter()
        for f in self.files:
            if f["kind"] not in ("source", "schema", "style"):
                continue
            parts = f["path"].split("/")
            names = [p for p in parts[:-1] if p.lower() not in GENERIC_DIRS]
            stem = re.sub(r"(_controller|_service|_spec|_test|\.test|\.spec)$", "", parts[-1].rsplit(".", 1)[0]).lower()
            cand = re.sub(r"^\d+[-_]*", "", names[-1].lower() if names else stem)
            if cand and cand not in GENERIC_DIRS and not cand.isdigit():
                weight[re.sub(r"[^a-z0-9-]+", "-", cand).strip("-")] += f["added"] + f["removed"] + 1
        return [s for s, _ in weight.most_common(5) if s]
