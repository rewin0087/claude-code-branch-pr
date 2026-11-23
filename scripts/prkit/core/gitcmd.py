"""Git: a thin wrapper around the git CLI for one repository (queries only, no decisions)."""
import subprocess

from .errors import PRError


class Git(object):
    def __init__(self, cwd):
        self.cwd = cwd

    def run(self, args, check=True):
        """stdout of `git <args>`. With check=False a failing command returns ""."""
        r = self._exec(args)
        if r.returncode != 0:
            if check:
                raise PRError("git %s failed:\n%s" % (" ".join(args), r.stderr.strip()))
            return ""
        return r.stdout

    def run_diff(self, args):
        """`git diff` output; `--no-index` exits 1 when the files differ, which is not an error here."""
        r = self._exec(args)
        if r.returncode not in (0, 1):
            raise PRError("git %s failed:\n%s" % (" ".join(args), r.stderr.strip()))
        return r.stdout

    def _exec(self, args):
        return subprocess.run(["git", "-c", "core.quotepath=off"] + list(args), cwd=self.cwd,
                              capture_output=True, text=True, errors="replace")

    # ---- repository facts ----------------------------------------------------------------
    def root(self):
        return self.run(["rev-parse", "--show-toplevel"], check=False).strip()

    def git_dir(self):
        return self.run(["rev-parse", "--git-common-dir"], check=False).strip()

    def branch(self):
        return self.run(["rev-parse", "--abbrev-ref", "HEAD"], check=False).strip()

    def head_sha(self):
        return self.run(["rev-parse", "--short", "HEAD"], check=False).strip()

    def has_commits(self):
        return bool(self.run(["rev-parse", "--verify", "--quiet", "HEAD"], check=False).strip())

    def is_dirty(self):
        return bool(self.run(["status", "--porcelain"], check=False).strip())

    def remote_url(self):
        return self.run(["config", "--get", "remote.origin.url"], check=False).strip()

    def origin_head(self):
        """origin's default branch as 'origin/main', or ''."""
        return self.run(["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"], check=False).strip().replace("refs/remotes/", "")

    # ---- refs and history ----------------------------------------------------------------
    def ref_exists(self, ref):
        return subprocess.run(["git", "rev-parse", "--verify", "--quiet", ref + "^{commit}"], cwd=self.cwd,
                              capture_output=True).returncode == 0

    def resolve_ref(self, ref):
        """ref, or origin/<ref> when only the remote-tracking branch exists, else None."""
        for cand in (ref, "origin/" + ref):
            if self.ref_exists(cand):
                return cand
        return None

    def merge_base(self, base, head="HEAD", check=True):
        return self.run(["merge-base", base, head], check=check).strip()

    def count_commits(self, since, head="HEAD"):
        return int(self.run(["rev-list", "--count", since + ".." + head]).strip() or 0)

    def commits(self, since, head="HEAD"):
        """Commits on the branch, oldest first, with subject and body."""
        raw = self.run(["log", "--reverse", "--no-merges", "--format=%h%x1f%an%x1f%ad%x1f%s%x1f%b%x1e",
                        "--date=short", since + ".." + head], check=False)
        out = []
        for rec in raw.split("\x1e"):
            parts = rec.strip("\n").split("\x1f")
            if len(parts) == 5:
                out.append({"short": parts[0], "author": parts[1], "date": parts[2],
                            "subject": parts[3], "body": parts[4].strip()})
        return out

    # ---- the working tree ----------------------------------------------------------------
    @staticmethod
    def diff_args(since, uncommitted):
        """Diff range: merge-base -> working tree (uncommitted work included) or -> HEAD."""
        return [since] if uncommitted else [since, "HEAD"]

    def untracked(self):
        out = self.run(["ls-files", "--others", "--exclude-standard"], check=False)
        return [p for p in out.split("\n") if p]
