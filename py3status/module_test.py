import logging
import time
from ast import literal_eval
from sys import argv
from threading import Event

from py3status.core import Common, Module
from py3status.log import log_message, resolve_log_level


class ExcludeModuleFilter(logging.Filter):
    """Suppress module.py framework logs during module_test runs."""

    def __init__(self, path):
        self.path = path

    def filter(self, record):
        return record.pathname != self.path


def setup_logging(level="INFO"):
    level = resolve_log_level(level)
    logging.basicConfig(
        level=level,
        format="%(levelname)s [%(name)s] %(message)s",
    )
    module_path = __file__.replace("_test.py", ".py")
    module_filter = ExcludeModuleFilter(module_path)
    for handler in logging.getLogger().handlers:
        handler.addFilter(module_filter)


class MockPy3statusWrapper:
    """ """

    class EventThread:
        def process_event(self, *arg, **kw):
            pass

    class UdevMonitor:
        def subscribe(self, *arg):
            pass

    def __init__(self, config):
        self.logger = logging.getLogger(__name__)

        self.config = {
            "py3_config": config,
            "include_paths": [],
            "cache_timeout": 1,
            "minimum_interval": 0.1,
            "testing": True,
            "log_file": True,
            "wm": {"msg": "i3-msg", "nag": "i3-nagbar"},
        }
        self.events_thread = self.EventThread()
        self.udev_monitor = self.UdevMonitor()
        self.json_list = []
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

    def clear_timeout_due(self, *arg, **kw):
        pass

    def log(self, message, level="info"):
        log_message(self.logger, message=message, level=level)


def module_test(module_class, config=None):
    if not config:
        config = {}

    # user cli arguments
    log_level = "INFO"
    term = False

    arguments = argv[1:]
    index = 0
    while index < len(arguments):
        arg = arguments[index]
        if arg == "--term":
            term = True
            index += 1
            continue
        if arg == "--log-level" and index + 1 < len(arguments):
            log_level = arguments[index + 1]
            index += 2
            continue
        if arg[0:2] == "--" and index + 1 < len(arguments):
            key = arg[2:]
            value = arguments[index + 1]
            try:
                value = literal_eval(value)
            except (SyntaxError, ValueError):
                pass
            config[key] = value
            index += 2
            continue
        index += 1

    setup_logging(log_level)

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
            for my_method in m.methods.values():
                my_method["cached_until"] = time.monotonic()
            m.run()
            output = m.get_latest()
            for item in output:
                if "instance" in item:
                    del item["instance"]
                if "name" in item:
                    del item["name"]

            if term:
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

            time.sleep(1)
        except KeyboardInterrupt:
            m.kill()
            break
