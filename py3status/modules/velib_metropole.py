# -*- coding: utf-8 -*-
"""
Display velib available to a station.
# https://velib-metropole-opendata.smoove.pro/opendata/Velib_Metropole/station_status.json
# curl 'https://www.velib-metropole.fr/webapi/map/details?gpsTopLatitude=48.85170875805659&gpsTopLongitude=2.3991161073518583&gpsBotLatitude=48.85146608086396&gpsBotLongitude=2.397838705306725&zoomLevel=20' | jq .
"""
from datetime import datetime
from re import sub


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 60
    # format = '[\?color=aqi {city_name}: {aqi} {category}]'
    format = u"{station_name}: {station_state} free: {nb_bike}/{nb_dock}"
    gps_top_latitude = "48.8517"
    gps_top_longitude = "2.399"
    # gps_top_latitude = "48.87429034098611"
    # gps_top_longitude = "2.3535048444482243"
    gps_bot_latitude = str(float(gps_top_latitude) - 0.0003)
    gps_bot_longitude = str(float(gps_top_longitude) - 0.002)
    # gps_bot_latitude = "48.8514"
    # gps_bot_longitude = "2.397"
    station_code = "20043"

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
                    },
                    "format_strings": ["format"],
                }
            ]
        }

    def post_config_hook(self):
        self.request_timeout = 30
        self.url = (
            "https://www.velib-metropole.fr/webapi/map/details?gpsTopLatitude=%s&gpsTopLongitude=%s&gpsBotLatitude=%s&gpsBotLongitude=%s&zoomLevel=%s"
            % (
                self.gps_top_latitude,
                self.gps_top_longitude,
                self.gps_bot_latitude,
                self.gps_bot_longitude,
                20,
            )
        )
        self.py3.log(self.url)
        self.placeholders = self.py3.get_placeholders_list(self.format)
        self.velib_data = {}

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

    def _get_velib_data(self):
        try:
            return self.py3.request(self.url, timeout=self.request_timeout).json()
        except self.py3.RequestException:
            return None

    def _manipulate(self, data):
        # flat data
        # convert key from camel to snake case
        new_data = {}
        for k, v in self.py3.flatten_dict(data, delimiter="_").items():
            new_data[self._camel_to_snake_case("".join(k.replace("0_", "", 1)))] = v
        return new_data

    def velib_metropole(self):
        self.velib_data = self._get_velib_data()
        # for k,v in self.velib_data:
        #     if self.velib_data[k] == "stationCode":
        #         if v == self.station_code:
        #             self.py3.log('pinnnng: k + %s, v: %s'.format(k, v))

        self.velib_data = self._manipulate(self.velib_data)
        if self.velib_data:
            self.velib_data = self._manipulate(self.velib_data)
            self.velib_data.update(
                {k: self._cast_number(self.velib_data[k]) for k in self.placeholders}
            )
            
        self.py3.log(self.velib_data)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, self.velib_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
    #    {'credit_card': 'yes',
    # 'density_level': 1,
    # 'kiosk_state': 'yes',
    # 'max_bike_overflow': 27,
    # 'nb_bike': 12,
    # 'nb_bike_overflow': 0,
    # 'nb_dock': 27,
    # 'nb_e_bike_overflow': 0,
    # 'nb_e_dock': 0,
    # 'nb_ebike': 1,
    # 'nb_free_dock': 14,
    # 'nb_free_e_dock': 0,
    # 'overflow': 'no',
    # 'overflow_activation': 'no',
    # 'station_code': '20043',
    # 'station_due_date': 1529013600,
    # 'station_gps_latitude': 48.85160266522164,
    # 'station_gps_longitude': 2.398403047037931,
    # 'station_name': 'Charonne - Avron',
    # 'station_state': 'Close',
    # 'station_type': 'no'}
