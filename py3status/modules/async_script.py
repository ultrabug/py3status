# -*- coding: utf-8 -*-
"""
Display output of a given script, updating the display when new lines
come in.

TODO:rewrite Display output of any executable script set by `script_path`.
Only the first two lines of output will be used. The first line is used
as the displayed text. If the output has two or more lines, the second
line is set as the text color (and should hence be a valid hex color
code such as #FF0000 for red).
The script should not have any parameters, but it could work.

Configuration parameters:
    color_on_even_lines: if true, skips every second line of output and
        uses its content as color (default False)
    format: see placeholders below (default '{output}')
    restart_on_exit: restarts the script when it exits (default: True)
    script_path: script you want to show output of (compulsory)
        (default None)
    strip_output: shall we strip leading and trailing spaces from output
        (default False)

Format placeholders:
    {output} output of script given by "script_path"

i3status.conf example:

```
external_script {
    format = "{output}"
    script_path = "/usr/bin/dmesg"
}
```

@author frimdo ztracenastopa@centrum.cz

SAMPLE OUTPUT
{'full_text': 'script output'}

example
{'full_text': '[193957.380605] wlp3s0: authenticated'}
"""

import re
from threading import Thread
STRING_ERROR = 'missing script_path'


class Py3status:
    """
    """
    # available configuration parameters
    color_on_even_lines = False  # TODO
    format = '{output}'
    restart_on_exit = True  # TODO
    script_path = None
    strip_output = False

    def post_config_hook(self):
        # class variables:
        self.command_thread = Thread()
        self.command_output = None

        if not self.script_path:
            raise Exception(STRING_ERROR)

    def external_script(self):
        response = {}
        response['cached_until'] = self.py3.time_in(self.py3.CACHE_FOREVER)

        if not self.command_thread.is_alive():
            self.command_thread = Thread(target=self._command_start)
            self.command_thread.daemon = True
            self.command_thread.start()
        #if re.search(r'^#[0-9a-fA-F]{6}$', output_color):
        #    response['color'] = output_color

        #if self.command_output is not None:
        #    output_text = output_lines[-1]
        #    if self.strip_output:
        #        output_text = output_text.strip()
        #else:
        #    output_text = ''

        response['full_text'] = self.py3.safe_format(
            self.format, {'output': self.command_output})
        return response

    def _command_start(self):
        # start application, update self.command_output
        # restart if self.restart_on_exit, save color if self.color_on_even_lines

        import shlex, subprocess
        command = subprocess.Popen(shlex.split(self.script_path), stdout=subprocess.PIPE)
        try:
          while True:
            output = command.stdout.readline().decode()
            self.py3.log(output)
            self.command_output = output[-1]
            self.py3.update()
        except Exception as e:
            self.py3.log(str(e))

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
