import argparse
import os
import subprocess

from platform import python_version
from py3status.version import version


def parse_cli_args():
    """
    Parse the command line arguments
    """
    # get config paths
    home_path = os.path.expanduser("~")
    xdg_home_path = os.environ.get("XDG_CONFIG_HOME", "{}/.config".format(home_path))
    xdg_dirs_path = os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg")

    # get i3status path
    try:
        with open(os.devnull, "w") as devnull:
            command = ["which", "i3status"]
            i3status_path = (
                subprocess.check_output(command, stderr=devnull).decode().strip()
            )
    except subprocess.CalledProcessError:
        i3status_path = None

    # get window manager
    with open(os.devnull, "w") as devnull:
        if subprocess.call(["pgrep", "i3"], stdout=devnull) == 0:
            wm = "i3"
        else:
            wm = "sway"

    # i3status config file default detection
    # respect i3status' file detection order wrt issue #43
    i3status_config_file_candidates = [
        "{}/.i3status.conf".format(home_path),
        "{}/i3status/config".format(xdg_home_path),
        "{}/.config/i3/i3status.conf".format(home_path),
        "{}/.i3/i3status.conf".format(home_path),
        "{}/i3status/config".format(xdg_dirs_path),
        "/etc/i3status.conf",
    ]
    for fn in i3status_config_file_candidates:
        if os.path.isfile(fn):
            i3status_config_file_default = fn
            break
    else:
        # if files does not exists, defaults to ~/.i3/i3status.conf
        i3status_config_file_default = i3status_config_file_candidates[3]

    class Parser(argparse.ArgumentParser):
        # print usages and exit on errors
        def error(self, message):
            print("\x1b[1;31merror: \x1b[0m{}".format(message))
            self.print_help()
            self.exit(1)

        # hide choices on errors
        def _check_value(self, action, value):
            if action.choices is not None and value not in action.choices:
                raise argparse.ArgumentError(
                    action, "invalid choice: '{}'".format(value)
                )

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
        type=str,
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
    )
    parser.add_argument(
        "-l",
        "--log-file",
        action="store",
        dest="log_file",
        help="enable logging to FILE",
        metavar="FILE",
        type=str,
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
        default=i3status_path,
        dest="i3status_path",
        help="specify i3status path",
        metavar="PATH",
        type=str,
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

    # make it i3status if None
    if not options.i3status_path:
        options.i3status_path = "i3status"

    # make include path to search for user modules if None
    if not options.include_paths:
        options.include_paths = [
            "{}/.i3/py3status".format(home_path),
            "{}/.config/i3/py3status".format(home_path),
            "{}/i3status/py3status".format(xdg_home_path),
            "{}/i3/py3status".format(xdg_home_path),
        ]

    include_paths = []
    for path in options.include_paths:
        path = os.path.abspath(path)
        if os.path.isdir(path) and os.listdir(path):
            include_paths.append(path)
    options.include_paths = include_paths

    # defaults
    del options.interval
    del options.print_version
    options.minimum_interval = 0.1  # minimum module update interval
    options.click_events = not options.__dict__.pop("disable_click_events")

    # all done
    return options
