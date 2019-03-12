# -*- coding: utf-8 -*-
"""
Display air quality polluting in a given location.

An air quality index (AQI) is a number used by government agencies to communicate
to the public how polluted the air currently is or how polluted it is forecast to
become. As the AQI increases, an increasingly large percentage of the population
is likely to experience increasingly severe adverse health effects. Different
countries have their own air quality indices, corresponding to different national
air quality standards.

Configuration parameters:
    auth_token: Personal token required. See https://aqicn.org/data-platform/token
        for more information. (default 'demo')
    cache_timeout: refresh interval for this module. A message from the site:
        The default quota is max 1000 requests per minute (~16RPS) and with
        burst up to 60 requests. See https://aqicn.org/api/ for more information.
        (default 3600)
    format: display format for this module
        (default '[\?color=aqi {city_name}: {aqi} {category}]')
    format_datetime: specify strftime characters to format (default {})
    location: location or uid to query. To search for nearby stations in Kraków,
        try `https://api.waqi.info/search/?token=YOUR_TOKEN&keyword=kraków`
        For best results, use uid instead of name in location, eg `@8691`.
        (default 'Shanghai')
    quality_thresholds: specify a list of tuples, eg (number, 'color', 'name')
        *(default [(0, '#009966', 'Good'),
            (51, '#FFDE33', 'Moderate'),
            (101, '#FF9933', 'Sensitively Unhealthy'),
            (151, '#CC0033', 'Unhealthy'),
            (201, '#660099', 'Very Unhealthy'),
            (301, '#7E0023', 'Hazardous')])*
    thresholds: specify color thresholds to use (default {'aqi': True})

Notes:
    Your station may have individual scores for pollutants not listed below.
    See https://api.waqi.info/feed/@UID/?token=TOKEN (Replace UID and TOKEN)
    for a full list of placeholders to use.

Format placeholders:
    {aqi} air quality index
    {attributions_0_name} attribution name, there maybe more, change the 0
    {attributions_0_url} attribution url, there maybe more, change the 0
    {category} health risk category, eg Good, Moderate, Unhealthy, etc
    {city_geo_0} monitoring station latitude
    {city_geo_1} monitoring station longitude
    {city_name} monitoring station name
    {city_url} monitoring station url
    {dominentpol} dominant pollutant, eg pm25
    {idx} Unique ID for the city monitoring station, eg 7396
    {time} epoch timestamp, eg 1510246800
    {time_s} local timestamp, eg 2017-11-09 17:00:00
    {time_tz} local timezone, eg -06:00
    {iaqi_co}   individual score for pollutant carbon monoxide
    {iaqi_h}    individual score for pollutant h (?)
    {iaqi_no2}  individual score for pollutant nitrogen dioxide
    {iaqi_o3}   individual score for pollutant ozone
    {iaqi_pm25} individual score for pollutant particulates
                smaller than 2.5 μm in aerodynamic diameter
    {iaqi_pm10} individual score for pollutant particulates
                smaller than 10 μm in aerodynamic diameter
    {iaqi_pm15} individual score for pollutant particulates
                smaller than than 15 μm in aerodynamic diameter
    {iaqi_p}    individual score for pollutant particulates
    {iaqi_so2}  individual score for pollutant sulfur dioxide
    {iaqi_t}    individual score for pollutant t (?)
    {iaqi_w}    individual score for pollutant w (?)

    AQI denotes an air quality index. IQAI denotes an individual AQI score.
    Try https://en.wikipedia.org/wiki/Air_pollution#Pollutants for more
    information on the pollutants retrieved from your monitoring station.

format_datetime placeholders:
    key: epoch_placeholder, eg time, vtime
    value: % strftime characters to be translated, eg '%b %d' ----> 'Nov 11'

Color options:
    color_bad: print a color for error (if any) from the site

Color thresholds:
    xxx: print a color based on the value of `xxx` placeholder

Examples:
```
# show last updated time
air_quality {
    format = '{city_name}: {aqi} {category} - {time}'
    format_datetime = {'time': '%-I%P'}
}
```

@author beetleman, lasers
@license BSD

SAMPLE OUTPUT
{'color':'#009966', 'full_text':'Shanghai: 49 Good'}

aqi_moderate
{'color':'#FFDE33', 'full_text':'Shanghai: 65 Moderate'}

aqi_sensitively_unhealthy
{'color':'#FF9933', 'full_text':'Shanghai: 103 Sensitively Unhealthy'}

aqi_unhealthy
{'color':'#CC0033', 'full_text':'Shanghai: 165 Unhealthy'}

aqi_very_unhealthy
{'color':'#660099', 'full_text':'Shanghai: 220 Very Unhealthy'}

aqi_hazardous
{'color':'#7E0023', 'full_text':'Shanghai: 301 Hazardous'}
"""

from datetime import datetime


class Py3status:
    """
    """

    # available configuration parameters
    auth_token = "demo"
    cache_timeout = 3600
    format = "[\?color=aqi {city_name}: {aqi} {category}]"
    format_datetime = {}
    location = "Shanghai"
    quality_thresholds = [
        (0, "#009966", "Good"),
        (51, "#FFDE33", "Moderate"),
        (101, "#FF9933", "Sensitively Unhealthy"),
        (151, "#CC0033", "Unhealthy"),
        (201, "#660099", "Very Unhealthy"),
        (301, "#7E0023", "Hazardous"),
    ]
    thresholds = {"aqi": True}

    def post_config_hook(self):
        self.auth_token = {"token": self.auth_token}
        self.url = "https://api.waqi.info/feed/%s/" % self.location
        self.init_datetimes = []
        for word in self.format_datetime:
            if (self.py3.format_contains(self.format, word)) and (
                word in self.format_datetime
            ):
                self.init_datetimes.append(word)

        if isinstance(self.thresholds, dict):
            if self.thresholds.get("aqi") is True:
                aqi = [(x[0], x[1]) for x in self.quality_thresholds]
                self.thresholds["aqi"] = aqi

        self.thresholds_init = self.py3.get_color_names_list(self.format)

    def _get_aqi_data(self):
        try:
            return self.py3.request(self.url, params=self.auth_token).json()
        except self.py3.RequestException:
            return None

    def _organize(self, data):
        new_data = {}
        for k, v in self.py3.flatten_dict(data, delimiter="_").items():
            new_data["".join(k.replace("data_", "", 1).rsplit("_v", 1))] = v
        return new_data

    def _manipulate(self, data):
        for index_aqi, index_color, index_category in self.quality_thresholds:
            if data["aqi"] >= index_aqi:
                data["category"] = index_category

        for x in self.thresholds_init:
            if x in data:
                self.py3.threshold_get_color(data[x], x)

        for k in self.init_datetimes:
            if k in data:
                data[k] = self.py3.safe_format(
                    datetime.strftime(
                        datetime.fromtimestamp(data[k]), self.format_datetime[k]
                    )
                )
        return data

    def air_quality(self):
        aqi_data = self._get_aqi_data()
        if aqi_data:
            if aqi_data.get("status") == "ok":
                aqi_data = self._organize(aqi_data)
                aqi_data = self._manipulate(aqi_data)
            elif aqi_data.get("status") == "error":
                self.py3.error(aqi_data.get("data"))

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, aqi_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
