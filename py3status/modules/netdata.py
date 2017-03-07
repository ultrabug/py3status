# -*- coding: utf-8 -*-
"""
Display network speed and bandwidth usage.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (default 2)
    format: display format for this module (default '{format_netdata}'
    format_netdata: format for netdata
        (default 'LAN(Kb): {down}↓ {up}↑ \| T(Mb): {download}↓ {upload}↑ {total}↕')
    low_speed: threshold (default 30)
    low_traffic: threshold (default 400)
    med_speed: threshold (default 60)
    med_traffic: threshold (default 700)

Format placeholders:
    {format_netdata} format for netdata

Format_timer placeholders:
    {down}     number of download speed traffic
    {up}       number of up speed traffic
    {download} number of download usage
    {upload}   number of upload usage
    {total}    number of total usage

Color options:
    color_bad:      below low threshold
    color_degraded: below medium threshold
    color_good:     medium threshold or above

@author Shahin Azad <ishahinism at Gmail>
"""


class GetData:
    """Get system status.
    """
    def __init__(self, nic):
        self.nic = nic

    def netBytes(self):
        """Get bytes directly from /proc.
        """
        with open('/proc/net/dev') as fh:
            net_data = fh.read().split()
        interface_index = net_data.index(self.nic + ':')
        received_bytes = int(net_data[interface_index + 1])
        transmitted_bytes = int(net_data[interface_index + 9])
        return received_bytes, transmitted_bytes


class Py3status:
    """
    """
    # 'LAN(Kb): {:5.1f}↓ {:5.1f}↑ === T(Mb): {:3.0f}↓ {:3.0f}↑ {:3.0f}↕'

    # available configuration parameters
    cache_timeout = 2
    format = '{format_netdata}'
    format_netdata = u'LAN(Kb): {down}↓ {up}↑ \| T(Mb): {download}↓ {upload}↑ {total}↕'
    # format_netdata = u'[\?color={color_speed} LAN(Kb): {down}↓ {up}↑ ]
    # [\?color={color_traffic} T(Mb): {download}↓ {upload}↑ {total}↕]'
    low_speed = 30
    low_traffic = 400
    med_speed = 60
    med_traffic = 700
    nic = None

    class Meta:
        update_config = {
            'update_placeholder_format': [
                {
                    'placeholder_formats': {
                        'down': ':5.1f',
                    },
                    'format_strings': ['format_netdata'],
                },
                {
                    'placeholder_formats': {
                        'up': ':5.1f',
                    },
                    'format_strings': ['format_netdata'],
                },
                {
                    'placeholder_formats': {
                        'download': ':3.0f',
                    },
                    'format_strings': ['format_netdata'],
                },
                {
                    'placeholder_formats': {
                        'upload': ':3.0f',
                    },
                    'format_strings': ['format_netdata'],
                },
                {
                    'placeholder_formats': {
                        'total': ':3.0f',
                    },
                    'format_strings': ['format_netdata'],
                }
            ],
        }

    def __init__(self):
        self.old_transmitted = 0
        self.old_received = 0

    def post_config_hook(self):
        """Get network interface.
        """
        if self.nic is None:
            # Get default gateway directly from /proc.
            with open('/proc/net/route') as fh:
                for line in fh:
                    fields = line.strip().split()
                    if fields[1] == '00000000' and int(fields[3], 16) & 2:
                        self.nic = fields[0]
                        break
            if self.nic is None:
                self.nic = 'lo'
                self.py3.notify_user(
                    'netdata: cannot find a nic to use. selected nic: lo instead.'
                )
            self.py3.log('selected nic: %s' % self.nic)

    def netdata(self):
        """
        Calculate network speed
        Calculate networks used traffic.
        """
        data = GetData(self.nic)
        received_bytes, transmitted_bytes = data.netBytes()

        # net_speed (stats)
        down = (received_bytes - self.old_received) / 1024.
        up = (transmitted_bytes - self.old_transmitted) / 1024.
        self.old_received = received_bytes
        self.old_transmitted = transmitted_bytes

        # net_traffic (stats)
        download = received_bytes / 1024 / 1024.
        upload = transmitted_bytes / 1024 / 1024.
        total = download + upload

        # net_speed (color)
        if down < self.low_speed:
            color_speed = self.py3.COLOR_BAD
        elif down < self.med_speed:
            color_speed = self.py3.COLOR_DEGRADED
        else:
            color_speed = self.py3.COLOR_GOOD

        # net_traffic (color)
        if total < self.low_traffic:
            color_traffic = self.py3.COLOR_GOOD
        elif total < self.med_traffic:
            color_traffic = self.py3.COLOR_DEGRADED
        else:
            color_traffic = self.py3.COLOR_BAD

        # convert float2string
        down = str(down)
        up = str(up)
        download = str(download)
        upload = str(upload)
        total = str(total)

        # net_speed (composite)
        down = self.py3.composite_create({'full_text': down, 'color': color_speed})
        up = self.py3.composite_create({'full_text': up, 'color': color_speed})

        # net_traffic (composite)
        download = self.py3.composite_create({'full_text': download, 'color': color_traffic})
        upload = self.py3.composite_create({'full_text': upload, 'color': color_traffic})
        total = self.py3.composite_create({'full_text': total, 'color': color_traffic})

        netdata = self.py3.safe_format(self.format_netdata, {'down': down,
                                                             'up': up,
                                                             'download': download,
                                                             'upload': upload,
                                                             'total': total})

        full_text = self.py3.safe_format(self.format, {'format_netdata': netdata})

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': full_text
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
