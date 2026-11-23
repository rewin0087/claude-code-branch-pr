"""FileHunks: diff.patch split per file -> {path: (added lines, removed lines)}."""


class FileHunks(object):
    @staticmethod
    def split(patch_text):
        out, cur = {}, None
        for line in patch_text.split("\n"):
            if line.startswith("diff --git "):
                cur = line.rsplit(" b/", 1)[-1]
                out[cur] = ([], [])
            elif cur is None or line.startswith(("+++ ", "--- ")):
                continue
            elif line.startswith("+"):
                out[cur][0].append(line[1:])
            elif line.startswith("-"):
                out[cur][1].append(line[1:])
        return out
