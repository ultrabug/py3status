from __future__ import print_function

import sys

try:
    from thread import allocate_lock, start_new_thread
except ImportError:
    from _thread import allocate_lock, start_new_thread


def print_line(line):
    """
    Print given line to stdout (i3bar).
    """
    print(line, file=sys.__stdout__)


def print_stderr(line):
    """Print line to stderr
    """
    print(line, file=sys.stderr)


def sanitize_text(text):
    """
    Clean up newlines from text and ensure that it's unicode
    """
    try:
        text = text.decode()
    except AttributeError:
        # Python 3, already a string
        pass
    return text.strip()


class InputReader(object):
    def __init__(self, io):
        self.io = io
        self.queue = []
        self.lock = allocate_lock()

    def start(self):
        start_new_thread(self._reader, ())

    def get(self):
        with self.lock:
            if self.queue:
                return self.queue.pop(0)

    def _reader(self):
        for line in self.io:
            line = sanitize_text(line)
            if line == '[':
                continue
            with self.lock:
                self.queue.append(line)
