from __future__ import division

import collections
import os
import sys
import shlex

from copy import deepcopy
from fnmatch import fnmatch
from math import log10
from pprint import pformat
from subprocess import Popen, PIPE, STDOUT
from time import time

from py3status import exceptions
from py3status.constants import COLOR_NAMES
from py3status.formatter import Formatter, Composite
from py3status.request import HttpResponse
from py3status.storage import Storage
from py3status.util import Gradiants


PY3_CACHE_FOREVER = -1
PY3_LOG_ERROR = 'error'
PY3_LOG_INFO = 'info'
PY3_LOG_WARNING = 'warning'

# basestring does not exist in python3
try:
    basestring
except NameError:
    basestring = str


class ModuleErrorException(Exception):
    """
    This exception is used to indicate that a module has returned an error
    """

    def __init__(self, msg, timeout):
        self.msg = msg
        self.timeout = timeout


class NoneColor:
    """
    This class represents a color that has explicitly been set as None by the user.
    We need this so that we can do things like

    color = self.py3.COLOR_MUTED or self.py3.COLOR_BAD

    Py3 provides a helper function is_color() that will treat a NoneColor as
    False, whereas a simple if would show True
    """
    # this attribute is used to identify that this is a none color
    none_setting = True

    def __repr__(self):
        # this is for output via module_test
        return 'None'


class Py3:
    """
    Helper object that gets injected as ``self.py3`` into Py3status
    modules that have not got that attribute set already.

    This allows functionality like:

    -   User notifications
    -   Forcing module to update (even other modules)
    -   Triggering events for modules

    Py3 is also used for testing in which case it does not get a module when
    being created.  All methods should work in this situation.
    """

    CACHE_FOREVER = PY3_CACHE_FOREVER
    """
    Special constant that when returned for ``cache_until`` will cause the
    module to not update unless externally triggered.
    """

    LOG_ERROR = PY3_LOG_ERROR
    """Show as Error"""
    LOG_INFO = PY3_LOG_INFO
    """Show as Informational"""
    LOG_WARNING = PY3_LOG_WARNING
    """Show as Warning"""

    # Shared by all Py3 Instances
    _formatter = None
    _gradients = Gradiants()
    _none_color = NoneColor()
    _storage = Storage()

    # Exceptions
    Py3Exception = exceptions.Py3Exception
    CommandError = exceptions.CommandError
    RequestException = exceptions.RequestException
    RequestInvalidJSON = exceptions.RequestInvalidJSON
    RequestTimeout = exceptions.RequestTimeout
    RequestURLError = exceptions.RequestURLError

    def __init__(self, module=None):
        self._audio = None
        self._config_setting = {}
        self._english_env = dict(os.environ)
        self._english_env['LC_ALL'] = 'C'
        self._format_placeholders = {}
        self._format_placeholders_cache = {}
        self._is_python_2 = sys.version_info < (3, 0)
        self._module = module
        self._report_exception_cache = set()
        self._thresholds = None
        self._threshold_gradients = {}

        if module:
            self._i3s_config = module._py3_wrapper.config['py3_config']['general']
            self._module_full_name = module.module_full_name
            self._output_modules = module._py3_wrapper.output_modules
            self._py3status_module = module.module_class
            self._py3_wrapper = module._py3_wrapper
            # create formatter we only if need one but want to pass py3_wrapper so
            # that we can do logging etc.
            if not self._formatter:
                self.__class__._formatter = Formatter(module._py3_wrapper)

    def __getattr__(self, name):
        """
        Py3 can provide COLOR constants
        eg COLOR_GOOD, COLOR_BAD, COLOR_DEGRADED
        but also any constant COLOR_XXX we find this color in the config
        if it exists
        """
        if not name.startswith('COLOR_'):
            raise AttributeError('Attribute `%s` not in Py3' % name)
        return self._get_config_setting(name.lower())

    def _get_config_setting(self, name, default=None):
        try:
            return self._config_setting[name]
        except KeyError:
            fn = self._py3_wrapper.get_config_attribute
            param = fn(self._module_full_name, name)

            # colors are special we want to make sure that we treat a color
            # that was explicitly set to None as a True value.  Ones that are
            # not set should be treated as None
            if name.startswith('color_'):
                if hasattr(param, 'none_setting'):
                    # see if named color and use if it is
                    param = COLOR_NAMES.get(name[6:].lower())
                elif param is None:
                    param = self._none_color
            # if a non-color parameter and was not set then set to default
            elif hasattr(param, 'none_setting'):
                param = default
            self._config_setting[name] = param
        return self._config_setting[name]

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
        return self._get_config_setting(name)

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

        # If we just report the error the traceback will end in the try
        # except block that we are calling from.
        # We want to show the traceback originating from the module that
        # called the Py3 method so get the correct error frame and pass this
        # along.
        error_frame = sys._getframe(0)
        while frame_skip:
            error_frame = error_frame.f_back
            frame_skip -= 1
        self._py3_wrapper.report_exception(
            msg, notify_user=False, error_frame=error_frame
        )

    def error(self, msg, timeout=None):
        """
        Raise an error for the module.

        :param msg: message to be displayed explaining the error
        :param timeout: how long before we should retry.  For permanent errors
            `py3.CACHE_FOREVER` should be returned.  If not supplied then the
            modules `cache_timeout` will be used.
        """
        raise ModuleErrorException(msg, timeout)

    def flatten_dict(self, d, delimiter='-', intermediates=False, parent_key=None):
        """
        Flatten a dictionary.

        Values that are dictionaries are flattened using delimiter in between
        (eg. parent-child)

        Values that are lists are flattened using delimiter
        followed by the index (eg. parent-0)

        example:

        .. code-block:: python

            {
                'fish_facts': {
                    'sharks': 'Most will drown if they stop moving',
                    'skates': 'More than 200 species',
                },
                'fruits': ['apple', 'peach', 'watermelon'],
                'number': 52
            }

            # becomes

            {
                'fish_facts-sharks': 'Most will drown if they stop moving',
                'fish_facts-skates': 'More than 200 species',
                'fruits-0': 'apple',
                'fruits-1': 'peach',
                'fruits-2': 'watermelon',
                'number': 52
            }

            # if intermediates is True then we also get unflattened elements
            # as well as the flattened ones.

            {
                'fish_facts': {
                    'sharks': 'Most will drown if they stop moving',
                    'skates': 'More than 200 species',
                },
                'fish_facts-sharks': 'Most will drown if they stop moving',
                'fish_facts-skates': 'More than 200 species',
                'fruits': ['apple', 'peach', 'watermelon'],
                'fruits-0': 'apple',
                'fruits-1': 'peach',
                'fruits-2': 'watermelon',
                'number': 52
            }
        """
        items = []
        if isinstance(d, list):
            d = dict(enumerate(d))
        for k, v in d.items():
            if parent_key:
                k = u'{}{}{}'.format(parent_key, delimiter, k)
            if intermediates:
                items.append((k, v))
            if isinstance(v, list):
                v = dict(enumerate(v))
            if isinstance(v, collections.Mapping):
                items.extend(self.flatten_dict(v, delimiter, intermediates, str(k)).items())
            else:
                items.append((str(k), v))
        return dict(items)

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
        eg ``unit=KiB`` would force the output to be in Kibibytes.  By default we
        use non-si units but if the unit is si eg kB then we will switch to si
        units.  Units can also be things like ``Mbit/sec``.

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
        return not (color is None or hasattr(color, 'none_setting'))

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

        # nicely format logs if we can using pretty print
        if isinstance(message, (dict, list, set, tuple)):
            message = pformat(message)
        # start on new line if multi-line output
        try:
            if '\n' in message:
                message = '\n' + message
        except:
            pass
        message = 'Module `{}`: {}'.format(
            self._module.module_full_name, message)
        self._py3_wrapper.log(message, level)

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
        # we do a deep copy so that any user does not change the actual output
        # of the module.
        return deepcopy(output)

    def trigger_event(self, module_name, event):
        """
        Trigger an event on a named module.
        """
        if module_name:
            self._py3_wrapper.events_thread.process_event(
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
        if isinstance(msg, Composite):
            msg = msg.text()
        # force unicode for python2 str
        if self._is_python_2 and isinstance(msg, str):
            msg = msg.decode('utf-8')
        if msg:
            module_name = self._module.module_full_name
            self._py3_wrapper.notify_user(
                msg=msg,
                level=level,
                rate_limit=rate_limit,
                module_name=module_name,
            )

    def register_function(self, function_name, function):
        """
        Register a function for the module.

        The following functions can be registered


            ..  py:function:: content_function()

            Called to discover what modules a container is displaying.  This is
            used to determine when updates need passing on to the container and
            also when modules can be put to sleep.

            the function must return a set of module names that are being
            displayed.

            .. note::

                This function should only be used by containers.

            ..  py:function:: urgent_function(module_names)

            This function will be called when one of the contents of a container
            has changed from a non-urgent to an urgent state.  It is used by the
            group module to switch to displaying the urgent module.

            ``module_names`` is a list of modules that have become urgent

            .. note::

                This function should only be used by containers.
        """
        my_info = self._get_module_info(self._module.module_full_name)
        my_info[function_name] = function

    def time_in(self, seconds=None, sync_to=None, offset=0):
        """
        Returns the time a given number of seconds into the future.  Helpful
        for creating the ``cached_until`` value for the module output.

        .. note::

            from version 3.1 modules no longer need to explicitly set a
            ``cached_until`` in their response unless they wish to directly control
            it.

        :param seconds: specifies the number of seconds that should occure before the
            update is required.  Passing a value of ``CACHE_FOREVER`` returns
            ``CACHE_FOREVER`` which can be useful for some modules.

        :param sync_to: causes the update to be syncronised to a time period.  1 would
            cause the update on the second, 60 to the nearest minute. By defalt we
            syncronise to the nearest second. 0 will disable this feature.

        :param offset: is used to alter the base time used. A timer that started at a
            certain time could set that as the offset and any syncronisation would
            then be relative to that time.
        """

        # if called with CACHE_FOREVER we just return this
        if seconds is self.CACHE_FOREVER:
            return self.CACHE_FOREVER

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

    def format_contains(self, format_string, names):
        """
        Determines if ``format_string`` contains a placeholder string ``names``
        or a list of placeholders ``names``.

        ``names`` is tested against placeholders using fnmatch so the following
        patterns can be used:

        .. code-block:: none

            * 	    matches everything
            ? 	    matches any single character
            [seq] 	matches any character in seq
            [!seq] 	matches any character not in seq

        This is useful because a simple test like
        ``'{placeholder}' in format_string``
        will fail if the format string contains placeholder formatting
        eg ``'{placeholder:.2f}'``
        """
        # We cache things to prevent parsing the format_string more than needed
        if isinstance(names, list):
            key = str(names)
        else:
            key = names
            names = [names]
        try:
            return self._format_placeholders_cache[format_string][key]
        except KeyError:
            pass

        if format_string not in self._format_placeholders:
            placeholders = self._formatter.get_placeholders(format_string)
            self._format_placeholders[format_string] = placeholders
        else:
            placeholders = self._format_placeholders[format_string]

        if format_string not in self._format_placeholders_cache:
            self._format_placeholders_cache[format_string] = {}

        for name in names:
            for placeholder in placeholders:
                if fnmatch(placeholder, name):
                    self._format_placeholders_cache[format_string][key] = True
                    return True
        self._format_placeholders_cache[format_string][key] = False
        return False

    def get_placeholders_list(self, format_string, match=None):
        """
        Returns a list of placeholders in ``format_string``.

        If ``match`` is provided then it is used to filter the result using
        fnmatch so the following patterns can be used:

        .. code-block:: none

            * 	    matches everything
            ? 	    matches any single character
            [seq] 	matches any character in seq
            [!seq] 	matches any character not in seq

        This is useful because we just get simple placeholder without any
        formatting that may be applied to them
        eg ``'{placeholder:.2f}'`` will give ``['{placeholder}']``
        """
        if format_string not in self._format_placeholders:
            placeholders = self._formatter.get_placeholders(format_string)
            self._format_placeholders[format_string] = placeholders
        else:
            placeholders = self._format_placeholders[format_string]

        if not match:
            return list(placeholders)
        # filter matches
        found = []
        for placeholder in placeholders:
            if fnmatch(placeholder, match):
                found.append(placeholder)
        return found

    def get_placeholder_formats_list(self, format_string):
        """
        Parses the format_string and returns a list of tuples
        [(placeholder, format), ...].

        eg ``'{placeholder:.2f}'`` will give ``[('placeholder', ':.2f')]``
        """
        return self._formatter.get_placeholder_formats_list(format_string)

    def update_placeholder_formats(self, format_string, formats):
        """
        Update a format string adding formats if they are not already present.
        This is useful when for example a placeholder has a floating point
        value but by default we only want to show it to a certain precision.
        """

        return self._formatter.update_placeholder_formats(
            format_string, formats
        )

    def safe_format(self, format_string, param_dict=None,
                    force_composite=False, attr_getter=None):
        """
        Parser for advanced formatting.

        Unknown placeholders will be shown in the output eg ``{foo}``.

        Square brackets ``[]`` can be used. The content of them will be removed
        from the output if there is no valid placeholder contained within.
        They can also be nested.

        A pipe (vertical bar) ``|`` can be used to divide sections the first
        valid section only will be shown in the output.

        A backslash ``\`` can be used to escape a character eg ``\[`` will show ``[``
        in the output.

        ``\?`` is special and is used to provide extra commands to the format
        string,  example ``\?color=#FF00FF``. Multiple commands can be given
        using an ampersand ``&`` as a separator, example ``\?color=#FF00FF&show``.

        ``{<placeholder>}`` will be converted, or removed if it is None or empty.
        Formating can also be applied to the placeholder eg
        ``{number:03.2f}``.

        example format_string:

        ``"[[{artist} - ]{title}]|{file}"``
        This will show ``artist - title`` if artist is present,
        ``title`` if title but no artist,
        and ``file`` if file is present but not artist or title.

        param_dict is a dictionary of palceholders that will be substituted.
        If a placeholder is not in the dictionary then if the py3status module
        has an attribute with the same name then it will be used.

        .. note::

            Added in version 3.3

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
        .. note::
            deprecated in 3.3 use safe_format().

        Build a composite output using a format string.

        Takes a format_string and treats it the same way as ``safe_format()`` but
        also takes a composites dict where each key/value is the name of the
        placeholder and either an output eg ``{'full_text': 'something'}`` or a
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
        Checks to see if commands in list are available using ``which``.

        returns the first available command.

        If a string is passed then that command will be checked for.
        """
        # if a string is passed then convert it to a list.  This prevents an
        # easy mistake that could be made
        if isinstance(cmd_list, basestring):
            cmd_list = [cmd_list]

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
            return Popen(
                command, stdout=PIPE, stderr=PIPE, close_fds=True
            ).wait()
        except Exception as e:
            # make a pretty command for error loggings and...
            if isinstance(command, basestring):
                pretty_cmd = command
            else:
                pretty_cmd = ' '.join(command)
            msg = 'Command `{cmd}` {error}'.format(cmd=pretty_cmd, error=e.errno)
            raise exceptions.CommandError(msg, error_code=e.errno)

    def command_output(self, command, shell=False, capture_stderr=False, localized=False):
        """
        Run a command and return its output as unicode.
        The command can either be supplied as a sequence or string.

        :param command: command to run can be a str or list
        :param shell: if `True` then command is run through the shell
        :param capture_stderr: if `True` then STDERR is piped to STDOUT
        :param localized: if `False` then command is forced to use its default (English) locale

        A CommandError is raised if an error occurs
        """
        # make a pretty command for error loggings and...
        if isinstance(command, basestring):
            pretty_cmd = command
        else:
            pretty_cmd = ' '.join(command)
        # convert the non-shell command to sequence if it is a string
        if not shell and isinstance(command, basestring):
            command = shlex.split(command)

        stderr = STDOUT if capture_stderr else PIPE
        env = self._english_env if not localized else None

        try:
            process = Popen(command, stdout=PIPE, stderr=stderr, close_fds=True,
                            universal_newlines=True, shell=shell,
                            env=env)
        except Exception as e:
            msg = 'Command `{cmd}` {error}'.format(cmd=pretty_cmd, error=e)
            raise exceptions.CommandError(msg, error_code=e.errno)

        output, error = process.communicate()
        if self._is_python_2 and isinstance(output, str):
            output = output.decode('utf-8')
            error = error.decode('utf-8')
        retcode = process.poll()
        if retcode:
            # under certain conditions a successfully run command may get a
            # return code of -15 even though correct output was returned see
            # #664.  This issue seems to be related to arch linux but the
            # reason is not entirely clear.
            if retcode == -15:
                msg = 'Command `{cmd}` returned SIGTERM (ignoring)'
                self.log(msg.format(cmd=pretty_cmd))
            else:
                msg = 'Command `{cmd}` returned non-zero exit status {error}'
                output_oneline = output.replace('\n', ' ')
                if output_oneline:
                    msg += ' ({output})'
                msg = msg.format(cmd=pretty_cmd, error=retcode, output=output_oneline)
                raise exceptions.CommandError(
                    msg, error_code=retcode, error=error, output=output
                )
        if error:
            msg = "Command '{cmd}' had error {error}".format(
                cmd=pretty_cmd, error=error
            )
            raise exceptions.CommandError(
                msg, error_code=retcode, error=error, output=output
            )
        return output

    def _storage_init(self):
        """
        Ensure that storage is initialized.
        """
        if not self._storage.initialized:
            self._storage.init(self._module._py3_wrapper, self._is_python_2)

    def storage_set(self, key, value):
        """
        Store a value for the module.
        """
        if not self._module:
            return
        self._storage_init()
        module_name = self._module.module_full_name
        return self._storage.storage_set(module_name, key, value)

    def storage_get(self, key):
        """
        Retrieve a value for the module.
        """
        if not self._module:
            return
        self._storage_init()
        module_name = self._module.module_full_name
        return self._storage.storage_get(module_name, key)

    def storage_del(self, key=None):
        """
        Remove the value stored with the key from storage.
        If key is not supplied then all values for the module are removed.
        """
        if not self._module:
            return
        self._storage_init()
        module_name = self._module.module_full_name
        return self._storage.storage_del(module_name, key=key)

    def storage_keys(self):
        """
        Return a list of the keys for values stored for the module.

        Keys will contain the following metadata entries:
        - '_ctime': storage creation timestamp
        - '_mtime': storage last modification timestamp
        """
        if not self._module:
            return []
        self._storage_init()
        module_name = self._module.module_full_name
        return self._storage.storage_keys(module_name)

    def storage_items(self):
        """
        Return key, value pairs of the stored data for the module.

        Keys will contain the following metadata entries:
        - '_ctime': storage creation timestamp
        - '_mtime': storage last modification timestamp
        """
        if not self._module:
            return {}.items()
        self._storage_init()
        items = []
        module_name = self._module.module_full_name
        for key in self._storage.storage_keys(module_name):
            value = self._storage.storage_get(module_name, key)
            items.add((key, value))
        return items

    def play_sound(self, sound_file):
        """
        Plays sound_file if possible.
        """
        self.stop_sound()
        cmd = self.check_commands(['ffplay', 'paplay', 'play'])
        if cmd:
            if cmd == 'ffplay':
                cmd = 'ffplay -autoexit -nodisp -loglevel 0'
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

        If the gradients config parameter is True then rather than sharp
        thresholds we will use a gradient between the color values.
        """
        # If first run then process the threshold data.
        if self._thresholds is None:
            self._thresholds_init()

        color = None
        # if value is None, pass it along. otherwise try it.
        if value is not None:
            try:
                value = float(value)
            except ValueError:
                color = self._get_color('error') or self._get_color('bad')

        # if name not in thresholds info then use defaults
        name_used = name
        if name_used not in self._thresholds:
            name_used = None
        thresholds = self._thresholds.get(name_used)
        # if value is None, pass it along. otherwise try it.
        if value is not None and color is None and thresholds:
            # if gradients are enabled then we use them
            if self._get_config_setting('gradients'):
                try:
                    colors, minimum, maximum = self._threshold_gradients[name_used]
                except KeyError:
                    colors = self._gradients.make_threshold_gradient(self, thresholds)
                    minimum = min(thresholds)[0]
                    maximum = max(thresholds)[0]
                    self._threshold_gradients[name_used] = (colors, minimum, maximum)

                if value < minimum:
                    color = colors[0]
                elif value > maximum:
                    color = colors[-1]
                else:
                    value -= minimum
                    col_index = int(((len(colors) - 1) / (maximum - minimum)) * value)
                    color = colors[col_index]

            elif color is None:
                color = thresholds[0][1]
                for threshold in thresholds:
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

    def request(self, url, params=None, data=None, headers=None,
                timeout=None, auth=None, cookiejar=None):
        """
        Make a request to a url and retrieve the results.

        :param url: url to request eg `http://example.com`
        :param params: extra query string parameters as a dict
        :param data: POST data as a dict.  If this is not supplied the GET method will be used
        :param headers: http headers to be added to the request as a dict
        :param timeout: timeout for the request in seconds
        :param auth: authentication info as tuple `(username, password)`
        :param cookiejar: an object of a CookieJar subclass

        :returns: HttpResponse
        """

        # The aim of this function is to be a limited lightweight replacement
        # for the requests library but using only pythons standard libs.

        # IMPORTANT NOTICE
        # This function is excluded from private variable hiding as it is
        # likely to need api keys etc which people may have obfuscated.
        # Therefore it is important that no logging is done in this function
        # that might reveal this information.

        if headers is None:
            headers = {}

        return HttpResponse(url,
                            params=params,
                            data=data,
                            headers=headers,
                            timeout=timeout,
                            auth=auth,
                            cookiejar=cookiejar)
