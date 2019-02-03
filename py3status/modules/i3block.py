# -*- coding: utf-8 -*-
"""
Support i3blocks blocklets in py3status.

i3blocks, https://github.com/vivien/i3blocks, is a project to allow simple
scripts to provide output to the i3bar. This module allows these blocklets to
run under py3status. The configuration of the blocklets is similar to how they
are configured in i3blocks.

Configuration parameters:
    cache_timeout: How often the blocklet should be called (in seconds).
        This is similar to cache_timeout used by standard modules. However it
        can also take the following values; `once` the blocklet will be called
        once, `repeat` the blocklet will be called constantly, or `persist`
        where the command will be expected to keep providing new data. If this
        is not set or is `None` then the blocklet will not be called unless
        clicked on. To simplify i3block compatability, this configuration
        parameter can also be provided as `interval`.
        (default None)
    command: Path to blocklet or command (default None)
    format: What to display on the bar (default '{output}')
    instance: Will be provided to the blocklet as $BLOCK_INSTANCE (default '')
    label: Will be prepended to the blocklets output (default '')
    name: Name of the blocklet - passed as $BLOCK_NAME (default '')

Format placeholders:
    {output} The output of the blocklet

Notes:
    i3blocks and i3blocklets are subject to their respective licenses.

    This support is experimental and done for convenience to users so they
    can benefit from both worlds, issues or PRs regarding i3blocks related
    blocklets should not be raised.

    Some blocklets may return pango markup eg `<span ...` if so set
    `markup = pango` in the config for that module.

    `format` configuration parameter is used as is standard in py3status, not
    as in i3blocks configuration. Currently blocklets must provide responses
    in the standard i3blocks manner of one line per value (not as json).

Examples:
```
# i3blocks config
[time]
command=date '+%D %T'
interval=5

[wifi]
instance=wls1
label='wifi:'
command=~/i3blocks/wifi.sh
interval=5

# py3status config
order += 'i3block time'
i3block time {
    command = "date '+%D %T'"
    interval = 5
}

# different py3status config
order += 'i3block wifi'
i3block wifi {
    instance = wls1
    label = 'wifi:'
    command = '~/i3blocks/wifi.sh'
    interval = 5
}
```

@author tobes

SAMPLE OUTPUT
{'full_text': 'wifi:100%', 'color': '#00FF00'}

bandwidth
{'full_text': 'bandwidth: 334 / 113 kB/s'}
"""

import fcntl
import os
import re

from os import environ
from subprocess import Popen, PIPE
from threading import Thread

RESPONSE_FIELDS = [
    "full_text",
    "short_text",
    "color",
    "min_width",
    "align",
    "urgent",
    "separator",
    "separator_block_width",
    "markup",
]


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = None
    command = None
    format = "{output}"
    instance = ""
    label = ""
    name = ""

    def post_config_hook(self):
        # set interval.  If cache_timeout is used it takes precedence
        if self.cache_timeout:
            self.interval = self.cache_timeout
        self.interval = getattr(self, "interval", None)
        # implement i3block interval rules
        self.first_run = True
        self.cache_forever = False
        if self.interval in ["once", "persist"] or not self.interval:
            self.cache_forever = True
        if self.interval == "repeat":
            self.cache_timeout = 1
        else:
            self.cache_timeout = self.interval
        # no button has been pressed
        self.x = ""
        self.y = ""
        self.button = ""

        # set our environ
        self.env = {
            "BLOCK_INTERVAL": str(self.interval),
            "BLOCK_INSTANCE": self.instance,
            "BLOCK_NAME": self.name,
        }
        self.env.update(environ)

        # allow chained commands
        # this allows support for pseudo click support
        # echo "Click me"; [[ -z "${BLOCK_BUTTON}" ]] || echo "clicked"
        # pattern finds unquoted ; to split command on
        pattern = re.compile(r"""((?:[^;"']|"[^"]*"|'[^']*')+)""")
        self.commands = pattern.split(self.command or "")[1::2]
        self.errors = []

        if self.interval == "persist":
            self.persistent_output = ""
            self.thread = Thread(target=self._persist)
            self.thread.daemon = True
            self.thread.start()
        else:
            self.thread = None

    def _persist(self):
        """
        Run the command inside a thread so that we can catch output for each
        line as it comes in and display it.
        """
        # run the block/command
        for command in self.commands:
            try:
                process = Popen(
                    [command],
                    stdout=PIPE,
                    stderr=PIPE,
                    universal_newlines=True,
                    env=self.env,
                    shell=True,
                )
            except Exception as e:
                retcode = process.poll()
                msg = "Command '{cmd}' {error} retcode {retcode}"
                self.py3.log(msg.format(cmd=command, error=e, retcode=retcode))

            # persistent blocklet output can be of two forms.  Either each row
            # of the output is on a new line this is much easier to deal with)
            # or else the output can be continuous and just flushed when ready.
            # The second form is more tricky, if we find newlines then we
            # switch to easy parsing of the output.

            # When we have output we store in self.persistent_output and then
            # trigger the module to update.

            fd = process.stdout.fileno()
            fl = fcntl.fcntl(fd, fcntl.F_GETFL)
            has_newlines = False
            while True:
                line = process.stdout.read(1)
                # switch to a non-blocking read as we do not know the output
                # length
                fcntl.fcntl(fd, fcntl.F_SETFL, fl | os.O_NONBLOCK)
                line += process.stdout.read(1024)
                # switch back to blocking so we can wait for the next output
                fcntl.fcntl(fd, fcntl.F_SETFL, fl)
                if process.poll():
                    break
                if self.py3.is_python_2():
                    line = line.decode("utf-8")
                self.persistent_output = line
                self.py3.update()
                if line[-1] == "\n":
                    has_newlines = True
                    break
                if line == "":
                    break
            if has_newlines:
                msg = "Switch to newline persist method {cmd}"
                self.py3.log(msg.format(cmd=command))
                # just read the output in a sane manner
                for line in iter(process.stdout.readline, b""):
                    if process.poll():
                        break
                    if self.py3.is_python_2():
                        line = line.decode("utf-8")
                    self.persistent_output = line
                    self.py3.update()
        self.py3.log("command exited {cmd}".format(cmd=command))
        self.persistent_output = "Error\nError\n{}".format(
            self.py3.COLOR_ERROR or self.py3.COLOR_BAD
        )
        self.py3.update()

    def _run_command(self, env):
        """
        Run command(s) and return output and urgency.
        """
        output = ""
        urgent = False
        # run the block/command
        for command in self.commands:
            try:
                process = Popen(
                    command,
                    stdout=PIPE,
                    stderr=PIPE,
                    universal_newlines=True,
                    env=env,
                    shell=True,
                )
            except Exception as e:
                msg = "Command '{cmd}' {error}"
                raise Exception(msg.format(cmd=command, error=e))

            _output, _error = process.communicate()
            if self.py3.is_python_2():
                _output = _output.decode("utf-8")
                _error = _error.decode("utf-8")
            retcode = process.poll()

            # return code of 33 means urgent
            _urgent = retcode == 33

            if retcode and retcode != 33 or _error:
                msg = "i3block command '{cmd}' had an error see log for details."
                msg = msg.format(cmd=command)
                self.py3.notify_user(msg, rate_limit=None)
                msg = "i3block command '{cmd}' had error {error} returned {retcode}"
                msg = msg.format(cmd=command, error=_error, retcode=retcode)
                if hash(msg) not in self.errors:
                    self.py3.log(msg, level=self.py3.LOG_ERROR)
                    self.errors.append(hash(msg))
                _output = "Error\nError\n{}".format(
                    self.py3.COLOR_ERROR or self.py3.COLOR_BAD
                )
            # we have got output so update the received output
            # this provides support for i3blocks pseudo click support
            if _output:
                output = _output
                urgent = _urgent
        return output, urgent

    def i3block(self):
        # no command
        if not self.command:
            return {"cached_until": self.py3.CACHE_FOREVER, "full_text": ""}

        # If an interval is not given then we do not want to create output
        # initially as we should only be reacting to clicks.
        # We just use provided fields
        if not self.interval and self.first_run:
            self.first_run = False
            block_response = {"full_text": ""}
            for field in RESPONSE_FIELDS:
                if hasattr(self, field):
                    block_response[field] = getattr(self, field)
            i3block = self.py3.composite_create(block_response)
            full_text = self.py3.safe_format(self.format, {"output": i3block})
            return {"cached_until": self.py3.CACHE_FOREVER, "full_text": full_text}

        if self.interval == "persist":
            output = self.persistent_output
            urgent = False
        else:
            # set any buttons if they have been pressed
            env = {"BLOCK_BUTTON": self.button, "BLOCK_X": self.x, "BLOCK_Y": self.y}
            env.update(self.env)

            # reset button click info
            self.x = ""
            self.y = ""
            self.button = ""

            output, urgent = self._run_command(env)

        output = output.splitlines()

        if self.cache_forever:
            cached_until = self.py3.CACHE_FOREVER
        else:
            # we use sync_to to ensure that any time related blocklets update
            # at nice times eg on the second, minute etc
            cached_until = self.py3.time_in(sync_to=self.cache_timeout)

        block_response = {"full_text": ""}  # in  case we have no response

        # i3blocks output fields one per line in a set order
        response_lines = len(output)
        for index, field in enumerate(RESPONSE_FIELDS):
            if index < response_lines and output[index]:
                block_response[field] = output[index]
            elif hasattr(self, field):
                block_response[field] = getattr(self, field)

        # blocklet label gets prepended
        if self.label:
            block_response["full_text"] = u"{}{}".format(
                self.label, block_response["full_text"]
            )
            if "short_text" in block_response:
                block_response["short_text"] = u"{}{}".format(
                    self.label, block_response["short_text"]
                )

        # we can now use the blocklet output in our py3status format
        i3block = self.py3.composite_create(block_response)
        full_text = self.py3.safe_format(self.format, {"output": i3block})

        # if urgent then set this for the full output
        if urgent:
            if self.py3.is_composite(full_text):
                for item in full_text:
                    item["urgent"] = True

        # finally output our response
        response = {"cached_until": cached_until, "full_text": full_text}

        if urgent:
            response["urgent"] = True

        return response

    def on_click(self, event):
        # Store button info so we can pass to the blocklet script
        # they are expected to be strings
        self.x = str(event["x"])
        self.y = str(event["y"])
        self.button = str(event["button"])


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    config = {"command": "date '+%D %T'", "interval": 1}
    module_test(Py3status, config)
