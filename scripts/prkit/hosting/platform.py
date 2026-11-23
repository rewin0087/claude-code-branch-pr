"""HostingPlatform: GitHub / GitLab / Bitbucket / Azure DevOps, from the origin remote.

It decides what the description is called (pull request or merge request) and the size limit of
the description field. CreateCommand (commands.py) builds the CLI command that opens one.
"""
import re

PLATFORMS = (   # name, remote pattern, noun, short noun, description size limit
    ("github", re.compile(r"github", re.I), "pull request", "PR", 65536),
    ("gitlab", re.compile(r"gitlab", re.I), "merge request", "MR", 1000000),
    ("bitbucket", re.compile(r"bitbucket", re.I), "pull request", "PR", 32768),
    ("azure", re.compile(r"dev\.azure\.com|visualstudio\.com", re.I), "pull request", "PR", 4000),
)
UNKNOWN = ("unknown", "pull request", "PR", 65536)
SSH_REMOTE = re.compile(r"^(?:git@|ssh://git@)([^:/]+)(?::\d+)?[:/](.+?)(?:\.git)?/?$")
HTTP_REMOTE = re.compile(r"^https?://(?:[^@/]+@)?([^/]+)/(.+?)(?:\.git)?/?$")


class HostingPlatform(object):
    def __init__(self, name, noun, short, limit, web_url):
        self.name, self.noun, self.short, self.limit, self.web_url = name, noun, short, limit, web_url

    @classmethod
    def from_remote(cls, remote, override=None):
        web = cls.web_url_of(remote)
        for name, rx, noun, short, limit in PLATFORMS:
            if (override and override == name) or (not override and rx.search(remote or "")):
                return cls(name, noun, short, limit, web)
        return cls(UNKNOWN[0], UNKNOWN[1], UNKNOWN[2], UNKNOWN[3], web)

    @classmethod
    def from_dict(cls, d):
        return cls(d["name"], d["noun"], d["short"], d["limit"], d["web_url"])

    @staticmethod
    def web_url_of(remote):
        """git@github.com:me/repo.git | https://gitlab.com/g/repo.git -> https://host/path"""
        m = SSH_REMOTE.match(remote or "") or HTTP_REMOTE.match(remote or "")
        return "https://%s/%s" % (m.group(1), m.group(2)) if m else None

    def as_dict(self):
        return {"name": self.name, "noun": self.noun, "short": self.short, "limit": self.limit, "web_url": self.web_url}
