from subprocess import Popen
from time import time


class Py3status:
    """
    This module allows you to take actions based on click events made on
    the i3status modules. For example, thanks to this module you could
    launch the wicd GUI when clicking on the ethernet or wireless module
    of your i3status output !

    IMPORTANT:
        This module file name is reserved and should NOT be changed if you
        want py3status to handle your i3status modules click events !

        The behavior described above will only work if this file is named
        'i3bar_click_events.py' !
    """
    def __init__(self):
        """
        This is where you setup your actions based on your i3status config.

        Configuration:
        --------------
        self.actions = {
            "<module name and instance>": {
                <button number>: [<function to run>, <arg1>, <arg2>],
            }
        }

        Variables:
        ----------
        <button number> is an integer from 1 to 3:
            1 : left click
            2 : middle click
            3 : right click

        <function to run> is a python function written in this module.
            The 'external_command' function is provided for convenience if
            you want to call an external program from this module.
            You can of course write your own functions and have them executed
            on a click event at will with possible arguments <arg1>, <arg2>...

        <module name and instance> is a string made from the module
        attribute 'name' and 'instance' using a space as separator:
            For i3status modules, it's simply the name of the module as it
            appears in the 'order' instruction of your i3status.conf.
            Example:
                in i3status.conf -> order += "wireless wlan0"
                self.actions key -> "wireless wlan0"

        Usage example:
        --------------
            - Open the wicd-gtk GUI when we LEFT click on the ethernet
            module of i3status.
            - Open emelfm2 to /home when we LEFT click on
            the /home instance of disk_info
            - Open emelfm2 to / when we LEFT click on
            the / instance of disk_info

            The related i3status.conf looks like:
                order += "disk /home"
                order += "disk /"
                order += "ethernet eth0"

            The resulting self.actions should be:
                self.actions = {
                    "ethernet eth0": {
                        1: [external_command, 'wicd-gtk', '-n'],
                    },
                    "disk_info /home": {
                        1: [external_command, 'emelfm2', '-1', '~'],
                    },
                    "disk_info /": {
                        1: [external_command, 'emelfm2', '-1', '/'],
                    },
                }
        """
        # CONFIGURE ME PLEASE, LOVE YOU BIG TIME !
        self.actions = {
        }

    def on_click(self, i3status_output_json, i3status_config, event):
        """
        If an action is configured for the given i3status module 'name' and
        'instance' (if present), then we'll execute the given function with
        its arguments (if present).

        Usually you SHOULD NOT modify this part of the code.
        """
        button = event['button']
        key_name = '{} {}'.format(
            event['name'],
            event.get('instance', '')
        ).strip()
        if key_name in self.actions and button in self.actions[key_name]:
            # get the function to run
            func = self.actions[key_name][button][0]
            assert hasattr(func, '__call__'), \
                'first element of the action list must be a function'

            # run the function with the possibly given arguments
            func(*self.actions[key_name][button][1:])

    def i3bar_click_events(self, i3status_output_json, i3status_config):
        """
        Cached empty output, this module doesn't show anything.
        """
        response = {'full_text': '', 'name': 'i3bar_click_events'}
        response['cached_until'] = time() + 3600
        return (-1, response)


def external_command(*cmd):
    """
    This convenience function lets you call an external program at will.

    NOTE:
        The stdout and stderr MUST be suppressed as shown here to avoid any
        output from being caught by the i3bar (this would freeze it).
        See issue #20 for more info.
    """
    Popen(
        cmd,
        stdout=open('/dev/null', 'w'),
        stderr=open('/dev/null', 'w')
    )
