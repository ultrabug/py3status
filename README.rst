*********
py3status
*********
|travis| |readthedocs|

.. |travis| image:: https://travis-ci.org/ultrabug/py3status.svg?branch=master
.. |readthedocs| image:: https://readthedocs.org/projects/py3status/badge/?version=latest

**py3status** is an extensible i3status wrapper written in python.

Using py3status, you can take control of your i3bar easily by:

- using one of the available
  `modules <https://py3status.readthedocs.io/en/latest/modules.html>`_
  shipped with py3status
- grouping multiple modules and automatically or manually cycle their display
- writing your own modules and have their output displayed on your bar
- handling click events on your i3bar and play with them in no time
- seeing your clock tick every second whatever your i3status interval

**No extra configuration file needed**, just install & enjoy !

About
=====
You will love `py3status` if you're using `i3wm <https://i3wm.org>`_ (or `sway <https://swaywm.org>`_) and are frustrated by the i3status `limitations <https://faq.i3wm.org/question/459/external-scriptsprograms-in-i3status-without-loosing-colors/>`_ on your i3bar such as:

* you cannot hack into it easily
* you want more than the built-in modules and their limited configuration
* you cannot pipe the result of one of more scripts or commands in your bar easily

Philosophy
----------
* **no added configuration file, use the standard i3status.conf**
* **rely on i3status**' strengths and its **existing configuration** as much as possible
* **be extensible**, it must be easy for users to add their own stuff/output by writing a simple python class which will be loaded and executed dynamically
* **easily allow interactivity** with the i3bar
* add some **built-in enhancement/transformation** of basic i3status modules output

We apply the `Zen of py3status <https://py3status.readthedocs.io/en/latest/contributing.html#zen-of-py3status>`_ to improve this project and encourage everyone to read it!

Documentation
=============
Up-to-date `documentation <https://py3status.readthedocs.io>`_:

-  `Installation <https://py3status.readthedocs.io/en/latest/intro.html#installation>`_

-  `Using modules <https://py3status.readthedocs.io/en/latest/configuration.html>`_

-  `Custom click events <https://py3status.readthedocs.io/en/latest/configuration.html#custom-click-events>`_

-  `Writing custom modules <https://py3status.readthedocs.io/en/latest/writing_modules.html>`_

-  `Contributing <https://py3status.readthedocs.io/en/latest/contributing.html>`_

-  `The py3-cmd command line <https://py3status.readthedocs.io/en/latest/py3-cmd.html>`_

Get help or share your ideas on IRC:

- channel **#py3status** on **FreeNode**

Usage
=====
In your i3 config file, simply switch from *i3status* to *py3status* in your *status_command*:
::

    status_command py3status

Usually you have your own i3status configuration, just point to it:
::

    status_command py3status -c ~/.i3/i3status.conf

Available modules
=================

`All modules <https://py3status.readthedocs.io/en/latest/modules.html>`_ shipped with py3status are `configurable directly from your current i3status.conf <https://py3status.readthedocs.io/en/latest/configuration.html#using-modules>`_!

`Check them out <https://py3status.readthedocs.io/en/latest/modules.html>`_ to see all the configuration options.

Installation
============

See the up to date and complete `installation instructions <https://py3status.readthedocs.io/en/latest/intro.html#installation>`_ for your favorite distribution.

Options
=======
You can see the help of py3status by issuing `py3status -h`:
::

    usage: py3status [-h] [-b] [-c FILE] [-d] [-g] [-i PATH] [-l FILE] [-s]
                     [-t INT] [-m] [-u PATH] [-v] [--wm WINDOW_MANAGER]

    The agile, python-powered, i3status wrapper

    optional arguments:
      -h, --help            show this help message and exit
      -b, --dbus-notify     send notifications via dbus instead of i3-nagbar
                            (default: False)
      -c, --config FILE     load config (default: /home/alexys/.i3/i3status.conf)
      -d, --debug           enable debug logging in syslog and --log-file
                            (default: False)
      -g, --gevent          enable gevent monkey patching (default: False)
      -i, --include PATH    append additional user-defined module paths (default:
                            None)
      -l, --log-file FILE   enable logging to FILE (default: None)
      -s, --standalone      run py3status without i3status (default: False)
      -t, --timeout INT     default module cache timeout in seconds (default: 60)
      -m, --disable-click-events
                            disable all click events (default: False)
      -u, --i3status PATH   specify i3status path (default: /usr/bin/i3status)
      -v, --version         show py3status version and exit (default: False)
      --wm WINDOW_MANAGER   specify window manager i3 or sway (default: i3)

Control
=======
Just like i3status, you can force an update of your i3bar by sending a SIGUSR1 signal to py3status.
Note that this will also send a SIGUSR1 signal to i3status.
::

    killall -USR1 py3status

To refresh individual modules, the `py3-cmd <http://py3status.readthedocs.io/en/latest/py3-cmd.html>`_ utility can be used, e.g.:
::

   py3-cmd refresh wifi
