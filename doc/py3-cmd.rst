.. _py3-cmd:

The py3-cmd CLI
===============

py3status can be controlled remotely via the ``py3-cmd`` cli utility.

This utility allows you to run a number of commands.

.. code-block:: shell

    # button numbers
    1 = left click
    2 = middle click
    3 = right click
    4 = scroll up
    5 = scroll down


Commands available
------------------


click
^^^^^

Send a click event to a module as though it had been clicked on.
You can specify the button to simulate.

.. code-block:: shell

    # send a left/middle/right click
    py3-cmd click --button 1 dpms      # left
    py3-cmd click --button 2 sysdata   # middle
    py3-cmd click --button 3 pomodoro  # right

    # send a up/down click
    py3-cmd click --button 4 volume_status  # up
    py3-cmd click --button 5 volume_status  # down

.. code-block:: shell

    # toggle button in frame module
    py3-cmd click --button 1 --index button frame  # left

    # change modules in group module
    py3-cmd click --button 5 --index button group  # down

    # change time units in timer module
    py3-cmd click --button 4 --index hours timer    # up
    py3-cmd click --button 4 --index minutes timer  # up
    py3-cmd click --button 4 --index seconds timer  # up


list
^^^^

Print a list of modules or module docstrings.

.. code-block:: shell

    # list one or more modules
    py3-cmd list clock loadavg xrandr  # full
    py3-cmd list coin* git* window*    # fnmatch
    py3-cmd list [a-e]*                # abcde

    # list all modules
    py3-cmd list --all

    # show full (i.e. docstrings)
    py3-cmd list vnstat uname -f


refresh
^^^^^^^

Cause named module(s) to have their output refreshed.

.. code-block:: shell

    # refresh all instances of the wifi module
    py3-cmd refresh wifi

    # refresh multiple modules
    py3-cmd refresh coin_market github weather_yahoo

    # refresh module with instance name
    py3-cmd refresh "weather_yahoo chicago"

    # refresh all modules
    py3-cmd refresh --all


Calling commands from i3
------------------------

``py3-cmd`` can be used in your i3 configuration file.


To send a click event to the whatismyip module when ``Mod+x`` is pressed

.. code-block:: none

    bindsym $mod+x exec py3-cmd click whatismyip


This example shows how volume control keys can be bound to change the volume
and then cause the volume_status module to be updated.

.. code-block:: none

    bindsym XF86AudioRaiseVolume  exec "amixer -q sset Master 5%+ unmute; py3-cmd refresh volume_status"
    bindsym XF86AudioLowerVolume  exec "amixer -q sset Master 5%- unmute; py3-cmd refresh volume_status"
    bindsym XF86AudioMute         exec "amixer -q sset Master toggle; py3-cmd refresh volume_status"



.. note::

    ``py3-cmd`` was added in py3status version 3.6 if you
    are using a source installation from a prior version, then you may
    have to run ``setup.py`` again so that it is correctly installed
    see :ref:`setup`.
