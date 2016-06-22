import os
import re
import shlex
from time import time
from subprocess import Popen, call


PY3_CACHE_FOREVER = -1
PY3_LOG_ERROR = 'error'
PY3_LOG_INFO = 'info'
PY3_LOG_WARNING = 'warning'


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
    LOG_ERROR = PY3_LOG_ERROR
    LOG_INFO = PY3_LOG_INFO
    LOG_WARNING = PY3_LOG_WARNING

    def __init__(self, module):
        self._audio = None
        self._module = module
        self._output_modules = module._py3_wrapper.output_modules

    def _get_module_info(self, module_name):
        """
        THIS IS PRIVATE AND UNSUPPORTED.
        Get info for named module.  Info comes back as a dict containing.

        'module': the instance of the module,
        'position': list of places in i3bar, usually only one item
        'type': module type py3status/i3status
        """
        return self._output_modules.get(module_name)

    def log(self, message, level=LOG_INFO):
        """
        Log the message.
        The level must be one of LOG_ERROR, LOG_INFO or LOG_WARNING
        """
        assert level in [
            self.LOG_ERROR, self.LOG_INFO, self.LOG_WARNING
        ], 'level must be LOG_ERROR, LOG_INFO or LOG_WARNING'

        if self._module:
            message = 'Module `{}`: {}'.format(
                self._module.module_full_name, message)
            self._module._py3_wrapper.log(message, level)

    def update(self, module_name=None):
        """
        Update a module.  If module_name is supplied the module of that
        name is updated.  Otherwise the module calling is updated.
        """
        if not module_name:
            return self._module.force_update()
        else:
            module_info = self._get_module_info(module_name)
            if module_info:
                module_info['module'].force_update()

    def get_output(self, module_name):
        """
        Return the output of the named module.  This will be a list.
        """
        output = []
        module_info = self._get_module_info(module_name)
        if module_info:
            output = module_info['module'].get_latest()
        return output

    def trigger_event(self, module_name, event):
        """
        Trigger an event on a named module.
        """
        if module_name:
            self._module._py3_wrapper.events_thread.process_event(
                module_name, event)

    def prevent_refresh(self):
        """
        Calling this function during the on_click() method of a module will
        request that the module is not refreshed after the event. By default
        the module is updated after the on_click event has been processed.
        """
        self._module.prevent_refresh = True

    def notify_user(self, msg, level='info', rate_limit=5):
        """
        Send a notification to the user.
        level must be 'info', 'error' or 'warning'.
        rate_limit is the time period in seconds during which this message
        should not be repeated.
        """
        module_name = self._module.module_full_name
        self._module._py3_wrapper.notify_user(
            msg, level=level, rate_limit=rate_limit, module_name=module_name)

    def time_in(self, seconds=0):
        """
        Returns the time a given number of seconds into the future.  Helpful
        for creating the `cached_until` value for the module output.
        """
        return time() + seconds

    def safe_format(self, format_string, param_dict):
        """
        Perform a safe formatting of a string.  Using format fails if the
        format string contains placeholders which are missing.  Since these can
        be set by the user it is possible that they add unsupported items.
        This function will escape missing placemolders so that modules do not
        crash hard.
        """
        keys = param_dict.keys()

        def replace_fn(match):
            item = match.group()
            if item[1:-1] in keys:
                return item
            return '{' + item + '}'

        format_string = re.sub('\{[^}]*\}', replace_fn, format_string)
        return format_string.format(**param_dict)

    def check_commands(self, cmd_list):
        """
        Checks to see if commands in list are available using `which`.
        Returns the first available command.
        """
        devnull = open(os.devnull, 'w')
        for cmd in cmd_list:
            c = shlex.split('which {}'.format(cmd))
            if call(c, stdout=devnull, stderr=devnull) == 0:
                return cmd

    def play_sound(self, sound_file):
        """
        Plays sound_file if possible.
        """
        self.stop_sound()
        cmd = self.check_commands(['paplay', 'play'])
        if cmd:
            sound_file = os.path.expanduser(sound_file)
            c = shlex.split('{} {}'.format(cmd, sound_file))
            self._audio = Popen(c)

    def stop_sound(self):
        """
        Stops any currently playing sounds for this module.
        """
        if self._audio:
            self._audio.kill()
            self._audio = None
