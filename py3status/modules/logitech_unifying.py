# -*- coding: utf-8 -*-
"""
Display information on Logitech Unifying devices.

Configuration parameters:
    button_toggle: mouse button to toggle between states (default 1)
    cache_timeout: refresh interval for this module (default 20)
    format: display format for this module
        (default '[\?if=is_plugged [\?color=#00CCFF \u2055{total}[\?if=is_toggled '
        |[{format_device}]]]|Logitech receiver not found]'
    format_device: display format for unifying devices
        (default '[{name}][ ({percent}%)]')
    format_separator: show separator only if more than one (default ' ')
    is_toggled: toggle to turn off device information (default False)
    threshold_low: paint color_bad for battery percent (default 5)
    threshold_mid: paint color_degraded for battery percent (default 15)

Control placeholders:
    is_plugged: a boolean based on unifying receiver
    is_reachable: a boolean based on unifying devices
    is_toggled: a boolean based on button_toggle mouse clicks

Format placeholders:
    {format_device} format for Logitech Unifying devices

Format_device placeholders:
    {rtotal} total number of receivers, eg 1
    {total} total number of devices, eg 2

    For Unifying receivers only.

    {rbootloader} version, eg 02.14
    {rcount_max} maximum number of devices capacity, eg 6
    {rcount} number of paired devices, eg 2
    {rdevice_activity_counters} information, eg 2=112
    {rdevice_path} path to device, eg /dev/hidraw3
    {rfirmware} version, eg 12.01.B0019
    {rname} device name, eg Unifying Receiver
    {rnotifications} information, eg wireless, software present (0x000900)
    {rserial} serial, eg abc123de
    {rusb_id} usb id, eg 0123:abcd

    For Unifying devices only.

    {bootloader} version, eg 02.06
    {charging} battery state, eg charging
    {codename} codename, eg M570
    {firmware} version, eg 26.00.B0003
    {kind} device type, eg trackball
    {name} device name, eg Wireless Trackball M570
    {other} eg, 00.01
    {percent} battery percent, eg 80
    {polling_rate} eg 8 ms
    {power_switch} eg The power switch is located on the base
    {protocol} eg HID++ 1.0
    {serial_number} eg 01234567
    {wireless_pid} eg 1028

Color options:
    color_bad: Battery less than threshold_low percent. Device offline.
    color_degraded: Battery less than threshold_mid percent.
    color_good: Battery more than threshold_mid percent.

Requires:
    solaar: a manager for Logitech Unifying devices

SAMPLE OUTPUT
[
    {'color': '#00CCFF', 'full_text': '\u20552'},
    {'color': '#FF0000', 'full_text': 'Wireless Touch Keyboard K400 '},
    {'color': '#00FF00', 'full_text': 'Wireless Trackball M570'},
    {'color': '#00CCFF', 'full_text': '('},
    {'color': '#00FF00', 'full_text': '15'},
    {'color': '#FFFF00', 'full_text': '%)'},
]

toggled
{'color': '#00CCFF', 'full_text': '\u20552'},

unplugged
{'color': '#FF0000', 'full_text': 'Logitech receiver not found'},
"""

STRING_NOT_INSTALLED = "isn't installed"
STRING_RECEIVER = 'Unifying Receiver'


class Py3status:
    """
    """
    # available configuration parameters
    button_toggle = 1
    cache_timeout = 20
    format = u'[\?if=is_plugged [\?color=#00CCFF \u2055{total}[\?if=is_toggled ' +\
             u'|[{format_device}]]]|Logitech receiver not found]'
    format_device = '[{name}][ ({percent}%)]'
    format_separator = ' '
    is_toggled = False
    threshold_low = 5
    threshold_mid = 15

    def post_config_hook(self):
        if not self.py3.check_commands('solaar'):
            raise Exception(STRING_NOT_INSTALLED)

    def _get_solaar_data(self):
        try:
            data = self.py3.command_output('solaar show').split('\n\n')
            data = filter(None, data)
            is_plugged = True
        except:
            data = {}
            is_plugged = False

        return data, is_plugged

    def _manipulate(self, data):
        sorted_data = []
        rtotal = total = 0

        for per_device in data:
            temporary = {}

            # key/values to be modified
            for line in per_device.splitlines():
                key, _, value = line.partition(':')
                key = key.strip('.').strip(',').strip()
                value = value.strip(',').strip()

                if key.isdigit():
                    temporary['name'] = value
                elif 'paired device(s)' in key:
                    num = [s for s in key.split() if s.isdigit()]
                    temporary['count'] = num[0]
                    temporary['count_max'] = num[1]
                elif 'power switch' in key.lower():
                        temporary['power_switch'] = key
                elif 'battery' in key.lower():
                    if 'unknown' in value:
                        temporary['percent'] = None
                        temporary['charging'] = None
                    else:
                        percent, charging = value.split('%, ')
                        temporary['percent'] = percent
                        temporary['charging'] = charging
                else:
                    new_key = key.replace(' ', '_').lower()
                    temporary[new_key] = value

            # is receiver or device?
            if per_device.startswith(STRING_RECEIVER):
                temporary['name'] = STRING_RECEIVER
                temporary = dict(('r' + k, v) for k, v in temporary.items())
                temporary['is_reachable'] = True
                rtotal += 1
            else:
                total += 1

            # is reachable?
            if 'device is offline' in per_device:
                temporary['is_reachable'] = False
            else:
                temporary['is_reachable'] = True

            # end of loop: append modified output.
            sorted_data.append(temporary)

        return sorted_data, total, rtotal

    def logitech_unifying(self):
        """
        """
        color = self.py3.COLOR_BAD
        data = is_plugged = total = rtotal = None
        is_toggled = self.is_toggled
        unifying = []

        data, is_plugged = self._get_solaar_data()
        data, total, rtotal = self._manipulate(data)

        for per_device in data:
            format_color = '\?color={} {}'
            reachable = per_device.get('is_reachable', False)

            for k, v in per_device.items():
                _fmt = None

                # skip if empty
                if v is None:
                    continue

                # colorize all keys based on (is device reachable?)
                if reachable and k != 'percent':
                    if not isinstance(v, bool):
                        _fmt = format_color.format('good', v)
                else:
                    if not isinstance(v, bool):
                        _fmt = format_color.format('bad', v)

                # colorize percent keys based on (percent number)
                if k == 'percent':
                    v = int(v)
                    if v <= self.threshold_low:
                        _fmt = format_color.format('bad', v)
                    elif v <= self.threshold_mid:
                        _fmt = format_color.format('degraded', v)
                    else:
                        _fmt = format_color.format('good', v)

                # safe format
                if _fmt:
                    per_device[k] = self.py3.safe_format(_fmt)

            # end of loop: append modified output.
            unifying.append(self.py3.safe_format(
                self.format_device, per_device))

        format_separator = self.py3.safe_format(self.format_separator)
        format_device = self.py3.composite_join(format_separator, unifying)
        logitech_unifying = self.py3.safe_format(self.format,
                                                 dict(
                                                     format_device=format_device,
                                                     is_plugged=is_plugged,
                                                     is_toggled=is_toggled,
                                                     rtotal=rtotal,
                                                     total=total,
                                                 ))
        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': logitech_unifying,
            'color': color,
        }

    def on_click(self, event):
        button = event['button']
        if button == self.button_toggle:
            self.is_toggled = not self.is_toggled
        else:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
