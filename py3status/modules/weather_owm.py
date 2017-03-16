# -*- coding: utf-8 -*-
'''
Ultimately customizable weather module based on IP-API Geolocation API
and the OpenWeatherMap API.

Requires an API key for OpenWeatherMap, but the free tier allows you enough
requests/sec to function properly.

This module allows you to specify an icon for nearly every weather scenario
imaginable. The default configuration options lump many of the icons into
a few groups, and due to the limitations of UTF-8, this is really as expressive
as it gets.

I would highly suggest you install an additional font, such as the incredible
https://erikflowers.github.io/weather-icons font, which has most of the
icon mappings.

For more information, see https://openweathermap.org/weather-conditions
on what weather conditions are supported. See the configuration options
for how to specify each weather icon.

Configuration parameters:
  api_key: Your OpenWeatherMap API key.
    See https://openweathermap.org/appid

    (default None)

  lang: An ISO 639-1 code for your language (two letters)
    (default 'en')

  req_timeout: The timeout in seconds for contacting the IP API.
    (default 10)

  cache_duration: The time between weather polling in seconds
    It is recommended to keep this at a higher value to avoid rate
    limiting with the API's.

    (default 60)

  icons: A dictionary relating weather code to icon.
    See https://openweathermap.org/weather-conditions for a complete list
    of supported icons. This will fall-back to the listed icon if there is
    no specific icon present.

    There are multiple ways to specify individual icons based on the id:
      - Use the key 'i601' to reference the condition with id = 601 (snow)
      - Use the key 'i230_i232' to reference a span of conditions inclusive,
          in this case conditions (230, 231, 232) (thunderstorm with drizzle)

    Also, you can specify the icons for the various formatting sections below.
    For example, to specify the icon for 'format_pressure', use 'pressure'. A
    few formatting sections will take from the defaults or be dynamic, including
      - clouds
      - rain
      - wind
      - sunrise
    These may be specified regardless.

    Example:
    icons = {
      i200 = "☔",
      ii230_i232 = "🌧"

      clouds = "☁"
    }

    (default None)

  format: How to display the weather. This also dictates the type of forecast
    Available placeholders:
      icon, clouds, snow, wind, humidity, pressure, temp, sunrise, sunset
      descript, descript_long, forecast

    You may also use the icons in the icon dictionary with their identifiers

    (default '{icon}: {temp}')

  format_clouds: Formatting for cloud coverage (percentage).
    Available placeholders:
      icon, coverage

    (default '{icon}: {coverage}%')

  format_rain: Formatting for rain volume over the past 3 hours
    Available placeholders:
      icon, mm, cm, m, in, ft, yrd

    (default '{icon}: {in} inches')

  format_snow: Formatting for snow volume over the past 3 hours
    Available placeholders:
      icon, mm, cm, m, in, ft, yrd

    (default '{icon}: {in} inches')

  format_wind: Formatting for wind degree and speed
    Available placeholders:
      icon, deg, msec_speed, kmh_speed, fsec_speed, mph_speed,
      msec_gust, kmh_gust, fsec_gust, mph_gust

    (default '{icon}: {mph_speed} mph')

  format_humidity: Formatting for humidity (percentage)
    Available placeholders:
      icon, humid

    (default '{icon}: {humid}%')

  format_pressure: Formatting for atmospheric pressure
    Available placeholders:
      icon, press, sea_level

    (default '{icon}: {press} hPa')

  format_temp: Formatting for temperature
    Available placeholders:
      icon, c, c_min, c_max, f, f_min, f_max, k, k_min, k_max

    (default '{icon}: {f}°')

  format_sunrise_time: Formatting string for sunrise time
    This follows the datetime.strftime() spec.

  format_sunrise: Formatting for sunrise time
    Available placeholders:
      icon, strftime

    (default '{icon}: {strftime}')

  format_sunset_time: Formatting string for sunset time
    This follows the datetime.strftime() spec.

  format_sunset: Formatting for sunset time
    Available placeholders:
      icon, strftime

    (default '{icon}: {strftime}')

  forecast_format: Formatting for future forecasts
    Available placeholders:
      icon, clouds, snow, wind, humidity, pressure, temp,
      descript, descript_long

    This is similar to the 'format' field, but contains information
    for future weather

    (default '{icon}')

  forecast_separator: Separator between entries in the forecast
    (default ' ')

  forecast_today: Include today in the forecast? (Boolean)
    (default False)

  forecast_num: Number of days to include in the forecast, including today
    (regardless of the 'forecast_today' flag)

    (default 0)
'''

import pyowm
import datetime

class Py3status:
  # OpenWeatherMap settings
  api_key = None
  lang = 'en'

  # IP API settings
  req_timeout = 10

  # Py3status behavior
  cache_duration = 60

  # Formatting settings
  icons = None
  format = '{icon}: {temp}'
  format_clouds = '{icon}: {coverage}%'
  format_rain = '{icon}: {in} inches'
  format_snow = '{icon}: {in} inches'
  format_wind = '{icon}: {mph_speed} mph'
  format_humidity = '{icon}: {humid}%'
  format_pressure = '{icon}: {press} hPa'
  format_temp = '{icon}: {f}°'

  format_sunrise_time = '%X'
  format_sunrise = '{icon}: {strftime}'
  format_sunset_time = '%X'
  format_sunset = '{icon}: {strftime}'

  # Forcast options
  forecast_format = '{icon}'
  forecast_separator = ' '
  forecast_today = False
  forecast_num = 0

  # Conversion factors
  in_from_mm = 0.0393701
  ft_from_meter = 3.28084
  kmh_from_msec = 0.277778
  mph_from_fsec = 1.46667

  def __init__(self):
    self.icons = self._get_icons()

  def _get_icons(self):
    if (self.icons is None):
      self.icons = {}

    # Defaults for weather ranges
    defaults = {
        'i200_i299': '⛈',
        'i300_i399': '🌧',
        'i500_i599': '🌧',
        'i600_i699': '❄',
        'i700_i799': '🌫',
        'i800':      '☼',
        'i801_i809': '⛅',
        'i900_i909': '⚠',
        'i950_i959': '☴',
        'i960_i999': '⚠',
      }

    # Default mappings for other icons
    others = {
        'clouds':   802,
        'rain':     501,
        'snow':     601,
        'wind':     954,
        'humidity': '●',
        'pressure': '◌',
        'temp':     '○',
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
              raise Exception('Icon range is not properly' +
                  ' formatted! (%s)' % key)

            # Populate each code
            (start, end) = tuple(map(int, key[1:].split('_i')))
            for code in range(start, end + 1):
              data[code] = defaults[key]

          else:
            data[int(key[1:])] = defaults[key]
        else:
          data[key] = defaults[key]

    # Weather icons for formatting sections
    for key in others:
      if (isinstance(others[key], int)):
        data[key] = data[others[key]]
      else:
        data[key] = others[key]

    return data

  def _init(self):
    # Verify the API key
    if (self.api_key is None):
      raise Exception("API Key for OpenWeatherMap cannot be empty!" + \
          " Go to http://openweathermap.org/appid to get an API Key.")

    self.owm = pyowm.OWM(self.api_key, language = self.lang)

  def _get_coords(self):
    # Contact the IP API
    url = "http://ip-api.com/json"
    req = self.py3.request(url, timeout = self.req_timeout)
    try:
      data = req.json()
    except (self.py3.RequestException):
      return None

    # Extract the data
    try:
      return (data['lat'], data['lon'])
    except (TypeError):
      return None

  def _get_weather(self, coords):
    # Get the weather
    obs = self.owm.weather_at_coords(*coords)
    return obs.get_weather()

  def _get_forecast(self, coords):
    # Get the next few days
    if (self.forecast_num == 0):
      return []

    fc = self.owm.daily_forecast_at_coords(*coords,
        limit = (self.forecast_num + 1))
    fcst = fc.get_forecast()
    fcsts = fcst.get_weathers()
    return fcsts[:-1] if (self.forecast_today) else fcsts[1:]

  def _get_icon(self, wthr):
    # Lookup the icon from the weather code
    return self.icons[wthr.get_weather_code()]

  def _format_clouds(self, wthr):
    # Format the cloud cover
    return self.py3.safe_format(self.format_clouds, {
        'icon':     self.icons['clouds'],
        'coverage': wthr.get_clouds(),
      })

  def _format_rain(self, wthr):
    # Format rain fall
    key = '3h'
    rain = wthr.get_rain()
    if(key not in rain):
      rain[key] = 0

    # Data comes as mm
    inches = rain[key] * self.in_from_mm

    # Format the rain fall
    return self.py3.safe_format(self.format_rain, {
        'icon': self.icons['rain'],
        'mm':   round(rain[key]),
        'cm':   round(rain[key] / 10),
        'm':    round(rain[key] / 100),
        'in':   round(inches),
        'ft':   round(inches / 12),
        'yrd':  round(inches / 36),
      })

  def _format_snow(self, wthr):
    # Format snow fall
    key = '3h'
    snow = wthr.get_snow()
    if(key not in snow):
      snow[key] = 0

    # Data comes as mm
    inches = snow[key] * self.in_from_mm

    # Format the snow fall
    return self.py3.safe_format(self.format_snow, {
        'icon': self.icons['snow'],
        'mm':   round(snow[key]),
        'cm':   round(snow[key] / 10),
        'm':    round(snow[key] / 100),
        'in':   round(inches),
        'ft':   round(inches / 12),
        'yrd':  round(inches / 36),
      })

  def _format_wind(self, wthr):
    wind = wthr.get_wind()

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
        'icon':       self.icons['wind'],
        'deg':        wind['deg'] if ('deg' in wind) else 0,

        'msec_speed': round(msec_speed),
        'kmh_speed':  round(kmh_speed),
        'fsec_speed': round(fsec_speed),
        'mph_speed':  round(mph_speed),

        'msec_gust':  round(msec_gust),
        'kmh_gust':   round(kmh_gust),
        'fsec_gust':  round(fsec_gust),
        'mph_gust':   round(mph_gust),
      })

  def _format_humidity(self, wthr):
    # Format the humidity
    return self.py3.safe_format(self.format_humidity, {
        'icon':  self.icons['humidity'],
        'humid': wthr.get_humidity(),
      })

  def _format_pressure(self, wthr):
    # Get data and add the icon
    pressure = wthr.get_pressure()
    pressure['icon'] =  self.icons['pressure']

    # Format the barometric pressure
    return self.py3.safe_format(self.format_humidity, pressure)

  def _format_temp(self, wthr):
    # Get data
    c_data = wthr.get_temperature(unit = 'celsius')
    f_data = wthr.get_temperature(unit = 'fahrenheit')
    k_data = wthr.get_temperature()

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
        'icon':       self.icons['temp'],

        'c':     round(c_data['temp']),
        'c_min': round(c_data['temp_min']),
        'c_max': round(c_data['temp_max']),

        'f':     round(f_data['temp']),
        'f_min': round(f_data['temp_min']),
        'f_max': round(f_data['temp_max']),

        'k':     round(k_data['temp']),
        'k_min': round(k_data['temp_min']),
        'k_max': round(k_data['temp_max']),
      })

  def _format_sunrise(self, wthr):
    # Get the ISO 8601 time
    raw_time = wthr.get_sunrise_time('iso')
    dt = datetime.datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S+00")

    # Format the sunrise
    return self.py3.safe_format(self.format_sunrise, {
        'icon':   self.icons['sunrise'],
        'strftime': dt.strftime(self.format_sunrise_time),
      })

  def _format_sunset(self, wthr):
    # Get the ISO 8601 time
    raw_time = wthr.get_sunset_time('iso')
    dt = datetime.datetime.strptime(raw_time, "%Y-%m-%d %H:%M:%S+00")

    # Format the sunset
    return self.py3.safe_format(self.format_sunset, {
        'icon':   self.icons['sunset'],
        'strftime': dt.strftime(self.format_sunset_time),
      })

  def _format_dict(self, wthr):
    return {
        # Standard options
        'icon':          self._get_icon(wthr),
        'clouds':        self._format_clouds(wthr),
        'rain':          self._format_rain(wthr),
        'snow':          self._format_rain(wthr),
        'wind':          self._format_wind(wthr),
        'humidity':      self._format_humidity(wthr),
        'pressure':      self._format_pressure(wthr),
        'temp':          self._format_temp(wthr),
        'sunrise':       self._format_sunrise(wthr),
        'sunset':        self._format_sunset(wthr),

        # Descriptions
        'descript':      wthr.get_status().title(),
        'descript_long': wthr.get_detailed_status()
      }

  def _format(self, wthr, fcsts):
    # Format all sections
    today = self._format_dict(wthr)

    # Insert forecasts
    forecasts = []
    for day in fcsts:
      future = self._format_dict(day)
      forecasts.append(self.py3.safe_format(self.forecast_format, future))

    # Give the final format
    today['forecast'] = self.forecast_separator.join(forecasts)
    return self.py3.safe_format(self.format, today)

  def weather(self):
    self._init()

    # Get weather information
    coords = self._get_coords()
    wthr = self._get_weather(coords)
    fcsts = self._get_forecast(coords)

    return {
      'full_text': self._format(wthr, fcsts),
      'cached_until': self.py3.time_in(seconds = self.cache_duration)
    }

if (__name__ == '__main__'):
  '''
  Run module in test mode.
  '''

  from py3status.module_test import module_test
  module_test(Py3status, config = {
      'api_key': 'YOUR_API_KEY',
    })
