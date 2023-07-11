import locale
import sys

try:
    from setproctitle import setproctitle

    setproctitle("py3status")
except ImportError:
    pass


def main():
    from py3status.argparsers import parse_cli_args

    options = parse_cli_args()

    from py3status.core import Py3statusWrapper

    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error as err:
        print(f"No locale available ({err})")
        sys.exit(2)

    py3 = None
    try:
        py3 = Py3statusWrapper(options)
        py3.setup()
    except (BrokenPipeError, KeyboardInterrupt) as err:
        if py3:
            py3.notify_user(f"Setup interrupted ({err})")
        sys.exit(0)
    except Exception as err:
        if py3:
            py3.report_exception(f"Setup error ({err})")
        else:
            # we cannot report this Exception
            raise
        sys.exit(2)

    try:
        py3.run()
    except (BrokenPipeError, KeyboardInterrupt):
        pass
    except Exception as err:
        py3.report_exception(f"Runtime error ({err})")
        sys.exit(3)
    finally:
        py3.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
