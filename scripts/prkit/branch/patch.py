"""PatchWriter: diff.patch, reviewable files first (lockfiles and build output left out).

Each ChangedFile gets `diff_line`, its start line in the patch, so a big diff can be read in parts.
"""
import os


class PatchWriter(object):
    def __init__(self, changeset):
        self.cs, self.git = changeset, changeset.git

    def write(self, path):
        """-> the number of lines written."""
        chunks, line = [], 1
        for f in self.cs.ordered():
            if f.kind == "noise":
                continue
            text = self.file_diff(f)
            if not text:
                continue
            f.diff_line = line
            text = text if text.endswith("\n") else text + "\n"
            chunks.append(text)
            line += text.count("\n")
        with open(path, "w") as fh:
            fh.write("".join(chunks))
        return line - 1

    def file_diff(self, f):
        if f.binary:
            return "Binary file %s: %s\n" % (f.status, f.path)
        if self.cs.since and not (self.cs.uncommitted and self.cs.is_untracked(f)):
            paths = [f.old_path, f.path] if f.old_path else [f.path]
            return self.git.run(["diff", "--no-color", "--no-ext-diff", "-M", "-U5"]
                                + self.git.diff_args(self.cs.since, self.cs.uncommitted) + ["--"] + paths, check=False)
        return self.git.run_diff(["diff", "--no-color", "--no-index", "--", os.devnull, f.path])
