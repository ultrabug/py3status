# -*- coding: utf-8 -*-

"""
Display the cmus playing status and current track.

Cmus can execute a shell script at every status change by setting
`:set status_display_program=path/to/cmus-status-script` in cmus.
This module assumes that the cmus `status_display_program` writes a single line
to a text file with the format '[playing/paused/stopped] track info'.
For example, '[playing] artist - track'. The module swaps in user-configurable
status icons and colors the output according to playback status.

Cmus has an example status_display_program in /usr/share/doc/cmus/examples/.
This script can be used as is after one small change: switch the append to
overwrite (use > instead of >>). You can also customize which information to
display, such as artist, album, track, duration, etc.


Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 2)
    indicator_pause: symbol for paused indicator (default '||')
    indicator_play: symbol for playing indicator (default '>')
    indicator_stop: symbol for stopped indicator (default '[stopped]')
    status_file: output file of status_display_program
        (default '~/.config/cmus/cmus-status.txt')

Example:

```
cmus {
    cache_timeout = 3
    indicator_play = ""
    indicator_pause = ""
    indicator_stop = ""
}
```

@author Toban Wiebe <tobanw@gmail.com>
@license BSD
"""

# import your useful libs here
from time import time
from os.path import expanduser


class Py3status:
    # available configuration parameters
    cache_timeout = 2
    indicator_play = '>'
    indicator_pause = '||'
    indicator_stop = '[stopped]'
    status_file = '~/.config/cmus/cmus-status.txt'

    def __init__(self):
        """
        This is the class constructor which will be executed once.
        """
        self.text = ''

    def cmus_status(self, i3s_output_list, i3s_config):
        """
        Prettify the cmus status with indicator icons and colors.
        """

        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': self.text,
            }

        with open(expanduser(self.status_file), 'r') as status_obj:
            # read in file as string,
            # remove trailing newline character,
            # split into list of two strings: indicator, and track info
            status = status_obj.read().strip('\n').split(' ', 1)

            play_state = status[0]

            # configure output based on playing/paused/stopped
            if play_state == '[stopped]':
                response['full_text'] = self.indicator_stop
                # response['color'] = i3s_config['color_bad']
            elif play_state == '[playing]':
                response['full_text'] = '{} {}'.format(self.indicator_play,
                                                       status[1])
                response['color'] = i3s_config['color_good']
            elif play_state == '[paused]':
                response['full_text'] = '{} {}'.format(self.indicator_pause,
                                                       status[1])
                response['color'] = i3s_config['color_degraded']
            else:
                response['full_text'] = 'ERROR'

        return response


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    This SHOULD work before contributing your module please.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.cmus_status([], config))
        sleep(1)
