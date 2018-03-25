import argparse
import os


def parse_cli():
    """
    Parse the command line arguments
    """

    # FIXME do we really want to do this here?

    # get home path
    home_path = os.path.expanduser('~')

    # i3status config file default detection
    # respect i3status' file detection order wrt issue #43
    i3status_config_file_candidates = [
        '{}/.i3status.conf'.format(home_path),
        '{}/i3status/config'.format(os.environ.get(
            'XDG_CONFIG_HOME', '{}/.config'.format(home_path))),
        '/etc/i3status.conf',
        '{}/i3status/config'.format(os.environ.get('XDG_CONFIG_DIRS',
                                                   '/etc/xdg'))
    ]
    for fn in i3status_config_file_candidates:
        if os.path.isfile(fn):
            i3status_config_file_default = fn
            break
    else:
        # if none of the default files exists, we will default
        # to ~/.i3/i3status.conf
        i3status_config_file_default = '{}/.i3/i3status.conf'.format(
            home_path)

    # command line options
    parser = argparse.ArgumentParser(
        description='The agile, python-powered, i3status wrapper')
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument(
        '-b',
        '--dbus-notify',
        action="store_true",
        default=False,
        dest="dbus_notify",
        help=("use notify-send to send user notifications "
              "rather than i3-nagbar, "
              "requires a notification daemon eg dunst"))
    parser.add_argument(
        '-c',
        '--config',
        action="store",
        dest="i3status_conf",
        type=str,
        default=i3status_config_file_default,
        help="path to i3status config file")
    parser.add_argument(
        '-d',
        '--debug',
        action="store_true",
        help="be verbose in syslog")
    parser.add_argument(
        '-g',
        '--gevent',
        action="store_true",
        default=False,
        dest="gevent",
        help="enable gevent monkey patching (default False)")
    parser.add_argument(
        '-i',
        '--include',
        action="append",
        dest="include_paths",
        help=("include user-written modules from those "
              "directories (default ~/.i3/py3status)"))
    parser.add_argument(
        '-l',
        '--log-file',
        action="store",
        dest="log_file",
        type=str,
        default=None,
        help="path to py3status log file")
    parser.add_argument(
        '-n',
        '--interval',
        action="store",
        dest="interval",
        type=float,
        default=1,
        help="update interval in seconds (default 1 sec)")
    parser.add_argument(
        '-s',
        '--standalone',
        action="store_true",
        help="standalone mode, do not use i3status")
    parser.add_argument(
        '-t',
        '--timeout',
        action="store",
        dest="cache_timeout",
        type=int,
        default=60,
        help="default injection cache timeout in seconds (default 60 sec)")
    parser.add_argument(
        '-m',
        '--disable-click-events',
        action="store_true",
        dest="disable_click_events",
        default=False,
        help="disable all click events")
    parser.add_argument(
        '-v',
        '--version',
        action="store_true",
        help="show py3status version and exit")
    # FIXME we should make all of these explicit so they self document etc
    parser.add_argument('cli_command', nargs='*', help=argparse.SUPPRESS)

    options = parser.parse_args()

    # only asked for version
    if options.version:
        import sys
        from platform import python_version
        from py3status.version import version
        print('py3status version {} (python {})'.format(version,
                                                        python_version()))
        sys.exit(0)

    # all done
    return options
