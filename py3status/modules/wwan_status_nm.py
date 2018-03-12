# -*- coding: utf-8 -*-
"""
Display wwan network operator, signal and access_technologies properties,
based on ModemManager, NetworkManager and dbus.

Configuration parameters:
    cache_timeout: How often we refresh this module in seconds.
        (default 5)
    format: What to display upon regular connection
        *(default '[\?color=state WWAN: {status}] '
        '[\?if=m3gpp_registration_state=HOME - {m3gpp_operator_name} ] '
        '[\?if=m3gpp_registration_state=ROAMING - {m3gpp_operator_name} ]'
        '[\?color=access_technologies {access_technologies} ]'
        '[([\?color=signal_quality_0 {signal_quality_0}%]) ]'
        '[\?if=signal_quality_1=False&color=signal_quality_1 \[!\]] '
        '[\?if=state=11 [{format_ipv4}] [{format_stats}]]')*
    format_ipv4: What to display about ipv4 network config
        (default '{address}')
    format_ipv6: What to display about ipv6 network config
        (default '{address}')
    format_stats: What to display about network usage
        (default '{duration_hms}')
    modem: The modem device to use. If None
        will use first find modem or
        'busctl introspect org.freedesktop.ModemManager1 /org/freedesktop/ModemManager1/Modem/0'
        and read '.EquipmentIdentifier')
        (default None)
    thresholds: specify color thresholds to use (see below for access_technologies values)
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
    {format_ipv4}               ipv4 format
    {format_ipv6}               ipv6 format
    {format_stats}              connection statistics
    {interface}                 interface name
    {access_technologies}       network speed
    {access_technologies_human}  network speed human readable
    {m3gpp_registration_state} is registred on network operator
    {m3gpp_operator_name}       network operator name
    {signal_quality_0}          network signal quality
    {signal_quality_1}          is signal quality recently updated (if True)
    {status}                    network status

format_ipv4 placeholders:
    {address}   ip address
    {dns1}      dns1
    {dns2}      dns2
    {gateway}   gateway
    {mtu}       mtu
    {prefix}    netmask prefix

format_ipv6 placeholders:
    {address}   ip address
    {dns1}      dns1
    {dns2}      dns2
    {gateway}   gateway
    {mtu}       mtu
    {prefix}    netmask prefix

format_stats placeholders:
    {duration}      time since connected
    {duration_hms}  time since connected h:m:s
    {tx_bytes}      tx-bytes (depends on modem)
    {rx_bytes}      rx-bytes (depends on modem)

Color thresholds:
    {state} State/Status color
    {access_technologies}  Access technologies color (2G, 3G, 4G)
    {signal_quality_0}     Signal quality color
    {signal_quality_1}     Signal quality recently updated boolean color

Enum:
    https://www.freedesktop.org/software/ModemManager/api/1.0.0/ModemManager-Flags-and-Enumerations.html

Requires:
    ModemManager
    NetworkManager
    pydbus


@author Cyril Levis <levis.cyril@gmail.com>, girst (https://gir.st/), lasers

SAMPLE OUTPUT
NOTE: Skip this part until we're finished with the module first.
"""

from datetime import timedelta

from pydbus import SystemBus

STRING_MODEMMANAGER_DBUS = 'org.freedesktop.ModemManager1'
STRING_NOT_INSTALLED = 'not installed'
STRING_UNKNOWN = "n/a"


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    format = (
        u'[\?color=state WWAN: {status}] '
        u'[\?if=m3gpp_registration_state=HOME - {m3gpp_operator_name} ] '
        u'[\?if=m3gpp_registration_state=ROAMING - {m3gpp_operator_name} ]'
        u'[\?color=access_technologies {access_technologies_human} ]'
        u'[([\?color=signal_quality_0 {signal_quality_0}%]) ]'
        u'[\?if=signal_quality_1]|[\?color=signal_quality_1 \[!\]]'
        u'[\?if=state=11 [{format_ipv4}] [{format_stats}]]')
    format_ipv4 = u'{address}'
    format_ipv6 = u'{address}'
    format_stats = u'{duration_hms}'
    modem = None
    thresholds = {
        'access_technologies_human': [(2, 'bad'), (32, 'orange'),
                                      (512, 'degraded'), (16384, 'good')],
        'signal_quality_0': [(0, 'bad'), (10, 'orange'), (30, 'degraded'),
                             (50, 'good')],
        'signal_quality_1': [(False, 'bad'), (True, 'good')],
        'state': [(-1, 'bad'), (4, 'orange'), (5, 'degraded'), (11, 'good')]
    }

    def post_config_hook(self):
        for command in ['ModemManager', 'NetworkManager']:
            if not self.py3.check_commands(command):
                raise Exception('%s %s' % (command, STRING_NOT_INSTALLED))

        # network states dict
        # https://www.freedesktop.org/software/ModemManager/api/1.0.0/ModemManager-Flags-and-Enumerations.html#MMModemState
        self.states = {
            -1: 'failed',
            0: STRING_UNKNOWN,
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

        # network speed dict
        # https://www.freedesktop.org/software/ModemManager/api/1.0.0/ModemManager-Flags-and-Enumerations.html#MMModemAccessTechnology
        self.speed = {
            0: STRING_UNKNOWN,
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

        # network registration states
        # https://www.freedesktop.org/software/ModemManager/api/1.0.0/ModemManager-Flags-and-Enumerations.html#MMModem3gppRegistrationState
        self.rstates = {
            0: 'IDLE',
            1: 'HOME',
            2: 'SEARCHING',
            3: 'DENIED',
            4: 'UNKNOWN',
            5: 'ROAMING'
        }

        self.bus = SystemBus()

    def _get_modem_proxy(self):
        try:
            modemmanager_proxy = self.bus.get(STRING_MODEMMANAGER_DBUS)
            modems = modemmanager_proxy.GetManagedObjects()
        except:
            modems = {}

        # browse modems objects
        for objects in modems.items():
            modem_path = objects[0]
            modem_proxy = self.bus.get(STRING_MODEMMANAGER_DBUS, modem_path)

            # we can maybe choose another selector
            # avoid weird issues with special unicode chars
            eqid = '{}'.format(modem_proxy.EquipmentIdentifier)

            # use selected modem or first find
            if self.modem is None or self.modem == eqid:
                # return modem proxy
                return modem_proxy
        else:
            return {}

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
        try:
            bearer_proxy = self.bus.get(STRING_MODEMMANAGER_DBUS, bearer)
            return bearer_proxy.Interface
        except:
            return None

    def _get_stats(self, bearer):
        stats = {}
        try:
            bearer_proxy = self.bus.get(STRING_MODEMMANAGER_DBUS, bearer)
            stats = bearer_proxy.Stats
            stats['duration_hms'] = timedelta(seconds=stats['duration'])
        except:
            pass
        return stats

    def _get_status(self, modem_proxy):
        modem_data = {}
        try:
            modem_data = modem_proxy.GetStatus()
            # use human readable status format
        except:
            # i try another solution for handle suspend/resume pb
            # i force a state unknow != no data state in dict
            modem_data['state'] = 0
        # and i translate state to human status here
        modem_data['status'] = self.states[modem_data['state']]
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
        data = {}

        # get status informations
        modem_proxy = self._get_modem_proxy()
        data = self._organize(self._get_status(modem_proxy))

        # start to build return data dict
        # if state < 8, we have no signal data

        # self.py3.log('-' * 20)
        # self.py3.log(data)
        # self.py3.log('-' * 20)

        # @lasers_question: can data['state'] fail here?
        # @Cyrinux_answer: now no, see _get_status (before sometime
        # we get empty dict with no state
        # we might not need this, but lets see.
        if data['state'] >= 8:

            # access technologies
            if data['access_technologies']:
                highest_access_bit = 1 << (
                    data['access_technologies'].bit_length() - 1)
            else:
                highest_access_bit = 0
            data['access_technologies_human'] = self.speed[highest_access_bit]

            # use human readable registration state format
            data['m3gpp_registration_state'] = self.rstates[data[
                'm3gpp_registration_state']]

            # @lasers_question: what else can we get from modem_proxy?
            #
            bearer = modem_proxy.Bearers[0]

            # get interface name
            interface = self._get_interface(bearer)
            data['interface'] = interface

            # Get network config
            network_config = self._get_network_config(bearer)
            ipv4 = network_config.get('ipv4', {})
            ipv6 = network_config.get('ipv6', {})

            # Add network config to data dict
            data['format_ipv4'] = self.py3.safe_format(self.format_ipv4, ipv4)
            data['format_ipv6'] = self.py3.safe_format(self.format_ipv6, ipv6)

            # Get connection statistics
            stats = self._organize(self._get_stats(bearer))
            data['format_stats'] = self.py3.safe_format(
                self.format_stats, stats)

            # @Cyrinux_question
            # get status color here, i put this here else we can loop over composite
            # maybe we must organize data and then loop over all?
            # not sure we want/can color network_config and stats for the moment
            # for now, we color everything. nice and easy. also, idk whats in data.
            for k, v in data.items():
                if isinstance(v, (float, int)):
                    self.py3.threshold_get_color(v, k)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(self.format, data)
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
