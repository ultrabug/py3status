"""
Display song currently playing in Clementine.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 5)
    format: display format for this module (default '♫ {current}')

Format placeholders:
    {current} currently playing

Requires:
    clementine: a modern music player and library organizer
    qdbus: a communication-interface for qt-based applications
        (may be part of qt5-tools)

@author Francois LASSERRE <choiz@me.com>
@license GNU GPL https://www.gnu.org/licenses/gpl.html

SAMPLE OUTPUT
{'full_text': '♫ Music For Programming - Hivemind'}
"""

CMD = "qdbus org.mpris.MediaPlayer2.clementine /org/mpris/MediaPlayer2 org.freedesktop.DBus.Properties.Get org.mpris.MediaPlayer2.Player Metadata"
STRING_NOT_INSTALLED = "not installed"
INTERNET_RADIO = "Internet Radio"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 5
    format = "♫ {current}"

    def post_config_hook(self):
        if not self.py3.check_commands("clementine"):
            raise Exception(STRING_NOT_INSTALLED)

    def clementine(self):
        artist = lines = now_playing = title = ""
        internet_radio = False

        try:
            metadata = self.py3.command_output(CMD)
            lines = filter(None, metadata.splitlines())
        except self.py3.CommandError:
            return {
                "cached_until": self.py3.time_in(self.cache_timeout),
                "full_text": "",
            }

        for item in lines:
            if "artist" in item:
                artist = item[14:]
            if "title" in item:
                title = item[13:]

        if ".mp3" in title or ".wav" in title:
            title = title[:-4]
        if "http" in title:
            title = ""
            internet_radio = True

        if artist and title:
            now_playing = f"{artist} - {title}"
        elif artist:
            now_playing = artist
        elif title:
            now_playing = title
        elif internet_radio:
            now_playing = INTERNET_RADIO

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, {"current": now_playing}),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
