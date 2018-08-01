# -*- coding: utf-8 -*-
"""
Display public IP address and online status.

Configuration parameters:
    button_refresh: mouse button to refresh this module (default 2)
    button_toggle: mouse button to toggle between states (default 1)
    cache_timeout: how often we refresh this module in seconds (default 60)
    expected: define expected values for format placeholders,
        and use `color_degraded` to show the output of this module
        if any of them does not match the actual value.
        This should be a dict eg {'country': 'France'}
        (default None)
    format: available placeholders are {ip} and {country},
        as well as any other key in JSON fetched from `url_geo`
        (default '{ip}')
    hide_when_offline: hide the module output when offline (default False)
    icon_off: what to display when offline (default '■')
    icon_on: what to display when online (default '●')
    ignore_warnings: ignore negative_cache_timeout warnings (default False)
    mode: default mode to display is 'ip' or 'status' (click to toggle)
        (default 'ip')
    negative_cache_timeout: how often to check again when offline (default 60)
    timeout: how long before deciding we're offline (default 5)
    url_geo: IP to check for geo location (must output json)
        (default 'https://ifconfig.co/json')

Format placeholders:
    {icon}        eg ●, ■
    {country}     eg France
    {country_iso} eg FR
    {ip}          eg 123.45.67.890
    {ip_decimal}  eg 1234567890
    {city}        eg Paris
    any other key in JSON fetched from `url_geo`

Color options:
    color_bad: Offline
    color_degraded: Output is unexpected (IP/country mismatch, etc.)
    color_good: Online

@author ultrabug, Cyril Levis (@cyrinux)

SAMPLE OUTPUT
{'full_text': '37.48.108.0'}

geo
{'full_text': '37.48.108.0 France'}

mode
{'color': '#00FF00', 'full_text': u'\u25cf'}
"""

URL_GEO_OLD_DEFAULT = 'http://ip-api.com/json'
URL_GEO_NEW_DEFAULT = 'https://ifconfig.co/json'
UA = 'Mozilla/5.0 py3status'


class Py3status:
    """
    """
    # available configuration parameters
    button_refresh = 2
    button_toggle = 1
    cache_timeout = 60
    expected = None
    format = '{ip}'
    hide_when_offline = False
    icon_off = u'■'
    icon_on = u'●'
    ignore_warnings = False
    mode = 'ip'
    negative_cache_timeout = 60
    timeout = 5
    url_geo = URL_GEO_NEW_DEFAULT

    class Meta:
        deprecated = {
            'remove': [
                {
                    'param': 'url',
                    'msg': 'obsolete parameter, use `url_geo` instead',
                },
            ],
            'rename': [
                {
                    'param': 'format_online',
                    'new': 'icon_on',
                    'msg': 'obsolete parameter, use `icon_on` instead',
                },
                {
                    'param': 'format_offline',
                    'new': 'icon_off',
                    'msg': 'obsolete parameter, use `icon_off` instead',
                },
            ],
        }

    def post_config_hook(self):
        if self.expected is None:
            self.expected = {}

        # Alert about negative_cache_timeout
        if self.negative_cache_timeout < 60 and self.ignore_warnings is False:
            self.py3.error(
                'warning, negative_cache_timeout should be > 60 to prevent ' +
                'from being blacklisted by API')

        # Backwards compatibility
        self.substitutions = {}
        if self.url_geo == URL_GEO_NEW_DEFAULT:
            self.substitutions['country_code'] = 'country_iso'
        elif self.url_geo == URL_GEO_OLD_DEFAULT:
            self.substitutions['ip'] = 'query'

    def on_click(self, event):
        """
        Toggle between display modes 'ip' and 'status'
        """
        button = event['button']
        if button == self.button_toggle:
            if self.mode == 'ip':
                self.mode = 'status'
            else:
                self.mode = 'ip'
        elif button != self.button_refresh:
            # prevent refresh
            self.py3.prevent_refresh()

    def _get_my_ip_info(self):
        """
        """
        self.headers = {'User-Agent': UA}

        try:
            info = self.py3.request(
                self.url_geo,
                timeout=self.timeout,
                headers=self.headers,
            ).json()
            for old, new in self.substitutions.items():
                info[old] = info.get(new)
            return info
        except self.py3.RequestException:
            return None

    def whatismyip(self):
        """
        """
        info = self._get_my_ip_info()
        response = {
            'cached_until': self.py3.time_in(self.negative_cache_timeout)
        }

        if info is None and self.hide_when_offline:
            response['full_text'] = ''
        elif info is not None:
            info['icon'] = self.icon_on
            response['cached_until'] = self.py3.time_in(self.cache_timeout)
            response['color'] = self.py3.COLOR_GOOD
            for key, val in self.expected.items():
                if val != info.get(key):
                    response['color'] = self.py3.COLOR_DEGRADED
                    break
            if self.mode == 'ip':
                response['full_text'] = self.py3.safe_format(self.format, info)
            else:
                response['full_text'] = self.icon_on
        else:
            response['full_text'] = self.icon_off
            response['color'] = self.py3.COLOR_BAD
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
