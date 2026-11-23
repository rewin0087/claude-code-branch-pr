"""Line rules: each looks at one file's added/removed lines and gathers examples for one signal.

  EnvVarRule, FeatureFlagRule, RouteRule, RemovedDefinitionRule, TodoRule, DebugOutputRule, SecretRule
Every rule has `feed(path, kind, added, removed)` and `emit(signal_list)`.
"""
from .patterns import DEBUG, ENV_VAR, FLAG, PUBLIC_DEF, PY_PRINT, ROUTE, SECRET, TODO


def sample(path, text):
    return "%s: %s" % (path, text.strip()[:100])


class LineRule(object):
    key = note = ""

    def __init__(self):
        self.examples = []

    def feed(self, path, kind, added, removed):
        raise NotImplementedError

    def emit(self, out):
        out.add(self.key, self.note, self.examples)


class EnvVarRule(LineRule):
    key, note = "env_vars", "Environment variables referenced in new code: make sure they are set in every environment"
    BARE_ASSIGNMENT = 10            # the NAME= group: only counts in .env-style files

    def __init__(self):
        super(EnvVarRule, self).__init__()
        self.found = {}

    def feed(self, path, kind, added, removed):
        for text in added:
            for m in ENV_VAR.finditer(text):
                if m.group(self.BARE_ASSIGNMENT) and ".env" not in path.split("/")[-1]:
                    continue
                self.found.setdefault(next(g for g in m.groups() if g), path)

    def emit(self, out):
        out.add(self.key, self.note, ["%s (%s)" % kv for kv in self.found.items()])


class FeatureFlagRule(LineRule):
    key, note = "feature_flags", "Feature flag code touched: note the flag name and its default"

    def feed(self, path, kind, added, removed):
        self.examples += [sample(path, t) for t in added if FLAG.search(t)]


class RouteRule(LineRule):
    key, note = "routes", "Routes / API endpoints / GraphQL fields added or changed"

    def feed(self, path, kind, added, removed):
        if kind in ("source", "config", "schema"):
            self.examples += [sample(path, t) for t in added + removed if ROUTE.search(t)]


class RemovedDefinitionRule(LineRule):
    key, note = "removed_definitions", "Definitions removed or renamed: possible breaking change for callers"

    def feed(self, path, kind, added, removed):
        if kind == "source":
            kept = {a.strip() for a in added}
            self.examples += [sample(path, r) for r in removed if PUBLIC_DEF.search(r) and r.strip() not in kept]


class TodoRule(LineRule):
    key, note = "todos", "TODO / FIXME left in the new code"

    def feed(self, path, kind, added, removed):
        self.examples += [sample(path, t) for t in added if TODO.search(t)]


class DebugOutputRule(LineRule):
    key, note = "debug_output", "Possible debug output left in"

    def feed(self, path, kind, added, removed):
        if kind == "source":
            self.examples += [sample(path, t) for t in added
                              if DEBUG.search(t) or (path.endswith(".py") and PY_PRINT.search(t))]


class SecretRule(LineRule):
    key, note = "secret_like", "Secret-looking value added: make sure it is not a real credential"

    def feed(self, path, kind, added, removed):
        self.examples += [path for t in added if SECRET.search(t)]

    def emit(self, out):
        out.add(self.key, self.note, sorted(set(self.examples)))


RULES = (EnvVarRule, FeatureFlagRule, RouteRule, RemovedDefinitionRule, TodoRule, DebugOutputRule, SecretRule)
