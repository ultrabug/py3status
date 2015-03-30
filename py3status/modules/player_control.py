# -*- coding: utf-8 -*-
"""
Control music/video players.

Provides an icon to control simple functions of audio/video players:
 - start (left click)
 - stop  (left click)
 - pause (middle click)

@author Federico Ceratto <federico.ceratto@gmail.com>
@license BSD
"""
# Any contributor to this module should add his/her name to the @author
# line, comma separated.

from syslog import syslog, LOG_INFO
from time import time, sleep
import os
import subprocess


def log(msg):
    syslog(LOG_INFO, "player_control: %s" % msg[:100])


class Py3status:
    """
    Configuration parameters:
        - debug: enable verbose logging (bool) (default: False)
        - supported_players: supported players (str) (whitespace separated list)
        - volume_tick: percentage volume change on mouse wheel (int) (positive number or None to disable it)

    """

    debug = False
    supported_players = 'audacious'
    volume_tick = 1

    def __init__(self):
        self.status = 'stop'
        self.icon = u'▶'

    def on_click(self, i3s_output_list, i3s_config, event):
        """
        """
        buttons = (None, 'left', 'middle', 'right', 'up', 'down')
        try:
            button = buttons[event['button']]
        except IndexError:
            return

        if button in ('up', 'down'):
            if self.volume_tick is None:
                return

            self._change_volume(button == 'up')
            return

        if self.status == 'play':
            if button == 'left':
                self._stop()

            elif button == 'middle':
                self._pause()

        elif self.status == 'stop':
            if button == 'left':
                self._play()

        elif self.status == 'pause':
            if button in ('left', 'right'):
                self._play()

    def _run(self, *args):
        if self.debug:
            log('running %s' % repr(*args))

        subprocess.check_output(*args, stderr=subprocess.STDOUT)

    def _play(self):
        self.status = 'play'
        self.icon = u'◼'
        player_name = self._detect_running_player()
        if player_name == 'audacious':
            self._run(['/usr/bin/audacious', '-p'])

    def _stop(self):
        self.status = 'stop'
        self.icon = u'▶'
        player_name = self._detect_running_player()
        if player_name == 'audacious':
            self._run(['/usr/bin/audacious', '-s'])

    def _pause(self):
        self.status = 'pause'
        self.icon = u'❚❚'
        player_name = self._detect_running_player()
        if player_name == 'audacious':
            self._run(['/usr/bin/audacious', '-u'])

    def _change_volume(self, increase):
        """Change volume using amixer
        """
        sign = '+' if increase else '-'
        delta = "%d%%%s" % (self.volume_tick, sign)
        self._run(('/usr/bin/amixer', '-q', 'sset', 'Master', delta))

    def _detect_running_player(self):
        """Detect running player process, if any
        """
        supported_players = self.supported_players.split(' ')
        running_players = []
        for pid in os.listdir('/proc'):
            if not pid.isdigit():
                continue

            fn = os.path.join('/proc', pid, 'comm')
            try:
                with open(fn, 'rb') as f:
                    player_name = f.read().decode().rstrip()

            except:
                continue

            if player_name in supported_players:
                running_players.append(player_name)

        # Pick which player to use based on the order in self.supported_players
        for player_name in supported_players:
            if player_name in running_players:
                if self.debug:
                    log('found player: %s' % player_name)

                return player_name

        return None

    def player_control(self, i3s_output_list, i3s_config):
        return dict(
            full_text=self.icon,
            cached_until=time(),
        )


if __name__ == "__main__":
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.player_control([], config))
        sleep(1)
