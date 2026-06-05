r"""
Display headset connection state.

This module displays the connection state and battery for supported headsets.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds (default 10)
    format: Display format (default 'Headsetcontrol: {devices}')

Format placeholders:
    {devices}: The list of devices attached.
    {vendor}: The vendor of a device as reported by headsetcontrol.
    {product}: The product name of a device as reported by headsetcontrol.
    {battery}: The battery level of a device, formated.
    {battery_level}: The unformated battary level in percent as reported by headsetcontrol.

Requires:
    headsetcontrol: A cross-platform tool to control USB gaming headsets.

Example:

```
headsetcontrol {
    format = "{devices}"
    format_device = "{vendor} {product} {battery}"
    format_battery = "({battery_level}%)"
}
```

@author Valentin Weber <valentin+py3status@wv2.ch>
@license BSD

SAMPLE OUTPUT
{'full_text': 'Headsetcontrol: Test Device (42%)'}
"""

import json


class Py3status:
    # available configuration parameters
    cache_timeout = 10
    format = "Headsetcontrol: {devices}"
    format_device = "{product} {battery}"
    format_device_separator = " "
    format_battery = "({battery_level}%)"

    def _get_headset_data(self):
        try:
            headsetcontrol_raw_json = self.py3.command_output("headsetcontrol -o json")
            return json.loads(headsetcontrol_raw_json)
        except (ValueError, UnicodeDecodeError):
            self.py3.error("Headsetcontrol returned no valid JSON.")
        except self.py3.CommandError:
            return {"devices": []}

    def headsetcontol(self):

        headset_data = self._get_headset_data()

        devices = []

        for device in headset_data["devices"]:
            headset_data_flat = {
                "vendor": self.py3.safe_format(device["vendor"]),
                "product": self.py3.safe_format(device["product"]),
                "battery": "",
            }

            if "CAP_BATTERY_STATUS" in device["capabilities"]:
                headset_data_flat["battery"] = self.py3.safe_format(
                    self.format_battery, {"battery_level": device["battery"]["level"]}
                )

            devices.append(self.py3.safe_format(self.format_device, headset_data_flat))

        format_device_separator = self.py3.safe_format(self.format_device_separator)
        devices = self.py3.composite_join(format_device_separator, devices)

        return {
            "full_text": self.py3.safe_format(self.format, param_dict={"devices": devices}),
            "cached_until": self.py3.time_in(self.cache_timeout),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """

    from py3status.module_test import module_test

    module_test(Py3status)
