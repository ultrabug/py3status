r"""
Display bluetooth status.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default 'BT[: {format_device}]')
    format_device: display format for bluetooth devices (default '{name}')
    format_separator: show separator if more than one (default '\|')

Format placeholders:
    {format_device} format for bluetooth devices

format_device placeholders:
    {mac} bluetooth device address
    {name} bluetooth device name

Color options:
    color_bad: No connection
    color_good: Active connection

Requires:
    pydbus: pythonic dbus library

@author jmdana <https://github.com/jmdana>
@license GPLv3 <https://www.gnu.org/licenses/gpl-3.0.txt>

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'BT: Microsoft Bluetooth Notebook Mouse 5000'}

off
{'color': '#FF0000', 'full_text': u'BT'}
"""

from pydbus import SystemBus

DEFAULT_FORMAT = "BT[: {format_device}]"


def get_connected_devices():
    bus = SystemBus()
    manager = bus.get("org.bluez", "/")["org.freedesktop.DBus.ObjectManager"]
    objects = manager.GetManagedObjects()
    devices = []

    for dev_path, interfaces in objects.items():
        if "org.bluez.Device1" in interfaces:
            properties = objects[dev_path]["org.bluez.Device1"]

            if properties["Connected"] == 1:
                devices.append((properties["Address"], properties["Name"]))

    return devices


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    format = DEFAULT_FORMAT
    format_device = "{name}"
    format_separator = r"\|"

    class Meta:
        def deprecate_function(config):
            if not config.get("format_separator") and config.get("device_separator"):
                sep = config.get("device_separator")
                sep = sep.replace("\\", "\\\\")
                sep = sep.replace("[", r"\[")
                sep = sep.replace("]", r"\]")
                sep = sep.replace("|", r"\|")

                return {"format_separator": sep}
            else:
                return {}

        deprecated = {
            "function": [{"function": deprecate_function}],
            "remove": [
                {
                    "param": "device_separator",
                    "msg": "obsolete set using `format_separator`",
                }
            ],
        }

    def post_config_hook(self):
        # DEPRECATION WARNING. SPECIAL CASE. DO NOT USE THIS AS EXAMPLE.
        format_prefix = getattr(self, "format_prefix", None)
        format_no_conn = getattr(self, "format_no_conn", None)
        format_no_conn_prefix = getattr(self, "format_no_conn_prefix", None)

        placeholders = set(self.py3.get_placeholders_list(self.format))
        if {"name", "mac"} & placeholders:
            # this is an old format so should be format_device
            self.format_device = self.format
            self.format = DEFAULT_FORMAT
            msg = "DEPRECATION WARNING: your format is using invalid "
            msg += "placeholders you should update your configuration."
            self.py3.log(msg)

        if self.format != DEFAULT_FORMAT:
            # The user has set a format using the new style format so we are
            # done here.
            return

        if format_prefix or format_no_conn_prefix or format_no_conn:
            # create a format that will give the expected output
            self.format = r"[\?if=format_device {}{{format_device}}|{}{}]".format(
                format_prefix or "BT: ",
                format_no_conn_prefix or "BT: ",
                format_no_conn or "OFF",
            )
            msg = "DEPRECATION WARNING: you are using old style configuration "
            msg += "parameters you should update to use the new format."
            self.py3.log(msg)

    def bluetooth(self):
        devices = get_connected_devices()

        if devices:
            data = []
            for mac, name in devices:
                data.append(
                    self.py3.safe_format(self.format_device, {"name": name, "mac": mac})
                )

            format_separator = self.py3.safe_format(self.format_separator)
            format_device = self.py3.composite_join(format_separator, data)
            color = self.py3.COLOR_GOOD
        else:
            format_device = None
            color = self.py3.COLOR_BAD

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(
                self.format, {"format_device": format_device}
            ),
            "color": color,
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
