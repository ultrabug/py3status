# -*- coding: utf-8 -*-
"""
Display information about Velib Métropole stations.

Vélib' Métropole, https://en.wikipedia.org/wiki/Vélib'_Métropole, is a large-
scale public bicycle sharing system in Paris, France and surrounding cities.

Configuration parameters:
    button_next: mouse button to display next station (default 4)
    button_previous: mouse button to display previous station (default 5)
    cache_timeout: refresh interval for this module (default 60)
    format: display format for this module
        (default '{format_station}|No Velib')
    format_station: display format for stations
        *(default "{name} [\?if=state=Closed&color=state {state} ]"
        "[\?color=greenyellow {bike}/{free_dock} ]"
        "[\?color=deepskyblue {ebike}/{free_edock}]")*
    stations: specify a list of station codes to use, find your
        station code at https://www.velib-metropole.fr/map
        (default [20043, 11014, 20012, 20014, 10042])
    thresholds: specify color thresholds to use
        (default [("Operative", "good"), ("Closed", "bad")])

Format placeholders:
    {format_station}      format for stations
    {station}             total number of stations, eg 12

format_station placeholders:
    {index}               index number, eg 1
    {bike}                number of available bike, eg 3
    {bike_overflow}       number of bike in overflow, eg 0
    {code}                code, eg 10042
    {credit_card}         credit card, eg no, yes
    {density_level}       density level, eg 1
    {dock}                number of dock, eg 0
    {due_date}            due date, eg 1527717600
    {ebike}               number of electric bike, eg 0
    {ebike_overflow}      overflow bike, eg 0
    {edock}               number of electric dock, eg 33
    {free_dock}           available bike places, eg 0
    {free_edock}          available electric bike places, eg 30
    {kiosk_state}         kiosk in working, eg no, yes
    {latitude}            latitude, eg 48.87242006305313
    {longitude}           longitude, eg 2.348395236282807
    {max_bike_overflow}   max overflow bike, eg 33
    {name}                name, eg Enghien - Faubourg Poissonnière
    {overflow}            support overflow, eg no, yes
    {overflow_activation} state of overflow support, eg no, yes
    {state}               state, eg Closed, Operative
    {type}                type, eg no, yes

Color thresholds:
    format:
        xxx: print a color based on the value of `xxx` placeholder
    format_station:
        xxx: print a color based on the value of `xxx` placeholder

@author Cyril Levis (@cyrinux)

SAMPLE OUTPUT
[
    {'full_text': 'Charonne - Avron '},
    {'full_text': '10/0 ', 'color': '#adff2f'},
    {'full_text': '0/0 ', 'color': '#00bfff'},
    {'full_text': '1/5'}
]

second
[
    {'full_text': 'Buzenval - Vignoles '},
    {'full_text': 'Closed ', 'color': '#ff0000'},
    {'full_text': '13/1 ', 'color': '#adff2f'},
    {'full_text': '3/1 ', 'color': '#00bfff'},
    {'full_text': '2/5'}
]

no_velib
{'full_text': 'No Velib'}
"""

from re import sub
from time import time

STRING_MISSING_STATIONS = "missing stations"
VELIB_ENDPOINT = "https://www.velib-metropole.fr/webapi/map/details"


class Py3status:
    """
    """

    # available configuration parameters
    button_next = 4
    button_previous = 5
    cache_timeout = 60
    format = "{format_station}|No Velib"
    format_station = (
        "{name} [\?if=state=Closed&color=state {state} ]"
        "[\?color=greenyellow {bike}/{free_dock} ]"
        "[\?color=deepskyblue {ebike}/{free_edock}]"
    )
    stations = [20043, 11014, 20012, 20014, 10042]
    thresholds = [("Operative", "good"), ("Closed", "bad")]

    class Meta:
        update_config = {
            "update_placeholder_format": [
                {
                    "placeholder_formats": {
                        "bike": ":.0f",
                        "bike_overflow": ":.0f",
                        "density_level": ":.0f",
                        "dock": ":.0f",
                        "due_date": ".0f",
                        "ebike": ":.0f",
                        "ebike_overflow": ":.0f",
                        "edock": ":.0f",
                        "free_dock": ":.0f",
                        "free_edock": ":.0f",
                        "latitude": ":.3f",
                        "longitude": ".3f",
                        "max_bike_overflow": ":.0f",
                    },
                    "format_strings": ["format_station"],
                }
            ]
        }

    def post_config_hook(self):
        if not self.stations:
            raise Exception(STRING_MISSING_STATIONS)

        if not isinstance(self.stations, list):
            self.stations = [self.stations]
        self.station_codes = [format(x) for x in self.stations]

        self.empty_defaults = {
            x: "" for x in self.py3.get_placeholders_list(self.format)
        }
        self.gps = {
            "gpsTopLatitude": 49.0,
            "gpsTopLongitude": 2.5,
            "gpsBotLatitude": 48.6,
            "gpsBotLongitude": 2.2,
            "zoomLevel": 15,
        }
        self.active_index = 0
        self.button_refresh = 2
        self.cache_station_keys = {}
        self.first_request = True
        self.idle_time = 0
        self.scrolling = False
        self.station_data = {}

        self.thresholds_init = {}
        for name in ["format", "format_station"]:
            self.thresholds_init[name] = self.py3.get_color_names_list(
                getattr(self, name)
            )

    def _set_optimal_area(self, data):
        """
        Reduce the zone to reduce the size of fetched data on refresh
        """
        lats = [station["latitude"] for station in data.values()]
        longs = [station["longitude"] for station in data.values()]
        self.gps.update(
            {
                "gpsTopLatitude": max(lats),
                "gpsTopLongitude": max(longs),
                "gpsBotLatitude": min(lats),
                "gpsBotLongitude": min(longs),
            }
        )

    def _get_velib_data(self):
        try:
            return self.py3.request(VELIB_ENDPOINT, params=self.gps).json()
        except self.py3.RequestException:
            return None

    def _manipulate(self, data):
        new_data = {}
        index = 0

        for code in self.station_codes:
            for station in data:
                if station["station"]["code"] == code:
                    temporary = station.copy()
                    break
            else:
                continue

            for x in ["station", "gps"]:
                temporary.update(temporary.pop(x, {}))
            temporary = self.py3.flatten_dict(temporary, delimiter="_")

            station = {"index": index + 1}
            for original, value in temporary.items():
                try:
                    new_key = self.cache_station_keys[original]
                except KeyError:
                    # camel to snake_case
                    key = sub("(.)([A-Z][a-z]+)", r"\1_\2", original)
                    key = sub("([a-z0-9])([A-Z])", r"\1_\2", key).lower()
                    # change some keys
                    if key.startswith("nb_"):
                        key = key[3:]
                    if key.startswith("e_"):
                        key = key[0] + key[2:]
                    if "_e_" in key:
                        key = key.replace("_e_", "_e")
                    self.cache_station_keys[original] = new_key = key
                station[new_key] = value

            for x in self.thresholds_init["format_station"]:
                if x in temporary:
                    self.py3.threshold_get_color(station[x], x)

            new_data[index] = station
            index += 1

        return new_data

    def velib_metropole(self):
        # refresh
        current_time = time()
        refresh = current_time >= self.idle_time

        # time
        if refresh:
            self.idle_time = current_time + self.cache_timeout
            cached_until = self.cache_timeout
        else:
            cached_until = self.idle_time - current_time

        # button
        if self.scrolling and not refresh:
            self.scrolling = False
            data = self.station_data
        else:
            data = self._manipulate(self._get_velib_data() or {})
            self.station_data = data

            if self.first_request and data:
                self.first_request = False
                self._set_optimal_area(data)

        if data:
            self.count_stations = len(data)
            station = data[self.active_index]
            format_station = self.py3.safe_format(self.format_station, station)

            velib_data = {
                "format_station": format_station,
                "station": self.count_stations,
            }

            for x in self.thresholds_init["format"]:
                if x in velib_data:
                    self.py3.threshold_get_color(velib_data[x], x)
        else:
            velib_data = self.empty_defaults

        return {
            "cached_until": self.py3.time_in(cached_until),
            "full_text": self.py3.safe_format(self.format, velib_data),
        }

    def on_click(self, event):
        button = event["button"]
        if button in [self.button_next, self.button_previous]:
            if self.station_data:
                self.scrolling = True
                if button == self.button_next:
                    self.active_index += 1
                elif button == self.button_previous:
                    self.active_index -= 1
                self.active_index %= self.count_stations
            else:
                self.py3.prevent_refresh()
        elif button == self.button_refresh:
            self.idle_time = 0
        else:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
