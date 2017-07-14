.. _py3-cmd:

py3-cmd
=======

py3status can be controlled remotely via the ``py3-cmd`` cli utility.

This utility allows you to run a number of commands.

Commands available
------------------

refresh
^^^^^^^

Cause named module(s) to have their output refreshed.
To refresh all modules use the ``all`` keyword.

.. code-block:: shell

    # refresh any wifi modules
    py3-cmd refresh wifi

    # refresh wifi module instance eth0
    py3-cmd refresh "wifi eth0"

    # refresh any wifi or whatismyip modules
    py3-cmd refresh wifi whatismyip

    # refresh all py3status modules
    py3-cmd refresh all


click
^^^^^

Send a click event to a module as though it had been clicked on.
You can specify the button to simulate.

.. code-block:: shell

    # send a click event to the whatismyip module (button 1)
    py3-cmd click whatismyip

    # send a click event to the backlight module with button 5
    py3-cmd click 5 backlight

You can also specify the button using one of the named shortcuts
``leftclick``, ``rightclick``, ``middleclick``, ``scrollup``, ``scrolldown``.

.. code-block:: shell

    # send a click event to the whatismyip module (button 1)
    py3-cmd leftclick whatismyip

    # send a click event to the backlight module with button 5
    py3-cmd scrolldown backlight


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
