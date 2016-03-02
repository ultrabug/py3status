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
        err = sys.exc_info()[1]
        py3.i3_nagbar('setup interrupted (KeyboardInterrupt)')
        sys.exit(0)
    except Exception:
        err = sys.exc_info()[1]
        py3.i3_nagbar('setup error ({})'.format(err))
        py3.stop()
        sys.exit(2)

    try:
        py3.run()
    except Exception:
        err = sys.exc_info()[1]
        py3.i3_nagbar('runtime error ({})'.format(err))
        sys.exit(3)
    except KeyboardInterrupt:
        pass
    finally:
        py3.stop()
        sys.exit(0)


if __name__ == '__main__':
    main()
