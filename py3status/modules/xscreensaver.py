# -*- coding: utf-8 -*-
"""
Indicator for Xscreensaver, can be toggled by left clicking.

This is a partial rewrite of dpms.py. Most credit
goes to the original author Andre Doser. This module shows the status
of Xscreensaver and activates or deactivates it upon left click.

This script is useful for people who let Xscreensaver manage dpms
settings. Xscreensaver has its own dpms variables separate from xset.
Dpms can be safely turned off in xset as long as xscreensaver is running.
Settings can be managed using "xscreensaver-demo".

Configuration parameters:
    format_off:    string to display when Xscreensaver is disabled
    format_on:     string to display when Xscreensaver is enabled
    cache_timeout: interval for checking whether Xscreensaver is running
                   (default 30s)

Example configuration in py3status.conf:

```
order += "xscreensaver"
xscreensaver {
    format_off = "xscreensaver off"
    format_on  = "xscreensaver on"
}
```

@author neutronst4r <c7420{at}gmx{dot}net>
"""
from os import setpgrp
from subprocess import call, Popen, DEVNULL
from time import time


class Py3status:
    """
    """
    # available configuration parameters
    format_off = "xscreensaver off"
    format_on = "xscreensaver on"
    color_on = None
    color_off = None
    cache_timeout = 30

    def xscreensaver(self, i3s_output_list, i3s_config):
        """
        Display a colorful state of xscreensaver.
        """
        self.run = call(["pidof", "xscreensaver"],
                        stdout=DEVNULL,
                        stderr=DEVNULL,
                        preexec_fn=setpgrp) == 0
        full_text = self.format_on if self.run else self.format_off
        if self.run:
            color = self.color_on or i3s_config['color_good']
        else:
            color = self.color_off or i3s_config['color_bad']
        return {'full_text': full_text,
                'color': color,
                'cached_until': time() + self.cache_timeout}

    def on_click(self, i3s_output_list, i3s_config, event):
        """
        Enable/Disable xscreensaver on left click.
        """
        if event['button'] == 1:
            if self.run:
                self.run = False
                Popen(["killall", "xscreensaver"],
                      stdout=DEVNULL,
                      stderr=DEVNULL,
                      preexec_fn=setpgrp)
            else:
                self.run = True
                Popen(
                    ["xscreensaver", "-no-splash", "-no-capture-stderr"],
                    stdout=DEVNULL,
                    stderr=DEVNULL,
                    preexec_fn=setpgrp)


if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {'color_bad': '#FF0000', 'color_good': '#00FF00', }
    while True:
        print(x.xscreensaver([], config))
        sleep(1)
