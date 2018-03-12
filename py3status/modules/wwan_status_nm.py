# -*- coding: utf-8 -*-
"""
Display wwan network operator, signal and netgen properties,
based on ModemManager, NetworkManager and dbus.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds.
        (default 5)
    consider_3G_degraded: If set to True, only 4G-networks will be
        considered 'good'; 3G connections are shown
        as 'degraded', which is yellow by default. Mostly
        useful if you want to keep track of where there
        is a 4G connection.
        (default False)
    format_down: What to display when the modem is not plugged in
        (default 'WWAN: {operator} {netgen} ({signal})')
    format_error: What to display when modem can't be accessed.
        (default 'WWAN: {error}')
    format_no_service: What to display when the modem does not have a
        network connection. This allows to omit the (then
        meaningless) network generation.
        (default 'WWAN: {operator}')
    format_up: What to display upon regular connection
        (default 'WWAN: {operator} {netgen} ({signal})')
    modem: The device to use from NetworkManager config
        (default '', empty value will use first find modem or 
        use 'busctl introspect org.freedesktop.ModemManager1 \
                                /org/freedesktop/ModemManager1/Modem/0'
        and read .EquipmentIdentifier)

Color options:
    color_bad: Error or no connection
    color_degraded: Low generation connection eg 2G
    color_good: Good connection

Requires:
    ModemManager
    NetworkManager
    pydbus

@author Cyril Levis <levis.cyril@gmail.com>

SAMPLE OUTPUT
{'color': '#00FF00', 'full_text': u'Bouygues Telecom 4G (19%)'}

off
{'color': '#FF0000', 'full_text': u'Bouygues Telecom 4G (12%)'}
"""

from pydbus import SystemBus


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    consider_3G_degraded = False
    format_error = 'WWAN: {error}'
    format_down = 'WWAN: {operator} {netgen} ({signal})'
    format_up = 'WWAN: {operator} {netgen} ({signal})'
    modem = ""

    def wwan_status_nm(self):
        response = {}
        response['cached_until'] = self.py3.time_in(self.cache_timeout)

        bus = SystemBus()
        """
        find the modem
        """
        for id in range(0, 20):
            device = 'Modem/' + str(id)

            try:
                proxy = bus.get('.ModemManager1', device)

                eqid = str(proxy.EquipmentIdentifier)

                if (self.modem != ""
                        and eqid == self.modem) or (self.modem == ""):
                    state = proxy.State
                    signal = str(proxy.SignalQuality[0]) + '%'
                    modes = proxy.CurrentModes[0]
                    operator = proxy.OperatorName
                    netgen = self._get_capabilities(modes)

                    if state == 11:
                        response['full_text'] = self.py3.safe_format(
                            self.format_up,
                            dict(
                                netgen=netgen[1],
                                signal=signal,
                                operator=operator))
                        """
                        green color if 4G, else yellow
                        """
                        if netgen[0] == 4:
                            response['color'] = self.py3.COLOR_GOOD
                        elif netgen[0] == 3 and self.consider_3G_degraded is False:
                            response['color'] = self.py3.COLOR_GOOD
                        else:
                            response['color'] = self.py3.COLOR_DEGRADED

                    else:
                        response['full_text'] = self.py3.safe_format(
                            self.format_down,
                            dict(
                                netgen=netgen[1],
                                signal=signal,
                                operator=operator))
                        response['color'] = self.py3.COLOR_BAD
                else:
                    response['full_text'] = self.py3.safe_format(
                        self.format_error, dict(error='wrong or empty modem'))
                    response['color'] = self.py3.COLOR_BAD
                return response

            except:
                pass

    def _get_capabilities(self, c):
        """
        TODO: improve the following dict based on this doc
        https://developer.gnome.org/NetworkManager/stable/nm-dbus-types.html#NMDeviceModemCapabilities
        """
        capabilities = {8: (3, '3G+'), 12: (4, '4G')}
        return capabilities.get(c, (0, 'no data'))


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
