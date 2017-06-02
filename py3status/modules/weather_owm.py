# -*- coding: utf-8 -*-
'''
Ultimately customizable weather module based on the IP-API Geolocation API
(http://ip-api.com) and the OpenWeatherMap API (https://openweathermap.org).

Requires an API key for OpenWeatherMap (OWM), but the free tier allows you
enough requests/sec to get accurate weather even up to the second.

This module allows you to specify an icon for nearly every weather scenario
imaginable. The default configuration options lump many of the icons into
a few groups, and due to the limitations of UTF-8, this is really as expressive
as it gets.

I would highly suggest you install an additional font, such as the incredible
(and free!) Weather Icons font (https://erikflowers.github.io/weather-icons),
which has icons for most weather scenarios.

For more information, see the documentation
(https://openweathermap.org/weather-conditions) on what weather conditions are
supported. See the configuration options for how to specify each weather icon.

Configuration parameters:
    api_key: Your OpenWeatherMap API key.
        See https://openweathermap.org/appid
        (default None)
    cache_timeout: The time between weather polling in seconds
        It is recommended to keep this at a higher value to avoid rate
        limiting with the API's.
        (default 600)
    format_forecast: Formatting for future forecasts
        Available placeholders:
            See 'format'
        This is similar to the 'format' field, but contains information
        for future weather
        (default '{icon}')
    forecast_days: Number of days to include in the forecast, including today
        (regardless of the 'forecast_include_today' flag)
        (default 0)
    forecast_text_separator: Separator between entries in the forecast
        (default ' ')
    forecast_include_today: Include today in the forecast? (Boolean)
        (default False)
    format: How to display the weather. This also dictates the type of
        forecast. The placeholders here refer to the format_[...] variables
        found below.
        Available placeholders:
            icon, clouds, rain, snow, wind, humidity, pressure, temp, sunrise,
            sunset, desc, desc_long, forecast
        You may also use the icons in the icon dictionary with their identifiers
        (default '{icon}: {temp}')
    format_clouds: Formatting for cloud coverage (percentage).
        Available placeholders:
            icon, coverage
        (default '{icon}: {coverage}%')
    format_humidity: Formatting for humidity (percentage)
        Available placeholders:
            icon, humid
        (default '{icon}: {humid}%')
    format_pressure: Formatting for atmospheric pressure
        Available placeholders:
            icon, press, sea_level
        (default '{icon}: {press} hPa')
    format_rain: Formatting for rain volume over the past 3 hours
        Available placeholders:
            icon, mm, cm, m, in, ft, yrd
        (default '{icon}: {in} inches')
    format_snow: Formatting for snow volume over the past 3 hours
        Available placeholders:
            icon, mm, cm, m, in, ft, yrd
        (default '{icon}: {in} inches')
    format_sunrise: Formatting for sunrise time.
        Note that this format accepts strftime/strptime placeholders to populate
        the output with the time information.
        Available placeholders:
            icon
        (default '{icon}: %X')
    format_sunset: Formatting for sunset time.
        This format accepts strftime/strptime placeholders to populate the
        output with the time information.
        Available placeholders:
            icon
        (default '{icon}: %X')
    format_temp: Formatting for temperature
        Available placeholders:
            icon, c, c_min, c_max, f, f_min, f_max, k, k_min, k_max
        (default '{icon}: {f}°')
    format_wind: Formatting for wind degree and speed
        Available placeholders:
            icon, deg, msec_speed, kmh_speed, fsec_speed, mph_speed,
            msec_gust, kmh_gust, fsec_gust, mph_gust
        (default '{icon}: {mph_speed} mph')
    icon_atmosphere: Icon for atmospheric conditions, like fog, smog, etc.
        (default '🌫')
    icon_breeze: Icon for wind or breeze
        (default '☴')
    icon_cloud: Icon for clouds
        (default '☁')
    icon_extreme: Icon for extreme weather
        (default '⚠')
    icon_rain: Icon for rain
        (default '🌧')
    icon_snow: Icon for snow
        (default '❄')
    icon_sun: Icon for sunshine
        (default '☼')
    icon_humidity: Icon for humidity
        (default '●')
    icon_pressure: Icon for pressure
        (default '◌')
    icon_temp: Icon for temperature
        (default '○')
    icon_thunderstorm: Icon for thunderstorms
        (default '⛈')
    icons: A dictionary relating weather code to icon.
        See https://openweathermap.org/weather-conditions for a complete list
        of supported icons. This will fall-back to the listed icon if there is
        no specific icon present.
        There are multiple ways to specify individual icons based on the id:
            - Use the key 'i601' to reference the condition with id = 601
              (snow)
            - Use the key 'i230_i232' to reference a span of conditions
              inclusive, in this case conditions (230, 231, 232) (thunderstorm
              with drizzle)
        Also, you can specify the icons for the various formatting sections
        below. For example, to specify the icon for 'format_pressure', use
        'pressure'. A few formatting sections will take from the defaults or be
        dynamic, including
            - clouds
            - rain
            - wind
            - sunrise
            - sunset
        These may be specified regardless.
        (default None)
    lang: An ISO 639-1 code for your language (two letters)
        (default 'en')
    request_timeout: The timeout in seconds for contacting the IP API.
        (default 10)

Format Placeholders:
 - All:
   - {icon}: The icon associated with a formatting section
 - format_cloud:
   - {coverage}: Cloud coverage percentage.
 - format_humidity:
   - {humid}: The humidity percentage
 - format_pressure:
   - {press}: The measurement of current atmospheric pressure in Pascals
   - {sea_level}: The measurement of current atmospheric pressure at
     sea-level in Pascals.
 - format_rain:
   - {cm}: Measurement in centimeters.
   - {ft}: Measurement in feet.
   - {in}: Measurement in inches.
   - {mm}: Measurement in millimeters.
   - {m}: Measurement in meters.
   - {yrd}: Measurement in yards.
 - format_snow:
   - {cm}: Measurement in centimeters.
   - {ft}: Measurement in feet.
   - {in}: Measurement in inches.
   - {mm}: Measurement in millimeters.
   - {m}: Measurement in meters.
   - {yrd}: Measurement in yards.
 - format_temp:
   - {c_max}: The maximum Celsius temperature.
   - {c_min}: The minimum Celsius temperature.
   - {c}: Current Celsius temperature reading.
   - {f_max}: The maximum Fahrenheit temperature.
   - {f_min}: The minimum Fahrenheit temperature.
   - {f}: Current Fahrenheit temperature reading.
   - {k_max}: The maximum Kelvin temperature.
   - {k_min}: The minimum Kelvin temperature.
   - {k}: Current Kelvin temperature reading.
 - format_wind:
   - {deg}: Current wind speed heading (in degrees)
   - {fsec_gust}: The speed in ft/sec of current wind gusts.
   - {fsec_speed}: The speed in ft/sec of current wind speeds.
   - {kmh_gust}: The speed in km/hr of current wind gusts.
   - {kmh_speed}: The speed in km/hr of current wind speeds.
   - {mph_gust}: The speed in mph of current wind gusts.
   - {mph_speed}: The speed in mph of current wind speeds.
   - {msec_gust}: The speed in m/sec of current wind gusts.
   - {msec_speed}: The speed in m/sec of current wind speeds.
 - format only:
   - {forecast}: Contains the formatted result of format_forecast.
 - format, format_forecast:
   - {clouds}: Contains the formatted result of format_clouds.
   - {desc_long}: Natural description of the current weather.
   - {desc}: Short description of the current weather.
   - {humidity}: Contains the formatted result of format_humidity.
   - {pressure}: Contains the formatted result of format_pressure.
   - {snow}: Contains the formatted result of format_snow.
   - {sunrise}: Contains the formatted result of format_sunrise.
   - {sunset}: Contains the formatted result of format_sunset.
   - {temp}: Contains the formatted result of format_temp.
   - {wind}: Contains the formatted result of format_wind.


Example configuration:
```
weather_owm {
  api_key = '...'

  icons {
    i200 = "☔"
    i230_i232 = "🌧"

    clouds = "☁"
  }

  format = '{icon}: {temp}, {forecast}'
  forecast_days = 3
}
```
Outputs: 🌫: ○: 59°, ⛅ ☼ 🌧`
- Currently foggy, 59° F outside, with forecast of cloudy tomorrow, sunny the
  next day, then rainy


@author alexoneill
@licence MIT
'''

import datetime


class OWMException(Exception): pass


class Py3status:

    api_key = None
    cache_timeout = 600
    forecast_days = 0
    forecast_include_today = False
    forecast_text_separator = ' '
    format = '{icon}: {temp}'
    format_clouds = '{icon}: {coverage}%'
    format_forecast = '{icon}'
    format_humidity = '{icon}: {humid}%'
    format_pressure = '{icon}: {press} hPa'
    format_rain = '{icon}: {in} inches'
    format_snow = '{icon}: {in} inches'
    format_sunrise = '{icon}: %X'
    format_sunset = '{icon}: %X'
    format_temp = u'{icon}: {f}°'
    format_wind = '{icon}: {mph_speed} mph'
    icon_atmosphere = '🌫'
    icon_breeze = '☴'
    icon_cloud = '☁'
    icon_extreme = '⚠'
    icon_rain = '🌧'
    icon_snow = '❄'
    icon_sun = '☼'
    icon_humidity = '●'
    icon_pressure = '◌'
    icon_temp = '○'
    icon_thunderstorm = '⛈'
    icons = None
    lang = 'en'
    request_timeout = 10


    # API information
    OWM_API = '2.5'
    OWM_CURR_ENDPOINT = 'http://api.openweathermap.org/data/%s/weather?' \
        'APPID=%s&lat=%f&lon=%f&lang=%s'
    OWM_FUTURE_ENDPOINT = 'http://api.openweathermap.org/data/%s/forecast?' \
        'APPID=%s&lat=%f&lon=%f&lang=%s&cnt=%%d'

    # Paths of information to extract from JSON
    OWM_WEATHER_ICON = '//weather:0/id'
    OWM_CLOUD_COVER  = '//clouds/all'
    OWM_RAIN         = '//rain'
    OWM_SNOW         = '//snow'
    OWM_WIND         = '//wind'
    OWM_HUMIDITY     = '//main'
    OWM_PRESSURE     = '//main'
    OWM_TEMP         = '//main'
    OWM_SUNRISE      = '//sys/sunrise'
    OWM_SUNSET       = '//sys/sunset'
    OWM_DESC         = '//weather:0/main'
    OWM_DESC_LONG    = '//weather:0/description'

    def _get_icons(self):
        if (self.icons is None):
            self.icons = {}

        # Defaults for weather ranges
        defaults = {
            'i200_i299': self.icon_thunderstorm,
            'i300_i399': self.icon_rain,
            'i500_i599': self.icon_rain,
            'i600_i699': self.icon_snow,
            'i700_i799': self.icon_atmosphere,
            'i800':      self.icon_sun,
            'i801_i809': self.icon_cloud,
            'i900_i909': self.icon_extreme,
            'i950_i959': self.icon_breeze,
            'i960_i999': self.icon_extreme,
        }

        # Default mappings for other icons
        others = {
            'clouds':   802,
            'rain':     501,
            'snow':     601,
            'wind':     954,
            'humidity': self.icon_humidity,
            'pressure': self.icon_pressure,
            'temp':     self.icon_temp,
            'sunrise':  800,
            'sunset':   801,
        }

        # Handling ranges from OpenWeatherMap
        data = {}
        for source in (defaults, self.icons):
            for key in source:
                if (key[0] != 'i' and key not in others):
                    raise Exception('Icon identifier is invalid! (%s)' % key)

                if (key[0] == 'i'):
                    if('_' in key):
                        if (key.count('_i') != 1):
                            raise Exception('Icon range is not properly'
                                            'formatted! (%s)' % key)

                        # Populate each code
                        (start, end) = tuple(map(int, key[1:].split('_i')))
                        for code in range(start, end + 1):
                            data[code] = source[key]

                    else:
                        data[int(key[1:])] = source[key]
                else:
                    data[key] = source[key]

        # Weather icons for formatting sections
        for key in others:
            if (key not in data):
                if (isinstance(others[key], int)):
                    data[key] = data[others[key]]
                else:
                    data[key] = others[key]

        return data

    def post_config_hook(self):
        # Generate our icon array
        self.icons = self._get_icons()

        # Conversion factors
        self.in_from_mm = 0.0393701
        self.ft_from_meter = 3.28084
        self.kmh_from_msec = 0.277778
        self.mph_from_fsec = 1.46667

    def _init(self):
        # Verify the API key
        if (self.api_key is None):
            raise OWMException('API Key for OpenWeatherMap cannot be empty!'
                            ' Go to http://openweathermap.org/appid to'
                            ' get an API Key.')

    def _get_coords(self):
        # Contact the IP API
        url = "http://ip-api.com/json"
        try:
            req = self.py3.request(url, timeout=self.request_timeout)
            data = req.json()
        except (self.py3.RequestException):
            return None
        except (self.py3.RequestURLError):
            return None

        # Extract the data
        try:
            return (data['lat'], data['lon'])
        except (TypeError):
            return None

    def _get_req_url(self, base, coords):
      params = [self.OWM_API, self.api_key] + list(coords) + [self.lang]
      return base % tuple(params)

    def _make_req(self, url):
      req = self.py3.request(url)
      if(req.status_code != 200):
        data = req.json()
        raise OWMException(data['message'])

      return req.json()

    def _jpath(self, data, query, default = None):
      parts = query.strip('/').split('/')
      for part in parts:
        try:
          if(':' in part):
            (part, index) = tuple(part.split(':'))
            data = data[part]
            data = data[int(index)]
          else:
            data = data[part]
        except (KeyError, IndexError, TypeError):
          return default

      return data

    def _get_weather(self, coords):
      url = self._get_req_url(self.OWM_CURR_ENDPOINT, coords)
      return self._make_req(url)

    def _get_forecast(self, coords):
        # Get the next few days
        if (self.forecast_days == 0):
            return []

        # Get raw data
        url = (self._get_req_url(self.OWM_FUTURE_ENDPOINT, coords)
            % (self.forecast_days + 1))
        data = self._make_req(url)

        # Extract forecast
        weathers = data['list']
        return weathers[:-1] if (self.forecast_include_today) else weathers[1:]

    def _get_icon(self, wthr):
        # Lookup the icon from the weather code (default sunny)
        return self.icons[self._jpath(wthr, self.OWM_WEATHER_ICON, 800)]

    def _format_clouds(self, wthr):
        # Format the cloud cover (default clear)
        return self.py3.safe_format(self.format_clouds, {
            'icon': self.icons['clouds'],
            'coverage': self._jpath(wthr, self.OWM_CLOUD_COVER, 0),
        })

    def _format_rain(self, wthr):
        # Format rain fall
        key = '3h'
        rain = self._jpath(wthr, self.OWM_RAIN, dict())
        if(key not in rain):
            rain[key] = 0

        # Data comes as mm
        inches = rain[key] * self.in_from_mm

        # Format the rain fall
        return self.py3.safe_format(self.format_rain, {
            'icon': self.icons['rain'],
            'mm': round(rain[key]),
            'cm': round(rain[key] / 10),
            'm': round(rain[key] / 100),
            'in': round(inches),
            'ft': round(inches / 12),
            'yrd': round(inches / 36),
        })

    def _format_snow(self, wthr):
        # Format snow fall
        key = '3h'
        snow = self._jpath(wthr, self.OWM_SNOW)
        if(key not in snow):
            snow[key] = 0

        # Data comes as mm
        inches = snow[key] * self.in_from_mm

        # Format the snow fall
        return self.py3.safe_format(self.format_snow, {
            'icon': self.icons['snow'],
            'mm': round(snow[key]),
            'cm': round(snow[key] / 10),
            'm': round(snow[key] / 100),
            'in': round(inches),
            'ft': round(inches / 12),
            'yrd': round(inches / 36),
        })

    def _format_wind(self, wthr):
        wind = self._jpath(wthr, self.OWM_WIND, dict())

        # Speed
        msec_speed = wind['speed'] if ('speed' in wind) else 0
        kmh_speed = msec_speed * self.kmh_from_msec
        fsec_speed = msec_speed * self.ft_from_meter
        mph_speed = fsec_speed * self.mph_from_fsec

        # Gusts
        msec_gust = wind['gust'] if ('gust' in wind) else 0
        kmh_gust = msec_gust * self.kmh_from_msec
        fsec_gust = msec_gust * self.ft_from_meter
        mph_gust = fsec_gust * self.mph_from_fsec

        # Format the wind speed
        return self.py3.safe_format(self.format_wind, {
            'icon': self.icons['wind'],
            'deg': wind['deg'] if ('deg' in wind) else 0,

            'msec_speed': round(msec_speed),
            'kmh_speed': round(kmh_speed),
            'fsec_speed': round(fsec_speed),
            'mph_speed': round(mph_speed),

            'msec_gust': round(msec_gust),
            'kmh_gust': round(kmh_gust),
            'fsec_gust': round(fsec_gust),
            'mph_gust': round(mph_gust),
        })

    def _format_humidity(self, wthr):
        # Format the humidity (default zero humidity)
        return self.py3.safe_format(self.format_humidity, {
            'icon': self.icons['humidity'],
            'humid': self._jpath(wthr, self.OWM_HUMIDITY, 0),
        })

    def _format_pressure(self, wthr):
        # Get data and add the icon
        pressure = self._jpath(wthr, self.OWM_PRESSURE, dict())
        pressure['icon'] = self.icons['pressure']

        # Format the barometric pressure
        return self.py3.safe_format(self.format_humidity, pressure)

    def _format_temp(self, wthr):
        # Get Kelvin data (default absolute zero)
        k_data = self._jpath(wthr, self.OWM_TEMP, 0)

        def trans(key, value, fn):
          if(key.startswith('temp')):
            return fn(value)

          return value

        # Convert each Kelvin data point to Celsius
        c_data = {k: trans(k, v, lambda v: v - 273.15)
            for k, v in k_data.items()}

        # Convert each Kelvin data point to Fahrenheit
        f_data = {k: trans(k, v, lambda v: v * (9.0/5.0) - 459.67)
            for (k, v) in k_data.items()}

        # Fix forecasts
        for group in (c_data, f_data, k_data):
            if ('temp' not in group):
                group['temp'] = group['day']

            if ('temp_min' not in group):
                group['temp_min'] = group['min']

            if ('temp_max' not in group):
                group['temp_max'] = group['max']

        # Format the temperature
        return self.py3.safe_format(self.format_temp, {
            'icon': self.icons['temp'],

            'c': round(c_data['temp']),
            'c_min': round(c_data['temp_min']),
            'c_max': round(c_data['temp_max']),

            'f': round(f_data['temp']),
            'f_min': round(f_data['temp_min']),
            'f_max': round(f_data['temp_max']),

            'k': round(k_data['temp']),
            'k_min': round(k_data['temp_min']),
            'k_max': round(k_data['temp_max']),
        })

    def _format_sunrise(self, wthr):
        # Get the time for sunrise (default is the start of time)
        dt = datetime.datetime.utcfromtimestamp(
            self._jpath(wthr, self.OWM_SUNRISE, 0))

        # Format the sunrise
        replaced = dt.strftime(self.format_sunrise)
        return self.py3.safe_format(replaced, {
            'icon': self.icons['sunrise'],
        })

    def _format_sunset(self, wthr):
        # Get the time for sunset (default is the start of time)
        dt = datetime.datetime.utcfromtimestamp(
            self._jpath(wthr, self.OWM_SUNSET, 0))

        # Format the sunset
        replaced = dt.strftime(self.format_sunset)
        return self.py3.safe_format(replaced, {
            'icon': self.icons['sunset'],
        })

    def _format_dict(self, wthr):
        return {
            # Standard options
            'icon': self._get_icon(wthr),
            'clouds': self._format_clouds(wthr),
            'rain': self._format_rain(wthr),
            'snow': self._format_rain(wthr),
            'wind': self._format_wind(wthr),
            'humidity': self._format_humidity(wthr),
            'pressure': self._format_pressure(wthr),
            'temp': self._format_temp(wthr),
            'sunrise': self._format_sunrise(wthr),
            'sunset': self._format_sunset(wthr),

            # Descriptions (defaults to empty)
            'desc': self._jpath(wthr, self.OWM_DESC, ''),
            'desc_long': self._jpath(wthr, self.OWM_DESC_LONG, '')
        }

    def _format(self, wthr, fcsts):
        # Format all sections
        today = self._format_dict(wthr)

        # Insert forecasts
        forecasts = []
        for day in fcsts:
            future = self._format_dict(day)
            forecasts.append(self.py3.safe_format(self.format_forecast, future))

        # Give the final format
        today['forecast'] = self.py3.composite_join(
            self.forecast_text_separator, forecasts)
        return self.py3.safe_format(self.format, today)

    def weather(self):
        self._init()

        # Get weather information
        coords = self._get_coords()
        text = ''
        if (coords is not None):
            wthr = self._get_weather(coords)
            fcsts = self._get_forecast(coords)

            text = self._format(wthr, fcsts)

        return {
            'full_text': text,
            'cached_until': self.py3.time_in(seconds=self.cache_timeout)
        }

    def on_click(self, event):
        # Avoid hitting rate limits on APIs
        self.py3.prevent_refresh()


if (__name__ == '__main__'):
    '''
    Run module in test mode.
    '''

    import os
    from py3status.module_test import module_test
    module_test(Py3status, config={
        'api_key': os.getenv('OWM_API_KEY'),

        'icons': {
            'i200': "☔",
            'i230_i232': "🌧",

            'clouds': "☁",
        },

        'format': '{icon}: {temp}, {forecast}',
        'forecast_days': 3,
    })
