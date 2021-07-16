# -*- coding: utf-8 -*-
"""
Display sway inhibit idle status.

This Module shows an indicator, if an idle is inhibited by an inhibitor.
For more information about inhibit idle see `man 5 sway`

Configuration parameters:
    format: Display format (default 'Inhibit Idle: [\?if=inhibit_idle=True True]|False')

Format placeholders:
    {inhibit_idle} Returns 'True' if idle is inhibited, 'False' else.

Example:

```
sway_idle {
    format = "[\?if=inhibit_idle=True Idle Inhibited]"
}
```

@author Valentin Weber <valentin+py3status@wv2.ch>
@license BSD
"""

class Py3status:

    format = 'Inhibit Idle: [\?if=inhibit_idle=True True]|False'

    def sway_idle(self):
        sway_tree = self.py3.command_output(self.py3.get_wm_msg() + ' -t get_tree')
        inhibit_idle = str(sway_tree.find('inhibit_idle": true') > 0)
        return {
            'full_text': self.py3.safe_format(self.format,param_dict={'inhibit_idle': inhibit_idle}),
            'cached_until': self.py3.time_in(seconds=1)
        }

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
