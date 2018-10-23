import argparse
import os


def parse_cli():
    """
    Parse the command line arguments
    """

    # FIXME do we really want to do this here?

    # get home path
    home_path = os.path.expanduser("~")

    # i3status config file default detection
    # respect i3status' file detection order wrt issue #43
    i3status_config_file_candidates = [
        "{}/.i3status.conf".format(home_path),
        "{}/i3status/config".format(
            os.environ.get("XDG_CONFIG_HOME", "{}/.config".format(home_path))
        ),
        "{}/.config/i3/".format(home_path),
        "/etc/i3status.conf",
        "{}/i3status/config".format(os.environ.get("XDG_CONFIG_DIRS", "/etc/xdg")),
    ]
    for fn in i3status_config_file_candidates:
        if os.path.isfile(fn):
            i3status_config_file_default = fn
            break
    else:
        # if none of the default files exists, we will default
        # to ~/.i3/i3status.conf
        i3status_config_file_default = "{}/.i3/i3status.conf".format(home_path)

    # command line options
    class HelpFormatter(argparse.HelpFormatter):
        def _format_action_invocation(self, action):
            metavar = self._format_args(action, action.dest.upper())
            return "{} {}".format(", ".join(action.option_strings), metavar)

    parser = argparse.ArgumentParser(formatter_class=HelpFormatter)
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
        metavar="FILE",
        action="store",
        dest="i3status_conf",
        type=str,
        default=i3status_config_file_default,
        help="load config (default %(default)s)",
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
        metavar="PATH",
        action="append",
        dest="include_paths",
        help="append additional module paths",
    )
    parser.add_argument(
        "-l",
        "--log-file",
        metavar="FILE",
        action="store",
        dest="log_file",
        type=str,
        help="enable logging to FILE",
        default=None,
    )
    parser.add_argument(
        "-m",
        "--disable-click-events",
        action="store_false",
        dest="click_events",
        help="disable i3bar click events",
    )
    parser.add_argument(
        "-n",
        "--interval",
        metavar="INT",
        action="store",
        dest="interval",
        type=float,
        help="refresh interval for py3status (default %(default)s)",
        default=1,
    )
    parser.add_argument(
        "-s",
        "--standalone",
        action="store_true",
        help="run py3status without i3status",
    )
    parser.add_argument(
        "-t",
        "--timeout",
        metavar="INT",
        action="store",
        dest="cache_timeout",
        type=int,
        help="injection cache timeout (default %(default)s)",
        default=60,
    )
    parser.add_argument(
        "-v",
        "--version",
        action="store_true",
        help="show py3status version and exit",
    )

    # FIXME we should make all of these explicit so they self document etc
    parser.add_argument("cli_command", nargs="*", help=argparse.SUPPRESS)
    options = parser.parse_args()

    if options.version:
        from platform import python_version
        from py3status.version import version

        print("py3status {} (python {})".format(version, python_version()))
        parser.exit()

    return options
