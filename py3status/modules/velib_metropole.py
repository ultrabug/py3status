# -*- coding: utf-8 -*-
"""
Display velib available to a station.

Configuration parameters:
    button_next: Display next station (default 3)
    button_previous: Display previous station (default 1)
    button_refresh: refresh stations (default 2)
    cache_timeout: The time between API polling in seconds
        It is recommended to keep this at a higher value to avoid rate
        limiting with the API's. (default 60)
    format: How to display the velib data.
        (default 'Velib Metropole: {index}/{stations} {format_station}')
    format_station: How to display the velib station data.
        (default '{station_name}: [\\?color=station_state_code {station_state}]')
    station_codes: List of velib station to monitor.
        You can get stations id on map here:
        https://www.velib-metropole.fr/map  (default [20043, 11014, 20012, 20014, 10042])
    thresholds: Configure colors of format station.
        (default {'station_state_code': [(0, 'good'), (1, 'bad')]})
"""
from datetime import datetime
from re import sub

STRING_MISSING_STATIONS = "No velib stations set"


class Py3status:
    """
    """

    # available configuration parameters
    button_next = 3
    button_previous = 1
    button_refresh = 2
    cache_timeout = 60
    format = u"Velib Metropole: {index}/{stations} {format_station}"
    format_station = u"{station_name}: [\?color=station_state_code {station_state}]"
    format_station += "[\?soft  ][\?color=greenyellow {nb_bike}/{nb_free_e_dock}]"
    format_station += "[\?soft  ][\?color=deepskyblue {nb_ebike}/{nb_free_e_dock}]"
    station_codes = [20043, 11014, 20012, 20014, 10042]
    thresholds = {"station_state_code": [(0, "good"), (1, "bad")]}

    class Meta:
        update_config = {
            "update_placeholder_format": [
                {
                    "placeholder_formats": {
                        "density_level": ":.0f",
                        "max_bike_overflow": ":.0f",
                        "nb_bike": ":.0f",
                        "nb_bike_overflow": ":.0f",
                        "nb_dock": ":.0f",
                        "nb_e_bike_overflow": ":.0f",
                        "nb_e_dock": ":.0f",
                        "nb_ebike": ":.0f",
                        "nb_free_dock": ":.0f",
                        "nb_free_e_dock": ":.0f",
                        "station_gps_latitude": ":.3f",
                        "station_gps_longitude": ".3f",
                        "station_due_date": ".0f",
                    },
                    "format_strings": ["format_station"],
                }
            ]
        }

    def post_config_hook(self):
        if not self.station_codes:
            raise Exception("%s" % (STRING_MISSING_STATIONS))

        self.request_timeout = 10

        # take the whole map for first run
        # zone is shrinked later
        self.gps_top_right_latitude = 49.0
        self.gps_top_right_longitude = 2.5
        self.gps_bot_left_latitude = 48.6
        self.gps_bot_left_longitude = 2.2
        self.gps_zoom_level = 15

        self.station_states = {"Operative": 0, "Close": 1}

        json = self._get_velib_data()
        if json:
            self.number_of_stations, self.stations = self._manipulate(json)
            self._get_usefull_area(self.stations)

        # get placeholders
        self.placeholders = []
        for x in ["format", "format_station"]:
            self.placeholders.append(self.py3.get_placeholders_list(x))

        self.refresh = True
        self.station_index = 1

    def _camel_to_snake_case(self, data):
        if not isinstance(data, (int, float)):
            s1 = sub("(.)([A-Z][a-z]+)", r"\1_\2", data)
            return sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()
        else:
            return data

    def _cast_number(self, value):
        try:
            value = float(value)
        except ValueError:
            try:
                value = int(value)
            except ValueError:
                pass
        return value

    def _get_usefull_area(self, data):
        """
        reduce the zone to reduce the size of fetched data on refresh
        """

        latitudes = []
        longitudes = []
        for x in data:
            latitudes.append(float(data[x]["station_gps_latitude"]))
            longitudes.append(float(data[x]["station_gps_longitude"]))
        self.gps_top_right_latitude = max(latitudes)
        self.gps_top_right_longitude = max(longitudes)
        self.gps_bot_left_latitude = min(latitudes)
        self.gps_bot_left_longitude = min(longitudes)

    def _get_velib_data(self):
        url = "".join(
            [
                "https://www.velib-metropole.fr/webapi/map/details?",
                "gpsTopLatitude=%s",
                "&gpsTopLongitude=%s",
                "&gpsBotLatitude=%s",
                "&gpsBotLongitude=%s",
                "&zoomLevel=%s",
            ]
        )
        url = url % (
            self.gps_top_right_latitude,
            self.gps_top_right_longitude,
            self.gps_bot_left_latitude,
            self.gps_bot_left_longitude,
            self.gps_zoom_level,
        )

        try:
            return self.py3.request(url, timeout=self.request_timeout).json()
        except self.py3.RequestException:
            return None

    def _manipulate(self, data):
        index = 1
        stations = {}

        for code in self.station_codes:
            new_station = {}

            # search station
            station = next(
                (item for item in data if int(item["station"]["code"]) == int(code)),
                None,
            )

            # flat, camel to snake and cast...
            for k, v in self.py3.flatten_dict(station, delimiter="_").items():
                new_station[self._camel_to_snake_case(k)] = self._cast_number(v)

            # station_due_date_s: station due date in dateime iso format
            # station_state_code: station code for thresholds
            station_due_date = datetime.fromtimestamp(
                int(new_station["station_due_date"])
            )
            new_station.update(
                {
                    "station_due_date_s": station_due_date.isoformat(),
                    "station_state_code": int(
                        self.station_states[new_station["station_state"]]
                    ),
                }
            )

            stations[index] = new_station
            index += 1

        return len(stations), stations

    def velib_metropole(self):
        if self.refresh is True:
            # get number of stations and station list
            json = self._get_velib_data()
            if json:
                self.number_of_stations, self.stations = self._manipulate(json)

        # reset refresh
        self.refresh = True

        if not self.stations:
            full_text = None
        else:
            # reset station_index counter
            if self.station_index == 0:
                self.station_index = 1

            # thresholds
            for x in self.thresholds:
                if x in self.stations[self.station_index]:
                    self.py3.threshold_get_color(
                        self.stations[self.station_index][x], x
                    )

            # forge data output
            velib_data = {
                "stations": self.number_of_stations,
                "format_station": self.py3.safe_format(
                    self.format_station, self.stations[self.station_index]
                ),
                "index": self.station_index,
            }
            full_text = self.py3.safe_format(self.format, velib_data)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": full_text,
        }

    def on_click(self, event):
        button = event["button"]
        if self.stations:
            if button == self.button_next:
                self.refresh = False
                self.station_index += 1
                self.station_index %= self.number_of_stations + 1
            elif button == self.button_previous:
                self.refresh = False
                self.station_index -= 1
                self.station_index %= self.number_of_stations + 1
        elif button == self.button_refresh:
            self.refresh = True


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
