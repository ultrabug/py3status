# -*- coding: utf-8 -*-
"""
Display Yahoo! Weather forecast as icons.

Based on Yahoo! Weather. forecast, thanks guys !
    http://developer.yahoo.com/weather/

Find your city code using:
    http://answers.yahoo.com/question/index?qid=20091216132708AAf7o0g

Find your woeid using:
    http://woeid.rosselliot.co.nz/

Configuration parameters:
    - cache_timeout : how often to check for new forecasts
    - city_code : city code to use
    - woeid : use Yahoo woeid (extended location) instead of city_code
    - forecast_days : how many forecast days you want shown
    - request_timeout : check timeout
    - units : Celsius (C) of Fahrenheit (F)
    - today_format : possibple placeholders: {icon}, {temp}, {units}, {text}
        example:
            format = "Now: {icon}{temp}{units}° {text}"
        output:
            Now: ☂-4C° Light Rain/Windy
    - forecast_format : possibple placeholders: {icon}, {low}, {high}, {units},
        {text}
    - forecast_include_today: show today forecast as well, default false
    - icon_sun: sun icon, default '☀'
    - icon_cloud: cloud icon, default '☁'
    - icon_rain: rain icon, default '☂'
    - icon_snow: snow icon, default '☃'
    - icon_default: unknown weather icon, default '?'

The city_code in this example is for Paris, France => FRXX0076
"""

from time import time
import requests


class Py3status:

    # available configuration parameters
    cache_timeout = 1800
    city_code = 'FRXX0076'
    woeid = None
    forecast_days = 3
    request_timeout = 10
    units = 'c'
    today_format = '{icon}{temp}{units} '
    forecast_format = '{icon} '
    forecast_include_today = False
    icon_sun = '☀'
    icon_cloud = '☁'
    icon_rain = '☂'
    icon_snow = '☃'
    icon_default = '?'

    def _get_forecast(self):
        """
        Ask Yahoo! Weather. for a forecast
        """
        where = 'location="%s"' % self.city_code
        if self.woeid:
            where = 'woeid="%s"' % self.woeid
        q = requests.get(
            'http://query.yahooapis.com/v1/public/yql?q=' +
            'select * from weather.forecast ' +
            'where {where} and u="{units}"&format=json'.format(
                where=where, units=self.units.lower()[0]),
            timeout=self.request_timeout
        )
        q.raise_for_status()
        r = q.json()
        today = r['query']['results']['channel']['item']['condition']
        forecasts = r['query']['results']['channel']['item']['forecast']
        if not self.forecast_include_today:
            # Do not include today in forecasts
            forecasts.pop(0)
        # limit to forecast_days
        forecasts = forecasts[:self.forecast_days]
        # return current today + forecast_days days forecast
        return today, forecasts

    def _get_icon(self, forecast):
        """
        Return an unicode icon based on the forecast code and text
        See: http://developer.yahoo.com/weather/#codes
        """
        code = int(forecast['code'])
        text = forecast['text'].lower()

        # sun
        if 'sun' in text or code in [31, 32, 33, 34, 36]:
            return self.icon_sun

        # cloud / early rain
        if 'cloud' in text or code in [
                19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
                44
                ]:
            return self.icon_cloud

        # rain
        if 'rain' in text or code in [
                0, 1, 2, 3, 4, 5, 6, 9,
                11, 12,
                37, 38, 39,
                40, 45, 47
                ]:
            return self.icon_rain

        # snow
        if 'snow' in text or code in [
                7, 8,
                10, 13, 14, 15, 16, 17, 18,
                35,
                41, 42, 43, 46
                ]:
            return self.icon_snow

        return self.icon_default

    def weather_yahoo(self, i3s_output_list, i3s_config):
        """
        This method gets executed by py3status
        """
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': ''
        }

        today, forecasts = self._get_forecast()
        response['full_text'] = self.today_format.format(
            icon=self._get_icon(today), units=self.units.upper()[0], **today)
        for forecast in forecasts:
            response['full_text'] += self.forecast_format.format(
                icon=self._get_icon(forecast), units=self.units.upper()[0],
                **forecast)

        response['full_text'] = response['full_text'].strip()
        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_good': '#00FF00',
        'color_bad': '#FF0000',
    }
    while True:
        print(x.weather_yahoo([], config))
        sleep(1)
