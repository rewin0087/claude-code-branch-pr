"""FinalizeOptions: the finalize.py flags."""


class FinalizeOptions(object):
    def __init__(self, repo=".", copy=False, draft=False):
        self.repo, self.copy, self.draft = repo, copy, draft
