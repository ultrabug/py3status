# -*- coding: utf-8 -*-
"""
Basic actionable trigger

Will display the format text indefinitely. Will run executable script set by
`script_path`.

Configuration parameters:
    color: color to use for the button.
        (default '#FFFFFF')
    format: anything text you want
        (default '■')
    script_path: script you want to run or command you want to invoke.
    (compulsory)
        (default None)

Format placeholders:
    None

Examples:
```
button {
    format = ""
    script_path = "cmus-remote --prev"
    color = "#00FF00"
}
```

@author gunslingerfry gunslingerfry@gmail.com

SAMPLE OUTPUT
{'full_text': "" }

"""
STRING_ERROR = "missing script_path"


class Py3status:
    # available configuration parameters
    color = "#FFFFFF"
    format = "■"
    script_path = None

    def post_config_hook(self):
        if not self.script_path:
            raise Exception(STRING_ERROR)

    def button(self):
        return {
            "full_text": self.format,
            "cached_until": self.py3.CACHE_FOREVER,
            "color": self.color,
        }

    def on_click(self, event):
        try:
            self.py3.command_run(self.script_path)

        except self.py3.CommandError as e:
            # something went wrong show error to user
            output = e.output or e.error
            self.py3.error(output)
