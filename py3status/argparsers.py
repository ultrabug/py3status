import argparse
import os
from pathlib import Path
from platform import python_version
from shutil import which

from py3status.constants import CACHE_TIMEOUT_DEFAULT
from py3status.version import version

# Symbolic search-order templates - single source of truth for both the
# real defaults (resolved via _resolve_path_template()) and the docs
# (main.py's config_search_paths()/module_search_paths() macros).
CONFIG_FILE_TEMPLATES = [
    "$XDG_CONFIG_HOME/py3status/config",
    "$XDG_CONFIG_HOME/i3status/config",
    "$XDG_CONFIG_HOME/i3/i3status.conf",
    "~/.i3status.conf",
    "~/.i3/i3status.conf",
    "$XDG_CONFIG_DIRS/i3status/config",
    "/etc/i3status.conf",
]

MODULE_SEARCH_PATH_TEMPLATES = [
    "$XDG_CONFIG_HOME/py3status/modules",
    "$XDG_CONFIG_HOME/i3status/py3status",
    "$XDG_CONFIG_HOME/i3/py3status",
    "~/.i3/py3status",
]


def _resolve_path_template(template, home_path, xdg_home_path, xdg_dirs_path):
    if template.startswith("$XDG_CONFIG_HOME/"):
        return xdg_home_path / template.removeprefix("$XDG_CONFIG_HOME/")
    if template.startswith("$XDG_CONFIG_DIRS/"):
        return xdg_dirs_path / template.removeprefix("$XDG_CONFIG_DIRS/")
    if template.startswith("~/"):
        return home_path / template.removeprefix("~/")
    return Path(template)


def build_parser():
    """
    Build the command line argument parser, without parsing anything.

    Split out from parse_cli_args() so docs can reuse the real flag
    definitions (eg for a rendered --help) without needing sys.argv or
    triggering the post-parse steps below.
    """
    # get config paths
    home_path = Path.home()
    xdg_home_path = Path(os.environ.get("XDG_CONFIG_HOME", home_path / ".config"))
    xdg_dirs_path = Path(os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg"))

    # get window manager
    sock = os.environ.get('SWAYSOCK')
    if sock and Path(sock).is_socket():
        wm = "sway"
    else:
        wm = "i3"

    # i3status config file default detection
    # respect i3status' file detection order wrt issue #43
    i3status_config_file_candidates = [
        _resolve_path_template(template, home_path, xdg_home_path, xdg_dirs_path)
        for template in CONFIG_FILE_TEMPLATES
    ]
    for path in i3status_config_file_candidates:
        if path.exists():
            i3status_config_file_default = path
            break
    else:
        # if files does not exists, defaults to ~/.i3/i3status.conf
        i3status_config_file_default = i3status_config_file_candidates[3]

    class Parser(argparse.ArgumentParser):
        # print usages and exit on errors
        def error(self, message):
            print(f"\x1b[1;31merror: \x1b[0m{message}")
            self.print_help()
            self.exit(1)

        # hide choices on errors
        def _check_value(self, action, value):
            if action.choices is not None and value not in action.choices:
                raise argparse.ArgumentError(action, f"invalid choice: '{value}'")

    class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
        def _format_action_invocation(self, action):
            metavar = self._format_args(action, action.dest.upper())
            return "{} {}".format(", ".join(action.option_strings), metavar)

    # command line options
    parser = Parser(
        prog="py3status",
        description="The agile, python-powered, i3status wrapper",
        formatter_class=HelpFormatter,
    )
    parser.add_argument(
        "-b",
        "--dbus-notify",
        action="store_true",
        dest="dbus_notify",
        help="send notifications via dbus instead of i3-nagbar",
    )
    parser.add_argument(
        "-c",
        "--config",
        action="store",
        default=i3status_config_file_default,
        dest="i3status_config_path",
        help="load config",
        metavar="FILE",
        type=Path,
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="enable debug logging in syslog or log file if --log-file option is passed",
    )
    parser.add_argument(
        "-i",
        "--include",
        action="append",
        dest="include_paths",
        help="append additional user-defined module paths",
        metavar="PATH",
        type=Path,
    )
    parser.add_argument(
        "-l",
        "--log-file",
        action="store",
        dest="log_file",
        help="enable logging to FILE (this option is not set by default)",
        metavar="FILE",
        type=Path,
    )
    parser.add_argument(
        "-s",
        "--standalone",
        action="store_true",
        dest="standalone",
        help="run py3status without i3status",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        action="store",
        default=CACHE_TIMEOUT_DEFAULT,
        dest="cache_timeout",
        help="default module cache timeout in seconds",
        metavar="INT",
        type=int,
    )
    parser.add_argument(
        "-m",
        "--disable-click-events",
        action="store_true",
        dest="disable_click_events",
        help="disable all click events",
    )
    parser.add_argument(
        "-u",
        "--i3status",
        action="store",
        default=which("i3status") or "i3status",
        dest="i3status_path",
        help="specify i3status path",
        metavar="PATH",
        type=Path,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        dest="print_version",
        help="show py3status version and exit",
    )
    parser.add_argument(
        "--wm",
        action="store",  # add comment to preserve formatting
        dest="wm",
        metavar="WINDOW_MANAGER",
        default=wm,
        choices=["i3", "sway"],
        help="specify window manager i3 or sway",
    )

    return parser


def parse_cli_args():
    """
    Parse the command line arguments
    """
    parser = build_parser()

    # get config paths (again - build_parser() doesn't expose these)
    home_path = Path.home()
    xdg_home_path = Path(os.environ.get("XDG_CONFIG_HOME", home_path / ".config"))
    xdg_dirs_path = Path(os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg"))

    # parse options, command, etc
    options = parser.parse_args()

    # make versions
    options.python_version = python_version()
    options.version = version
    if options.print_version:
        msg = "py3status version {version} (python {python_version}) on {wm}"
        print(msg.format(**vars(options)))
        parser.exit()

    # get wm
    options.wm_name = options.wm
    options.wm = {
        "i3": {"msg": "i3-msg", "nag": "i3-nagbar"},
        "sway": {"msg": "swaymsg", "nag": "swaynag"},
    }[options.wm]

    # make include path to search for user modules if None
    if not options.include_paths:
        options.include_paths = [
            _resolve_path_template(template, home_path, xdg_home_path, xdg_dirs_path)
            for template in MODULE_SEARCH_PATH_TEMPLATES
        ]

    include_paths = []
    for path in options.include_paths:
        path = path.resolve()
        if path.is_dir() and any(path.iterdir()):
            include_paths.append(path)
    options.include_paths = include_paths

    # defaults
    del options.print_version
    options.minimum_interval = 0.1  # minimum module update interval
    options.click_events = not options.__dict__.pop("disable_click_events")

    # all done
    return options
