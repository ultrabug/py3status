import locale
import sys

try:
    from setproctitle import setproctitle

    setproctitle("py3status")
except ImportError:
    pass

try:
    # python3
    IOPipeError = BrokenPipeError
except NameError:
    # python2
    IOPipeError = IOError


def main():
    from py3status.argparsers import parse_cli_args

    options = parse_cli_args()
    # detect gevent option early because monkey patching should be done before
    # everything else starts kicking
    if options.gevent:
        try:
            from gevent import monkey

            monkey.patch_all()
        except Exception:
            # user will be notified when we start
            pass

    from py3status.core import Py3statusWrapper

    try:
        locale.setlocale(locale.LC_ALL, "")
    except locale.Error:
        print("No locale available")
        sys.exit(2)

    py3 = None
    try:
        py3 = Py3statusWrapper(options)
        py3.setup()
    except (IOPipeError, KeyboardInterrupt):
        if py3:
            py3.notify_user("Setup interrupted")
        sys.exit(0)
    except Exception:
        if py3:
            py3.report_exception("Setup error")
        else:
            # we cannot report this Exception
            raise
        sys.exit(2)

    try:
        py3.run()
    except (IOPipeError, KeyboardInterrupt):
        pass
    except Exception:
        py3.report_exception("Runtime error")
        sys.exit(3)
    finally:
        py3.stop()
        sys.exit(0)


if __name__ == "__main__":
    main()
