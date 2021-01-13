import argparse
import os
import subprocess
from pathlib import Path
from shutil import which

from platform import python_version
from py3status.version import version


def parse_cli_args():
    """
    Parse the command line arguments
    """
    # get config paths
    home_path = Path.home()
    xdg_home_path = Path(os.environ.get("XDG_CONFIG_HOME", home_path / ".config"))
    xdg_dirs_path = Path(os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg"))

    # get window manager
    with Path(os.devnull).open("w") as devnull:
        if subprocess.call(["pgrep", "i3"], stdout=devnull) == 0:
            wm = "i3"
        else:
            wm = "sway"

    # i3status config file default detection
    # respect i3status' file detection order wrt issue #43
    i3status_config_file_candidates = [
        xdg_home_path / "py3status/config",
        xdg_home_path / "i3status/config",
        xdg_home_path / "i3/i3status.conf",  # custom
        home_path / ".i3status.conf",
        home_path / ".i3/i3status.conf",  # custom
        xdg_dirs_path / "i3status/config",
        Path("/etc/i3status.conf"),
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
        help="enable debug logging in syslog and --log-file",
    )
    parser.add_argument(
        "-g",
        "--gevent",
        action="store_true",
        dest="gevent",
        help="enable gevent monkey patching",
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
        help="enable logging to FILE",
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
        default=60,
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

    # deprecations
    parser.add_argument("-n", "--interval", help=argparse.SUPPRESS)

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
            xdg_home_path / "py3status/modules",
            xdg_home_path / "i3status/py3status",
            xdg_home_path / "i3/py3status",
            home_path / ".i3/py3status",
        ]

    include_paths = []
    for path in options.include_paths:
        path = path.resolve()
        if path.is_dir() and any(path.iterdir()):
            include_paths.append(path)
    options.include_paths = include_paths

    # defaults
    del options.interval
    del options.print_version
    options.minimum_interval = 0.1  # minimum module update interval
    options.click_events = not options.__dict__.pop("disable_click_events")

    # all done
    return options
