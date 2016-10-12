import sys
import os
import shlex
from time import time
from subprocess import Popen, call

from py3status.formatter import Formatter


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

    Py3 is also used for testing in which case it does not get a module when
    being created.  All methods should work in this situation.
    """

    CACHE_FOREVER = PY3_CACHE_FOREVER

    LOG_ERROR = PY3_LOG_ERROR
    LOG_INFO = PY3_LOG_INFO
    LOG_WARNING = PY3_LOG_WARNING

    # All Py3 Instances can share a formatter
    _formatter = Formatter()

    def __init__(self, module=None, i3s_config=None, py3status=None):
        self._audio = None
        self._colors = {}
        self._i3s_config = i3s_config or {}
        self._module = module
        self._is_python_2 = sys.version_info < (3, 0)

        if py3status:
            self._py3status_module = py3status

        # we are running through the whole stack.
        # If testing then module is None.
        if module:
            self._output_modules = module._py3_wrapper.output_modules
            if not i3s_config:
                config = self._module.i3status_thread.config['general']
                self._i3s_config = config
            self._py3status_module = module.module_class

    def __getattr__(self, name):
        """
        Py3 can provide COLOR constants
        eg COLOR_GOOD, COLOR_BAD, COLOR_DEGRADED
        but also any constant COLOR_XXX we find this color in the config
        if it exists
        """
        if not name.startswith('COLOR_'):
            raise AttributeError
        name = name.lower()
        if name not in self._colors:
            if self._module:
                color_fn = self._module._py3_wrapper.get_config_attribute
                color = color_fn(self._module.module_full_name, name)
            else:
                color = self._i3s_config.get(name)
            self._colors[name] = color
        return self._colors[name]

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

    def is_python_2(self):
        """
        True if the version of python being used is 2.x
        Can be helpful for fixing python 2 compatability issues
        """
        return self._is_python_2

    def is_my_event(self, event):
        """
        Checks if an event triggered belongs to the module recieving it.  This
        is mainly for containers who will also recieve events from any children
        they have.

        Returns True if the event name and instance match that of the module
        checking.
        """
        if not self._module:
            return False

        return (
            event.get('name') == self._module.module_name and
            event.get('instance') == self._module.module_inst
        )

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
        request that the module is not refreshed after the event. By default
        the module is updated after the on_click event has been processed.
        """
        if self._module:
            self._module.prevent_refresh = True

    def notify_user(self, msg, level='info', rate_limit=5):
        """
        Send a notification to the user.
        level must be 'info', 'error' or 'warning'.
        rate_limit is the time period in seconds during which this message
        should not be repeated.
        """
        if self._module:
            # force unicode for python2 str
            if self._is_python_2 and isinstance(msg, str):
                msg = msg.decode('utf-8')
            module_name = self._module.module_full_name
            self._module._py3_wrapper.notify_user(
                msg, level=level, rate_limit=rate_limit, module_name=module_name)

    def register_function(self, function_name, function):
        """
        Register a function for the module.

        The following functions can be registered

        > __content_function()__
        >
        > Called to discover what modules a container is displaying.  This is
        > used to determine when updates need passing on to the container and
        > also when modules can be put to sleep.
        >
        > the function must return a set of module names that are being
        > displayed.
        >
        > Note: This function should only be used by containers.
        >
        > __urgent_function(module_names)__
        >
        > This function will be called when one of the contents of a container
        > has changed from a non-urgent to an urgent state.  It is used by the
        > group module to switch to displaying the urgent module.
        >
        > `module_names` is a list of modules that have become urgent
        >
        > Note: This function should only be used by containers.
        """
        if self._module:
            my_info = self._get_module_info(self._module.module_full_name)
            my_info[function_name] = function

    def time_in(self, seconds=None, sync_to=None, offset=0):
        """
        Returns the time a given number of seconds into the future.  Helpful
        for creating the `cached_until` value for the module output.

        Note: form version 3.1 modules no longer need to explicitly set a
        `cached_until` in their response unless they wish to directly control
        it.

        seconds specifies the number of seconds that should occure before the
        update is required.

        sync_to causes the update to be syncronised to a time period.  1 would
        cause the update on the second, 60 to the nearest minute. By defalt we
        syncronise to the nearest second. 0 will disable this feature.

        offset is used to alter the base time used. A timer that started at a
        certain time could set that as the offset and any syncronisation would
        then be relative to that time.
        """

        if seconds is None:
            # If we have a sync_to then seconds can be 0
            if sync_to and sync_to > 0:
                seconds = 0
            else:
                try:
                    # use py3status modules cache_timeout
                    seconds = self._py3status_module.cache_timeout
                except AttributeError:
                    # use default cache_timeout
                    seconds = self._module.config['cache_timeout']

        # Unless explicitly set we sync to the nearest second
        # Unless the requested update is in less than a second
        if sync_to is None:
            if seconds and seconds < 1:
                sync_to = 0
            else:
                sync_to = 1

        requested = time() + seconds - offset

        # if sync_to then we find the sync time for the requested time
        if sync_to:
            requested = (requested + sync_to) - (requested % sync_to)

        return requested + offset

    def safe_format(self, format_string, param_dict=None):
        """
        Parser for advanced formating.

        Unknown placeholders will be shown in the output eg `{foo}`

        Square brackets `[]` can be used. The content of them will be removed
        from the output if there is no valid placeholder contained within.
        They can also be nested.

        A pipe (vertical bar) `|` can be used to divide sections the first
        valid section only will be shown in the output.

        A backslash `\` can be used to escape a character eg `\[` will show `[`
        in the output.  Note: `\?` is reserved for future use and is removed.

        `{<placeholder>}` will be converted, or removed if it is None or empty.
        Formating can also be applied to the placeholder eg
        `{number:03.2f}`.

        example format_string:
        "[[{artist} - ]{title}]|{file}"
        This will show `artist - title` if artist is present,
        `title` if title but no artist,
        and `file` if file is present but not artist or title.

        param_dict is a dictionary of palceholders that will be substituted.
        If a placeholder is not in the dictionary then if the py3status module
        has an attribute with the same name then it will be used.
        """
        try:
            return self._formatter.format(
                format_string,
                self._py3status_module,
                param_dict
            )
        except Exception:
            return 'invalid format'

    def build_composite(self, format_string, param_dict=None, composites=None):
        """
        Build a composite output using a format string.

        Takes a format_string and treats it the same way as `safe_format` but
        also takes a composites dict where each key/value is the name of the
        placeholder and either an output eg `{'full_text': 'something'}` or a
        list of outputs.
        """
        try:
            return self._formatter.format(
                format_string,
                self._py3status_module,
                param_dict,
                composites,
            )
        except Exception:
            return [{'full_text': 'invalid format'}]

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
