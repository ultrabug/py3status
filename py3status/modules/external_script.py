# -*- coding: utf-8 -*-
"""
Display output of a given script.

Display output of any executable script set by `script_path`.
Pay attention. The output must be one liner, or will break your i3status !
The script should not have any parameters, but it could work.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds
        (default 15)
    format: see placeholders below (default '{output}')
    script_path: script you want to show output of (compulsory)
        (default None)
    strip_output: shall we strip leading and trailing spaces from output
        (default False)

Format placeholders:
    {output} output of script given by "script_path"

i3status.conf example:

```
external_script {
    format = "my name is {output}"
    script_path = "/usr/bin/whoami"
}
```

@author frimdo ztracenastopa@centrum.cz

SAMPLE OUTPUT
{'full_text': 'script output'}

example
{'full_text': 'It is now: Wed Feb 22 22:24:13'}
"""

STRING_UNAVAILABLE = "external_script: N/A"
STRING_ERROR = "external_script: error"


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 15
    format = '{output}'
    script_path = None
    strip_output = False

    def external_script(self):
        if not self.script_path:
            return {
                'cached_until': self.py3.CACHE_FOREVER,
                'color': self.py3.COLOR_BAD,
                'full_text': STRING_UNAVAILABLE
            }
        try:
            output = self.py3.command_output(self.script_path, shell=True)
            output = output.splitlines()[0]
        except:
            return {
                'cached_until': self.py3.time_in(self.cache_timeout),
                'color': self.py3.COLOR_BAD,
                'full_text': STRING_ERROR
            }

        if self.strip_output:
            output = output.strip()

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, {'output': output})
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
