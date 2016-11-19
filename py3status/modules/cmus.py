# -*- coding: utf-8 -*-
"""
Display information about the current song in cmus.

Toggle play/pause by click.

Configuration parameters:
    format: see placeholders below
        (default '{state} [{artist} - ][{title}]')
    format_none: define output if no cmus is running
        (default 'no player')
    state_pause: text for placeholder {state} when song is paused (default '▮')
    state_play: text for placeholder {state} when song is playing (default '▶')
    state_stop: text for placeholder {state} when song is stopped (default '◾')
    state_unknown: text for placeholder {state} when song is in unknown status (default '?')

Format of status string placeholders:
    {album} album name
    {artist} artiste name
    {state} playback status of the player
    {title} name of the song

i3status.conf example:

```
cmus {
    format = "{state} [[{artist} - {title}]|[{title}]]"
    format_none = "no player"
}
```

@author protosphere, raspbeguy
"""

import subprocess


class Py3status:
    format = '{state} [{artist} - ][{title}]'
    format_none = "no player"
    state_pause = u'▮'
    state_play = u'▶'
    state_stop = u'◾'
    state_unknown = u'?'

    def _get_cmus_info(self):
        cmus_remote_pipe = subprocess.Popen(["cmus-remote", "-Q"],
                                            stdout=subprocess.PIPE,
                                            stderr=subprocess.PIPE)
        cmus_info_text = cmus_remote_pipe.communicate()[0].decode()

        if cmus_info_text == "":
            return {}

        cmus_info = {
            "tags": {}
        }

        for line in cmus_info_text.splitlines():
            entry = line.split(None, 2)
            if entry[0] == "tag" and len(entry) > 2:
                cmus_info["tags"][entry[1]] = entry[2]
            elif len(entry) > 1:
                cmus_info[entry[0]] = entry[1]

        return cmus_info

    def _get_text(self, cmus_info):
        if "status" in cmus_info:
            if cmus_info["status"] == "playing":
                color = self.py3.COLOR_PLAYING or self.py3.COLOR_GOOD
                state_symbol = self.state_play
            elif cmus_info["status"] == "paused":
                color = self.py3.COLOR_PAUSED or self.py3.COLOR_DEGRADED
                state_symbol = self.state_pause
            elif cmus_info["status"] == "stopped":
                color = self.py3.COLOR_STOPPED or self.py3.COLOR_BAD
                state_symbol = self.state_stop
            else:
                color = self.py3.COLOR_BAD
                state_symbol = self.state_unknown

        placeholders = {
            'state': state_symbol,
            'album': cmus_info["tags"]["album"] if "album" in cmus_info["tags"] else "",
            'artist': cmus_info["tags"]["artist"] if "artist" in cmus_info["tags"] else "",
            'title': cmus_info["tags"]["title"] if "title" in cmus_info["tags"] else "",
        }

        return (placeholders, color)

    def cmus(self, i3s_output_list, i3s_config):
        cmus_info = self._get_cmus_info()
        (text, color) = self._get_text(cmus_info)
        full_text = self.py3.safe_format(self.format, text)
        response = {
            'color': color,
            'full_text': full_text,
        }

        return response

    def on_click(self, event):
        button = event['button']
        if button == 1:
            subprocess.call(["cmus-remote", "--pause"])


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
