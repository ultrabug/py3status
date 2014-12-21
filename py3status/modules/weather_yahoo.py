# -*- coding: utf-8 -*-
"""
Display current day + 3 days weather forecast as icons on your i3bar
Based on Yahoo! Weather. forecast, thanks guys !
    http://developer.yahoo.com/weather/

Find your city code using:
    http://answers.yahoo.com/question/index?qid=20091216132708AAf7o0g

The city_code in this example is for Paris, France => FRXX0076
"""

from time import time
import requests


class Py3status:

    # available configuration parameters
    cache_timeout = 1800
    city_code = 'FRXX0076'
    forecast_days = 3
    request_timeout = 10

    def _get_forecast(self):
        """
        Ask Yahoo! Weather. for a forecast
        """
        q = requests.get(
            'http://query.yahooapis.com/v1/public/yql?q=' +
            'select item from weather.forecast ' +
            'where location="%s"&format=json' % self.city_code,
            timeout=self.request_timeout
        )

        r = q.json()
        status = q.status_code
        forecasts = []

        if status == 200:
            forecasts = r['query']['results']['channel']['item']['forecast']
            # reset today
            forecasts[0] = r['query']['results']['channel']['item']['condition']
        else:
            raise Exception('got status {}'.format(status))

        # return current today + forecast_days days forecast
        return forecasts[:self.forecast_days + 1]

    def _get_icon(self, forecast):
        """
        Return an unicode icon based on the forecast code and text
        See: http://developer.yahoo.com/weather/#codes
        """
        icons = ['☀', '☁', '☂', '☃', '?']
        code = int(forecast['code'])
        text = forecast['text'].lower()

        # sun
        if 'sun' in text or code in [31, 32, 33, 34, 36]:
            code = 0

        # cloud / early rain
        elif 'cloud' in text or code in [
                19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30,
                44
                ]:
            code = 1

        # rain
        elif 'rain' in text or code in [
                0, 1, 2, 3, 4, 5, 6, 9,
                11, 12,
                37, 38, 39,
                40, 45, 47
                ]:
            code = 2

        # snow
        elif 'snow' in text or code in [
                7, 8,
                10, 13, 14, 15, 16, 17, 18,
                35,
                41, 42, 43, 46
                ]:
            code = 3

        # dunno
        else:
            code = -1

        return icons[code]

    def weather_yahoo(self, i3s_output_list, i3s_config):
        """
        This method gets executed by py3status
        """
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': ''
        }

        forecasts = self._get_forecast()
        for forecast in forecasts:
            icon = self._get_icon(forecast)
            response['full_text'] += '{} '.format(icon)
        response['full_text'] = response['full_text'].strip()

        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    while True:
        print(x.weather_yahoo([], {}))
        sleep(1)
