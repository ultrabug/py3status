from __future__ import division

import os
import sys
import shlex

from fnmatch import fnmatch
from math import log10
from time import time
from subprocess import Popen, PIPE

from py3status.formatter import Formatter, Composite


PY3_CACHE_FOREVER = -1
PY3_LOG_ERROR = 'error'
PY3_LOG_INFO = 'info'
PY3_LOG_WARNING = 'warning'

# basestring does not exist in python3
try:
    basestring
except NameError:
    basestring = str


class NoneColor:
    """
    This class represents a none color, that is a color that has been setto
    None in the config.  We need this so that we can do things like

    color = self.py3.COLOR_MUTED or self.py3.COLOR_BAD

    Py3 provides a helper function is_color() that will treat a NoneColor as
    False, whereas a simple if would show True
    """
    # this attribute is used to identify that this is a none color
    none_color = True

    def __repr__(self):
        # this is for output via module_test
        return 'None'


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

    # Shared by all Py3 Instances
    _formatter = Formatter()
    _none_color = NoneColor()

    def __init__(self, module=None, i3s_config=None, py3status=None):
        self._audio = None
        self._colors = {}
        self._format_placeholders = {}
        self._format_placeholders_cache = {}
        self._i3s_config = i3s_config or {}
        self._module = module
        self._is_python_2 = sys.version_info < (3, 0)
        self._report_exception_cache = set()
        self._thresholds = None

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
        return self._get_color_by_name(name)

    def _get_color_by_name(self, name):
        name = name.lower()
        if name not in self._colors:
            if self._module:
                color_fn = self._module._py3_wrapper.get_config_attribute
                color = color_fn(self._module.module_full_name, name)
            else:
                # running in test mode so config is not available
                color = self._i3s_config.get(name, False)
            if color:
                self._colors[name] = color
            elif color is False:
                # False indicates color is not defined
                self._colors[name] = None
            else:
                # None indicates that no color is wanted
                self._colors[name] = self._none_color
        return self._colors[name]

    def _get_color(self, color):
        if not color:
            return
        # fix any hex colors so they are #RRGGBB
        if color.startswith('#'):
            color = color.upper()
            if len(color) == 4:
                color = ('#' + color[1] + color[1] + color[2] +
                         color[2] + color[3] + color[3])
            return color

        name = 'color_%s' % color
        return self._get_color_by_name(name)

    def _thresholds_init(self):
        """
        Initiate and check any thresholds set
        """
        thresholds = getattr(self._py3status_module, 'thresholds', [])
        self._thresholds = {}
        if isinstance(thresholds, list):
            thresholds.sort()
            self._thresholds[None] = [(x[0], self._get_color(x[1]))
                                      for x in thresholds]
            return
        elif isinstance(thresholds, dict):
            for key, value in thresholds.items():
                if isinstance(value, list):
                    value.sort()
                    self._thresholds[key] = [(x[0], self._get_color(x[1]))
                                             for x in value]

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

    def _report_exception(self, msg, frame_skip=2):
        """
        THIS IS PRIVATE AND UNSUPPORTED.
        logs an exception that occurs inside of a Py3 method.  We only log the
        exception once to prevent spamming the logs and we do not notify the
        user.

        frame_skip is used to change the place in the code that the error is
        reported as coming from.  We want to show it as coming from the
        py3status module where the Py3 method was called.
        """
        # We use a hash to see if the message is being repeated.
        msg_hash = hash(msg)
        if msg_hash in self._report_exception_cache:
            return
        self._report_exception_cache.add(msg_hash)

        if self._module:
            # If we just report the error the traceback will end in the try
            # except block that we are calling from.
            # We want to show the traceback originating from the module that
            # called the Py3 method so get the correct error frame and pass this
            # along.
            error_frame = sys._getframe(0)
            while frame_skip:
                error_frame = error_frame.f_back
                frame_skip -= 1
            self._module._py3_wrapper.report_exception(
                msg, notify_user=False, error_frame=error_frame
            )

    def format_units(self, value, unit='B', optimal=5, auto=True, si=False):
        """
        Takes a value and formats it for user output, we can choose the unit to
        use eg B, MiB, kbits/second.  This is mainly for use with bytes/bits it
        converts the value into a human readable form.  It has various
        additional options but they are really only for special cases.

        The function returns a tuple containing the new value (this is a number
        so that the user can still format it if required) and a unit that is
        the units that we have been converted to.

        By supplying unit to the function we can force those units to be used
        eg `unit=KiB` would force the output to be in Kibibytes.  By default we
        use non-si units but if the unit is si eg kB then we will switch to si
        units.  Units can also be things like `Mbit/sec`.

        If the auto parameter is False then we use the unit provided.  This
        only makes sense when the unit is singular eg 'Bytes' and we want the
        result in bytes and not say converted to MBytes.

        optimal is used to control the size of the output value.  We try to
        provide an output value of that number of characters (including decimal
        point), it may also be less due to rounding.  If a fixed unit is used
        the output may be more than this number of characters.
        """

        UNITS = 'KMGTPEZY'
        DECIMAL_SIZE = 1000
        BINARY_SIZE = 1024
        CUTOFF = 1000

        can_round = False

        if unit:
            # try to guess the unit.  Do we have a known prefix too it?
            if unit[0].upper() in UNITS:
                index = UNITS.index(unit[0].upper()) + 1
                post = unit[1:]
                si = len(unit) > 1 and unit[1] != 'i'
                if si:
                    post = post[1:]
                auto = False
            else:
                index = 0
                post = unit
        if si:
            size = DECIMAL_SIZE
        else:
            size = BINARY_SIZE

        if auto:
            # we will try to use an appropriate prefix
            if value < CUTOFF:
                unit_out = post
            else:
                value /= size
                for prefix in UNITS:
                    if abs(value) < CUTOFF:
                        break
                    value /= size
                if si:
                    # si kilo is lowercase
                    if prefix == 'K':
                        prefix = 'k'
                else:
                    post = 'i' + post

                unit_out = prefix + post
                can_round = True
        else:
            # we are using a fixed unit
            unit_out = unit
            size = pow(size, index)
            if size:
                value /= size
                can_round = True

        if can_round and optimal and value:
            # we will try to make the output value the desired size
            # we need to keep out value as a numeric type
            places = int(log10(abs(value)))
            if places >= optimal - 2:
                value = int(value)
            else:
                value = round(value, max(optimal - places - 2, 0))

        return value, unit_out

    def is_color(self, color):
        """
        Tests to see if a color is defined.
        Because colors can be set to None in the config and we want this to be
        respected in an expression like.

        color = self.py3.COLOR_MUTED or self.py3.COLOR_BAD

        The color is treated as True but sometimes we want to know if the color
        has a value set in which case the color should count as False.  This
        function is a helper for this second case.
        """
        return not (color is None or hasattr(color, 'none_color'))

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

        Note: from version 3.1 modules no longer need to explicitly set a
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

    def format_contains(self, format_string, name):
        """
        Determines if `format_string` contains placeholder `name`

        `name` is tested against placeholders using fnmatch so the following
        patterns can be used:

            * 	    matches everything
            ? 	    matches any single character
            [seq] 	matches any character in seq
            [!seq] 	matches any character not in seq

        This is useful because a simple test like
        `'{placeholder}' in format_string`
        will fail if the format string contains placeholder formatting
        eg `'{placeholder:.2f}'`
        """

        # We cache things to prevent parsing the format_string more than needed
        try:
            return self._format_placeholders_cache[format_string][name]
        except KeyError:
            pass

        if format_string not in self._format_placeholders:
            placeholders = self._formatter.get_placeholders(format_string)
            self._format_placeholders[format_string] = placeholders
        else:
            placeholders = self._format_placeholders[format_string]

        result = False
        for placeholder in placeholders:
            if fnmatch(placeholder, name):
                result = True
                break
        if format_string not in self._format_placeholders_cache:
            self._format_placeholders_cache[format_string] = {}
        self._format_placeholders_cache[format_string][name] = result
        return result

    def safe_format(self, format_string, param_dict=None,
                    force_composite=False, attr_getter=None):
        """
        Parser for advanced formatting.

        Unknown placeholders will be shown in the output eg `{foo}`.

        Square brackets `[]` can be used. The content of them will be removed
        from the output if there is no valid placeholder contained within.
        They can also be nested.

        A pipe (vertical bar) `|` can be used to divide sections the first
        valid section only will be shown in the output.

        A backslash `\` can be used to escape a character eg `\[` will show `[`
        in the output.

        `\?` is special and is used to provide extra commands to the format
        string,  example `\?color=#FF00FF`. Multiple commands can be given
        using an ampersand `&` as a separator, example `\?color=#FF00FF&show`.

        `{<placeholder>}` will be converted, or removed if it is None or empty.
        Formating can also be applied to the placeholder eg
        `{number:03.2f}`.

        example format_string:

        `"[[{artist} - ]{title}]|{file}"`
        This will show `artist - title` if artist is present,
        `title` if title but no artist,
        and `file` if file is present but not artist or title.

        param_dict is a dictionary of palceholders that will be substituted.
        If a placeholder is not in the dictionary then if the py3status module
        has an attribute with the same name then it will be used.

        __Since version 3.3__

        Composites can be included in the param_dict.

        The result returned from this function can either be a string in the
        case of simple parsing or a Composite if more complex.

        If force_composite parameter is True a composite will always be
        returned.

        attr_getter is a function that will when called with an attribute name
        as a parameter will return a value.
        """
        try:
            return self._formatter.format(
                format_string,
                self._py3status_module,
                param_dict,
                force_composite=force_composite,
                attr_getter=attr_getter,
            )
        except Exception:
            self._report_exception(
                u'Invalid format `{}`'.format(format_string)
            )
            return 'invalid format'

    def build_composite(self, format_string, param_dict=None, composites=None,
                        attr_getter=None):
        """
        __deprecated in 3.3__ use safe_format().

        Build a composite output using a format string.

        Takes a format_string and treats it the same way as `safe_format` but
        also takes a composites dict where each key/value is the name of the
        placeholder and either an output eg `{'full_text': 'something'}` or a
        list of outputs.
        """

        if param_dict is None:
            param_dict = {}

        # merge any composites into the param_dict.
        # as they are no longer dealt with separately
        if composites:
            for key, value in composites.items():
                param_dict[key] = Composite(value)

        try:
            return self._formatter.format(
                format_string,
                self._py3status_module,
                param_dict,
                force_composite=True,
                attr_getter=attr_getter,
            )
        except Exception:
            self._report_exception(
                u'Invalid format `{}`'.format(format_string)
            )
            return [{'full_text': 'invalid format'}]

    def composite_update(self, item, update_dict, soft=False):
        """
        Takes a Composite (item) if item is a type that can be converted into a
        Composite then this is done automatically.  Updates all entries it the
        Composite with values from update_dict.  Updates can be soft in which
        case existing values are not overwritten.

        A Composite object will be returned.
        """
        return Composite.composite_update(item, update_dict, soft=False)

    def composite_join(self, separator, items):
        """
        Join a list of items with a separator.
        This is used in joining strings, responses and Composites.

        A Composite object will be returned.
        """
        return Composite.composite_join(separator, items)

    def composite_create(self, item):
        """
        Create and return a Composite.

        The item may be a string, dict, list of dicts or a Composite.
        """
        return Composite(item)

    def is_composite(self, item):
        """
        Check if item is a Composite and return True if it is.
        """
        return isinstance(item, Composite)

    def check_commands(self, cmd_list):
        """
        Checks to see if commands in list are available using `which`.
        Returns the first available command.
        """
        for cmd in cmd_list:
            if self.command_run('which {}'.format(cmd)) == 0:
                return cmd

    def command_run(self, command):
        """
        Runs a command and returns the exit code.
        The command can either be supplied as a sequence or string.

        An Exception is raised if an error occurs
        """
        # convert the command to sequence if a string
        if isinstance(command, basestring):
            command = shlex.split(command)
        try:
            return Popen(command, stdout=PIPE, stderr=PIPE).wait()
        except Exception as e:
            msg = "Command '{cmd}' {error}"
            raise Exception(msg.format(cmd=command[0], error=e))

    def command_output(self, command):
        """
        Run a command and return its output as unicode.
        The command can either be supplied as a sequence or string.

        An Exception is raised if an error occurs
        """
        # convert the command to sequence if a string
        if isinstance(command, basestring):
            command = shlex.split(command)
        try:
            process = Popen(command, stdout=PIPE, stderr=PIPE,
                            universal_newlines=True)
        except Exception as e:
            msg = "Command '{cmd}' {error}"
            raise Exception(msg.format(cmd=command[0], error=e))

        output, error = process.communicate()
        if self._is_python_2:
            output = output.decode('utf-8')
            error = error.decode('utf-8')
        retcode = process.poll()
        if retcode:
            msg = "Command '{cmd}' returned non-zero exit status {error}"
            raise Exception(msg.format(cmd=command[0], error=retcode))
        if error:
            msg = "Command '{cmd}' had error {error}"
            raise Exception(msg.format(cmd=command[0], error=error))
        return output

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

    def threshold_get_color(self, value, name=None):
        """
        Obtain color for a value using thresholds.

        The value will be checked against any defined thresholds.  These should
        have been set in the i3status configuration.  If more than one
        threshold is needed for a module then the name can also be supplied.
        If the user has not supplied a named threshold but has defined a
        general one that will be used.
        """
        # If first run then process the threshold data.
        if self._thresholds is None:
            self._thresholds_init()

        color = None
        try:
            value = float(value)
        except ValueError:
            color = self._get_color('error') or self._get_color('bad')

        # if name not in thresholds info then use defaults
        name_used = name
        if name_used not in self._thresholds:
            name_used = None

        if color is None:
            for threshold in self._thresholds.get(name_used, []):
                if value >= threshold[0]:
                    color = threshold[1]
                else:
                    break

        # save color so it can be accessed via safe_format()
        if name:
            color_name = 'color_threshold_%s' % name
        else:
            color_name = 'color_threshold'
        setattr(self._py3status_module, color_name, color)

        return color
