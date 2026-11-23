"""Git: a thin wrapper around the git CLI for one repository."""
import os
import subprocess

from .errors import PRError

BASE_CANDIDATES = ("main", "master", "develop", "development", "dev", "trunk")


class Git(object):
    def __init__(self, cwd):
        self.cwd = cwd

    def run(self, args, check=True):
        """stdout of `git <args>`. With check=False a failing command returns ""."""
        r = subprocess.run(["git", "-c", "core.quotepath=off"] + list(args), cwd=self.cwd,
                           capture_output=True, text=True, errors="replace")
        if r.returncode != 0:
            if check:
                raise PRError("git %s failed:\n%s" % (" ".join(args), r.stderr.strip()))
            return ""
        return r.stdout

    def run_diff(self, args):
        """`git diff` output; `--no-index` exits 1 when the files differ, which is not an error here."""
        r = subprocess.run(["git", "-c", "core.quotepath=off"] + list(args), cwd=self.cwd,
                           capture_output=True, text=True, errors="replace")
        if r.returncode not in (0, 1):
            raise PRError("git %s failed:\n%s" % (" ".join(args), r.stderr.strip()))
        return r.stdout

    # ---- facts ---------------------------------------------------------------------------
    def root(self):
        return self.run(["rev-parse", "--show-toplevel"], check=False).strip()

    def branch(self):
        return self.run(["rev-parse", "--abbrev-ref", "HEAD"], check=False).strip()

    def head_sha(self):
        return self.run(["rev-parse", "--short", "HEAD"], check=False).strip()

    def has_commits(self):
        return bool(self.run(["rev-parse", "--verify", "--quiet", "HEAD"], check=False).strip())

    def ref_exists(self, ref):
        return subprocess.run(["git", "rev-parse", "--verify", "--quiet", ref + "^{commit}"], cwd=self.cwd,
                              capture_output=True).returncode == 0

    def resolve_ref(self, ref):
        """ref, or origin/<ref> when only the remote-tracking branch exists, else None."""
        for cand in (ref, "origin/" + ref):
            if self.ref_exists(cand):
                return cand
        return None

    def remote_url(self):
        return self.run(["config", "--get", "remote.origin.url"], check=False).strip()

    # ---- the branch ----------------------------------------------------------------------
    def detect_base(self, current, head="HEAD"):
        """The candidate base whose merge-base is closest to head (fewest commits ahead)."""
        cands = []
        origin_head = self.run(["symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"], check=False).strip()
        if origin_head:
            cands.append(origin_head.replace("refs/remotes/", ""))
        for name in BASE_CANDIDATES:
            cands += [name, "origin/" + name]
        best, seen = None, set()
        for ref in cands:
            if ref in seen or ref in (current, "origin/" + current) or not self.ref_exists(ref):
                continue
            seen.add(ref)
            mb = self.run(["merge-base", ref, head], check=False).strip()
            if not mb:
                continue
            ahead = int(self.run(["rev-list", "--count", mb + ".." + head]).strip() or 0)
            if best is None or ahead < best[1]:
                best = (ref, ahead)
        return best[0] if best else None

    def merge_base(self, base, head="HEAD"):
        return self.run(["merge-base", base, head]).strip()

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

    def diff_args(self, since, uncommitted):
        return [since] if uncommitted else [since, "HEAD"]

    def untracked(self):
        out = self.run(["ls-files", "--others", "--exclude-standard"], check=False)
        return [p for p in out.split("\n") if p]

    def ensure_ignored(self, entry):
        """Keep the output folder out of commits without touching the tracked .gitignore."""
        git_dir = self.run(["rev-parse", "--git-common-dir"], check=False).strip()
        if not git_dir:
            return
        exclude = os.path.join(git_dir if os.path.isabs(git_dir) else os.path.join(self.cwd, git_dir), "info", "exclude")
        try:
            os.makedirs(os.path.dirname(exclude), exist_ok=True)
            existing = open(exclude).read() if os.path.exists(exclude) else ""
            if entry not in existing.split("\n"):
                with open(exclude, "a") as fh:
                    fh.write(("" if existing.endswith("\n") or not existing else "\n") + entry + "\n")
        except OSError:
            pass
