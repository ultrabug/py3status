# -*- coding: utf-8 -*-
"""
Display WWANs, IP addresses, signals, properties, and more.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module
        *(default '\?color=state WW: [\?if=state_name=connected '
        '({signal_quality_0}% at {m3gpp_operator_name}) '
        '[{format_ipv4}][ {format_ipv6}]|{state_name}]')*
    format_ipv4: display format for ipv4 network (default '[{address}]')
    format_ipv6: display format for ipv6 network (default '[{address}]')
    format_stats: display format for statistics (default '{duration_hms}')
    modem: specify a modem device to use. otherwise, auto (default None)
    thresholds: specify color thresholds to use
        (default [(0, 'bad'), (11, 'good')])

Format placeholders:
    {access_technologies}           network speed, in bit, eg 192
    {access_technologies_name}      network speed names, eg LTE
    {current_bands}                 modem band, eg 1
    {current_bands_name}            modem band name, eg GSM/GPRS/EDGE 900 MHz
    {format_ipv4}                   format for ipv4 network config
    {format_ipv6}                   format for ipv6 network config
    {format_stats}                  format for network connection statistics
    {interface_name}                network interface name, eg wwp0s20f0u2i12
    {m3gpp_registration_state}      network registration state, eg 1
    {m3gpp_registration_state_name} network registration state name, eg HOME
    {m3gpp_operator_code}           network operator code, eg 496
    {m3gpp_operator_name}           network operator name, eg Py3status Telecom
    {signal_quality_0}              signal quality percentage, eg 88
    {signal_quality_1}              signal quality refreshed, eg True/False
    {state}                         network state, eg 0, 7, 11
    {state_name}                    network state name, eg searching, connected

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

Requires:
    modemmanager: mobile broadband modem management service
    networkmanager: network connection manager and user applications
    pydbus: pythonic dbus library

Examples:
```
# show state names, eg initializing, searching, registred, connecting.
wwan {
    format = '\?color=state WWAN: {state_name}'
}

# show state names, and when connected, show network information too.
wwan {
    format = 'WWAN: [\?color=state [{format_ipv4}]'
    format += '[{format_ipv6}] {state_name}]'
}

# show internet access technologies name with up/down state.
wwan
    format = 'WWAN: [\?color=state [{access_technologies_name}]'
    format += ' [\?if=state=11 up|down]]'
}

# add starter pack thresholds. you do not need to add them all.
wwan {
    thresholds = {
        'access_technologies': [
            (2, 'bad'), (32, 'orange'), (512, 'degraded'), (16384, 'good')
        ],
        'signal_quality_0': [
            (0, 'bad'), (10, 'orange'), (30, 'degraded'), (50, 'good')
        ],
        'signal_quality_1': [
            (False, 'darkgrey'), (True, 'degraded')
        ],
        'state': [
            (-1, 'bad'), (4, 'orange'), (5, 'degraded'), (11, 'good')
        ]
    }
}

# customize WWAN format
wwan {
    format = 'WWAN: [\?color=state {state_name}] '
    format += '[\?if=m3gpp_registration_state_name=HOME {m3gpp_operator_name} ] '
    format += '[\?if=m3gpp_registration_state_name=ROAMING {m3gpp_operator_name} ]'
    format += '[\?color=access_technologies {access_technologies_name} ]'
    format += '[([\?color=signal_quality_0 {signal_quality_0}]]'
    format += '[\?if=!signal_quality_1&color=signal_quality_1 \[!\]|] '
    format += '[\?if=state_name=connected [{format_ipv4}] [{format_stats}]]')
}
```

@author Cyril Levis <levis.cyril@gmail.com>, girst (https://gir.st/), lasers

SAMPLE OUTPUT
{'color': '#00ff00', 'full_text': 'WW: (88% at Py3status Telcom) 12.69.169.32'}

down
{'color': '#ff0000', 'full_text': 'WW: down'}
"""

from datetime import timedelta
from pydbus import SystemBus

STRING_MODEMMANAGER_DBUS = 'org.freedesktop.ModemManager1'
STRING_MODEM_ERROR = 'MM_MODEM_STATE_FAILED'
STRING_NOT_INSTALLED = 'not installed'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 10
    format = ('\?color=state WW: [\?if=state_name=connected '
              '({signal_quality_0}% at {m3gpp_operator_name}) '
              '[{format_ipv4}][ {format_ipv6}]|{state_name}]')
    format_ipv4 = u'[{address}]'
    format_ipv6 = u'[{address}]'
    format_stats = u'{duration_hms}'
    modem = None
    thresholds = [(0, 'bad'), (11, 'good')]

    def post_config_hook(self):
        modem_manager = ['ModemManager', '/usr/sbin/ModemManager']
        network_manager = ['NetworkManager', '/usr/sbin/NetworkManager']
        for command in (modem_manager, network_manager):
            if not self.py3.check_commands(command):
                raise Exception('%s %s' % (command[0], STRING_NOT_INSTALLED))

        # search: modemmanager flags and enumerations
        # enum 1: #MMModemState
        # enum 2: #MMModemAccessTechnology
        # enum 3: #MMModem3gppRegistrationState
        # enum 4: #MMModemBand

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
            0: 'Unknown',
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
        # enum 4: modem bands
        self.modem_bands = {
            0: 'Unknown or invalid band',
            1: 'GSM/GPRS/EDGE 900 MHz',
            2: 'GSM/GPRS/EDGE 1800 MHz',
            3: 'GSM/GPRS/EDGE 1900 MHz',
            4: 'GSM/GPRS/EDGE 850 MHz',
            5: 'WCDMA 2100 MHz (Class I)',
            6: 'WCDMA 3GPP 1800 MHz (Class III)',
            7: 'WCDMA 3GPP AWS 1700/2100 MHz (Class IV)',
            8: 'WCDMA 3GPP UMTS 800 MHz (Class VI)',
            9: 'WCDMA 3GPP UMTS 850 MHz (Class V)',
            10: 'WCDMA 3GPP UMTS 900 MHz (Class VIII)',
            11: 'WCDMA 3GPP UMTS 1700 MHz (Class IX)',
            12: 'WCDMA 3GPP UMTS 1900 MHz (Class II)',
            13: 'WCDMA 3GPP UMTS 2600 MHz (Class VII, internal)',
            31: 'E-UTRAN band I',
            32: 'E-UTRAN band II',
            33: 'E-UTRAN band III',
            34: 'E-UTRAN band IV',
            35: 'E-UTRAN band V',
            36: 'E-UTRAN band VI',
            37: 'E-UTRAN band VII',
            38: 'E-UTRAN band VIII',
            39: 'E-UTRAN band IX',
            40: 'E-UTRAN band X',
            41: 'E-UTRAN band XI',
            42: 'E-UTRAN band XII',
            43: 'E-UTRAN band XIII',
            44: 'E-UTRAN band XIV',
            47: 'E-UTRAN band XVII',
            48: 'E-UTRAN band XVIII',
            49: 'E-UTRAN band XIX',
            50: 'E-UTRAN band XX',
            51: 'E-UTRAN band XXI',
            52: 'E-UTRAN band XXII',
            53: 'E-UTRAN band XXIII',
            54: 'E-UTRAN band XXIV',
            55: 'E-UTRAN band XXV',
            56: 'E-UTRAN band XXVI',
            63: 'E-UTRAN band XXXIII',
            64: 'E-UTRAN band XXXIV',
            65: 'E-UTRAN band XXXV',
            66: 'E-UTRAN band XXXVI',
            67: 'E-UTRAN band XXXVII',
            68: 'E-UTRAN band XXXVIII',
            69: 'E-UTRAN band XXXIX',
            70: 'E-UTRAN band XL',
            71: 'E-UTRAN band XLI',
            72: 'E-UTRAN band XLII',
            73: 'E-UTRAN band XLIII',
            128: 'CDMA Band Class 0 (US Cellular 850MHz)',
            129: 'CDMA Band Class 1 (US PCS 1900MHz)',
            130: 'CDMA Band Class 2 (UK TACS 900MHz)',
            131: 'CDMA Band Class 3 (Japanese TACS)',
            132: 'CDMA Band Class 4 (Korean PCS)',
            134: 'CDMA Band Class 5 (NMT 450MHz)',
            135: 'CDMA Band Class 6 (IMT2000 2100MHz)',
            136: 'CDMA Band Class 7 (Cellular 700MHz)',
            137: 'CDMA Band Class 8 (1800MHz)',
            138: 'CDMA Band Class 9 (900MHz)',
            139: 'CDMA Band Class 10 (US Secondary 800)',
            140: 'CDMA Band Class 11 (European PAMR 400MHz)',
            141: 'CDMA Band Class 12 (PAMR 800MHz)',
            142: 'CDMA Band Class 13 (IMT2000 2500MHz Expansion)',
            143: 'CDMA Band Class 14 (More US PCS 1900MHz)',
            144: 'CDMA Band Class 15 (AWS 1700MHz)',
            145: 'CDMA Band Class 16 (US 2500MHz)',
            146: 'CDMA Band Class 17 (US 2500MHz Forward Link Only)',
            147: 'CDMA Band Class 18 (US 700MHz Public Safety)',
            148: 'CDMA Band Class 19 (US Lower 700MHz)',
            256: 'auto'
        }

        self.bus = SystemBus()
        self.init = {'ip': []}
        names = [
            'current_bands_name', 'access_technologies_name',
            'm3gpp_registration_name', 'interface_name', 'ipv4', 'ipv6',
            'stats'
        ]
        placeholders = [
            'current_bands_name', 'access_technologies_name',
            'm3gpp_registration_name', 'interface_name', 'format_ipv4',
            'format_ipv6', 'format_stats'
        ]
        for name, placeholder in zip(names, placeholders):
            self.init[name] = self.py3.format_contains(self.format,
                                                       placeholder)
            if name in ['ipv4', 'ipv6'] and self.init[name]:
                self.init['ip'].append(name)

    def _get_modem_proxy(self):
        modemmanager_proxy = self.bus.get(STRING_MODEMMANAGER_DBUS)
        modems = modemmanager_proxy.GetManagedObjects()

        for objects in modems.items():
            modem_path = objects[0]
            modem_proxy = self.bus.get(STRING_MODEMMANAGER_DBUS, modem_path)
            eqid = modem_proxy.EquipmentIdentifier

            if self.modem is None or self.modem == eqid:
                return modem_proxy
        else:
            return {}

    def _get_modem_status_data(self, modem_proxy):
        modem_data = {}
        try:
            modem_data = modem_proxy.GetStatus()
        except:
            pass
        return modem_data

    def _get_bearer(self, modem_proxy):
        bearer = {}
        try:
            bearer = modem_proxy.Bearers[0]
        except:
            pass
        return bearer

    def _get_interface(self, bearer):
        return self.bus.get(STRING_MODEMMANAGER_DBUS, bearer).Interface

    def _get_network_config(self, bearer):
        bearer_proxy = self.bus.get(STRING_MODEMMANAGER_DBUS, bearer)
        return {
            'ipv4': bearer_proxy.Ip4Config,
            'ipv6': bearer_proxy.Ip6Config,
        }

    def _get_stats(self, bearer):
        return self.bus.get(STRING_MODEMMANAGER_DBUS, bearer).Stats

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

    def wwan(self):
        modem_proxy = self._get_modem_proxy()
        wwan_data = self._get_modem_status_data(modem_proxy)
        wwan_data = self._organize(wwan_data)

        # state and name
        key = 'state'
        name = '_name'
        wwan_data[key] = wwan_data.get(key, 0)
        wwan_data[key + name] = self.network_states[wwan_data[key]]

        # if state is -1, modem failed. stop here. report error.
        # if state is less than 8, we are not connected. skip.
        # if state is 8 or more, we are connected. start work.
        if wwan_data[key] == -1:
            self.py3.error(STRING_MODEM_ERROR)
        elif wwan_data[key] < 8:
            pass
        else:
            # access technologies and name
            if self.init['access_technologies_name']:
                key = 'access_technologies'
                if wwan_data[key]:
                    bit = 1 << (wwan_data[key].bit_length() - 1)
                else:
                    bit = 0
                wwan_data[key + name] = self.network_speed[bit]

            # modem band
            if self.init['current_bands_name']:
                key = 'current_bands'
                wwan_data[key + name] = self.modem_bands[wwan_data[key]]

            # registration state and name
            if self.init['m3gpp_registration_name']:
                key = 'm3gpp_registration_state'
                wwan_data[key
                          + name] = self.registration_states[wwan_data[key]]

            # get bearer
            bearer = self._get_bearer(modem_proxy)

            if bearer:
                # interface name
                if self.init['interface_name']:
                    wwan_data['interface_name'] = self._get_interface(bearer)

                # ipv4 and ipv6 network config
                if self.init['ip']:
                    network_config = self._get_network_config(bearer)
                    format_ip = {
                        'ipv4': self.format_ipv4,
                        'ipv6': self.format_ipv6
                    }
                    for x in self.init['ip']:
                        wwan_data['format_' + x] = self.py3.safe_format(
                            format_ip[x], network_config.get(x, {}))

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
