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
You will love `py3status` if you're using `i3wm <http://i3wm.org>`_ and are frustrated by the i3status `limitations <https://faq.i3wm.org/question/459/external-scriptsprograms-in-i3status-without-loosing-colors/>`_ on your i3bar such as:

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

Documentation
=============
Up-to-date `documentation <https://py3status.readthedocs.io>`_:

-  `Using modules <https://py3status.readthedocs.io/en/latest/configuration.html>`_

-  `Custom click events <https://py3status.readthedocs.io/en/latest/configuration.html#custom-click-events>`_

-  `Writing custom modules <https://py3status.readthedocs.io/en/latest/writing_modules.html>`_

-  `Contributing <https://py3status.readthedocs.io/en/latest/contributing.html>`_

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
You can get a list with short descriptions of all available modules by using the CLI:
::

    $ py3status modules list


To get more details about all available modules and their configuration, use:
::

    $ py3status modules details

All modules shipped with py3status are present as the Python source files in the `py3status/modules <https://github.com/ultrabug/py3status/tree/master/py3status/modules>`_ directory.

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
Thanks to @Horgix, py3status is present in the Arch User Repository:

- `py3status <https://aur.archlinux.org/packages/py3status>`_, which is a
  stable version updated at each release
- `py3status-git <https://aur.archlinux.org/packages/py3status-git/>`_, which
  builds directly against the upstream master branch

Thanks to @waaaaargh and @carstene1ns for initially creating the packages.

Fedora
------
Using dnf:
::

    $ dnf install py3status

NixOS
----------
Installing in local environment using nix-env:
::
    $ nix-env -i python3.6-py3status-3.7

To have it globally persistent add to your NixOS configuration file py3status as a Python 3.6 package with
::
    (python36.withPackages(ps: with ps; [ py3status ]))

If you are, and you probably are, using `i3 <https://i3wm.org/>`_ you might want a section in your `/etc/nixos/configuration.nix` that looks like this:
::
    services.xserver.windowManager.i3 = {
      enable = true;
      extraPackages = with pkgs; [
        dmenu
        i3status
        i3lock
        (python36.withPackages(ps: with ps; [ py3status pytz tzlocal ]))
      ];
    };

In this example I included the python packages **pytz** and **tzlocal** which are necessary for the py3status module **clock**.
The default packages that come with i3 (dmenu, i3status, i3lock) have to be mentioned if they should still be there.

Debian/Ubuntu
-------------
Packaged by @sdelafond, and available via apt-get:
::

    $ apt-get install py3status

For now it's only in testing and unstable, but will soon be added to
stable-backports.

Note: if you want to use pip, you should consider using *pypi-install*
from the *python-stdeb* package (which will create a .deb out from a
python package) instead of directly calling pip.

Options
=======
You can see the help of py3status by issuing `py3status -h`:
::

    -h, --help            show this help message and exit
    -b, --dbus-notify     use notify-send to send user notifications rather than
                          i3-nagbar, requires a notification daemon eg dunst
    -c I3STATUS_CONF, --config I3STATUS_CONF
                          path to i3status config file
    -d, --debug           be verbose in syslog
    -i INCLUDE_PATHS, --include INCLUDE_PATHS
                          include user-written modules from those directories
                          (default ~/.i3/py3status)
    -l LOG_FILE, --log-file LOG_FILE
                          path to py3status log file
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

To refresh individual modules, the `py3-cmd <http://py3status.readthedocs.io/en/latest/py3-cmd.html>`_ utility can be used, e.g.:
::

   py3-cmd refresh wifi
