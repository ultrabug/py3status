import sys
import os
import re
import shlex
from time import time
from subprocess import Popen, call
from string import Formatter


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

    def __init__(self, module=None, i3s_config=None):
        self._audio = None
        self._module = module
        self._i3s_config = i3s_config or {}
        self.is_python_2 = sys.version_info < (3, 0)
        # we are running through the whole stack.
        # If testing then module is None.
        if module:
            self._output_modules = module._py3_wrapper.output_modules
            if not i3s_config:
                config = self._module.i3status_thread.config['general']
                self._i3s_config = config

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
            if self.is_python_2 and isinstance(msg, str):
                msg = msg.decode('utf-8')
            module_name = self._module.module_full_name
            self._module._py3_wrapper.notify_user(
                msg, level=level, rate_limit=rate_limit, module_name=module_name)

    def register_content_function(self, content_function):
        """
        Register a function that can be called to discover what modules a
        container is displaying.  This is used to determine when updates need
        passing on to the container and also when modules can be put to sleep.

        the function must return a set of module names that are being
        displayed.

        Note: This function should only be used by containers.
        """
        if self._module:
            my_info = self._get_module_info(self._module.module_full_name)
            my_info['content_function'] = content_function

    def time_in(self, seconds=0):
        """
        Returns the time a given number of seconds into the future.  Helpful
        for creating the `cached_until` value for the module output.
        """
        return time() + seconds

    def _fix_unicode_dict(self, a_dict):
        """
        Takes a dict and replaces any str values with their unicode equivalent.
        Only works for python2
        """
        for key, value in a_dict.items():
            if isinstance(value, str):
                a_dict[key] = value.decode('utf-8')

    def _safe_format(self, format_string, param_dict):
        """
        Parse a format string. we make sure that no undefined parameters are
        included in the format and if they do we escape them.  We also apply
        rules around [ | ] etc.
        """

        # we need to treat \{ and \} specially for the formatter
        # change them to {{ and }}
        def my_replace(match):
            match = match.group()
            if match == '\\{':
                return '{{'
            if match == '\\}':
                return '}}'
            return match
        format_string = re.sub('\\\\.', my_replace, format_string)

        # this class helps us maintain state in the next_item function
        class Info:
            part = 0
            char = None

        try:
            parsed = list(Formatter().parse(format_string))
        except ValueError:
            return 'Invalid Format'

        def next_item(ignore_slash=False):
            """
            Get the next item from the pared info.  This will be a single
            character or placeholder and may be preceded by a backslash.
            """
            if Info.part >= len(parsed):
                # We got to the end of the format string.
                return None, None
            # Find the next character location
            if Info.char is None:
                Info.char = 0
            else:
                Info.char += 1
            if Info.char >= len(parsed[Info.part][0]):
                # We have gone of the end of the string is there a placeholder?
                if parsed[Info.part][1]:
                    Info.char = None
                    param = parsed[Info.part][1]
                    Info.part += 1
                    if param_dict.get(param) is not None:
                        # valid placeholder so return it along with any extras
                        conversion = parsed[Info.part - 1][3]
                        if conversion:
                            param += '!%s' % conversion
                        field_format = parsed[Info.part - 1][2]
                        if field_format:
                            param += ':%s' % field_format
                        return '{%s}' % param, True
                    elif param not in param_dict:
                        # Missing placeholder
                        return '{{%s}}' % param, True
                    else:
                        # Empty placeholder
                        return '', False
                # Move to next part of the format string
                Info.char = 0
                Info.part += 1
                if Info.part >= len(parsed):
                    return None, None
            found = None
            n = parsed[Info.part][0][Info.char]
            if n == '\\' and not ignore_slash:
                # the next item is escaped
                m, found = next_item(ignore_slash=True)
                if m:
                    n += m
            return n, found

        parts = [['', True, 0]]
        level = 0
        block_level = None
        # We will go through the parsed format string one character/placeholder
        # at a time.
        while True:
            n, found = next_item()
            if n is None:
                # Finished
                break
            if found:
                # A placeholder exists so this section is valid
                parts[len(parts) - 1][1] = True
                # We need to work out which other sections depend on this one
                # so that we can make sure they are shown.
                # [ [ ] | [ ] ] [show [{placeholder}] | [ ] ]
                fix_level = level
                for i in range(len(parts) - 2, 0, -1):
                    part_level = parts[i][2]
                    if part_level >= fix_level:
                        continue
                    parts[i][1] = True
                    if part_level == 0:
                        break
                    fix_level = part_level
            if n == '':
                continue
            if n == '[':
                # Start a new section
                level += 1
                parts.append(['', False, level])
                continue
            if n == ']':
                # Section finished remove if no placeholders found
                if not parts[len(parts) - 1][1]:
                    parts = parts[:-1]
                level -= 1
                if block_level is not None and level < block_level:
                    block_level = None
                continue
            if n == '|':
                # Alternative section if we already have output then prevent
                # any more at this depth.
                if parts[len(parts) - 1][1]:
                    if block_level is None:
                        block_level = level
                continue
            if n[0] == '\\':
                # The item was escaped remove the escape character
                n = n[1:]
            if n == '{':
                n = '{{'
            if n == '}':
                n = '}}'
            if block_level is None:
                # Add the item if we are not blocking
                parts[len(parts) - 1][0] += n

        return ''.join([p[0] for p in parts if p[1]])

    def safe_format(self, format_string, param_dict):
        """
        Parser for advanced formating.

        Unknown placeholders will be shown in the output eg `{foo}`

        Square brackets `[]` can be used. The content of them will be removed
        from the output if there is no valid placeholder contained within.
        They can also be nested.
        A pipe (vertical bar) `|` can be used to divide sections the first
        valid section only will be shown in the output.
        A backslash `\` can be used to escape a character eg `\[` will show `[`
        in the output.
        `{<placeholder>}` will be converted, or removed if it is None or empty.
        Formating can also be applied to the placeholder eg
        `{number:03.2f}`.

        example format_string:
        "[[{artist} - ]{title}]|{file}"
        This will show `artist - title` if artist is present,
        `title` if title but no artist,
        and `file` if file is present but not artist or title.
        """
        if self.is_python_2:
            self._fix_unicode_dict(param_dict)
        # Output our format string with the placeholders substituted.
        return self._safe_format(format_string, param_dict).format(**param_dict)

    def build_composite(self, format_string, param_dict=None, composites=None):
        """
        Build a composite output using a format string.

        Takes a format_string and treats it the same way as `safe_format` but
        also takes a composites dict where each key/value is the name of the
        placeholder and either an output eg `{'full_text': 'something'}` or a
        list of outputs.
        """
        if param_dict is None:
            param_dict = {}
        if composites is None:
            composites = {}

        if self.is_python_2:
            self._fix_unicode_dict(param_dict)

        # Make sure that placeholders for our composites are kept by adding
        # entries if not in param_dict
        my_data = param_dict.copy()
        for composite in composites:
            if composite not in my_data:
                my_data[composite] = True

        output_format = self._safe_format(format_string, my_data)
        parsed = list(Formatter().parse(output_format))

        output = []
        text = u''
        for item in parsed:
            text += item[0]
            if item[1]:
                if item[1] in param_dict:
                    text = u'{}{}'.format(text, param_dict[item[1]])
                else:
                    if text:
                        output.append({'full_text': text})
                        text = u''
                    composite = composites[item[1]]
                    if isinstance(composite, list):
                        output += composite
                    else:
                        output.append(composite)
        if text:
            output.append({'full_text': text})
        return output

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
