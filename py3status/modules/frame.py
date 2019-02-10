# -*- coding: utf-8 -*-
"""
Group modules and treat them as a single one.

This can be useful for example when adding modules to a group and you wish two
modules to be shown at the same time.

By adding the `{button}` placeholder in the format you can enable a toggle
button to hide or show the content.

Configuration parameters:
    button_toggle: Button used to toggle if one in format.
        Setting to None disables (default 1)
    format: Display format to use (default '{output}')
    format_button_closed: Format for the button when frame open (default '+')
    format_button_open: Format for the button when frame closed (default '-')
    format_separator: Specify separator between contents.
        If this is None then the default i3bar separator will be used
        (default None)
    open: If button then the frame can be set to be open or close
        (default True)

Format placeholders:
    {button} If used a button will be used that can be clicked to hide/show
        the contents of the frame.
    {output} The output of the modules in the frame

Examples:
```
# A frame showing times in different cities.
# We also have a button to hide/show the content
frame time {
    format = '{output}{button}'
    format_separator = ' '  # have space instead of usual i3bar separator

    tztime la {
        format = "LA %H:%M"
        timezone = "America/Los_Angeles"
    }
    tztime ny {
        format = "NY %H:%M"
        timezone = "America/New_York"
    }
    tztime du {
        format = "DU %H:%M"
        timezone = "Asia/Dubai"
    }
}

# Define a group which shows volume and battery info or the current time.
# The frame, volume_status and battery_level modules are named to prevent
# them clashing with any other defined modules of the same type.
group {
    frame {
        volume_status {}
        battery_level {}
    }
    time {}
}
```

@author tobes

SAMPLE OUTPUT
[
    {'full_text': u'module 1', 'separator': True},
    {'full_text': u'module 2', 'separator': True},
    {'full_text': u'module 3', 'separator': True},
    {'full_text': u'-', 'separator': True}
]

closed
{'full_text': u'+'}

"""


class Py3status:
    """
    """

    # available configuration parameters
    button_toggle = 1
    format = "{output}"
    format_button_closed = u"+"
    format_button_open = u"-"
    format_separator = None
    open = True

    class Meta:
        container = True

    def post_config_hook(self):
        self.urgent = False
        if not self.py3.format_contains(self.format, "button"):
            self.open = True
        self.py3.register_function("urgent_function", self._urgent_function)

    def _urgent_function(self, module_list):
        self.urgent = True

    def frame(self):

        if not self.items:
            return {"full_text": "", "cached_until": self.py3.CACHE_FOREVER}

        # get the child modules output.
        output = []
        if self.open:
            for item in self.items:
                out = self.py3.get_output(item)[:]
                if self.format_separator is None:
                    if out and "separator" not in out[-1]:
                        # we copy the item as we do not want to change the
                        # original.
                        last_item = out[-1].copy()
                        last_item["separator"] = True
                        out[-1] = last_item
                else:
                    if self.format_separator:
                        out += [{"full_text": self.format_separator}]
                output += out
            urgent = False

            # Remove last separator
            if self.format_separator:
                output = output[:-1]
        else:
            urgent = self.urgent

        if self.py3.format_contains(self.format, "button"):
            if self.open:
                format_control = self.format_button_open
            else:
                format_control = self.format_button_closed

            button = {"full_text": format_control, "index": "button"}
        else:
            button = None

        composites = {
            "output": self.py3.composite_create(output),
            "button": self.py3.composite_create(button),
        }
        output = self.py3.safe_format(self.format, composites)
        response = {"cached_until": self.py3.CACHE_FOREVER, "full_text": output}

        if urgent:
            response["urgent"] = urgent

        return response

    def on_click(self, event):
        """
        Switch the displayed module or pass the event on to the active module
        """
        if event["button"] == self.button_toggle:
            # we only toggle if button was used
            if event.get("index") == "button" and self.py3.is_my_event(event):
                self.urgent = False
                self.open = not self.open


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
