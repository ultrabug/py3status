from collections import defaultdict

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
        #     "detected udev action '%s' on subsystem '%s'" % (action, device.subsystem)
        # )
        self.trigger_actions(device.subsystem)

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
                    "module %s: invalid action %s on udev events subscription"
                    % (py3_module.module_full_name, trigger_action)
                )
                return False
            self.udev_consumers[subsystem].append((py3_module, trigger_action))
            self.py3_wrapper.log(
                "module %s subscribed to udev events on %s"
                % (py3_module.module_full_name, subsystem)
            )
            return True
        else:
            self.py3_wrapper.log(
                "pyudev module not installed: module %s not subscribed to events on %s"
                % (py3_module.module_full_name, subsystem)
            )
            return False

    def trigger_actions(self, subsystem):
        """
        Refresh all modules which subscribed to the given subsystem.
        """
        for py3_module, trigger_action in self.udev_consumers[subsystem]:
            if trigger_action in ON_TRIGGER_ACTIONS:
                self.py3_wrapper.log(
                    "%s udev event, refresh consumer %s"
                    % (subsystem, py3_module.module_full_name)
                )
                py3_module.force_update()
