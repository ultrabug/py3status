PY3_CACHE_FOREVER = -1

PY3_COLOR_BAD = 1
PY3_COLOR_DEGRADED = 2
PY3_COLOR_GOOD = 3

COLOR_MAPPINGS = {
    'color': None,
    'color_bad': PY3_COLOR_BAD,
    'color_degraded': PY3_COLOR_DEGRADED,
    'color_good': PY3_COLOR_GOOD,
}


class Py3:
    """
    Helper object that gets injected as self.py3 into Py3status
    modules that have not got that attribute set already.

    This allows functionality like:
        User notifications
        Forcing module to update (even other modules)
        Triggering events for modules
    """

    CACHE_FOREVER = PY3_CACHE_FOREVER
    COLOR_BAD = PY3_COLOR_BAD
    COLOR_DEGRADED = PY3_COLOR_DEGRADED
    COLOR_GOOD = PY3_COLOR_GOOD

    def __init__(self, module):
        self._module = module

    def update(self, module_name=None):
        """
        Update a module.  If module_name is supplied the module of that
        name is updated.  Otherwise the module calling is updated.
        """
        if not module_name:
            return self._module.force_update()
        else:
            module = self.get_module_info(self, module_name).get(module_name)
            if module:
                module.force_update()

    def get_module_info(self, module_name):
        """
        Helper function to get info for named module.
        Info comes back as a dict containing.

        'module': the instance of the module,
        'position': list of places in i3bar, usually only one item
        'type': module type py3status/i3status
        """
        return self._module._py3_wrapper.output_modules.get(module_name)

    def trigger_event(self, module_name, event):
        """
        Trigger the event on named module
        """
        if module_name:
            self._module._py3_wrapper.events_thread.process_event(
                module_name, event)

    def notify_user(self, msg, level='info'):
        """
        Send notification to user.
        level can be 'info', 'error' or 'warning'
        """
        self._module._py3_wrapper.notify_user(msg, level=level)
