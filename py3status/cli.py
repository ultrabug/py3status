import argparse
import os
import subprocess

from platform import python_version
from py3status.version import version


def parse_cli():
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

    class HelpFormatter(argparse.ArgumentDefaultsHelpFormatter):
        def _format_action_invocation(self, action):
            metavar = self._format_args(action, action.dest.upper())
            return "{} {}".format(", ".join(action.option_strings), metavar)

    # command line options
    parser = argparse.ArgumentParser(
        add_help=True,
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
        help="load config (default %(default)s)",
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

    # parse options, command, etc
    options, command = parser.parse_known_args()

    # make versions
    options.python_version = python_version()
    options.version = version
    if options.print_version:
        msg = "py3status version {version} (python {python_version})"
        print(msg.format(**vars(options)))
        parser.exit()

    # handle possible obsolete interval option
    for obsolete_arg in ["-n", "--interval"]:
        if obsolete_arg in command:
            command.pop(command.index(obsolete_arg) + 1)
            command.pop(command.index(obsolete_arg))
    options.cli_command = command

    # defaults
    del options.print_version
    options.minimum_interval = 0.1  # minimum module update interval
    options.click_events = not options.__dict__.pop("disable_click_events")

    # make it i3status if None
    if not options.i3status_path:
        options.i3status_path = "i3status"

    # make include path to search for user modules if None
    if not options.include_paths:
        options.include_paths = [
            "{}/.i3/py3status/".format(home_path),
            "{}/.config/i3/py3status/".format(home_path),
            "{}/i3status/py3status".format(xdg_home_path),
            "{}/i3/py3status".format(xdg_home_path),
        ]

    # all done
    return options
