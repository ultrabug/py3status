# -*- coding: utf-8 -*-
"""
Display your dropbox status.

Configuration parameters:
    - format : Prefix text for the dropbox status

Requires:
    - the 'dropbox-cli' command

@author Tjaart van der Walt (github:tjaartvdwalt)
@license BSD 2-Clause License -- http://opensource.org/licenses/BSD-2-Clause
"""
import subprocess


class Py3status:
    format = "Dropbox: {}"

    def dropbox(self, i3status_output_json, i3status_config):
        response = {}

        lines = subprocess.check_output(["dropbox-cli", "status"]).decode(
            "utf-8").split("\n")
        status = lines[0]
        full_text = self.format.format(str(status))
        response['full_text'] = full_text

        if (status == "Dropbox isn't running!"):
            response.update({'color': i3status_config['color_bad']})
        elif (status == "Up to date"):
            response.update({'color': i3status_config['color_good']})
        else:
            response.update({'color': i3status_config['color_degraded']})
        return response

if __name__ == "__main__":
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.dropbox([], config))
        sleep(1)
