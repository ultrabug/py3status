Introduction
============

Using py3status, you can take control of your i3bar easily by:

* using one of the available :ref:`modules` shipped with py3status
* grouping multiple modules and automatically or manually cycle their
  display
* writing your own modules and have their output displayed on your bar
* handling click events on your i3bar and play with them in no time
* seeing your clock tick every second whatever your i3status interval

No extra configuration file needed, just install & enjoy!

About
-----

You will love py3status if you're using `i3wm
<http://i3wm.org>`_ and are frustrated by the i3status
limitations on your i3bar such as:

* you cannot hack into it easily
* you want more than the built-in modules and their limited configuration
* you cannot pipe the result of one of more scripts or commands in
  your bar easily

Philosophy
----------

* no added configuration file, use the standard i3status.conf
* rely on i3status' strengths and its existing configuration
  as much as possible
* be extensible, it must be easy for users to add their own
  stuff/output by writing a simple python class which will be loaded
  and executed dynamically
* easily allow interactivity with the i3bar
* add some built-in enhancement/transformation of basic i3status
  modules output
* support python 2.7 and python 3.x

We apply the :ref:`zen` to improve this project and encourage everyone to read it!

Installation
------------

+-------------------+-------------------------------+-------------------------------------+
|Distro             |Helpful Command                |Useful Note                          |
+===================+===============================+=====================================+
|**Arch Linux**     |``$ pacman -S py3status``      |Stable updates. Official releases.   |
+                   +-------------------------------+-------------------------------------+
|                   |``$ yay -S py3status-git``     |Real-time updates from master branch.|
+-------------------+-------------------------------+-------------------------------------+
|**Debian & Ubuntu**|``$ apt-get install py3status``|Stable updates.                      |
|                   |                               |In testing and unstable, and soon in |
|                   |                               |stable backports.                    |
+-------------------+-------------------------------+-------------------------------------+
|**Fedora**         |``$ dnf install py3status``    |                                     |
+-------------------+-------------------------------+-------------------------------------+
|**Gentoo Linux**   |``$ emerge -a py3status``      |Check available USE flags!           |
+-------------------+-------------------------------+-------------------------------------+
|**Pypi**           |``$ pip install py3status``    |There are optional requirements that |
|                   |                               |you could find useful:               |
|                   |                               |                                     |
|                   |                               |py3status[gevent] for gevent support.|
|                   |                               |py3status[udev] for udev support.    |
|                   |                               |                                     |
|                   |                               |Or if you want everything:           |
|                   |                               |py3status[all] to install all core   |
|                   |                               |extra requirements and features.     |
+-------------------+-------------------------------+-------------------------------------+
|**Void Linux**     |``$ xbps-install -S py3status``|                                     |
+-------------------+-------------------------------+-------------------------------------+
|**NixOS**          |``$ nix-env -i``               |Not a global install. See below.     |
|                   |  ``python3.6-py3status-3.7``  |                                     |
+-------------------+-------------------------------+-------------------------------------+


Debian/Ubuntu
^^^^^^^^^^^^^

.. note::

  If you want to use pip, you should consider using *pypi-install*
  from the *python-stdeb* package (which will create a .deb out from a
  python package) instead of directly calling pip.


NixOS
^^^^^

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


Support
-------

Get help, share ideas or feedbacks, join community, report bugs, or others, see:

Github
^^^^^^

`Issues <https://github.com/ultrabug/py3status/issues>`_ /
`Pull requests <https://github.com/ultrabug/py3status/pulls>`_

Live IRC Chat
^^^^^^^^^^^^^


Visit `#py3status <https://webchat.freenode.net/?channels=%23py3status&uio=d4>`_
at `freenode.net <https://freenode.net>`_


Usage
-----

In your i3 config file, simply switch from *i3status* to *py3status* in your *status_command*:

.. code-block:: shell

    status_command py3status

Usually you have your own i3status configuration, just point to it:

.. code-block:: shell

    status_command py3status -c ~/.i3/i3status.conf

Available modules
^^^^^^^^^^^^^^^^^

You can get a list with short descriptions of all available modules by using the CLI:

.. code-block:: shell

    $ py3status modules list


To get more details about all available modules and their configuration, use:

.. code-block:: shell

    $ py3status modules details

All modules shipped with py3status are present as the Python source files in
the ``py3status/modules`` directory.


Options
^^^^^^^

You can see the help of py3status by issuing ``py3status --help``:

.. code-block:: shell

    -h, --help            show this help message and exit
    -b, --dbus-notify     use notify-send to send user notifications rather than
                          i3-nagbar, requires a notification daemon eg dunst
    -c I3STATUS_CONF, --config I3STATUS_CONF
                          path to i3status config file
    -d, --debug           be verbose in syslog
    -g, --gevent          enable gevent monkey patching (default False)
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
    -m, --disable-click-events
                          disable all click events
    -v, --version         show py3status version and exit

Control
^^^^^^^

Just like i3status, you can force an update of your i3bar by sending a SIGUSR1 signal to py3status.
Note that this will also send a SIGUSR1 signal to i3status.

.. code-block:: shell

    killall -USR1 py3status

.. note::

    Since version 3.6 py3status can be controlled via the
    :ref:`py3-cmd` which is **recommended**.


Contributing
------------

We value very much any kind of feedback/contribution, see :ref:`contributing` to
read more about how to help!
