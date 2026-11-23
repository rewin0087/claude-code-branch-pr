"""FileSignals: signals that come from which files changed (their kind and status), not their content."""

KIND_NOTES = (
    ("migration", "Database migration: check it is reversible, its run order and lock time on large tables"),
    ("schema", "Schema / API contract file changed: consumers may need updating"),
    ("dependency", "Dependencies changed: install/lockfile update needed on deploy"),
    ("infra", "Infrastructure / container config changed"),
    ("ci", "CI pipeline changed"),
)


class FileSignals(object):
    def __init__(self, files):
        self.files = files

    def collect(self, out):
        for kind, note in KIND_NOTES:
            out.add(kind, note, [f.path for f in self.files if f.kind == kind])
        out.add("tests_deleted", "Test files deleted",
                [f.path for f in self.files if f.kind == "test" and f.status == "deleted"])
        source = [f for f in self.files if f.kind == "source"]
        if source and not any(f.kind == "test" for f in self.files):
            out.add("no_tests", "Source changed but no test files changed", [f.path for f in source])
        out.add("source_deleted", "Source files deleted: check nothing else still uses them",
                [f.path for f in source if f.status == "deleted"])
