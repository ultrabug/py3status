import argparse
import os
import subprocess


def parse_cli():
    """
    Parse the command line arguments
    """

    # FIXME do we really want to do this here?

    # get home path
    home_path = os.path.expanduser("~")

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
        "{}/i3status/config".format(
            os.environ.get("XDG_CONFIG_HOME", "{}/.config".format(home_path))
        ),
        "{}/.config/i3/i3status.conf".format(home_path),
        "{}/.i3/i3status.conf".format(home_path),
        "{}/i3status/config".format(os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg")),
        "/etc/i3status.conf",
    ]
    for fn in i3status_config_file_candidates:
        if os.path.isfile(fn):
            i3status_config_file_default = fn
            break
    else:
        # if none of the default files exists, we will default
        # to ~/.i3/i3status.conf
        i3status_config_file_default = "{}/.i3/i3status.conf".format(home_path)

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
        default=False,
        dest="dbus_notify",
        help="send notifications via dbus instead of i3-nagbar",
    )
    parser.add_argument(
        "-c",
        "--config",
        action="store",
        default=i3status_config_file_default,
        dest="i3status_conf",
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
        default=False,
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
        default=None,
        dest="log_file",
        help="enable logging to FILE",
        metavar="FILE",
        type=str,
    )
    parser.add_argument(
        "-s", "--standalone", action="store_true", help="run py3status without i3status"
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
        default=False,
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
        "-v", "--version", action="store_true", help="show py3status version and exit"
    )

    options, command = parser.parse_known_args()

    # handle possible obsolete interval option
    for obsolete_arg in ["-n", "--interval"]:
        if obsolete_arg in command:
            command.pop(command.index(obsolete_arg) + 1)
            command.pop(command.index(obsolete_arg))
    options.cli_command = command

    # only asked for version
    if options.version:
        import sys
        from platform import python_version
        from py3status.version import version

        print("py3status version {} (python {})".format(version, python_version()))
        sys.exit(0)

    # make it i3status if None
    if not options.i3status_path:
        options.i3status_path = "i3status"

    # all done
    return options
