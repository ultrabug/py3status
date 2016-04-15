import locale
import sys

from py3status.core import Py3statusWrapper

try:
    from setproctitle import setproctitle
    setproctitle('py3status')
except ImportError:
    pass


def main():
    try:
        locale.setlocale(locale.LC_ALL, '')
        py3 = Py3statusWrapper()
        py3.setup()
    except KeyboardInterrupt:
        py3.notify_user('Setup interrupted (KeyboardInterrupt).')
        sys.exit(0)
    except Exception:
        py3.report_exception('Setup error')
        sys.exit(2)

    try:
        py3.run()
    except Exception:
        py3.report_exception('Runtime error')
        sys.exit(3)
    except KeyboardInterrupt:
        pass
    finally:
        py3.stop()
        sys.exit(0)


if __name__ == '__main__':
    main()
