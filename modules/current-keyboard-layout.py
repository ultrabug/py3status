import subprocess
import time

"""
Module for showing current keyboard layout.
DEPENDS ON xkblayout-state!

@author shadowprince
@version 1.0
@license Eclipse Public License
"""

CACHE_TIME = 0.2 # maximum time to update indicator

# colors of layouts
# key must be compatible with xkblayout-state print %s!
LANG_COLORS = {
        "ru": "#F75252", 
        "us": "#729FCF", 
        "ua": "#FCE94F",
        }

class Py3status:
    def currentLayout(self, i3status_output_json, i3status_config):
        response = {'full_text': '', 'name': 'current-layout', 'cached_until': time.time()+CACHE_TIME}
        lang = subprocess.check_output(["xkblayout-state", "print", "%s"]).decode('utf-8')

        return (0, {
            "full_text": lang,
            "name": "current-layout",
            "cached_until": time.time() + CACHE_TIME,
            "color": LANG_COLORS.get(lang, "#ffffff"),
            })
