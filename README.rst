*********
py3status
*********
|version|

.. |version| image:: https://pypip.in/version/py3status/badge.png

**py3status** is an extensible i3status wrapper written in python.

Using py3status, you can take control of your i3bar easily by:

- writing your own modules and have their output displayed on your bar
- handling click events on your i3bar and play with them in no time
- seeing your clock tick every second whatever your i3status interval

No extra configuration file needed, just install & enjoy !

Documentation
=============
See the wiki for up to date documentation:

- https://github.com/ultrabug/py3status/wiki

Learn how to write your own modules:

- https://github.com/ultrabug/py3status/wiki/Write-your-own-modules

Get help or share your ideas on IRC:

- channel **#py3status** on **FreeNode**

Requirements
============
You **must** set the `output_format` to `i3bar` in the general section of your i3status.conf:
::
    general {
        colors = true
        interval = 5
        output_format = "i3bar"
    }

Usage
=====
In your i3 config file, simply switch from `i3status` to `py3status` in your `status_command`:
::
    status_command py3status

Usually you have your own i3status configuration, just point to it:
::
    status_command py3status -c ~/.i3/i3status.conf

Installation
============
Pypi
----
Using pip:
::
    $ pip install py3status

Gentoo Linux
------------
Using emerge:
::
    $ sudo emerge -a py3status

Arch Linux
----------
Thanks to @waaaaargh, py3status is present in the Arch User Repository using this URL:
::
    https://aur.archlinux.org/packages/py3status-git/

Fedora
------
Using yum:
::
    $ yum install py3status

Options
=======
You can see the help of py3status by issuing `py3status -h`:
::
    -c I3STATUS_CONF  path to i3status config file
    --debug           be verbose in syslog
    -i INCLUDE_PATHS  include user-written modules from those directories
                      (default .i3/py3status)
    -n INTERVAL       update interval in seconds (default 1 sec)
    -s, --standalone  standalone mode, do not use i3status
    -t CACHE_TIMEOUT  default injection cache timeout in seconds
                      (default 60 sec)
    -v, --version     show py3status version and exit

Control
=======
Just like i3status, you can force an update by sending a SIGUSR1 signal to py3status.
Note that this will also send a SIGUSR1 signal to i3status.
::
    killall -USR1 py3status
