from collections import Counter, defaultdict
from datetime import datetime
from time import sleep

from py3status.constants import ON_TRIGGER_ACTIONS

try:
    import pyudev
except ImportError:
    pyudev = None


class UdevMonitor:
    """
    This class allows us to react to udev events.
    """

    def __init__(self, py3_wrapper):
        """
        The udev monitoring will be lazy loaded if a module uses it.
        """
        self.py3_wrapper = py3_wrapper
        self.pyudev_available = pyudev is not None
        self.throttle = defaultdict(Counter)
        self.udev_consumers = defaultdict(list)
        self.udev_observer = None

    def _setup_pyudev_monitoring(self):
        """
        Setup the udev monitor.
        """
        context = pyudev.Context()
        monitor = pyudev.Monitor.from_netlink(context)
        self.udev_observer = pyudev.MonitorObserver(monitor, self._udev_event)
        self.udev_observer.start()
        self.py3_wrapper.log("udev monitoring enabled")

    def _udev_event(self, action, device):
        """
        This is a callback method that will trigger a refresh on subscribers.
        """
        # self.py3_wrapper.log(
        #     f"detected udev action '{action}' on subsystem '{device.subsystem}'"
        # )
        if not self.py3_wrapper.i3bar_running:
            return
        self.trigger_actions(action, device.subsystem)

    def subscribe(self, py3_module, trigger_action, subsystem):
        """
        Subscribe the given module to the given udev subsystem.

        Here we will lazy load the monitor if necessary and return success or
        failure based on the availability of pyudev.
        """
        if self.pyudev_available:
            # lazy load the udev monitor
            if self.udev_observer is None:
                self._setup_pyudev_monitoring()
            if trigger_action not in ON_TRIGGER_ACTIONS:
                self.py3_wrapper.log(
                    f"module {py3_module.module_full_name}: invalid action "
                    f"{trigger_action} on udev events subscription"
                )
                return False
            self.udev_consumers[subsystem].append((py3_module, trigger_action))
            self.py3_wrapper.log(
                f"module {py3_module.module_full_name} subscribed to udev events on {subsystem}"
            )
            return True
        else:
            self.py3_wrapper.log(
                f"pyudev module not installed: module {py3_module.module_full_name} "
                f"not subscribed to events on {subsystem}"
            )
            return False

    def trigger_actions(self, action, subsystem):
        """
        Refresh all modules which subscribed to the given subsystem.
        """
        resolution = datetime.now().strftime("%S")[0]
        for py3_module, trigger_action in self.udev_consumers[subsystem]:
            if trigger_action in ON_TRIGGER_ACTIONS:
                event_key = f"{subsystem}.{action}"
                occurences = self.throttle[event_key][resolution]
                # we allow at most 5 events per 10 seconds window
                if occurences >= 5:
                    self.py3_wrapper.log(
                        f"udev event {event_key}: throttled after {occurences} occurences",
                        level="warning",
                    )
                    continue
                self.py3_wrapper.log(
                    f"{event_key} udev event: refresh consumer {py3_module.module_full_name}"
                )
                sleep(0.1)
                py3_module.force_update()
                self.throttle[event_key].clear()
                self.throttle[event_key][resolution] = occurences + 1
