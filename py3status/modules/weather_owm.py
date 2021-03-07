r"""
Display ultimately customizable weather.

This module allows you to specify an icon for nearly every weather scenario
imaginable. The default configuration options lump many of the icons into
a few groups, and due to the limitations of UTF-8, this is really as expressive
as it gets.

This module uses OpenWeatherMap API (https://openweathermap.org).

setting `location` or `city` allows you to specify the location for the weather
you want displaying.

Requires an API key for OpenWeatherMap (OWM), but the free tier allows you
enough requests/sec to get accurate weather even up to the minute.

I would highly suggest you install an additional font, such as the incredible
(and free!) Weather Icons font (https://erikflowers.github.io/weather-icons),
which has icons for most weather scenarios. But, this will still work with
the i3bar default font, Deja Vu Sans Mono font, which has Unicode support.
You can see the (limited) weather icon support within Unicode in the defaults.

For more information, see the documentation
(https://openweathermap.org/weather-conditions) on what weather conditions are
supported. See the configuration options for how to specify each weather icon.

Configuration parameters:
    api_key: Your OpenWeatherMap API key
        See https://openweathermap.org/appid. Required!
        (default None)
    cache_timeout: The time between API polling in seconds
        It is recommended to keep this at a higher value to avoid rate
        limiting with the API's.
        (default 1800)
    city: The city to display for location information. If set,
        implicitly disables the Geo API for determining city name.
        (default None)
    country: The country to display for location information. If set,
        implicitly disables the Geo API for determining country name.
        (default None)
    forecast_days: Number of days to include in the forecast, including today
        (regardless of the 'forecast_include_today' flag)
        (default 3)
    forecast_include_today: Include today in the forecast? (Boolean)
        (default False)
    format: How to display the weather
        This also dictates the type of forecast. The placeholders here refer to
        the format_[...] variables found below.
        Available placeholders:
            icon, city, clouds, rain, snow, wind, humidity, pressure,
            temperature, sunrise, sunset, main, description, forecast
        (default '{city} {icon} {temperature}[ {rain}], {description} {forecast}')
    format_clouds: Formatting for cloud coverage (percentage)
        Available placeholders:
            icon, coverage
        (default '{icon} {coverage}%')
    format_forecast: Formatting for future forecasts
        Available placeholders:
            See 'format'
        This is similar to the 'format' field, but contains information
        for future weather. Notably, this does not include information about
        sunrise or sunset times.
        (default '{icon}')
    format_forecast_separator: Separator between entries in the forecast
        (default ' ')
    format_humidity: Formatting for humidity (percentage)
        Available placeholders:
            icon, humidity
        (default '{icon} {humidity}%')
    format_pressure: Formatting for atmospheric pressure
        Available placeholders:
            icon, pressure, sea_level
        (default '{icon} {pressure} hPa')
    format_rain: Formatting for rain volume over the past 3 hours
        Available placeholders:
            icon, amount
        (default '[\?if=amount {icon} {amount:.0f} {unit}]')
    format_snow: Formatting for snow volume over the past 3 hours
        Available placeholders:
            icon, amount
        (default '[\?if=amount {icon} {amount:.0f} {unit}]')
    format_sunrise: Formatting for sunrise time
        Note that this format accepts strftime/strptime placeholders to populate
        the output with the time information.
        Available placeholders:
            icon
        (default '{icon} %-I:%M %p')
    format_sunset: Formatting for sunset time
        This format accepts strftime/strptime placeholders to populate the
        output with the time information.
        Available placeholders:
            icon
        (default '{icon} %-I:%M %p')
    format_temperature: Formatting for temperature
        Available placeholders:
            current, icon, max, min
        (default '{icon} [\?color=all {current:.0f}°{unit}]')
    format_wind: Formatting for wind degree and speed
        The 'gust' option represents the speed of wind gusts in the wind unit.
        Available placeholders:
            icon, degree, speed, gust, direction
        (default '[\?if=speed {icon} {speed:.0f} {unit}]')
    icon_atmosphere: Icon for atmospheric conditions, like fog, smog, etc.
        (default '🌫')
    icon_cloud: Icon for clouds
        (default '☁')
    icon_extreme: Icon for extreme weather
        (default '⚠')
    icon_humidity: Icon for humidity
        (default '●')
    icon_pressure: Icon for pressure
        (default '◌')
    icon_rain: Icon for rain
        (default '🌧')
    icon_snow: Icon for snow
        (default '❄')
    icon_sun: Icon for sunshine
        (default '☼')
    icon_sunrise: Icon for sunrise
        (default '⇑')
    icon_sunset: Icon for sunset
        (default '⇓')
    icon_temperature: Icon for temperature
        (default '○')
    icon_thunderstorm: Icon for thunderstorms
        (default '⛈')
    icon_wind: Icon for wind or breeze
        (default '☴')
    icons: A dictionary relating weather code to icon
        See https://openweathermap.org/weather-conditions for a complete list
        of supported icons. This will fall-back to the listed icon if there is
        no specific icon present. However, options included here take precedent
        over the above 'icon_{...}' options.
        There are multiple ways to specify individual icons based on the id:
            * Use the key '601' to reference the condition with id = 601
              (snow)
            * Use the key '230_232' to reference a span of conditions
              inclusive, in this case conditions (230, 231, 232) (thunderstorm
              with drizzle)
        (default None)
    lang: An ISO 639-1 code for your language (two letters)
        (default 'en')
    location: A tuple of floats describing the desired weather location
        The tuple should follow the form (latitude, longitude), and if set,
        implicitly disables the Geo API for determining location.
        (default None)
    thresholds: Configure temperature colors based on limits
        The numbers specified inherit the unit of the temperature as configured.
        The default below is intended for Fahrenheit. If the set value is empty
        or None, the feature is disabled. You can specify this parameter using a
        dictionary:
            * Keys are names. You have the option of 'current', 'min', 'max',
              or 'all' to specify a threshold. The first three are tied to the
              various temperature values, the last sets the same threshold for
              all outputs. If both 'all' and one of the first three are set
              (lets say 'min' for this example), the threshold will default to
              be the value in 'min', not 'all'. This goes for any configuration
            * The values are lists of pairs, with temperature (in the
              configured unit) as the first and the color as the second
            * To use the thresholds color, place '\?color=all' in the
              formatting string for temperature, replacing 'all' with any of
              the valid threshold names for different coloring effects
            * To have smooth transitions between colors, consider setting the
              'gradients' configuration parameter to 'True', either in the
              global configuration, or in the module configuration!
        (default {'all': [(-100, '#0FF'), (0, '#00F'), (50, '#0F0'), (150, '#FF0')]})
    unit_rain: Unit for rain fall
        When specified, a unit may be any combination of upper and lower
        case, such as 'Ft', and still be considered valid as long as it is in
        the below options.
        Options:
            cm, ft, in, mm, m, yd
        (default 'in')
    unit_snow: Unit for snow fall
        Options:
            cm, ft, in, mm, m, yd
        (default 'in')
    unit_temperature: Unit for temperature
        Options:
            c, f, k
        (default 'F')
    unit_wind: Unit for wind speed
        Options:
            fsec, msec, mph, kmh
        (default 'mph')

Format placeholders:
        {icon} The icon associated with a formatting section
    format_clouds:
        {coverage} Cloud coverage percentage
    format_humidity:
        {humidity} Humidity percentage
    format_pressure:
        {pressure} Current atmospheric pressure in Pascals
        {sea_level} Sea-level atmospheric pressure in Pascals.
    format_rain:
        {amount} Rainfall in the specified unit
        {unit} The unit specified
    format_snow:
        {amount} Snowfall in the specified unit
        {unit} The unit specified
    format_temperature:
        {current} Current temperature
        {max} Maximum temperature in the configured unit
        {min} Minimum temperature
        {unit} The unit specified
    format_wind:
        {degree} Current wind heading
        {direction} Letter reprents direction e.g. N,NE,E etc
        {gust} Wind gusts speed in the specified unit
        {speed} Wind speed
        {unit} The unit specified
    format only:
        {city} The name of the city where the weather is
        {country} The name of the country where the weather is
        {forecast} Output of format_forecast
    format, format_forecast:
        {clouds} Output of format_clouds
        {description} Natural description of the current weather
        {humidity} Output of format_humidity
        {main} Short description of the current weather
        {pressure} Output of format_pressure
        {snow} Output of format_snow
        {sunrise} Output of format_sunrise
        {sunset} Output of format_sunset
        {temperature} Output of format_temperature
        {wind} Output of format_wind

Examples:
```
# change icons
weather_owm {
    api_key = <my api key>
    icons = {
        '200': "☔"
        '230_232': "🌧"
    }
}

# set a city
weather_owm {
    api_key = <my api key>
    city = 'London'
}

# set a location
weather_owm {
    api_key = <my api key>
    location = (48.9342, 2.3548)  # Saint-Denis
}
```

@author alexoneill
@licence MIT

SAMPLE OUTPUT
{'full_text': 'New York ○ 30°F, mist ☁ ☁ ☁'}

diff
{'full_text': '○ 59°F, foggy  ☼ '}
"""

import datetime


# API information
OWM_CURR_ENDPOINT = "https://api.openweathermap.org/data/2.5/weather?"
OWM_FUTURE_ENDPOINT = "https://api.openweathermap.org/data/2.5/forecast?"
IP_ENDPOINT = "http://geo.ultrabug.fr"

# Paths of information to extract from JSON
IP_CITY = "//city"
IP_COUNTRY = "//country"
IP_LAT = "//latitude"
IP_LON = "//longitude"
OWM_CLOUD_COVER = "//clouds/all"
OWM_DESC = "//weather:0/main"
OWM_DESC_LONG = "//weather:0/description"
OWM_HUMIDITY = "//main/humidity"
OWM_PRESSURE = "//main"
OWM_RAIN = "//rain/3h"
OWM_SNOW = "//snow/3h"
OWM_SUNRISE = "//sys/sunrise"
OWM_SUNSET = "//sys/sunset"
OWM_TEMP = "//main"
OWM_WEATHER_ICON = "//weather:0/id"
OWM_WIND = "//wind"

# Units constants
RAIN_UNITS = {"cm", "ft", "in", "mm", "m", "yd"}
SNOW_UNITS = RAIN_UNITS
TEMP_UNITS = {"c", "f", "k"}
WIND_UNITS = {"fsec", "msec", "mph", "kmh"}

# Conversion factors
FT_FROM_METER = 3.28084
IN_FROM_MM = 0.0393701
KMH_FROM_MSEC = 0.277778
MPH_FROM_MSEC = 2.23694

# Thresholds options
THRESHOLDS_ALL = "all"
THRESHOLDS_NAMES = {THRESHOLDS_ALL, "current", "min", "max"}

# Thresholds defaults
THRESHOLDS = {"all": [(-100, "#0FF"), (0, "#00F"), (50, "#0F0"), (150, "#FF0")]}


class Py3status:
    """
    """

    # available configuration parameters
    api_key = None
    cache_timeout = 1800
    city = None
    country = None
    forecast_days = 3
    forecast_include_today = False
    format = "{city} {icon} {temperature}[ {rain}], {description} {forecast}"
    format_clouds = "{icon} {coverage}%"
    format_forecast = "{icon}"
    format_forecast_separator = " "
    format_humidity = "{icon} {humidity}%"
    format_pressure = "{icon} {pressure} hPa"
    format_rain = r"[\?if=amount {icon} {amount:.0f} {unit}]"
    format_snow = r"[\?if=amount {icon} {amount:.0f} {unit}]"
    format_sunrise = "{icon} %-I:%M %p"
    format_sunset = "{icon} %-I:%M %p"
    format_temperature = r"{icon} [\?color=all {current:.0f}°{unit}]"
    format_wind = r"[\?if=speed {icon} {speed:.0f} {unit}]"
    icon_atmosphere = "🌫"
    icon_cloud = "☁"
    icon_extreme = "⚠"
    icon_humidity = "●"
    icon_pressure = "◌"
    icon_rain = "🌧"
    icon_snow = "❄"
    icon_sun = "☼"
    icon_sunrise = "⇑"
    icon_sunset = "⇓"
    icon_temperature = "○"
    icon_thunderstorm = "⛈"
    icon_wind = "☴"
    icons = None
    lang = "en"
    location = None
    thresholds = THRESHOLDS
    unit_rain = "in"
    unit_snow = "in"
    unit_temperature = "F"
    unit_wind = "mph"

    class Meta:
        deprecated = {
            "remove": [{"param": "offset_gmt", "msg": "obsolete"}],
            "rename": [
                {
                    "param": "forecast_text_separator",
                    "new": "format_forecast_separator",
                    "msg": "obsolete parameter, use format_forecast_separator",
                }
            ],
        }

    def _get_icons(self):
        if self.icons is None:
            self.icons = {}

        # Defaults for weather ranges
        defaults = {
            "200_299": self.icon_thunderstorm,
            "300_399": self.icon_rain,
            "500_599": self.icon_rain,
            "600_699": self.icon_snow,
            "700_799": self.icon_atmosphere,
            "800": self.icon_sun,
            "801_809": self.icon_cloud,
            "900_909": self.icon_extreme,
            "950_959": self.icon_wind,
            "960_999": self.icon_extreme,
        }

        # Handling ranges from OpenWeatherMap
        data = {}
        for source in (defaults, self.icons):
            for key in source:
                if not key.replace("_", "").isdigit():
                    raise Exception(f"Invalid icon id: ({key})")

                if "_" in key:
                    if key.count("_") != 1:
                        raise Exception("fInvalid icon range: {key}")

                    # Populate each code
                    start, _, end = key.partition("_")
                    for code in range(int(start), int(end) + 1):
                        data[code] = source[key]

                else:
                    data[int(key)] = source[key]

        return data

    def post_config_hook(self):
        # Verify the API key
        if self.api_key is None:
            raise Exception(
                "API Key for OpenWeatherMap cannot be empty!"
                " Go to https://openweathermap.org/appid to"
                " get an API Key."
            )

        # Generate our icon array
        self.icons = self._get_icons()

        # Verify the units configuration
        if self.unit_rain.lower() not in RAIN_UNITS:
            raise Exception("unit_rain is not recognized")
        if self.unit_snow.lower() not in SNOW_UNITS:
            raise Exception("unit_snow is not recognized")
        if self.unit_temperature.lower() not in TEMP_UNITS:
            raise Exception("unit_temperature is not recognized")
        if self.unit_wind.lower() not in WIND_UNITS:
            raise Exception("unit_wind is not recognized")

        # Check thresholds for validity
        if set(self.thresholds) > THRESHOLDS_NAMES:
            raise Exception("threshold name(s) are not recognized")

        # Copy thresholds if available
        if THRESHOLDS_ALL in self.thresholds:
            for name in THRESHOLDS_NAMES - {THRESHOLDS_ALL}:
                if name not in self.thresholds:
                    self.thresholds[name] = self.thresholds[THRESHOLDS_ALL]

        # Initialize per-format thresholds
        self.thresholds_init = {}
        for name in ("format_humidity",):
            self.thresholds_init[name] = self.py3.get_color_names_list(
                getattr(self, name)
            )

    def _make_req(self, url, params=None):
        # Make a request expecting a JSON response
        req = self.py3.request(url, params=params)
        if req.status_code != 200:
            data = req.json()
            if data and "message" in data:
                msg = data["message"]
            else:
                msg = "{_error_message} {_status_code}".format(**vars(req))
            self.py3.error(msg)

        return req.json()

    def _jpath(self, data, query, default=None):
        # Take the query expression and drill down into the given dictionary
        parts = query.strip("/").split("/")
        for part in parts:
            try:
                # This represents a key:index expression, representing first
                # selecting a key, then an index
                if ":" in part:
                    (part, index) = tuple(part.split(":"))
                    data = data[part]
                    data = data[int(index)]

                # Select a portion of the dictionary by key in the path
                else:
                    data = data[part]

            # Failed, so return the default
            except (KeyError, IndexError, TypeError):
                return default

        return data

    def _get_loc_tz_info(self):
        # Preference a user-set location
        if all(x is not None for x in (self.location, self.city, self.country)):
            return (self.location, self.city, self.country)

        data = {}
        lat_lng = None
        # Contact the Geo API
        if not (self.location or self.city):
            try:
                data = self._make_req(IP_ENDPOINT)
            except (self.py3.RequestException, self.py3.RequestURLError):
                pass

            # Extract location data
            if self.location is None:
                lat_lng = (
                    self._jpath(data, IP_LAT, "0"),
                    self._jpath(data, IP_LON, "0"),
                )

        if self.location:
            lat_lng = self.location

        # Extract city
        city = self.city
        if self.city is None:
            city = self._jpath(data, IP_CITY, "")

        # Extract country
        country = self.country
        if self.country is None:
            country = self._jpath(data, IP_COUNTRY, "")

        return (lat_lng, city, country)

    def _get_weather(self, extras):
        # Get and process the current weather
        params = {"APPID": self.api_key, "lang": self.lang}
        extras.update(params)
        return self._make_req(OWM_CURR_ENDPOINT, extras)

    def _get_forecast(self, extras):
        # Get the next few days
        if self.forecast_days == 0:
            return []
        # Get raw data
        params = {
            "APPID": self.api_key,
            "lang": self.lang,
            "cnt": self.forecast_days + 1,
        }
        extras.update(params)
        data = self._make_req(OWM_FUTURE_ENDPOINT, extras)
        # Extract forecast
        weathers = data["list"]
        return weathers[:-1] if self.forecast_include_today else weathers[1:]

    def _get_icon(self, wthr):
        # Lookup the icon from the weather code (default sunny)
        return self.icons[self._jpath(wthr, OWM_WEATHER_ICON, 800)]

    def _format_clouds(self, wthr):
        # Format the cloud cover (default clear)
        return self.py3.safe_format(
            self.format_clouds,
            {
                "icon": self.icon_cloud,
                "coverage": self._jpath(wthr, OWM_CLOUD_COVER, 0),
            },
        )

    def _format_rain(self, wthr):
        # Format rain fall
        rain = self._jpath(wthr, OWM_RAIN, 0)

        # Data comes as mm
        inches = rain * IN_FROM_MM

        options = {
            "mm": round(rain),
            "cm": round(rain / 10),
            "m": round(rain / 100),
            "in": round(inches),
            "ft": round(inches / 12),
            "yd": round(inches / 36),
        }

        # Format the rain fall
        return self.py3.safe_format(
            self.format_rain,
            {
                "icon": self.icon_rain,
                "amount": options[self.unit_rain.lower()],
                "unit": self.unit_rain,
            },
        )

    def _format_snow(self, wthr):
        # Format snow fall
        snow = self._jpath(wthr, OWM_SNOW, 0)

        # Data comes as mm
        inches = snow * IN_FROM_MM

        options = {
            "mm": round(snow),
            "cm": round(snow / 10),
            "m": round(snow / 100),
            "in": round(inches),
            "ft": round(inches / 12),
            "yd": round(inches / 36),
        }

        # Format the snow fall
        return self.py3.safe_format(
            self.format_snow,
            {
                "icon": self.icon_snow,
                "amount": options[self.unit_snow.lower()],
                "unit": self.unit_snow,
            },
        )

    def _format_wind(self, wthr):
        wind = self._jpath(wthr, OWM_WIND, dict())

        # Speed and Gust
        msec_speed = wind["speed"] if ("speed" in wind) else 0
        msec_gust = wind["gust"] if ("gust" in wind) else 0

        options = {
            "fsec": {
                "speed": msec_speed * FT_FROM_METER,
                "gust": msec_gust * FT_FROM_METER,
            },
            "msec": {"speed": msec_speed, "gust": msec_gust},
            "mph": {
                "speed": msec_speed * MPH_FROM_MSEC,
                "gust": msec_gust * MPH_FROM_MSEC,
            },
            "kmh": {
                "speed": msec_speed * KMH_FROM_MSEC,
                "gust": msec_gust * KMH_FROM_MSEC,
            },
        }

        # Get the choice and add more
        choice = options[self.unit_wind.lower()]
        choice["icon"] = self.icon_wind
        choice["degree"] = wind["deg"] if ("deg" in wind) else 0
        if wind["deg"] >= 20 and wind["deg"] < 65:
            direction = "NE"
        elif wind["deg"] >= 65 and wind["deg"] < 110:
            direction = "E"
        elif wind["deg"] >= 110 and wind["deg"] < 155:
            direction = "SE"
        elif wind["deg"] >= 155 and wind["deg"] < 200:
            direction = "S"
        elif wind["deg"] >= 200 and wind["deg"] < 245:
            direction = "SW"
        elif wind["deg"] >= 245 and wind["deg"] < 290:
            direction = "W"
        elif wind["deg"] >= 290 and wind["deg"] < 335:
            direction = "NW"
        else:
            direction = "N"
        choice["direction"] = direction
        choice["unit"] = self.unit_wind

        # Format the wind speed
        return self.py3.safe_format(self.format_wind, choice)

    def _format_humidity(self, wthr):
        # Format the humidity (default zero humidity)
        humidity_data = {
            "icon": self.icon_humidity,
            "humidity": self._jpath(wthr, OWM_HUMIDITY, 0),
        }

        for x in self.thresholds_init["format_humidity"]:
            if x in humidity_data:
                self.py3.threshold_get_color(humidity_data[x], x)

        return self.py3.safe_format(self.format_humidity, humidity_data)

    def _format_pressure(self, wthr):
        # Get data and add the icon
        pressure = self._jpath(wthr, OWM_PRESSURE, dict())
        pressure["icon"] = self.icon_pressure

        # Format the barometric pressure
        return self.py3.safe_format(self.format_pressure, pressure)

    def _format_temp(self, wthr):
        # Get Kelvin data (default absolute zero)
        kelvin = self._jpath(wthr, OWM_TEMP, 0)

        # Temperature conversion methods
        def kToC(val):
            return val - 273.15

        def kToF(val):
            return val * 9 / 5 - 459.67

        options = {
            "c": {
                "current": round(kToC(kelvin["temp"])),
                "max": round(kToC(kelvin["temp_max"])),
                "min": round(kToC(kelvin["temp_min"])),
            },
            "f": {
                "current": round(kToF(kelvin["temp"])),
                "max": round(kToF(kelvin["temp_max"])),
                "min": round(kToF(kelvin["temp_min"])),
            },
            "k": {
                "current": round(kelvin["temp"]),
                "max": round(kelvin["temp_max"]),
                "min": round(kelvin["temp_min"]),
            },
        }

        # Get the choice and add more
        choice = options[self.unit_temperature.lower()]
        choice["icon"] = self.icon_temperature
        choice["unit"] = self.unit_temperature

        # Calculate thresholds
        for name in THRESHOLDS_NAMES - {THRESHOLDS_ALL}:
            # Try to apply the specific threshold
            if name in self.thresholds:
                self.py3.threshold_get_color(choice[name], name)

        # Format the temperature
        return self.py3.safe_format(self.format_temperature, choice)

    def _format_sunrise(self, wthr):
        # Get the time for sunrise (default is the start of time)
        dt = datetime.datetime.utcfromtimestamp(self._jpath(wthr, OWM_SUNRISE, 0))

        # Format the sunrise
        replaced = dt.strftime(self.format_sunrise)
        return self.py3.safe_format(replaced, {"icon": self.icon_sunrise})

    def _format_sunset(self, wthr):
        # Get the time for sunset (default is the start of time)
        dt = datetime.datetime.utcfromtimestamp(self._jpath(wthr, OWM_SUNSET, 0))

        # Format the sunset
        replaced = dt.strftime(self.format_sunset)
        return self.py3.safe_format(replaced, {"icon": self.icon_sunset})

    def _format_dict(self, wthr, city, country):
        data = {
            # Standard options
            "icon": self._get_icon(wthr),
            "clouds": self._format_clouds(wthr),
            "rain": self._format_rain(wthr),
            "snow": self._format_snow(wthr),
            "wind": self._format_wind(wthr),
            "humidity": self._format_humidity(wthr),
            "pressure": self._format_pressure(wthr),
            "temperature": self._format_temp(wthr),
            "sunrise": self._format_sunrise(wthr),
            "sunset": self._format_sunset(wthr),
            # Descriptions (defaults to empty)
            "main": self._jpath(wthr, OWM_DESC, "").lower(),
            "description": self._jpath(wthr, OWM_DESC_LONG, "").lower(),
            # Location information
            "city": city,
            "country": country,
        }

        return data

    def _format(self, wthr, fcsts, city, country):
        # Format all sections
        today = self._format_dict(wthr, city, country)

        # Insert forecasts
        forecasts = []
        for day in fcsts:
            future = self._format_dict(day, city, country)
            forecasts.append(self.py3.safe_format(self.format_forecast, future))

        # Give the final format
        format_forecast_separator = self.py3.safe_format(self.format_forecast_separator)
        today["forecast"] = self.py3.composite_join(
            format_forecast_separator, forecasts
        )

        return self.py3.safe_format(self.format, today)

    def weather_owm(self):
        # Get weather information
        loc_tz_info = self._get_loc_tz_info()
        text = ""
        if loc_tz_info is not None:
            (coords, city, country) = loc_tz_info
            if coords:
                extras = {"lat": coords[0], "lon": coords[1]}
            elif city:
                extras = {"q": city}
            wthr = self._get_weather(extras)
            fcsts = self._get_forecast(extras)

            # try to get a nice city name
            city = wthr.get("name") or city or "unknown"
            # get the best country we can
            if not country:
                sys = wthr.get("sys", {})
                country = sys.get("country", "unknown")

            text = self._format(wthr, fcsts, city, country)

        return {
            "full_text": text,
            "cached_until": self.py3.time_in(seconds=self.cache_timeout),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    import os
    from py3status.module_test import module_test

    # All possible outputs
    all_string = "/".join(
        [
            "{clouds}",
            "{description}",
            "{main}",
            "{humidity}",
            "{pressure}",
            "{snow}",
            "{sunrise}",
            "{sunset}",
            "{temperature}",
            "{wind}",
        ]
    )

    module_test(
        Py3status,
        config={
            "api_key": os.getenv("OWM_API_KEY"),
            # Select icons
            "icons": {"200": "☔", "230_232": "🌧"},
            # Complete configuration
            "format_clouds": "{icon} {coverage}%",
            "format_humidity": "{icon} {humidity}%",
            "format_pressure": "{icon} {pressure} Pa, sea: {sea_level} Pa",
            "format_rain": "{icon} {amount:.0f} in",
            "format_snow": "{icon} {amount:.0f} in",
            "format_temperature": (
                r"{icon}: max: [\?color=max {max:.0f}°F], "
                r"min: [\?color=min {min:.0f}°F], "
                r"current: [\?color=current {current:.0f}°F]"
            ),
            "format_wind": (
                "{icon} {degree}°, gust: {gust:.0f} mph, " "speed: {speed:.0f} mph"
            ),
            "format": ("{city}, {country}: {icon} " + all_string + "//{forecast}"),
            "format_forecast": ("{icon} " + all_string),
            # Miscellaneous
            "forecast_days": 1,
            "format_forecast_separator": "//",
        },
    )
