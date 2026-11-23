"""HostingPlatform: GitHub / GitLab / Bitbucket / Azure DevOps from the origin remote.

It decides what the description is called (pull request or merge request), the size limit of the
description field, and the CLI command that would open one with the written description.
"""
import re

KNOWN = (
    ("github", re.compile(r"github", re.I), "pull request", "PR", 65536),
    ("gitlab", re.compile(r"gitlab", re.I), "merge request", "MR", 1000000),
    ("bitbucket", re.compile(r"bitbucket", re.I), "pull request", "PR", 32768),
    ("azure", re.compile(r"dev\.azure\.com|visualstudio\.com", re.I), "pull request", "PR", 4000),
)


class HostingPlatform(object):
    def __init__(self, name, noun, short, limit, web_url):
        self.name, self.noun, self.short, self.limit, self.web_url = name, noun, short, limit, web_url

    @classmethod
    def from_remote(cls, remote, override=None):
        web = cls.web_url(remote)
        for name, rx, noun, short, limit in KNOWN:
            if (override and override == name) or (not override and rx.search(remote or "")):
                return cls(name, noun, short, limit, web)
        if override == "gitlab" or (web and "gitlab" in web):
            return cls("gitlab", "merge request", "MR", 1000000, web)
        return cls("unknown", "pull request", "PR", 65536, web)

    @staticmethod
    def web_url(remote):
        """git@github.com:me/repo.git | https://gitlab.com/g/repo.git -> https://host/path"""
        m = re.match(r"^(?:git@|ssh://git@)([^:/]+)(?::\d+)?[:/](.+?)(?:\.git)?/?$", remote or "") or \
            re.match(r"^https?://(?:[^@/]+@)?([^/]+)/(.+?)(?:\.git)?/?$", remote or "")
        return "https://%s/%s" % (m.group(1), m.group(2)) if m else None

    def create_command(self, base, branch, body_file, title_file, draft=False):
        """The CLI command that opens the PR/MR with the written description, or None."""
        base = (base or "").replace("origin/", "")
        if self.name == "github":
            return 'gh pr create --base %s --head %s --title "$(cat %s)" --body-file %s%s' % (
                base, branch, title_file, body_file, " --draft" if draft else "")
        if self.name == "gitlab":
            return 'glab mr create --target-branch %s --source-branch %s --title "$(cat %s)" --description "$(cat %s)"%s' % (
                base, branch, title_file, body_file, " --draft" if draft else "")
        return None

    def as_dict(self):
        return {"name": self.name, "noun": self.noun, "short": self.short, "limit": self.limit, "web_url": self.web_url}
