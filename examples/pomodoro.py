"""
REQUIREMENTS
------------
* libnotify
* python-gobject


INSTALLATION
------------
Please add the following lines in your ~/.i3/config file::

    bindsym $mod+minus exec echo "stop" > ~/.i3/pomodoro.log
    bindsym $mod+equal exec echo "pause" > ~/.i3/pomodoro.log
    bindsym $mod+plus exec echo "start" > ~/.i3/pomodoro.log

"""
from datetime import timedelta
from gi.repository import Notify
import os.path
from time import time


LOG_FILE   = os.path.join(os.path.expanduser('~'), '.i3', 'pomodoro.log')
LONG_REST  = 1800  # 60 * 30
NB_REST    = 4
POMO       = 1500  # 60 * 25
POSITION   = 0
SHORT_REST = 300   # 60 * 5


class Py3status:
    """
    Pomodoro method
    """
    pomo = POMO
    rest = SHORT_REST
    nb_rest = NB_REST

    @property
    def response(self):
        return {
            'cached_until' : time(),
            'full_text': '',
            'name': 'pomodoro',
        }

    def pomodoro(self, json, i3status_config):
        """
        This function will update a timer in the i3status bar for 25 minutes,
        then print a red "Break time" message for 5 minutes.
        """
        status = self.get_status()

        if status == 'stop':
            self.pomo = POMO
            self.rest = SHORT_REST
            self.nb_rest = NB_REST
            return (POSITION, self.response)

        # Else run normally
        if not self.pomo:
            if status != 'pause':
                self.rest -= 1
            timer = self.rest
            self.full_text = 'Break time'
            color = 'color_bad'
        else:
            if status != 'pause':
                self.pomo -= 1
            timer = self.pomo
            self.full_text = 'Pomodoro'
            color = 'color_degraded'

        if status == 'pause':
            color = 'color_good'

        if not timer:
            # Pomodoro or Rest is finished, send notification
            self.send_notification()

        response = self.response
        response.update({
            'color': i3status_config[color],
            'full_text': '{}: {}'.format(
                self.full_text, str(timedelta(seconds=timer))[2:]),
        })

        return (POSITION, response)

    def get_status(self):
        """
        Read the log file and get the status value. Value is modifying via
        i3 key mapping.

        Value can be:
            * start
            * pause
            * stop (default)
        """
        with open(LOG_FILE, 'r') as f:
            status = f.read()

        return status.rstrip('\n')

    def send_notification(self):
        """
        Print a visual message
        """

        Notify.init('Pomodoro')
        notification = Notify.Notification.new (
            '<b>Attention:</b>',
            '{} is finished'.format(self.full_text),
            'dialog-information',
        )
        notification.show()

        if not self.rest:
            # Rest is finished, reinitialize data
            self.nb_rest -= 1
            self.pomo = POMO
            self.rest = SHORT_REST

        if not self.nb_rest:
            # Number of small rest reached, go for long rest
            self.rest = LONG_REST
            self.nb_rest = NB_REST
