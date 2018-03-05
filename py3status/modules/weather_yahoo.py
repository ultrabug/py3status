# -*- coding: utf-8 -*-
"""
Display Yahoo! Weather forecast.

See http://developer.yahoo.com/weather for more information.
Visit http://woeid.rosselliot.co.nz for WOEID, Where On Earth IDentifier.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 7200)
    forecast_days: specifiy number of days to forecast (default 3)
    forecast_today: show today's weather forecast (default False)
    format: display format for this module
        (default '[{format_today} ][{format_forecast}]')
    format_datetime: specify strftime characters to format (default {})
    format_forecast: display format for the forecasts (default '{icon}')
    format_separator: show separator if more than one (default ' ')
    format_today: format for today's forecast (default '{icon}')
    icon_cloud: specify cloud icon to use (default '☁')
    icon_default: specify unknown icon to use (default '?')
    icon_rain: specify rain icon to use (default '☂')
    icon_snow: specify snow icon to use (default '☃')
    icon_sun: specify sun icon to use (default '☀')
    request_timeout: time to wait for a response (default 10)
    retry_timeout: time to retry if request failed (default 60)
    thresholds: specify color thresholds to use (default [])
    unit: specify temperature unit to use: C, F (default 'C')
    woeid: specify Yahoo! WOEID to use, required (default None)

Note:
    The placeholder `{format_today}` will show the current conditions in `format`.
    The config `forecast_today` will show today's forecast in `format_forecast`.

Format placeholders:
    {atmosphere_humidity}   humidity, eg 96
    {atmosphere_pressure}   pressure, eg 1002.0
    {atmosphere_rising}     rising, eg 0
    {atmosphere_sunrise}    sunrise, eg 6:42 am
    {atmosphere_sunset}     sunset, eg 4:48 pm
    {atmosphere_visibility} visibility, eg 9.4
    {format_forecast}       format for weather forecasts
    {format_today}          format for today's current conditions
    {location_city}         location city, eg Chicago
    {location_country}      location country, eg United States
    {location_region}       location region, eg IL
    {units_distance}        unit distance, eg mi
    {units_pressure}        unit pressure, eg in
    {units_speed}           unit speed, eg mph
    {units_temperature}     unit temperature, eg F
    {wind_chill}            wind chill, eg 39
    {wind_direction}        wind direction, eg 20
    {wind_speed}            wind speed, eg 7
    {item_lat}              latitude, eg 41.881832
    {item_long}             longitude, eg -87.623177
    {item_pubDate}          last updated, eg Sun, 12 Nov 2017 10:00 AM CST

format_datetime placeholders:
    key: format_today (date), format_forecast (date), format (item_pubDate)
    value: % strftime characters, eg '%b %d' ----> 'Nov 12'

format_today placeholders:
    {icon} weather icon, eg ☂
    {code} weather code, eg 12',
    {date} date of the day, eg Sun, 12 Nov 2017 12:00 AM CST',
    {temp} current temperature, eg 40
    {text} weather description, eg Rain

format_forecast placeholders:
    {icon} weather icon, eg ☂
    {code} weather code, eg 39
    {text} weather description, eg Scattered Showers
    {date} date for the day, eg 12 Nov 2017
    {day}  day of the week, eg Sun
    {high} high temperature, eg 43
    {low}  low temperature, eg 37
    {unit} temperature unit, eg F

Color thresholds:
    format:
        temp: a color based on current temperature
    format_forecast:
        high: a color based on high temperature
        low: a color based on low temperature

Examples:
```
# show an example
weather_yahoo {
    woeid = 615702  # Paris, France
    format_today = 'Now: {icon}{temp}°{unit} {text}'
    forecast_days = 5
}

# customize date format
weather_yahoo {
    format = '[{format_today} ][{format_forecast}][ {item_pubDate}]'
    format_today = '{date} {icon}'
    format_forecast = '{date} {icon}'
    format_separator = '\?color=bad  - '

    format_datetime = {
        'format_today': '\?color=bad&show %A',
        'format_forecast': '%a %b %d',
        'format': '%-I%P'
    }
}

# simple color-coded temperature
weather_yahoo {
    format_today = '[\?color=temp {icon}] {temp}'
    thresholds = [(-100, '#0FF'), (0, '#00F'), (50, '#0F0'), (150, '#FF0')]
}
```

@author ultrabug, rail, lasers

SAMPLE OUTPUT
{'full_text': u'\u2602 \u2601 \u2601 \u2601'}
"""

from datetime import datetime
DATETIME_FORECAST = '%d %b %Y'
DATETIME_GENERAL = '%a, %d %b %Y %H:%M %p %Z'

URL = 'https://query.yahooapis.com/v1/public/yql?q='
URL += 'select * from weather.forecast where woeid='
URL += '"{woeid}" and u="{unit}"&format=json'
URL += '&env=store://datatables.org/alltableswithkeys'


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 7200
    forecast_days = 3
    forecast_today = False
    format = u'[{format_today} ][{format_forecast}]'
    format_datetime = {}
    format_forecast = u'{icon}'
    format_separator = ' '
    format_today = u'{icon}'
    icon_cloud = u'☁'
    icon_default = u'?'
    icon_rain = u'☂'
    icon_snow = u'☃'
    icon_sun = u'☀'
    request_timeout = 10
    retry_timeout = 60
    thresholds = []
    unit = 'C'
    woeid = None

    def post_config_hook(self):
        if not self.woeid:
            raise Exception('missing woeid')
        self.init_datetime_format = self.py3.format_contains(
            self.format, 'item_pubDate') and 'format' in self.format_datetime
        self.init_datetime_format_today = self.py3.format_contains(
            self.format_today, 'date') and 'format_today' in self.format_datetime
        self.init_datetime_format_forecast = self.py3.format_contains(
            self.format_forecast, 'date') and 'format_forecast' in self.format_datetime
        self.init_datetimes = any([
            self.init_datetime_format,
            self.init_datetime_format_today,
            self.init_datetime_format_forecast])
        self.unit = self.unit.upper()
        self.url = URL.format(woeid=self.woeid, unit=self.unit.lower())
        self.conditions = [
            ('sun', self.icon_sun,  # sun
                [31, 32, 33, 34, 36]),
            ('cloud', self.icon_cloud,  # cloud / early rain
                [19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 44]),
            ('snow', self.icon_snow,  # snow
                [7, 8, 10, 13, 14, 15, 16, 17, 18, 35, 41, 42, 43, 46]),
            ('rain', self.icon_rain,  # rain
                [0, 1, 2, 3, 4, 5, 6, 9, 11, 12, 37, 38, 39, 40, 45, 47]),
        ]

    class Meta:
        deprecated = {
            'rename': [
                {
                    'param': 'forecast_text_separator',
                    'new': 'format_separator',
                    'msg': 'obsolete parameter use `format_separator`',
                },
                {
                    'param': 'forecast_include_today',
                    'new': 'forecast_today',
                    'msg': 'obsolete parameter use `forecast_today`',
                },
                {
                    'param': 'units',
                    'new': 'unit',
                    'msg': 'obsolete parameter use `unit`',
                },
            ],
            'rename_placeholder': [
                {
                    'placeholder': 'forecasts',
                    'new': 'format_forecast',
                    'format_strings': ['format'],
                },
                {
                    'placeholder': 'today',
                    'new': 'format_today',
                    'format_strings': ['format'],
                },
            ],
        }

    def _get_weather_data(self):
        try:
            query = self.py3.request(self.url, timeout=self.request_timeout)
        except self.py3.RequestException:
            return {}
        if query.status_code != 200:
            self.py3.log('HTTP response returned code %s' % query.status_code)
            return {}
        return query.json()

    def _organize(self, data):
        try:
            today = data['query']['results']['channel']['item']['condition']
            forecasts = data['query']['results']['channel']['item']['forecast']
            # skip today?
            if not self.forecast_today:
                forecasts.pop(0)
            # set number of forecast_days
            forecasts = forecasts[:self.forecast_days]
            # add extras
            channel = data['query']['results']['channel']
            channel = self.py3.flatten_dict(channel, delimiter='_')
        except:
            today = {}
            forecasts = {}
            channel = {}
        return today, forecasts, channel

    def _get_icon(self, forecast):
        """
        Return an icon based on the condition code and description
        https://developer.yahoo.com/weather/documentation.html#codes
        """
        code = int(forecast['code'])
        description = forecast['text'].lower()
        for condition in self.conditions:
            if condition[0] in description or code in condition[2]:
                return condition[1]
        return self.icon_default

    def weather_yahoo(self):
        cached_until = self.retry_timeout
        format_forecast = None
        format_today = None
        channel = {}

        weather_data = self._get_weather_data()

        if weather_data:
            new_data = []
            cached_until = self.cache_timeout

            today, forecasts, channel = self._organize(weather_data)

            if self.init_datetimes:
                if self.init_datetime_format:
                    channel['item_pubDate'] = self.py3.safe_format(
                        datetime.strftime(datetime.strptime(
                            channel['item_pubDate'], DATETIME_GENERAL),
                            self.format_datetime['format']))

                if self.init_datetime_format_today:
                    today['date'] = self.py3.safe_format(
                        datetime.strftime(datetime.strptime(
                            today['date'], DATETIME_GENERAL),
                            self.format_datetime['format_today']))

                if self.init_datetime_format_forecast:
                    for forecast in forecasts:
                        forecast['date'] = self.py3.safe_format(
                            datetime.strftime(datetime.strptime(
                                forecast['date'], DATETIME_FORECAST),
                                self.format_datetime['format_forecast']))

            if today:
                if self.thresholds:
                    self.py3.threshold_get_color(today['temp'], 'temp')

                format_today = self.py3.safe_format(
                    self.format_today, dict(
                        icon=self._get_icon(today),
                        unit=self.unit,
                        **today
                    ))

            if forecasts:
                for forecast in forecasts:
                    if self.thresholds:
                        self.py3.threshold_get_color(forecast['high'], 'high')
                        self.py3.threshold_get_color(forecast['low'], 'low')

                    new_data.append(self.py3.safe_format(
                        self.format_forecast, dict(
                            icon=self._get_icon(forecast),
                            unit=self.unit,
                            **forecast
                        )))

            format_separator = self.py3.safe_format(self.format_separator)
            format_forecast = self.py3.composite_join(format_separator, new_data)

        return {
            'cached_until': self.py3.time_in(cached_until),
            'full_text': self.py3.safe_format(
                self.format, dict(
                    format_today=format_today,
                    format_forecast=format_forecast,
                    **channel
                )
            )
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
