# -*- coding: utf-8 -*-
"""
Display output of given script.

Display output of any executable script set by `script_path`.
Pay attention. The output must be one liner, or will break your i3status !
The script should not have any parameters, but it could work.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds
    color: color of printed text
    format: see placeholders below
    script_path: script you want to show output of (compulsory)

Format of status string placeholders:
    {output} output of script given by "script_path"

i3status.conf example:

```
external_script {
    color = "#00FF00"
    format = "my name is {output}"
    script_path = "/usr/bin/whoami"
}
```

@author frimdo ztracenastopa@centrum.cz
"""

import subprocess
from time import time


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 15
    color = None
    format = '{output}'
    script_path = None

    def external_script(self, i3s_output_list, i3s_config):
        if self.script_path:
            return_value = subprocess.check_output(self.script_path,
                                                   shell=True,
                                                   universal_newlines=True)
            response = {
                'cached_until': time() + self.cache_timeout,
                'color': self.color,
                'full_text': self.format.format(output=return_value.rstrip())
            }
        else:
            response = {
                'cached_until': time() + self.cache_timeout,
                'full_text': ''
            }
        return response


if __name__ == "__main__":
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.external_script([], config))
        sleep(1)
