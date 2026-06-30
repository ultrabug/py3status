import logging
from pprint import pformat

from py3status.constants import LOGGING_LOG_LEVELS

PACKAGE_LOGGER_PREFIX = "py3status."
MODULE_LOGGER_PREFIX = "py3status.modules."


class ShortnameFilter(logging.Filter):
    """
    This lets logging formats use `%(shortname)s` instead
    of `%(name)s` when shorter logger names are preferred.

    Examples:
        # shortname
        `py3status.core` -> `core`
        `py3status.events` -> `events`
        `py3status.modules.sysdata` -> `modules.sysdata`
    """

    def filter(self, record):
        if record.name.startswith(PACKAGE_LOGGER_PREFIX):
            record.shortname = record.name[len(PACKAGE_LOGGER_PREFIX) :]
        else:
            record.shortname = record.name

        return True


def module_logger_name(name):
    return f"{MODULE_LOGGER_PREFIX}{name}"


def resolve_log_level(level):
    if not isinstance(level, int):
        # logging.getLevelNamesMapping() is python 3.11+
        # use local mapping instead to support python 3.9+
        level = LOGGING_LOG_LEVELS.get(level.upper(), logging.DEBUG)
    return level


def log_message(logger, message, level):
    level = resolve_log_level(level)
    if not logger.isEnabledFor(level):
        return
    # nicely format logs if we can use pretty print
    if isinstance(message, (dict, list, set, tuple)):
        message = pformat(message)
    elif not isinstance(message, str):
        message = str(message)
    # start on new line if multi-line output
    if "\n" in message:
        message = "\n" + message
    logger.log(level, message)
