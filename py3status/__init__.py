try:
    from setproctitle import setproctitle

    setproctitle("py3status")
except ImportError:
    pass
