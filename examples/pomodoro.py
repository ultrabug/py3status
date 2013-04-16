"""
Pomodoro countdown on i3bar originally written by @Fandekasp (Adrien Lemaire)

Requires:
    - libnotify
    - python-gobject
    - python-keybinder
"""
from gi.repository import Notify
from gi.repository import GObject as gobject

#FIXME: keybinder gobject collides with Notify but its not blocking
import keybinder
import gtk

from threading import Thread
from time import time
from time import sleep

KEY_PAUSE = '<Mod1>B' #Alt + B(reak)
KEY_START = '<Mod1>P' #Alt + P(omodoro)
KEY_STOP  = '<Mod1>R' #Alt + R(eset)
MAX_BREAKS = 4
POSITION = 0
TIMER_POMODORO = 25 * 60
TIMER_BREAK = 5 * 60
TIMER_LONG_BREAK = 15 * 60

pomo_thread = None
gobject.threads_init()

class Pomodoro(Thread):
    """
    Handles Pomodoro and Break countdowns
    """
    def __init__(self):
        """
        Well, default values
        """
        Thread.__init__(self)
        self.kill = False
        self.callback('stop')

    @property
    def response(self):
        """
        Return the response full_text string
        """
        return '%s (%d)' % (self.prefix, self.timer)

    def callback(self, status):
        """
        Called on a keybinder event
        """
        self.status = status
        if status == 'stop':
            self.prefix = 'Pomodoro'
            self.status = 'stop'
            self.timer = TIMER_POMODORO
            self.breaks = 1

        elif status == 'start':
            self.prefix = 'Pomodoro'
            self.timer = TIMER_POMODORO

        elif status == 'pause':
            self.prefix = 'Break #%d' % self.breaks
            if self.breaks > MAX_BREAKS:
                self.timer = TIMER_LONG_BREAK
                self.breaks = 1
            else:
                self.breaks += 1
                self.timer = TIMER_BREAK

    def stop(self):
        """
        Exit nicely
        """
        self.kill = True

    def notify(self):
        """
        Print a visual message
        """
        try:
            Notify.init('')
            notification = Notify.Notification.new (
                '<b>Attention:</b>',
                '{} is finished'.format(self.response),
                'dialog-information',
                )
            notification.show()
        except Exception as err:
            pass

    def run(self):
        """
        Infinite loop setting the keybinder and waiting for key events
        """
        bindings = {
            'pause': KEY_PAUSE,
            'start': KEY_START,
            'stop' : KEY_STOP,
            }
        for status, keystr in bindings.items():
            keybinder.bind(keystr, self.callback, status)

        while not self.kill:
            gtk.main_iteration(block=False)
            if self.status != 'stop' and self.timer > 0:
                self.timer -= 1
                if self.timer == 0:
                    self.notify()
            sleep(1)

        for status, keystr in bindings.items():
            try:
                keybinder.unbind(keystr)
            except Exception as e:
                pass

class Py3status:
    """
    Main py3status class which spawns a thread for Pomodoro keybinder
    """
    def kill(self):
        """
        Exit nicely
        """
        pomo_thread.stop()

    def pomodoro(self, json, i3status_config):
        """
        Pomodoro response handling
        """
        response = {'full_text' : '', 'name' : 'pomodoro'}

        global pomo_thread

        if not pomo_thread:
            pomo_thread = Pomodoro()
            pomo_thread.start()
        else:
            response['full_text'] = pomo_thread.response

        if pomo_thread.status == 'start':
            response['color'] = i3status_config['color_good']
        elif pomo_thread.status == 'pause':
            response['color'] = i3status_config['color_degraded']
        else:
            response['color'] = i3status_config['color_bad']

        response['cached_until'] = time()
        return (POSITION, response)
