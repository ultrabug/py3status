r"""
Display sway inhibit idle status.

This Module shows an indicator, if an idle is inhibited by an inhibitor.
For more information about inhibit idle see `man 5 sway`

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds (default 1)
    format: Display format (default 'Inhibit Idle: {inhibit_idle}')

Format placeholders:
    {inhibit_idle} Returns 'True' if idle is inhibited, 'False' else.

Example:

```
sway_idle {
    format = "Inhibit Idle: [\?if=inhibit_idle=True True]|False"
}
```

@author Valentin Weber <valentin+py3status@wv2.ch>
@license BSD

SAMPLE OUTPUT
{full_text': 'Inhibit Idle: True'}
"""


class Py3status:
    # available configuration parameters
    cache_timeout = 1
    format = "Inhibit Idle: {inhibit_idle}"

    def sway_idle(self):
        sway_tree = self.py3.command_output(self.py3.get_wm_msg() + " -t get_tree")
        inhibit_idle = '"inhibit_idle": true' in sway_tree
        return {
            "full_text": self.py3.safe_format(
                self.format, param_dict={"inhibit_idle": inhibit_idle}
            ),
            "cached_until": self.py3.time_in(self.cache_timeout),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """

    from py3status.module_test import module_test

    module_test(Py3status)
