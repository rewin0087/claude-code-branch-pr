"""CollectOptions: the collect.py flags."""


class CollectOptions(object):
    def __init__(self, repo=".", base=None, committed_only=False, template=None, no_template=False, platform=None):
        self.repo, self.base, self.committed_only = repo, base, committed_only
        self.template, self.no_template, self.platform = template, no_template, platform
