# -*- coding: utf-8 -*-
"""
Display WWAN network operator, signal, properties, and more.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module
        *(default '\?color=state WW: [\?if=state=11 ({signal_quality_0}% at '
        '{m3gpp_operator_name}) [{format_ipv4}|{format_ipv6}]|down]')
    format_ipv4: display format for ipv4 network config (default '{address}')
    format_ipv6: display format for ipv4 network config (default '{address}')
    format_stats: display format for network statistics (default '{duration_hms}')
    modem: specify a modem device to use. otherwise, auto (default None)
    thresholds: specify color thresholds to use
    *(default {
        'signal_quality_0': [
            (0, 'bad'), (10, 'orange'), (30, 'degraded'), (50, 'good')],
        'signal_quality_1': [
            (False, 'bad'), (True, 'good')],
        'access_technologies': [
            (2, 'bad'), (32, 'orange'), (512, 'degraded'), (16384, 'good')],
        'state': [
            (-1, 'bad'), (4, 'orange'), (5, 'degraded'), (11, 'good')]
        })*

Format placeholders:
    {access_technologies}       network speed, in bit, eg 192
    {access_technologies_name}  network speed names, eg LTE
    {format_ipv4}               format for ipv4 network config
    {format_ipv6}               format for ipv6 network config
    {format_stats}              format for network connection statistics
    {interface_name}            network interface name
    {m3gpp_registration_state}  network registration states, eg 1
    {m3gpp_registration_name}   network registration names, eg HOME, ROAMING
    {m3gpp_operator_code}       network operator code, eg 496
    {m3gpp_operator_name}       network operator name, eg py3status Telecom
    {signal_quality_0}          signal quality percentage, eg 88
    {signal_quality_1}          signal quality refreshed
    {state}                     network states, eg 7, 11
    {state_name}                network state names, eg searching, connecting

format_ipv4 placeholders:
    {address} ip address
    {dns1}    dns1
    {dns2}    dns2
    {gateway} gateway
    {mtu}     mtu
    {prefix}  netmask prefix

format_ipv6 placeholders:
    {address} ip address
    {dns1}    dns1
    {dns2}    dns2
    {gateway} gateway
    {mtu}     mtu
    {prefix}  netmask prefix

format_stats placeholders:
    {duration}     time since connected, in seconds, eg 171
    {duration_hms} time since connected, in [HH:]MM:SS, eg 02:51
    {tx_bytes}     transmit bytes
    {rx_bytes}     receive bytes

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Enum:  # noqa
    0: https://www.freedesktop.org/software/ModemManager/api/1.0.0/ModemManager-Flags-and-Enumerations.html
    1: https://www.freedesktop.org/software/ModemManager/api/1.0.0/ModemManager-Flags-and-Enumerations.html#MMModemState
    2: https://www.freedesktop.org/software/ModemManager/api/1.0.0/ModemManager-Flags-and-Enumerations.html#MMModemAccessTechnology
    3: https://www.freedesktop.org/software/ModemManager/api/1.0.0/ModemManager-Flags-and-Enumerations.html#MMModem3gppRegistrationState

Requires:
    modemmanager: mobile broadband modem management service
    networkmanager: network connection manager and user applications
    pydbus: pythonic dbus library

Examples:
# ```
# customize WWAN format
wwan {
    format = 'WWAN [\?color=state {state_name}] '
    format += '[\?if=m3gpp_registration_name=HOME {m3gpp_operator_name} ] '
    format += '[\?if=m3gpp_registration_name=ROAMING {m3gpp_operator_name} ]'
    format += '[\?color=access_technologies {access_technologies_name} ]'
    format += '[([\?color=signal_quality_0 {signal_quality_0}]]'
    format += '[\?if=signal_quality_1=False&color=signal_quality_1 \[!\]|] '
    format += '[\?if=state=11 [{format_ipv4}] [{format_stats}]]')
}

# show state name and network information if connected, else show state only
wwan {
    format = '\?color=state [\?if=state=11 {state_name} [{format_ipv4}|{format_ipv6}]|{state_name}]'
}

# show state with state colored
wwan {
    format = '\?color=state {state_name}'
}

# show access technologies name, custom state up for connected and down if disconnected
wwan
    format = '{access_technologies_name} [\?if=state=11 \?color=state up|down]
}
# ```

@author Cyril Levis <levis.cyril@gmail.com>, girst (https://gir.st/), lasers

SAMPLE OUTPUT
NOTE: Skip this part until we're finished with the module first.
"""

from pydbus import SystemBus
from datetime import timedelta

STRING_MODEMMANAGER_DBUS = 'org.freedesktop.ModemManager1'
STRING_NOT_INSTALLED = 'not installed'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = ('\?color=state WW: [\?if=state=11 ({signal_quality_0}% at '
              '{m3gpp_operator_name}) [{format_ipv4}|{format_ipv6}]|down]')
    format_ipv4 = u'{address}'
    format_ipv6 = u'{address}'
    format_stats = u'{duration_hms}'
    modem = None
    thresholds = {
        'access_technologies': [(2, 'bad'), (32, 'orange'), (512, 'degraded'),
                                (16384, 'good')],
        'signal_quality_0': [(0, 'bad'), (10, 'orange'), (30, 'degraded'),
                             (50, 'good')],
        'signal_quality_1': [(False, 'darkgrey'), (True, 'degraded')],
        'state': [(-1, 'bad'), (4, 'orange'), (5, 'degraded'), (11, 'good')]
    }

    def post_config_hook(self):
        for command in ['ModemManager', 'NetworkManager']:
            if not self.py3.check_commands(command):
                raise Exception('%s %s' % (command, STRING_NOT_INSTALLED))

        # enum 1: network states
        self.network_states = {
            -1: 'failed',
            0: 'unknown',
            1: 'initializing',
            2: 'locked',
            3: 'disabled',
            4: 'disabling',
            5: 'enabling',
            6: 'enabled',
            7: 'searching',
            8: 'registered',
            9: 'disconnecting',
            10: 'connecting',
            11: 'connected'
        }
        # enum 2: network speed
        self.network_speed = {
            0: 'unknown',
            1 << 0: 'POTS',  # 2
            1 << 1: 'GSM',
            1 << 2: 'GSM Compact',
            1 << 3: 'GPRS',
            1 << 4: 'EDGE',
            1 << 5: 'UMTS',  # 32
            1 << 6: 'HSDPA',
            1 << 7: 'HSUPA',
            1 << 8: 'HSPA',
            1 << 9: 'HSPA+',  # 512
            1 << 10: '1XRTT',
            1 << 11: 'EVDO0',
            1 << 12: 'EVDOA',
            1 << 13: 'EVDOB',
            1 << 14: 'LTE'  # 16384
        }
        # enum 3: network registration state
        self.registration_states = {
            0: 'IDLE',
            1: 'HOME',
            2: 'SEARCHING',
            3: 'DENIED',
            4: 'UNKNOWN',
            5: 'ROAMING'
        }

        self.bus = SystemBus()
        self.init = {'ip': []}
        names = [
            'access_technologies_name', 'm3gpp_registration_name',
            'interface_name', 'ipv4', 'ipv6', 'stats'
        ]
        placeholders = [
            'access_technologies_name', 'm3gpp_registration_name',
            'interface_name', 'format_ipv4', 'format_ipv6', 'format_stats'
        ]
        for name, placeholder in zip(names, placeholders):
            self.init[name] = self.py3.format_contains(self.format,
                                                       placeholder)
            if name in ['ipv4', 'ipv6'] and self.init[name]:
                self.init['ip'].append(name)

    def _get_modem_proxy(self):
        modems = {}
        try:
            modemmanager_proxy = self.bus.get(STRING_MODEMMANAGER_DBUS)
            modems = modemmanager_proxy.GetManagedObjects()
        except:
            pass

        for objects in modems.items():
            modem_path = objects[0]
            modem_proxy = self.bus.get(STRING_MODEMMANAGER_DBUS, modem_path)
            eqid = '{}'.format(modem_proxy.EquipmentIdentifier)

            if self.modem is None or self.modem == eqid:
                return modem_proxy
        else:
            return {}

    def _get_bearer(self, modem_proxy):
        bearer = {}
        try:
            bearer = modem_proxy.Bearers[0]
        except:
            pass
        return bearer

    def _get_network_config(self, bearer):
        network_config = {}
        try:
            bearer_proxy = self.bus.get(STRING_MODEMMANAGER_DBUS, bearer)
            network_config['ipv4'] = bearer_proxy.Ip4Config
            network_config['ipv6'] = bearer_proxy.Ip6Config
        except:
            pass
        return network_config

    def _get_interface(self, bearer):
        interface = None
        try:
            bearer_proxy = self.bus.get(STRING_MODEMMANAGER_DBUS, bearer)
            interface = bearer_proxy.Interface
        except:
            pass
        return interface

    def _get_stats(self, bearer):
        stats = {}
        try:
            bearer_proxy = self.bus.get(STRING_MODEMMANAGER_DBUS, bearer)
            stats = bearer_proxy.Stats
        except:
            pass
        return stats

    def _get_status(self, modem_proxy):
        modem_data = {}
        try:
            modem_data = modem_proxy.GetStatus()
        except:
            pass
        return modem_data

    def _organize(self, data):
        new_data = {}
        for key, value in data.items():
            key = key.lower().replace('-', '_')
            if isinstance(value, (list, tuple)):
                if len(value) > 1:
                    for i, v in enumerate(value):
                        new_data['%s_%s' % (key, i)] = v
                elif len(value) == 1:
                    new_data[key] = value[0]
                else:
                    new_data[key] = None
            else:
                new_data[key] = value

        return new_data

    def wwan_status_nm(self):
        modem_proxy = self._get_modem_proxy()
        wwan_data = self._organize(self._get_status(modem_proxy))
        network_state = wwan_data.get('state', 0)
        wwan_data['state_name'] = self.network_states[network_state]

        # no signal data if less than 8
        if network_state >= 8:

            bearer = self._get_bearer(modem_proxy)

            # access technologies and name
            if self.init['access_technologies_name']:
                key = 'access_technologies'
                new_key = '%s_name' % key
                if wwan_data[key]:
                    bit = 1 << (wwan_data[key].bit_length() - 1)
                else:
                    bit = 0
                wwan_data[new_key] = self.network_speed[bit]

            # registration state and name
            if self.init['m3gpp_registration_name']:
                key = 'm3gpp_registration_state'
                new_key = key.replace('state', 'name')
                wwan_data[new_key] = self.registration_states[wwan_data[key]]

            # interface name
            if self.init['interface_name']:
                wwan_data['interface_name'] = self._get_interface(bearer)

            # ipv4 and ipv6 network config
            if self.init['ip']:
                network_config = self._get_network_config(bearer)
                formats = {'ipv4': self.format_ipv4, 'ipv6': self.format_ipv6}
                for x in self.init['ip']:
                    wwan_data['format_' + x] = self.py3.safe_format(
                        formats[x], network_config.get(x, {}))

            # network connection statistics
            if self.init['stats']:
                stats = self._organize(self._get_stats(bearer))
                stats['duration_hms'] = str(
                    timedelta(seconds=stats.get('duration', 0)))
                wwan_data['format_stats'] = self.py3.safe_format(
                    self.format_stats, stats)

            # thresholds
            for k, v in wwan_data.items():
                if isinstance(v, (float, int)):
                    self.py3.threshold_get_color(v, k)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, wwan_data)
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
