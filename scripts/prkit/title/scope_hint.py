"""ScopeHint: scope candidates, from the commits' own scopes, then the most-changed source areas."""
import re
from collections import Counter

GENERIC_DIRS = {"app", "src", "lib", "pkg", "internal", "packages", "services", "models", "controllers", "views",
                "components", "helpers", "utils", "api", "spec", "tests", "test", "config", "db", "migrate", "(root)"}
SCOPE_KINDS = ("source", "schema", "style")
ROLE_SUFFIX = re.compile(r"(_controller|_service|_spec|_test|\.test|\.spec)$")
MAX_SCOPES = 5


class ScopeHint(object):
    def __init__(self, commit_prefixes, files):
        self.prefixes, self.files = commit_prefixes, files

    def candidates(self):
        from_commits = self.from_commits()
        return (from_commits + [s for s in self.from_paths() if s not in from_commits])[:MAX_SCOPES]

    def from_commits(self):
        counts = Counter(scope for _, scope in self.prefixes if scope)
        return [s for s, _ in counts.most_common(3)]

    def from_paths(self):
        """Domain-ish folder or file names of the most-changed source files, generic folders skipped."""
        weight = Counter()
        for f in self.files:
            if f["kind"] not in SCOPE_KINDS:
                continue
            name = self.area_name(f["path"])
            if name and name not in GENERIC_DIRS and not name.isdigit():
                weight[re.sub(r"[^a-z0-9-]+", "-", name).strip("-")] += f["added"] + f["removed"] + 1
        return [s for s, _ in weight.most_common(MAX_SCOPES) if s]

    @staticmethod
    def area_name(path):
        parts = path.split("/")
        folders = [p for p in parts[:-1] if p.lower() not in GENERIC_DIRS]
        stem = ROLE_SUFFIX.sub("", parts[-1].rsplit(".", 1)[0]).lower()
        return re.sub(r"^\d+[-_]*", "", folders[-1].lower() if folders else stem)
