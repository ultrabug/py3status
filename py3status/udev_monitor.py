from collections import defaultdict

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
        self.enabled = pyudev is not None
        self.py3_wrapper = py3_wrapper
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
        self.refresh_subscribers(device.subsystem)

    def subscribe(self, py3_module, subsystem):
        """
        Subscribe the given module to the given udev subsystem.

        Here we will lazy load the monitor if necessary and return success or
        failure based on the availability of pyudev.
        """
        if self.enabled:
            # lazy load the udev monitor
            if self.udev_observer is None:
                self._setup_pyudev_monitoring()
            self.udev_consumers[subsystem].append(py3_module)
            self.py3_wrapper.log(
                "module %s subscribed to udev events on %s"
                % (py3_module._module_full_name, subsystem)
            )
            return True
        else:
            self.py3_wrapper.log(
                "could not subscribe module %s to udev events on %s"
                % (py3_module._module_full_name, subsystem)
            )
            return False

    def refresh_subscribers(self, subsystem):
        """
        Refresh all modules which subscribed to the given subsystem.
        """
        for py3_module in self.udev_consumers[subsystem]:
            self.py3_wrapper.log(
                "%s udev event, refresh consumer %s"
                % (subsystem, py3_module._module_full_name)
            )
            py3_module.update()
