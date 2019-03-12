from sys import argv
from threading import Event
from time import sleep, time

from py3status.core import Common, Module


class MockPy3statusWrapper:
    """
    """

    class EventThread:
        def process_event(self, *arg, **kw):
            pass

    class UdevMonitor:
        def subscribe(self, *arg):
            pass

    def __init__(self, config):
        self.config = {
            "py3_config": config,
            "include_paths": [],
            "debug": False,
            "cache_timeout": 1,
            "minimum_interval": 0.1,
            "testing": True,
            "log_file": True,
            "wm": {"msg": "i3-msg", "nag": "i3-nagbar"},
        }
        self.events_thread = self.EventThread()
        self.udev_monitor = self.UdevMonitor()
        self.i3status_thread = None
        self.lock = Event()
        self.output_modules = {}
        self.running = True

        self.lock.set()

        # shared code
        common = Common(self)
        self.get_config_attribute = common.get_config_attribute
        self.report_exception = common.report_exception

    def notify_update(self, *arg, **kw):
        pass

    def notify_user(self, *arg, **kw):
        pass

    def timeout_queue_add(self, *arg, **kw):
        pass

    def log(self, *arg, **kw):
        print(arg[0])


def module_test(module_class, config=None):

    if not config:
        config = {}

    py3_config = {
        "general": {
            "color_bad": "#FF0000",
            "color_degraded": "#FFFF00",
            "color_good": "#00FF00",
        },
        "py3status": {},
        ".module_groups": {},
        "test_module": config,
    }

    mock = MockPy3statusWrapper(py3_config)

    module = module_class()
    m = Module("test_module", {}, mock, module)
    m.sleeping = True
    m.prepare_module()

    while not m.error_messages:
        try:
            for meth in m.methods:
                m.methods[meth]["cached_until"] = time()
            m.run()
            output = m.get_latest()
            for item in output:
                if "instance" in item:
                    del item["instance"]
                if "name" in item:
                    del item["name"]

            if "--term" in argv:
                line = "\033[0m"
                for item in output:
                    if item.get("urgent"):
                        line += "\033[41m"
                    else:
                        color = item.get("color")
                        if color:
                            line += "\033[38;2;{};{};{}m".format(
                                *[int(color[1:][i : i + 2], 16) for i in (0, 2, 4)]
                            )
                    line += item["full_text"] + "\033[0m"
                print(line)
            else:
                if len(output) == 1:
                    output = output[0]
                print(output)

            sleep(1)
        except KeyboardInterrupt:
            m.kill()
            break
