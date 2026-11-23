"""CreateCommand: the `gh` / `glab` command that opens the PR/MR with the written title and description."""


class CreateCommand(object):
    def __init__(self, platform):
        self.platform = platform

    def build(self, base, branch, body_file, title_file, draft=False):
        """-> the command (run from the repo root), or None when the platform has no supported CLI."""
        base = (base or "").replace("origin/", "")
        if self.platform.name == "github":
            return 'gh pr create --base %s --head %s --title "$(cat %s)" --body-file %s%s' % (
                base, branch, title_file, body_file, " --draft" if draft else "")
        if self.platform.name == "gitlab":
            return 'glab mr create --target-branch %s --source-branch %s --title "$(cat %s)" --description "$(cat %s)"%s' % (
                base, branch, title_file, body_file, " --draft" if draft else "")
        return None
