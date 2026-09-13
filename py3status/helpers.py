import logging
import sys

logger = logging.getLogger(__name__)


def get_module_name(name):
    # the bare module type from a "type[ instance]" identity string
    # (eg "disk /" -> "disk")
    return name.partition(" ")[0]


def get_instance_name(name):
    # the instance half of a "type[ instance]" identity string
    # (eg "disk /" -> "/"), or "" if there is none
    return name.partition(" ")[2]


def print_stderr(line):
    """Print line to stderr"""
    print(line, file=sys.stderr)


def next_unclaimed_name(candidates, claimed):
    """
    Return the first of `candidates` not in `claimed`. Warns if a later
    candidate had to be used because an earlier one was already claimed.
    """
    first = None
    for index, candidate in enumerate(candidates):
        if first is None:
            first = candidate
        if candidate not in claimed:
            if index:
                logger.warning("'%s' already claimed - using '%s' instead", first, candidate)
            return candidate
    # unreachable today (every caller's candidates are unbounded), but
    # static analysis can't know that - fail loudly, not with None.
    raise ValueError("no unclaimed candidate found")
