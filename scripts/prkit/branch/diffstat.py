"""DiffStatParser: `git diff --name-status -z` and `--numstat -z` output -> ChangedFile objects."""
from .files import ChangedFile


class DiffStatParser(object):
    @staticmethod
    def name_status(raw):
        """'M\\0path\\0R100\\0old\\0new\\0' -> [ChangedFile] in diff order."""
        fields, files, i = raw.split("\0"), [], 0
        while i < len(fields) and fields[i]:
            code = fields[i][0]
            if code in "RC":
                files.append(ChangedFile.from_status_code(code, fields[i + 2], old_path=fields[i + 1]))
                i += 3
            else:
                files.append(ChangedFile.from_status_code(code, fields[i + 1]))
                i += 2
        return files

    @staticmethod
    def numstat(raw):
        """'1\\t2\\tpath\\0' and renames '1\\t2\\t\\0old\\0new\\0' -> [(path, added, removed)]."""
        fields, out, i = raw.split("\0"), [], 0
        while i < len(fields) and fields[i]:
            added, removed, path = fields[i].split("\t", 2)
            if path == "":
                path, i = fields[i + 2], i + 3
            else:
                i += 1
            out.append((path, added, removed))
        return out
