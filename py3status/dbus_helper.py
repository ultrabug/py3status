from threading import Thread


class DBus:

    def __init__(self, py3_wrapper):
        try:
            from gi.repository import GObject
            from pydbus import SystemBus, SessionBus
            self.GObject = GObject
            self.SessionBus = SessionBus
            self.SystemBus = SystemBus
            self.initialized = True
        except ImportError:
            # FIXME logging
            self.initialized = False
            pass
        self.py3_wrapper = py3_wrapper
        self.started = False
        self.bus_system = None
        self.bus_session = None

    def get_bus(self, bus):
        if bus == "system":
            if self.bus_system is None:
                self.bus_system = self.SystemBus()
            return self.bus_system
        if self.bus_session is None:
            self.bus_session = self.SessionBus()
        return self.bus_session

    def start_main_loop(self):
        self.GObject.threads_init()
        loop = self.GObject.MainLoop()
        t = Thread(target=loop.run)
        t.daemon = True
        t.start()
        self.started = True

    def subscribe(self, path, callback, event, bus):
        if not self.started:
            self.start_main_loop()
        bus = self.get_bus(bus)
        manager = bus.get(path)
        setattr(manager, event, callback)

    def module_update(self, module):
        """
        Create a small helper function that will force a module to update
        """
        def update(*args):
            module.force_update()
        return update
