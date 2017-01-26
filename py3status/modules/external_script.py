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
"""

import subprocess


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 15
    format = '{output}'
    script_path = None
    strip_output = False

    def external_script(self):
        if self.script_path:
            return_value = subprocess.check_output(self.script_path,
                                                   shell=True,
                                                   universal_newlines=True)

            # this is a convenience cleanup code to avoid breaking i3bar which
            # does not support multi lines output
            if len(return_value.split('\n')) > 2:
                return_value = return_value.split('\n')[0]
                self.py3.notify_user(
                    'Script {} output contains new lines.'.format(
                        self.script_path) +
                    ' Only the first one is being displayed to avoid breaking your i3bar',
                    rate_limit=3600)
            elif return_value[-1] == '\n':
                return_value = return_value.rstrip('\n')

            if self.strip_output:
                return_value = return_value.strip()

            response = {
                'cached_until': self.py3.time_in(self.cache_timeout),
                'full_text': self.py3.safe_format(self.format,
                                                  {'output': return_value})
            }
        else:
            response = {
                'cached_until': self.py3.time_in(self.cache_timeout),
                'full_text': ''
            }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
