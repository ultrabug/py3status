.. _using_modules:

Using modules
=============

py3status comes with a large range of :ref:`modules`.
Modules in py3status are configured using your usual ``i3status.conf``.

py3status tries to find the config in the following locations:

- ``~/.i3/i3status.conf``
- ``~/.i3status.conf``
- ``/etc/i3status.conf``
- ``XDG_CONFIG_HOME/.config/i3status/config``
- ``~/.config/i3status/config``
- ``XDG_CONFIG_DIRS/i3status/config``
- ``/etc/xdg/i3status/config``

You can also specify the config location using ``py3status -c <path to config
file>`` in your i3 configuration file.


Loading a py3status module and ordering modules output
------------------------------------------------------

To load a py3status module you just have to list it like any other i3status
module using the ``order +=`` parameter.

Ordering your py3status modules in your i3bar is just the same as i3status
modules, just list the order parameter where you want your module to be
displayed.

For example you could insert and load the ``imap`` module like this:

.. code-block:: py3status
    :caption: Example

    order += "disk /home"
    order += "disk /"
    order += "imap"
    order += "time"


Configuring a py3status module
------------------------------

Your py3status modules are configured the exact same way as i3status modules, directly from your ``i3status.conf``, like this :

.. code-block:: py3status
    :caption: Example

    # configure the py3status imap module
    # and run thunderbird when I left click on it
    imap {
        cache_timeout = 60
        imap_server = 'imap.myprovider.com'
        mailbox = 'INBOX'
        password = 'coconut'
        port = '993'
        user = 'mylogin'
        on_click 1 = "exec thunderbird"
    }


py3status configuration section
-------------------------------

This special section holds py3status specific configuration. Settings here
will affect all py3status modules.  Many settings e.g. colors can still be
overridden by also defining in the individual module.

Global options:

``nagbar_font``. Specify a font for ``i3-nagbar -f <font>``.

.. code-block:: py3status
    :caption: Example

    py3status {
        nagbar_font = 'pango:Ubuntu Mono 12'
    }

``storage``: Set storage name or path.

.. note::
    New in version 3.13

Store cache in $XDG_CACHE_HOME or ~/.cache

.. code-block:: py3status
    :caption: Example

    # default behavior
    py3status {
        storage = 'py3status_cache.data'
    }

Store per config cache in $XDG_CACHE_HOME or ~/.cache

.. code-block:: py3status

    # first config
    py3status {
        storage = 'py3status_top.data'
    }

.. code-block:: py3status

    # second config
    py3status {
        storage = 'py3status_bottom.data'
    }

Store per config cache in different directories.

.. code-block:: py3status

    # first config
    py3status {
        storage = '~/.config/py3status/cache_top.data'
    }

.. code-block:: py3status

    # second config
    py3status {
        storage = '~/.config/py3status/cache_bottom.data'
    }

.. note::
    New in version 3.14

You can specify the following options in module configuration.

``min_length``: Specify a minimum length of characters for modules.
``position``: Specify how modules should be positioned when the ``min_length``
is not reached. Either ``left`` (default), ``center``, or ``right``.

.. code-block:: py3status

    static_string {
        min_length = 15
        position = 'center'
    }

.. note::
    New in version 3.16

You can specify the options in module or py3status configuration section.

The following options will work on ``i3``.

``align``: Specify how modules should be aligned when the ``min_width``
is not reached. Either ``left`` (default), ``center``, or ``right``.
``background``: Specify a background color for py3status modules.
``markup``: Specify how modules should be parsed.
``min_width``: Specify a minimum width of pixels for modules.
``separator``: Specify a separator boolean for modules.
``separator_block_width``: Specify a separator block width for modules.

The following options will work on ``i3-gaps``.

``border``: Specify a border color for modules.
``border_bottom``: Specify a border width for modules
``border_left``: Specify a border width for modules.
``border_right``: Specify a border width for modules.
``border_top``: Specify a border width for modules.

The following options will work on ``py3status``.

``min_length``: Specify a minimum length of characters for modules.
``position``: Specify how modules should be positioned when the ``min_length``
is not reached. Either ``left`` (default), ``center``, or ``right``.

.. code-block:: py3status

   # customize a theme
   py3status {
      align = 'left'
      markup = 'pango'
      min_width = 20
      separator = True
      separator_block_width = 9

      background = '#285577'
      border = '#4c7899'
      border_bottom = 1
      border_left = 1
      border_right = 1
      border_top = 1

      min_length = 15
      position = 'right'
   }

.. note::
    New in version 3.16

The following options will work on ``i3bar`` and ``py3status``.

``urgent_background``: Specify urgent background color for modules.
``urgent_foreground``: Specify urgent foreground color for modules.
``urgent_border``: Specify urgent border color for modules.

The following options will work on ``i3bar-gaps`` and ``py3status``.

``urgent_border_bottom``: Specify urgent border width for modules
``urgent_border_left``: Specify urgent border width for modules.
``urgent_border_right``: Specify urgent border width for modules.
``urgent_border_top``: Specify urgent border width for modules.

You lose urgent functionality too that can be sometimes utilized by
container modules, e.g., frame and group.

.. code-block:: py3status

   # customize urgent
   py3status {
      urgent_background  = 'blue'
      urgent_foreground = 'white'
      urgent_border = 'red'
      urgent_border_bottom = 1
      urgent_border_left = 1
      urgent_border_right = 1
      urgent_border_top = 1
   }


Configuration obfuscation
-------------------------
Py3status allows you to hide individual configuration parameters so that they
do not leak into log files, user notifications or to the i3bar. Additionally
they allow you to obfuscate configuration parameters using base64 encoding.

.. note::
    ``hide()`` and ``base64()`` are new in version 3.13

To "hide" a value you can use the ``hide()``
configuration function. This prevents the module
displaying the value as a format placeholder and from
appearing in the logs.

.. code-block:: py3status
    :caption: Example

    # Example of 'hidden' configuration
    imap {
        imap_server = 'imap.myprovider.com'
        password = hide('hunter22')
        user = 'mylogin'
    }


To base64 encode a value you can use the ``base64()``
configuration function. This also  prevents the
module displaying the value as a format placeholder
and from appearing in the logs.


.. code-block:: py3status
    :caption: Example

    # Example of obfuscated configuration
    imap {
        imap_server = 'imap.myprovider.com'
        password = base64('Y29jb251dA==')
        user = 'mylogin'
    }

Since version 3.1 obfuscation options can also be
added by the legacy method. Add ``:hide`` or
``:base64`` to the name of the parameters.  You are
advised to use the new ``hide()`` and ``base64()``
configuration functions.

.. note::
    Legacy obfuscation is only available for string
    parameters with ``:hide`` or ``:base64``.  If you
    want other types then be sure to use ``hide()``
    and ``base64()`` configuration functions.

.. code-block:: py3status
    :caption: Example

    # normal_parameter will be shown in log files etc as 'some value'
    # obfuscated_parameter will be shown in log files etc as '***'
    module {
        normal_parameter = 'some value'
        obfuscated_parameter:hide = 'some value'
    }

In the previous example configuration the users password is in plain text.
Users may want to make it less easy to read. Py3status allows strings to be
base64 encoded.

To use an encoded string add ``:base64`` to the name of the parameter.

.. code-block:: py3status
    :caption: Example

    # Example of obfuscated configuration
    imap {
        imap_server = 'imap.myprovider.com'
        password:base64 = 'Y29jb251dA=='
        user = 'mylogin'
    }

.. note::
    Base64 encoding is very simple and should not be considered secure in any way.

Configuring colors
------------------

Since version 3.1 py3status allows greater color configuration.
Colors can be set in the general section of your ``i3status.conf`` or in an
individual modules configuration.  If a color is not in a modules configuration
then the values from the general section will be used.

If a module does not specify colors but it is in a container, then the colors
of the container will be used if they are set, before using ones defined in the
general section.

Generally colors can specified using hex values eg ``#FF00FF`` or ``#F0F``.  It
is also possible to use css3 color names eg ``red``
``hotpink``.  For a list of available color names see
`<https://drafts.csswg.org/css-color/#named-colors>`_.

.. code-block:: py3status
    :caption: Example

    general {
        # These will be used if not supplied by a module
        color = '#FFFFFF'
        color_good = '#00FF00'
        color_bad = '#FF0000'
        color_degraded = '#FFFF00'
    }

    time {
        color = 'FF00FF'
        format = "%H:%M"
    }

    battery_level {
        color_good = '#00AA00'
        color_bad = '#AA0000'
        color_degraded = '#AAAA00'
        color_charging = '#FFFF00'
    }

Configuring thresholds
----------------------

Some modules allow you to define thresholds in a module.  These are used to
determine which color to use when displaying the module.  Thresholds are
defined in the config as a list of tuples. With each tuple containing a value
and a color. The color can either be a named color eg ``good`` referring to
``color_good`` or a hex value.

.. code-block:: py3status
    :caption: Example

    volume_status {
        thresholds = [
            (0, "#FF0000"),
            (20, "degraded"),
            (50, "bad"),
        ]
    }

If the value checked against the threshold is equal to or more than a threshold
then that color supplied will be used.

In the above example the logic would be

.. code-block:: none

    if 0 >= value < 20 use #FF0000
    else if 20 >= value < 50 use color_degraded
    else if 50 >= value use color_good


Some modules may allow more than one threshold to be defined.  If all the thresholds are the same they can be defined as above but if you wish to specify them separately you can by giving a dict of lists.

.. code-block:: py3status
    :caption: Example

    my_module {
        thresholds = {
            'threshold_1': [
                (0, "#FF0000"),
                (20, "degraded"),
                (50, "bad"),
            ],
            'threshold_2': [
                (0, "good"),
                (30, "bad"),
            ],
        }
    }

.. note::
    New in version 3.17

You can specify ``hidden`` color to hide a block.

.. code-block:: py3status
    :caption: Example

    # hide a block when ``1avg`` (i.e., 12.4) is less than 20 percent
    format = "[\?color=1avg [\?color=darkgray&show 1min] {1min}]"
    loadavg {
       thresholds = [
            (0, "hidden"),
           (20, "good"),
           (40, "degraded"),
           (60, "#ffa500"),
           (80, "bad"),
       ]
    }

    # hide cpu block when ``cpu_used_percent`` is less than 50 percent
    # hide mem block when ``mem_used_percent`` is less than 50 percent
    sysdata {
        thresholds = [
            (50, "hidden"),
            (75, "bad"),
        ]
    }

Formatter
---------

All modules allow you to define the format of their output. This is done with the format option.
You can:

- display static text:

  .. code-block:: py3status
      :caption: Example

      mpd_status {
         format = "MPD:"
      }

- use a backslash ``\`` to escape a character (``\[`` will show ``[``).
- display data provided by the module. This is done with "placeholders", which follow the format {placeholder_name}.
  The following example shows the state of the MPD (play/pause/stop) and the artist and title of the currently playing song.

  .. code-block:: py3status
      :caption: Example

      mpd_status {
         format = "MPD: {state} {artist} {title}"
      }

  - Unknown placeholders act as if they were static text and placeholders that are empty or None will be removed.
  - Formatting can also be applied to the placeholder Eg ``{number:03.2f}``.

- hide invalid (no valid data or undefined) placeholders by enclosing them in ``[]``. The following example will show ``artist - title`` if artist is present and ``title`` if title but no artist is present.

  .. code-block:: py3status
      :caption: Example

      mpd_status {
         format = "MPD: {state} [[{artist} - ]{title}]"
      }

- show the first block with valid output by dividing them with a pipe ``|``. The following example will show the filename if neither artist nor title are present.

  .. code-block:: py3status
      :caption: Example

      mpd_status {
         format = "MPD: {state} [[{artist} - ]{title}]|{file}"
      }

- ``\?`` can be used to provide extra commands to the format string. Multiple commands can be given using an ampersand ``&`` as a separator.

  .. code-block:: py3status
      :caption: Example

      my_module {
         format = "\?color=#FF00FF&show blue"
      }

- change the output with conditions. This is done by following the ``\?`` with a an if statement. Multiple conditions or commands can be combined by using an ampersand ``&`` as a separator. Here are some examples:

  - ``\?if=online green | red`` checks if the placeholder exists and would display ``green`` in that case. A condition that evaluates to false invalidates a section and the section can be hidden with ``[]`` or skipped with ``|``
  - ``\?if=!online red | green`` this dose the same as the above condition, the only difference is that the exclamation mark ``!`` negates the condition.
  - ``\?if=state=play PLAYING! | not playing`` checks if the placeholder contains ``play`` and displays ``PLAYING!`` if not it will display ``not playing``.

A format string using nearly all of the above options could look like this:

.. code-block:: py3status
    :caption: Example

    mpd_status {
      format = "MPD: {state} [\?if=![stop] [[{artist} - ]{title}]|[{file}]]"
    }

This will show ``MPD: [state]`` if the state of the MPD is ``[stop]`` or ``MPD: [state] artist - title`` if it is ``[play]`` or ``[pause]`` and artist and title are present, ``MPD: [state] title`` if artist is missing and ``MPD: [state] file`` if artist and title are missing.

Urgent
------

Some modules use i3bar's urgent feature to indicate that something
important has occurred. The ``allow_urgent`` configuration parameter can
be used to allow/prevent a module from setting itself as urgent.


.. code-block:: py3status
    :caption: Example

    # prevent modules showing as urgent, except github
    py3status {
        allow_urgent = false
    }

    github {
        allow_urgent = true
    }


Grouping Modules
----------------

The :ref:`module_group`
module allows you to group several modules together.  Only one of the
modules are displayed at a time.  The displayed module can either be cycled
through automatically or by user action (the default, on mouse scroll).

This module is very powerful and allows you to save a lot of space on your bar.

.. code-block:: py3status
    :caption: Example

    order += "group tz"

    # cycle through different timezone hours every 10s
    group tz {
        cycle = 10
        format = "{output}"

        tztime la {
            format = "LA %H:%M"
            timezone = "America/Los_Angeles"
        }

        tztime ny {
            format = "NY %H:%M"
            timezone = "America/New_York"
        }

        tztime du {
            format = "DU %H:%M"
            timezone = "Asia/Dubai"
        }
    }

The :ref:`module_frame`
module also allows you to group several modules together, however in a frame
all the modules are shown.  This allows you to have more than one module shown
in a group.

.. code-block:: py3status
    :caption: Example

    order += "group frames"

    # group showing disk space or times using button to change what is shown.
    group frames {
        click_mode = "button"

        frame time {
            tztime la {
                format = "LA %H:%M"
                timezone = "America/Los_Angeles"
            }

            tztime ny {
                format = "NY %H:%M"
                timezone = "America/New_York"
            }

            tztime du {
                format = "DU %H:%M"
                timezone = "Asia/Dubai"
            }
        }

        frame disks {
            disk "/" {
                format = "/ %avail"
            }

            disk "/home" {
                format = "/home %avail"
            }
        }
    }

Frames can also have a toggle button to hide/show the content

.. code-block:: py3status
    :caption: Example

    # A frame showing times in different cities.
    # We also have a button to hide/show the content

    frame time {
        format = '{output}{button}'
        format_separator = ' '  # have space instead of usual i3bar separator

        tztime la {
            format = "LA %H:%M"
            timezone = "America/Los_Angeles"
        }

        tztime ny {
            format = "NY %H:%M"
            timezone = "America/New_York"
        }

        tztime du {
            format = "DU %H:%M"
            timezone = "Asia/Dubai"
        }
    }

Custom click events
-------------------

py3status allows you to easily add click events to modules in your i3bar.
These modules can be both i3status or py3status modules. This is done in
your ``i3status.config`` using the ``on_click`` parameter.

Just add a new configuration parameter named ``on_click [button number]`` to
your module config and py3status will then execute the given i3 command
(using i3-msg).

This means you can run simple tasks like executing a program or execute any
other i3 specific command.

As an added feature and in order to get your i3bar more responsive, every
``on_click`` command will also trigger a module refresh. This works for both
py3status modules and i3status modules as described in the refresh command
below.

.. code-block:: shell

    # button numbers
    1 = left click
    2 = middle click
    3 = right click
    4 = scroll up
    5 = scroll down


.. code-block:: py3status
    :caption: Example

    # reload the i3 config when I left click on the i3status time module
    # and restart i3 when I middle click on it
    time {
        on_click 1 = "reload"
        on_click 2 = "restart"
    }

    # control the volume with your mouse (need >i3-4.8)
    # launch alsamixer when I left click
    # kill it when I right click
    # toggle mute/unmute when I middle click
    # increase the volume when I scroll the mouse wheel up
    # decrease the volume when I scroll the mouse wheel down
    volume master {
        format = "♪: %volume"
        device = "default"
        mixer = "Master"
        mixer_idx = 0
        on_click 1 = "exec i3-sensible-terminal -e alsamixer"
        on_click 2 = "exec amixer set Master toggle"
        on_click 3 = "exec killall alsamixer"
        on_click 4 = "exec amixer set Master 1+"
        on_click 5 = "exec amixer set Master 1-"
    }

    # run wicd-gtk GUI when I left click on the i3status ethernet module
    # and kill it when I right click on it
    ethernet eth0 {
        # if you use %speed, i3status requires root privileges
        format_up = "E: %ip"
        format_down = ""
        on_click 1 = "exec wicd-gtk"
        on_click 3 = "exec killall wicd-gtk"
    }

    # run thunar when I left click on the / disk info module
    disk "/" {
        format = "/ %free"
        on_click 1 = "exec thunar /"
    }

    # this is a py3status module configuration
    # open an URL on opera when I left click on the weather_yahoo module
    weather_yahoo paris {
        cache_timeout = 1800
        woeid = 615702
        forecast_days = 2
        on_click 1 = "exec opera http://www.meteo.fr"
        request_timeout = 10
    }

Special on_click commands
-------------------------

There are two commands you can pass to the ``on_click`` parameter that have a
special meaning to py3status :

*  ``refresh`` : This will refresh (expire the cache) of the clicked module.
   This also works for i3status modules (it will send a SIGUSR1 to i3status
   for you).

*  ``refresh_all`` : This will refresh all the modules from your i3bar
   (i3status included). This has the same effect has sending a SIGUSR1 to
   py3status.

Module data and on_click commands
---------------------------------

Since version 3.3 it is possible to use the output text of a module in the
``on_click`` command.  To do this ``$OUTPUT`` can be used in command and it will be
substituted by the modules text output when the command is run.

.. code-block:: py3status
    :caption: Example

    # copy module output to the clipboard using xclip
    my_module {
        on_click 1 = 'exec echo $OUTPUT | xclip -i'
    }

If the output of a module is a composite then the output of the part clicked on
can be accessed using ``$OUTPUT_PART``.

Environment Variables
---------------------

.. note::
    New in version 3.8

You may use the value of an environment variable in your configuration with
the ``env(...)`` directive. These values are captured at startup and may be
converted to the needed datatype (only ``str``, ``int``, ``float``, ``bool``
and ``auto`` are currently supported).

Note, the ``auto`` conversion will try to guess the type of the contents and
automatically convert to that type. Without an explicit conversion function,
it defaults to ``auto``.

This is primarily designed to obfuscate sensitive information when sharing
your configuration file, such as usernames, passwords, API keys, etc.

The ``env(...)`` expression can be used anywhere a normal constant would be
used. Note, you cannot use the directive in place of a dictionary key, i.e
``{..., env(KEY): 'val', ...}``.

See the examples below!

.. code-block:: py3status
    :caption: Example

    order += "my_module"
    order += env(ORDER_MODULE)

    module {
        normal_parameter = 'some value'
        env_parameter = env(SOME_ENVIRONMENT_PARAM)
        sensitive_api_key = env(API_KEY)

        complex_parameter = {
          'key': env(VAL)
        }

        equivalent1 = env(MY_VAL)
        equivalent2 = env(MY_VAL, auto)

        list_of_tuples = [
          (env(APPLE_NUM, int), 'apple'),
          (2, env(ORANGE))
        ]

        float_param = env(MY_NUM, float)
    }


Inline Shell Code
-----------------

.. note::
    New in version 3.9

You can use the standard output of a shell script in your configuration with
the ``shell(...)`` directive. These values are captured at startup and may be
converted to the needed datatype (only ``str``, ``int``, ``float``, ``bool``
and ``auto`` (the default) are currently supported).

The shell script executed must return a single line of text on stdout and
then terminate. If the type is explicitly declared ``bool``, the exit status
of the script is respected (a non-zero exit status being interpreted falsey).
In any other case if the script exits with a non-zero exit status an error
will be thrown.

The ``shell(...)`` expression can be used anywhere a constant or an ``env(...)``
directive can be used (see the section "Environment Variables").

Usage example:

.. code-block:: py3status
    :caption: Example

    my_module {
        password = shell(pass show myPasswd | head -n1)
        some_string = shell(/opt/mydaemon/get_api_key.sh, str)
        pid = shell(cat /var/run/mydaemon/pidfile, int)
        my_bool = shell(pgrep thttpd, bool)
    }

Due to the way the config is parsed you need to to escape any
closing parenthesis ``)`` using a backslash ``\)``.

.. code-block:: py3status
    :caption: Example

    static_string {
        # note we need to explicitly cast the result to str
        # because we are using it as the format which must be a
        # string
        format = shell(echo $((6 + 2\)\), str)
    }

.. Note::
    Prior to version 3.13 you may not include any closing
    parenthesis ``)`` in the expression. Wrap your commands in a
    script file and call it instead.


Refreshing modules on udev events with on_udev dynamic options
--------------------------------------------------------------

.. note::
    New in version 3.14

Refreshing of modules can be triggered when an udev event is detected on a
specific subsystem using the ``on_udev_<subsystem>`` configuration parameter
and an associated action.

Possible actions:
- ``refresh``: immediately refresh the module and keep on updating it as usual
- ``refresh_and_freeze``: module is ONLY refreshed when said udev subsystem emits
an event

.. code-block:: py3status
    :caption: Example

    # refresh xrandr only when udev 'drm' events are triggered
    xrandr {
        on_udev_drm = "refresh_and_freeze"
    }

.. note::
    This feature will only activate when ``pyudev`` is installed on the system.
    This is an optional dependency of py3status and is therefore not enforced
    by all package managers.


Request Timeout
--------------------------------------------------------------

.. note::
    New in version 3.16

Request Timeout for URL request based modules can be specified in the
module configuration. To find out if your module supports that, look for
``self.py3.request`` in the code. Otherwise, we will use ``10``.

.. code-block:: py3status
    :caption: Example

    # stop waiting for a response after 10 seconds
    exchange_rate {
        request_timeout = 10
    }
