import sys


def print_line(line):
    """
    Print given line to stdout (i3bar).
    """
    sys.__stdout__.write(f"{line}\n")
    sys.__stdout__.flush()


def print_stderr(line):
    """Print line to stderr
    """
    print(line, file=sys.stderr)
