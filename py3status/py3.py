import os
import re
import shlex
from time import time
from subprocess import Popen, call


PY3_CACHE_FOREVER = -1


class Py3:
    """
    Helper object that gets injected as self.py3 into Py3status
    modules that have not got that attribute set already.

    This allows functionality like:
        User notifications
        Forcing module to update (even other modules)
        Triggering events for modules

    Py3 is also used for testing in which case it does not get a module when
    being created.  All methods should work in this situation.
    """

    CACHE_FOREVER = PY3_CACHE_FOREVER

    def __init__(self, module=None, i3s_config=None):
        self._audio = None
        self._module = module
        self._i3s_config = i3s_config
        # we are running through the whole stack.
        # If testing then module is None.
        if module:
            self._output_modules = module._py3_wrapper.output_modules

    def _get_module_info(self, module_name):
        """
        THIS IS PRIVATE AND UNSUPPORTED.
        Get info for named module.  Info comes back as a dict containing.

        'module': the instance of the module,
        'position': list of places in i3bar, usually only one item
        'type': module type py3status/i3status
        """
        if self._module:
            return self._output_modules.get(module_name)

    def i3s_config(self):
        """
        returns the i3s_config dict.
        """
        return self._i3s_config

    def update(self, module_name=None):
        """
        Update a module.  If module_name is supplied the module of that
        name is updated.  Otherwise the module calling is updated.
        """
        if not module_name and self._module:
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
        if module_name and self._module:
            self._module._py3_wrapper.events_thread.process_event(
                module_name, event)

    def prevent_refresh(self):
        """
        Calling this function during the on_click() method of a module will
        request that the module is not refreshed after the event which is the
        default action.
        """
        if self._module:
            self._module.prevent_refresh = True

    def notify_user(self, msg, level='info'):
        """
        Send notification to user.
        level must be 'info', 'error' or 'warning'
        """
        if self._module:
            self._module._py3_wrapper.notify_user(msg, level=level)

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
