"""Findings: the errors (must fix) and warnings (should fix) the checks produce, in order."""


class Findings(object):
    def __init__(self):
        self.errors, self.warnings = [], []

    def error(self, msg):
        self.errors.append(msg)

    def warn(self, msg):
        self.warnings.append(msg)

    def add(self, msg, as_error):
        (self.errors if as_error else self.warnings).append(msg)

    @property
    def ok(self):
        return not self.errors
