"""SignalList: the collected signals, each with a note and a few examples."""

MAX_EXAMPLES = 6


class SignalList(object):
    def __init__(self):
        self.items = []

    def add(self, key, note, examples):
        if examples:
            self.items.append({"signal": key, "note": note, "count": len(examples), "examples": list(examples)[:MAX_EXAMPLES]})
