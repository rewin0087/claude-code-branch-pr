"""Clipboard: copy text with the OS clipboard tool (pbcopy, wl-copy, xclip, xsel or clip.exe)."""
import shutil
import subprocess

TOOLS = (["pbcopy"], ["wl-copy"], ["xclip", "-selection", "clipboard"], ["xsel", "--clipboard", "--input"], ["clip.exe"])


class Clipboard(object):
    @staticmethod
    def copy(text):
        """-> the tool used, or None when no clipboard tool is available or it failed."""
        for cmd in TOOLS:
            if shutil.which(cmd[0]):
                try:
                    subprocess.run(cmd, input=text, text=True, check=True, timeout=10)
                    return cmd[0]
                except (subprocess.SubprocessError, OSError):
                    continue
        return None
