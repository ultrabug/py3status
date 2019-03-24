# -*- coding: utf-8 -*-
"""
Group modules and switch between them.

Groups can be configured in your config. The active one of these groups is
shown in the i3bar.  The active group can be changed by a user click.  If the
click is not used by the group module then it will be passed down to the
displayed module.

Modules can be i3status core modules or py3status modules.  The active group
can be cycled through automatically.

The group can handle clicks by reacting to any that are made on it or its
content or it can use a button and only respond to clicks on that.
The way it does this is selected via the `click_mode` option.

Configuration parameters:
    align: Text alignment when fixed_width is set
        can be 'left', 'center' or 'right' (default 'center')
    button_next: Button that when clicked will switch to display next module.
        Setting to `0` will disable this action. (default 5)
    button_prev: Button that when clicked will switch to display previous
        module.  Setting to `0` will disable this action. (default 4)
    button_toggle: Button that when clicked toggles the group content being
        displayed between open and closed.
        This action is ignored if `{button}` is not in the format.
        Setting to `0` will disable this action (default 1)
    click_mode: This defines how clicks are handled by the group.
        If set to `all` then the group will respond to all click events.  This
        may cause issues with contained modules that use the same clicks that
        the group captures.  If set to `button` then only clicks that are
        directly on the `{button}` are acted on.  The group
        will need `{button}` in its format.
        (default 'all')
    cycle: Time in seconds till changing to next module to display.
        Setting to `0` will disable cycling. (default 0)
    fixed_width: Reduce the size changes when switching to new group
        (default False)
    format: display format for this module, see Examples below (default None)
    format_button_closed: Format for the button when group open
        (default  '+')
    format_button_open: Format for the button when group closed
        (default '-')
    format_closed: Format for module output when closed.
        (default "{button}")
    open: Is the group open and displaying its content. Has no effect if
        `{button}` not in format (default True)

Format placeholders:
    {button} The button to open/close or change the displayed group
    {output} Output of current active module

Examples:
```
# default formats
group {
    format = '{output}'           # if click_mode is 'all'
    format = '{output} {button}'  # if click_mode is 'button'
}

# Create a disks group that will show space on '/' and '/home'
# Change between disk modules every 30 seconds
order += "group disks"
group disks {
    cycle = 30
    format = "Disks: {output} {button}"
    click_mode = "button"

    disk "/" {
        format = "/ %avail"
    }
    disk "/home" {
        format = "/home %avail"
    }
}
```

@author tobes

SAMPLE OUTPUT
{'full_text': 'module 1'}

cycle
{'full_text': 'module 2'}

cycle_again
{'full_text': 'module 3'}
"""

from time import time

# maximum wait for initial content at startup
MAX_NO_CONTENT_WAIT = 5
STRING_ERROR = "missing modules"


class Py3status:
    """
    """

    # available configuration parameters
    align = "center"
    button_next = 5
    button_prev = 4
    button_toggle = 1
    click_mode = "all"
    cycle = 0
    fixed_width = False
    format = None
    format_button_closed = u"+"
    format_button_open = u"-"
    format_closed = u"{button}"
    open = True

    class Meta:
        container = True

    def post_config_hook(self):
        if not self.items:
            raise Exception(STRING_ERROR)

        self.active = 0
        self.cycle_time = time() + self.cycle
        self.cycle_timeout = self.cycle
        self.last_active = 0
        self.urgent = False
        self.urgent_history = {}

        # set default format etc based on click_mode
        if self.format is None:
            if self.click_mode == "button":
                self.format = u"{output} {button}"
            else:
                self.format = u"{output}"
        # if no button then force open
        if not self.py3.format_contains(self.format, "button"):
            self.open = True
        self.py3.register_function("content_function", self._content_function)
        self.py3.register_function("urgent_function", self._urgent_function)

    def _content_function(self):
        """
        This returns a set containing the actively shown module.
        This is so we only get update events triggered for these modules.
        """
        # ensure that active is valid
        self.active = self.active % len(self.items)

        return set([self.items[self.active]])

    def _urgent_function(self, module_list):
        """
        A contained module has become urgent.
        We want to display it to the user.
        """
        for module in module_list:
            if module in self.items:
                self.active = self.items.index(module)
                self.urgent = True

    def _get_output(self):
        if not self.fixed_width:
            return self.py3.get_output(self.items[self.active])
        # fixed width we need to find the width of all outputs
        # and then pad with spaces to make correct width.
        current = []
        widths = []
        for i in range(len(self.items)):
            output = self.py3.get_output(self.items[i])
            if not output:
                widths.append(0)
            else:
                widths.append(sum([len(x["full_text"]) for x in output]))
            if i == self.active:
                current = output
                current_width = widths[-1]
        if widths and current:
            width = max(widths)
            padding = " " * (width - current_width)
            if self.align == "right":
                current[0]["full_text"] = padding + current[0]["full_text"]
            elif self.align == "center":
                cut = len(padding) // 2
                current[0]["full_text"] = padding[:cut] + current[0]["full_text"]
                current[-1]["full_text"] += padding[cut:]
            else:
                current[-1]["full_text"] += padding
        return current

    def _change_active(self, delta):
        # we want to ignore any empty outputs
        # to prevent endless cycling we limit ourselves to only going through
        # the outputs once.
        self.active = (self.active + delta) % len(self.items)
        if not self._get_output() and self.last_active != self.active:
            self._change_active(delta)
        self.last_active = self.active

    def group(self):
        update_time = None
        self.cycle = 0

        # get an output. again if empty (twice).
        for x in range(3):
            output = self._get_output()
            if output:
                break
            self._change_active(1)
        else:
            update_time = MAX_NO_CONTENT_WAIT

        # check for urgents
        urgent = output and output[0].get("urgent")
        self.urgent_history[self.active] = urgent
        mod_urgent = any(self.urgent_history.values())

        # keep cycling if no urgent
        if not urgent:
            self.cycle = self.cycle_timeout
            if time() >= self.cycle_time:
                self._change_active(1)
                self.cycle_time = time() + self.cycle

        # time
        update_time = update_time or self.cycle or None
        if update_time is not None:
            cached_until = self.py3.time_in(self.cycle)
        else:
            cached_until = self.py3.CACHE_FOREVER

        if self.open:
            format_control = self.format_button_open
            current_format = self.format
            urgent = False
        else:
            format_control = self.format_button_closed
            current_format = self.format_closed
            urgent = mod_urgent or self.urgent

        button = {"full_text": format_control, "index": "button"}
        response = {
            "cached_until": cached_until,
            "full_text": self.py3.safe_format(
                current_format,
                {
                    "output": self.py3.composite_create(output),
                    "button": self.py3.composite_create(button),
                },
            ),
        }
        if urgent:
            response["urgent"] = urgent
            self.urgent = False
        return response

    def on_click(self, event):
        """
        Switch the displayed module or pass the event on to the active module
        """
        button = event["button"]
        index = event["index"]

        # if click_mode is button, prevent the contents from changing when
        # if the events are not registered on the button index. this allow
        # the users to interact with the modules via scrolling or clicking
        # without group getting in the way of the contents.
        if self.click_mode == "button":
            if not self.py3.is_my_event(event) or index != "button":
                return

        self.cycle = self.cycle_timeout
        self.cycle_time = time() + self.cycle

        if button == self.button_next:
            if self.open:
                self._change_active(+1)
        elif button == self.button_prev:
            if self.open:
                self._change_active(-1)
        elif button == self.button_toggle:
            if index == "button":
                self.open = not self.open


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
