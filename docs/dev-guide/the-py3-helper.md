# The py3 module helper

The Py3 module is a special helper object that gets injected into py3status
modules, providing extra functionality. A module can access it via the
``self.py3`` instance attribute of its py3status class.

## Constants

### CACHE_FOREVER

Special constant that when returned for ``cached_until`` will cause the
module to not update unless externally triggered.

### LOG_ERROR

Show as Error

### LOG_INFO

Show as Informational

### LOG_WARNING

Show as Warning

## Exceptions

### CommandError

An error occurred running the given command.

This exception provides some additional attributes

``error_code``: The error code returned from the call

``output``: Any output returned by the call

``error``: Any error output returned by the call

### Py3Exception

Base Py3 exception class.  All custom Py3 exceptions derive from this
class.

### RequestException

A Py3.request() base exception.  This will catch any of the more specific
exceptions.

### RequestInvalidJSON

The request has not returned valid JSON

### RequestTimeout

A timeout has occurred during a request made via Py3.request().

### RequestURLError

A URL related error has occurred during a request made via Py3.request().

## Methods

### check_commands(cmd_list)

Checks to see if commands in list are available using shutil.which().

returns the first available command.

If a string is passed then that command will be checked for.

### command_output(command, shell=False, capture_stderr=False, localized=False)

Run a command and return its output as unicode.
The command can either be supplied as a sequence or string.

:param command: command to run can be a str or list
:param shell: if `True` then command is run through the shell
:param capture_stderr: if `True` then STDERR is piped to STDOUT
:param localized: if `False` then command is forced to use its default (English) locale

A CommandError is raised if an error occurs

### command_run(command)

Runs a command and returns the exit code.
The command can either be supplied as a sequence or string.

An Exception is raised if an error occurs

### composite_create(item)

Create and return a Composite.

The item may be a string, dict, list of dicts or a Composite.

### composite_join(separator, items)

Join a list of items with a separator.
This is used in joining strings, responses and Composites.

A Composite object will be returned.

### composite_update(item, update_dict, soft=False)

Takes a Composite (item) if item is a type that can be converted into a
Composite then this is done automatically.  Updates all entries it the
Composite with values from update_dict.  Updates can be soft in which
case existing values are not overwritten.

A Composite object will be returned.

### error(msg, timeout=None)

Raise an error for the module.

:param msg: message to be displayed explaining the error
:param timeout: how long before we should retry.  For permanent errors
    `py3.CACHE_FOREVER` should be returned.  If not supplied then the
    modules `cache_timeout` will be used.


### flatten_dict(d, delimiter='-', intermediates=False, parent_key=None)

Flatten a dictionary.

Values that are dictionaries are flattened using delimiter in between
(eg. parent-child)

Values that are lists are flattened using delimiter
followed by the index (eg. parent-0)

example:

```
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
```

### format_contains(format_string, names)

Determines if ``format_string`` contains a placeholder string ``names``
or a list of placeholders ``names``.

``names`` is tested against placeholders using fnmatch so the following
patterns can be used:

```
* 	    matches everything
? 	    matches any single character
[seq] 	matches any character in seq
[!seq] 	matches any character not in seq
```

This is useful because a simple test like
``'{placeholder}' in format_string``
will fail if the format string contains placeholder formatting
eg ``'{placeholder:.2f}'``


### format_units(value, unit='B', optimal=5, auto=True, si=False)

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


### get_color_names_list(format_string, matches=None)

Returns a list of color names in ``format_string``.

- ***format_string***: Accepts a format string.
- ***matches***: Filter results with a string or a list of strings.

If ``matches`` is provided then it is used to filter the result
using fnmatch so the following patterns can be used:

```
* 	    matches everything
? 	    matches any single character
[seq] 	matches any character in seq
[!seq] 	matches any character not in seq
```

### get_composite_string(format_string)

Return a string from a Composite.

### get_output(module_name)

Return the output of the named module.  This will be a list.

### get_placeholder_formats_list(format_string)

Parses the format_string and returns a list of tuples
[(placeholder, format), ...].

eg ``'{placeholder:.2f}'`` will give ``[('placeholder', ':.2f')]``

### get_placeholders_list(format_string, matches=None)

Returns a list of placeholders in ``format_string``.

If ``matches`` is provided then it is used to filter the result
using fnmatch so the following patterns can be used:

```
* 	    matches everything
? 	    matches any single character
[seq] 	matches any character in seq
[!seq] 	matches any character not in seq
```

This is useful because we just get simple placeholder without any
formatting that may be applied to them
eg ``'{placeholder:.2f}'`` will give ``['{placeholder}']``

### get_wm_msg()

Return the control program of the current window manager.

On i3, will return "i3-msg"
On sway, will return "swaymsg"

### i3s_config()

returns the i3s_config dict.

### is_color(color)

Tests to see if a color is defined.
Because colors can be set to None in the config and we want this to be
respected in an expression like.

```python
color = self.py3.COLOR_MUTED or self.py3.COLOR_BAD
```

The color is treated as True but sometimes we want to know if the color
has a value set in which case the color should count as False.  This
function is a helper for this second case.

### is_composite(item)

Check if item is a Composite and return True if it is.

### is_my_event(event)

Checks if an event triggered belongs to the module receiving it.  This
is mainly for containers who will also receive events from any children
they have.

Returns True if the event name and instance match that of the module
checking.

### log(message, level='info')

Log the message.
The level must be one of LOG_ERROR, LOG_INFO or LOG_WARNING

### notify_user(msg, level='info', rate_limit=5, title=None, icon=None)

Send a notification to the user.
level must be 'info', 'error' or 'warning'.
rate_limit is the time period in seconds during which this message
should not be repeated.
icon must be an icon path or icon name.

### play_sound(sound_file)

Plays sound_file if possible.

### prevent_refresh()

Calling this function during the on_click() method of a module will
request that the module is not refreshed after the event. By default
the module is updated after the on_click event has been processed.

### register_function(function_name, function)

Register a function for the module.

The following functions can be registered:

#### content_function()

Called to discover what modules a container is displaying.  This is
used to determine when updates need passing on to the container and
also when modules can be put to sleep.

the function must return a set of module names that are being
displayed.

!!! note
    This function should only be used by containers.

#### urgent_function(module_names)

This function will be called when one of the contents of a container
has changed from a non-urgent to an urgent state.  It is used by the
group module to switch to displaying the urgent module.

``module_names`` is a list of modules that have become urgent

!!! note
    This function should only be used by containers.

### request(url, params=None, data=None, headers=None, timeout=None, auth=None, cookiejar=None, retry_times=None, retry_wait=None)

Make a request to a url and retrieve the results.

If the headers parameter does not provide an 'User-Agent' key, one will
be added automatically following the convention:

    py3status/<version> <per session random uuid>

- url: url to request eg `http://example.com`
- params: extra query string parameters as a dict
- data: POST data as a dict.  If this is not supplied the GET method will be used
- headers: http headers to be added to the request as a dict
- timeout: timeout for the request in seconds
- auth: authentication info as tuple `(username, password)`
- cookiejar: an object of a CookieJar subclass
- retry_times: how many times to retry the request
- retry_wait: how long to wait between retries in seconds

returns: HttpResponse

### safe_format(format_string, param_dict=None, force_composite=False, attr_getter=None, max_width=None)

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

``\?if=<placeholder>`` can be used to check if a placeholder exists. An
exclamation mark ``!`` after the equals sign ``=`` can be used to negate
the condition.

``\?if=<placeholder>=<value>`` can be used to determine if {<placeholder>}
would be replaced with <value>. ``[]`` in <value> don't need to be escaped.

``{<placeholder>}`` will be converted, or removed if it is None or empty.
Formatting can also be applied to the placeholder Eg
``{number:03.2f}``.

example format_string:

``"[[{artist} - ]{title}]|{file}"``
This will show ``artist - title`` if artist is present,
``title`` if title but no artist,
and ``file`` if file is present but not artist or title.

param_dict is a dictionary of placeholders that will be substituted.
If a placeholder is not in the dictionary then if the py3status module
has an attribute with the same name then it will be used.

Composites can be included in the param_dict.

The result returned from this function can either be a string in the
case of simple parsing or a Composite if more complex.

If force_composite parameter is True a composite will always be
returned.

attr_getter is a function that will when called with an attribute name
as a parameter will return a value.

max_width lets you to control the total max width of 'full_text' the
module is allowed to output on the bar.

### stop_sound()

Stops any currently playing sounds for this module.

### storage_del(key=None)

Remove the value stored with the key from storage.
If key is not supplied then all values for the module are removed.

### storage_get(key)

Retrieve a value for the module.

### storage_items()

Return key, value pairs of the stored data for the module.

Keys will contain the following metadata entries:
- '_ctime': storage creation timestamp
- '_mtime': storage last modification timestamp

### storage_keys()

Return a list of the keys for values stored for the module.

Keys will contain the following metadata entries:
- '_ctime': storage creation timestamp
- '_mtime': storage last modification timestamp

### storage_set(key, value)

Store a value for the module.

### threshold_get_color(value, name=None)

Obtain color for a value using thresholds.

The value will be checked against any defined thresholds.  These should
have been set in the i3status configuration.  If more than one
threshold is needed for a module then the name can also be supplied.
If the user has not supplied a named threshold but has defined a
general one that will be used.

If the gradients config parameter is True then rather than sharp
thresholds we will use a gradient between the color values.

- value: numerical value to be graded
- name: accepts a string, otherwise 'threshold'
    accepts 3-tuples to allow name with different
    values eg ('name', 'key', 'thresholds')

### time_in(seconds=None, sync_to=None, offset=0)

Returns the time a given number of seconds into the future.  Helpful
for creating the ``cached_until`` value for the module output.

!!! note
    from version 3.1 modules no longer need to explicitly set a
    ``cached_until`` in their response unless they wish to directly control
    it.

- seconds: specifies the number of seconds that should occur before the
    update is required.  Passing a value of ``CACHE_FOREVER`` returns
    ``CACHE_FOREVER`` which can be useful for some modules.

- sync_to: causes the update to be synchronized to a time period.  1 would
    cause the update on the second, 60 to the nearest minute. By default we
    synchronize to the nearest second. 0 will disable this feature.

- offset: is used to alter the base time used. A timer that started at a
    certain time could set that as the offset and any synchronization would
    then be relative to that time.

### trigger_event(module_name, event)

Trigger an event on a named module.

### update(module_name=None)

Update a module.  If module_name is supplied the module of that
name is updated.  Otherwise the module calling is updated.

### update_placeholder_formats(format_string, formats)

Update a format string adding formats if they are not already present.
This is useful when for example a placeholder has a floating point
value but by default we only want to show it to a certain precision.
