# -*- coding: utf-8 -*-
"""
Group two or more modules as a single one.

This can be useful for example when adding modules to a group and you wish two
modules to be shown at the same time.

Example config:

```
# Define a group which shows volume and battery info
# or the current time.
# The frame, volume_status and battery_level modules are named
# to prevent them clashing with any other defined modules of the same type.
group {
    frame volume_battery {
        volume_status frame_volume {}
        battery_level frame_battery {}
    }

    time {}
}
```

@author tobes
"""


class Py3status:

    class Meta:
        container = True

    def frame(self):

        if not self.items:
            return {'full_text': '', 'cached_until': self.py3.CACHE_FOREVER}

        # get the child modules output.
        output = []
        for item in self.items:
            out = self.py3.get_output(item)
            if out and 'separator' not in out[-1]:
                out[-1]['separator'] = True
            output += out

        return {
            'cached_until': self.py3.CACHE_FOREVER,
            'composite': output,
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
