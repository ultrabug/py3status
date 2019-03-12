# -*- coding: utf-8 -*-
"""
Display output of a given script asynchronously.

Always displays the last line of output from a given script, set by
`script_path`. If a line contains only a color (/^#[0-F]{6}$/), it is used
as such (set force_nocolor to disable). The script may have parameters.

Configuration parameters:
    force_nocolor: if true, won't check if a line contains color
        (default False)
    format: see placeholders below (default '{output}')
    script_path: script you want to show output of (compulsory)
        (default None)
    strip_output: shall we strip leading and trailing spaces from output
        (default False)

Format placeholders:
    {output} output of script given by "script_path"

Examples:
```
async_script {
    format = "{output}"
    script_path = "ping 127.0.0.1"
}
```

@author frimdo ztracenastopa@centrum.cz, girst

SAMPLE OUTPUT
{'full_text': 'script output'}

example
{'full_text': '[193957.380605] wlp3s0: authenticated'}
"""

import re
import shlex
from subprocess import Popen, PIPE
from threading import Thread


class Py3status:
    """
    """

    # available configuration parameters
    force_nocolor = False
    format = "{output}"
    script_path = None
    strip_output = False

    def post_config_hook(self):
        # class variables:
        self.command_thread = Thread()
        self.command_output = None
        self.command_color = None
        self.command_error = None  # cannot throw self.py3.error from thread

        if not self.script_path:
            self.py3.error("script_path is mandatory")

    def async_script(self):
        response = {}
        response["cached_until"] = self.py3.CACHE_FOREVER

        if self.command_error is not None:
            self.py3.log(self.command_error, level=self.py3.LOG_ERROR)
            self.py3.error(self.command_error, timeout=self.py3.CACHE_FOREVER)
        if not self.command_thread.is_alive():
            self.command_thread = Thread(target=self._command_start)
            self.command_thread.daemon = True
            self.command_thread.start()

        if self.command_color is not None:
            response["color"] = self.command_color

        response["full_text"] = self.py3.safe_format(
            self.format, {"output": self.command_output}
        )
        return response

    def _command_start(self):
        try:
            command = Popen(shlex.split(self.script_path), stdout=PIPE)
            while True:
                if command.poll() is not None:  # script has exited/died; restart it
                    command = Popen(shlex.split(self.script_path), stdout=PIPE)

                output = command.stdout.readline().decode().strip()

                if re.search(r"^#[0-9a-fA-F]{6}$", output) and not self.force_nocolor:
                    self.command_color = output
                else:
                    if output != self.command_output:
                        self.command_output = output
                        self.py3.update()
        except Exception as e:
            self.command_error = str(e)
            self.py3.update()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status, config={"script_path": "ping 127.0.0.1"})
