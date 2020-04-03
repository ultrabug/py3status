"""
Display transfer rates of a tor instance.

Configuration parameters:
    cache_timeout: An integer specifying the cache life-time of the modules
        output in seconds (default 2)
    control_address: The address on which the Tor daemon listens for control
        connections (default "127.0.0.1")
    control_password: The password to use for the Tor control connection
        (default None)
    control_port: The port on which the Tor daemon listens for control
        connections (default 9051)
    format: A string describing the output format for the module
        (default "↑ {up} ↓ {down}")
    format_value: A string describing how to format the transfer rates
        (default "[\\?min_length=12 {rate:.1f} {unit}]")
    hide_socket_errors: Hide errors connecting to Tor control socket
        (default False)
    rate_unit: The unit to use for the transfer rates
        (default "B/s")
    si_units: A boolean value selecting whether or not to use SI units
        (default False)

Format placeholders:
    {down} The incoming transfer rate
    {up} The outgoing transfer rate

format_value placeholders:
    {rate} The current transfer-rate's value
    {unit} The current transfer-rate's unit

Requires:
    stem: python controller library for tor https://pypi.org/project/stem

Examples:
```
tor_rate {
    cache_timeout = 10
    format = "IN: {down} | OUT: {up}"
    control_port = 1337
    control_password = "TertiaryAdjunctOfUnimatrix01"
    si_units = True
}
```

@author Felix Morgner <felix.morgner@gmail.com>
@license 3-clause-BSD

SAMPLE OUTPUT
{'full_text': u'\u2191 652.3 B/s \u2193 938.1 B/s'}
"""

from stem import ProtocolError, SocketError
from stem.connection import AuthenticationFailure
from stem.control import Controller, EventType

ERROR_AUTHENTICATION = "Error: Failed to authenticate with Tor daemon!"
ERROR_CONNECTION = "Error: Failed to establish control connection!"
ERROR_PROTOCOL = "Error: Failed to register event handler!"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 2
    control_address = "127.0.0.1"
    control_password = None
    control_port = 9051
    format = "↑ {up} ↓ {down}"
    format_value = r"[\?min_length=12 {rate:.1f} {unit}]"
    hide_socket_errors = False
    rate_unit = "B/s"
    si_units = False

    def post_config_hook(self):
        self._auth_failure = False
        self._down = 0
        self._handler_active = False
        self._up = 0

    def tor_rate(self, outputs, config):
        text = ""
        if not self._handler_active and not self._auth_failure:
            try:
                self._register_event_handler()
            except ProtocolError:
                text = ERROR_PROTOCOL
            except SocketError:
                if not self.hide_socket_errors:
                    text = ERROR_CONNECTION
            except AuthenticationFailure:
                text = ERROR_AUTHENTICATION
                self._auth_failure = True
        elif self._auth_failure:
            text = ERROR_AUTHENTICATION
        else:
            text = self.py3.safe_format(self.format, self._get_rates())

        return {"cached_until": self.py3.time_in(self.cache_timeout), "full_text": text}

    def _get_rates(self):
        up, up_unit = self.py3.format_units(
            self._up, unit=self.rate_unit, si=self.si_units
        )
        down, down_unit = self.py3.format_units(
            self._down, unit=self.rate_unit, si=self.si_units
        )
        return {
            "up": self.py3.safe_format(
                self.format_value, {"rate": up, "unit": up_unit}
            ),
            "down": self.py3.safe_format(
                self.format_value, {"rate": down, "unit": down_unit}
            ),
        }

    def _handle_event(self, event):
        self._down = event.read
        self._up = event.written

    def _register_event_handler(self):
        self._control = Controller.from_port(
            address=self.control_address, port=self.control_port
        )
        if self.control_password:
            self._control.authenticate(password=self.control_password)
        self._control.add_event_listener(lambda e: self._handle_event(e), EventType.BW)
        self._handler_active = True


if __name__ == "__main__":
    from py3status.module_test import module_test

    config = {"control_password": "SevenOfNine"}
    module_test(Py3status, config)
