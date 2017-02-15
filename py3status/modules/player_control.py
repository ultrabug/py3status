# -*- coding: utf-8 -*-
"""
Control Audacious or VLC media player.

Provides an icon to control simple functions of audio/video players:
    - start (left click)
    - stop  (left click)
    - pause (middle click)

Configuration parameters:
    cache_timeout: how often to update in seconds (default 10)
    debug: enable verbose logging (bool) (default False)
    format: format of the output (default "{icon}")
    pause_icon: (default '❚❚')
    play_icon: (default '▶')
    stop_icon: (default '◼')
    supported_players: supported players (str) (comma separated list)
         (default 'audacious,vlc')
    volume_tick: percentage volume change on mouse wheel (int) (positive number
        or None to disable it) (default 1)

Format placeholders:
    {icon} an icon to control music/video players

@author Federico Ceratto <federico.ceratto@gmail.com>, rixx
@license BSD

SAMPLE OUTPUT
{'full_text': u'\u25b6'}

stop
{'full_text': u'\u25fc'}

pause
{'full_text': u'\u275a\u275a'}
"""
# Any contributor to this module should add his/her name to the @author
# line, comma separated.

import os
import subprocess

try:
    import dbus
    dbus_available = True
except:
    dbus_available = False


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    debug = False
    format = '{icon}'
    pause_icon = u'❚❚'
    play_icon = u'▶'
    stop_icon = u'◼'
    supported_players = 'audacious,vlc'
    volume_tick = 1

    def __init__(self):
        self.status = 'stop'
        self.icon = self.play_icon

    def on_click(self, event):
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
            self.py3.log('running %s' % repr(*args))

        subprocess.check_output(*args, stderr=subprocess.STDOUT)

    def _play(self):
        self.status = 'play'
        self.icon = self.stop_icon
        player_name = self._detect_running_player()
        if player_name == 'audacious':
            self._run(['/usr/bin/audacious', '-p'])
        elif player_name == 'vlc':
            player = self._get_vlc()
            if player:
                player.Play()

    def _stop(self):
        self.status = 'stop'
        self.icon = self.play_icon
        player_name = self._detect_running_player()
        if player_name == 'audacious':
            self._run(['/usr/bin/audacious', '-s'])
        elif player_name == 'vlc':
            player = self._get_vlc()
            if player:
                player.Stop()

    def _pause(self):
        self.status = 'pause'
        self.icon = self.pause_icon
        player_name = self._detect_running_player()
        if player_name == 'audacious':
            self._run(['/usr/bin/audacious', '-u'])
        elif player_name == 'vlc':
            player = self._get_vlc()
            if player:
                player.Pause()

    def _change_volume(self, increase):
        """Change volume using amixer
        """
        sign = '+' if increase else '-'
        delta = "%d%%%s" % (self.volume_tick, sign)
        self._run(('/usr/bin/amixer', '-q', 'sset', 'Master', delta))

    def _detect_running_player(self):
        """Detect running player process, if any
        """
        supported_players = self.supported_players.split(',')
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
                    self.py3.log('found player: %s' % player_name)

                # those players need the dbus module
                if player_name in ('vlc') and not dbus_available:
                    self.py3.log('%s requires the dbus python module' % player_name)
                    return None

                return player_name

        return None

    def _get_vlc(self):
        mpris = 'org.mpris.MediaPlayer2'
        mpris_slash = '/' + mpris.replace('.', '/')
        bus = dbus.SessionBus()
        proxy = bus.get_object(mpris + '.vlc', mpris_slash)
        return dbus.Interface(proxy, dbus_interface=mpris + '.Player')

    def player_control(self):
        return dict(
            full_text=self.py3.safe_format(self.format, {'icon': self.icon}),
            cached_until=self.py3.time_in(self.cache_timeout),
        )


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
