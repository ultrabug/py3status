*********
py3status
*********
|version|

.. |version| image:: https://pypip.in/version/py3status/badge.png

**py3status** is an extensible i3status wrapper written in python.

Using py3status, you can take control of your i3bar easily by:

- using one of the availables modules shipped with py3status
- writing your own modules and have their output displayed on your bar
- handling click events on your i3bar and play with them in no time
- seeing your clock tick every second whatever your i3status interval

No extra configuration file needed, just install & enjoy !

Documentation
=============
Up to date documentation:

- `See the wiki <https://github.com/ultrabug/py3status/wiki>`_

Learn how to easily **handle i3bar click events** directly from your i3status config:

- `Handle click events directly from your i3status config <https://github.com/ultrabug/py3status/wiki/Handle-click-events-directly-from-your-i3status-config>`_

Learn how to **extend your current i3status config** to easily interact with your i3bar:

- `Load and order py3status modules directly from your current i3status config <https://github.com/ultrabug/py3status/wiki/Load-and-order-py3status-modules-directly-from-your-current-i3status-config>`_

Learn how to write your own modules:

- `Write your own modules <https://github.com/ultrabug/py3status/wiki/Write-your-own-modules>`_

Get help or share your ideas on IRC:

- channel **#py3status** on **FreeNode**

Usage
=====
In your i3 config file, simply switch from `i3status` to `py3status` in your `status_command`:
::
    status_command py3status

Usually you have your own i3status configuration, just point to it:
::
    status_command py3status -c ~/.i3/i3status.conf

Available modules
=================
All the modules shipped with py3status are present in the sources in the `py3status/modules <https://github.com/ultrabug/py3status/tree/master/py3status/modules>`_ folder.

Most of them are **configurable directly from your current i3status.conf**, check them out to see all the configurable variables.

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
    -h, --help            show this help message and exit
    -c I3STATUS_CONF, --config I3STATUS_CONF
                          path to i3status config file
    -d, --debug           be verbose in syslog
    -i INCLUDE_PATHS, --include INCLUDE_PATHS
                          include user-written modules from those directories
                          (default ~/.i3/py3status)
    -n INTERVAL, --interval INTERVAL
                          update interval in seconds (default 1 sec)
    -s, --standalone      standalone mode, do not use i3status
    -t CACHE_TIMEOUT, --timeout CACHE_TIMEOUT
                          default injection cache timeout in seconds (default 60
                          sec)
    -v, --version         show py3status version and exit

Control
=======
Just like i3status, you can force an update of your i3bar by sending a SIGUSR1 signal to py3status.
Note that this will also send a SIGUSR1 signal to i3status.
::
    killall -USR1 py3status
