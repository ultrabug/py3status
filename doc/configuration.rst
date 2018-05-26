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

- ``nagbar_font``. It will be used as an argument to
    ``i3-nagbar -f``, thus setting its font.

.. code-block:: py3status
    :caption: Example

    py3status {
        nagbar_font = 'pango:Ubuntu Mono 12'
    }

Configuration obfuscation
-------------------------

.. note::
    New in version 3.1

Py3status allows you to hide individual configuration parameters so that they
do not leak into log files, user notifications or to the i3bar. Additionally
they allow you to obfuscate configuration parameters using base64 encoding.

To do this you need to add an obfuscation option to the configuration
parameter. Obfuscation options are added by adding `:hide` or `:base64` to the
name of the parameters.


.. note::
    Obfuscation is only available for string parameters.

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

Please be aware that due to the way the parser works, you may not include any
closing parenthesis ( ``)`` ) in the expression. Wrap your commands in a script
file and call it instead.

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
