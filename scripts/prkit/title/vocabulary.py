"""The Conventional Commits vocabulary (https://www.conventionalcommits.org/en/v1.0.0/)."""
import re

FORMAT = "<type>(<scope>): <description>"
TYPES = ("feat", "fix", "docs", "style", "refactor", "perf", "test", "build", "ci", "chore", "revert")
TYPE_MEANING = {
    "feat": "a new feature or user-visible capability", "fix": "a bug fix", "docs": "documentation only",
    "style": "formatting only, no code meaning change", "refactor": "restructuring without behaviour change",
    "perf": "a performance improvement", "test": "tests only", "build": "build system or dependencies",
    "ci": "CI configuration", "chore": "maintenance that touches no source or tests", "revert": "reverts earlier work",
}
# when a branch's commits use several types, the title takes the one that matters most to users
PRECEDENCE = ("revert", "feat", "fix", "perf", "refactor", "build", "ci", "test", "docs", "style", "chore")
TITLE = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^()\s]+)\))?(?P<bang>!)?: (?P<desc>\S.*)$")
COMMIT_PREFIX = re.compile(r"^(?P<type>[a-z]+)(?:\((?P<scope>[^()\s]+)\))?(?P<bang>!)?:\s")
