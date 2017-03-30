# -*- coding: utf-8 -*-

"""
Display the system's uptime

Configuration parameters:

    - format: what will be displayed, formatted with predefined placeholders;
      defaults to "{days} days, {hours} hours, {minutes} mins"

Available placeholders in format string:

    - {days}: days part of the uptime
    - {hours}: hours part of the uptime
    - {minutes}: minutes part of the uptime
    - {seconds}: seconds part of the uptime
    - {years}:  years part of the uptime

Hint: if you don't use one of the placeholders, the value will be carried over
the next unit! For example, given an uptime of 1h30min:

    - if the only placeholder you use is {minutes}, its value will be 90
    - if you use both {hours} and {minutes}, they will be respectively 1 and 30

The cache_timeout will be automatically set depending on the precision you
ask for in the format string.

@author Alexis "Horgix" Chotard <alexis.horgix.chotard@gmail.com>
@license BSD
"""

from time import time


class Py3status:
    """
    """
    # Available configuration parameters
    format = "{days} days, {hours} hours, {minutes} mins"

    def uptime(self, i3s_output_list, i3s_config):
        # Units will be computed from bare seconds since timedelta only
        # provides .days and .seconds anyway
        try:
            with open('/proc/uptime', 'r') as f:
                # Getting rid of the seconds part. Keeping the floating point
                # part would make divmod return floats, and thus would require
                # days/hours/minutes/seconds to be casted to int before
                # formatting, which would be dirty to handle since we can't
                # cast None to int
                up = int(float(f.readline().split()[0]))
        except:
            return {'full_text': "None"}
        # Setting things to None directly to avoid an else clause everywhere
        cache_timeout = years = days = hours = minutes = seconds = None
        # Years
        if '{years}' in self.format:
            years, up = divmod(up, 31536000)  # 365 days year
            cache_timeout = 31536000
        # Days
        if '{days}' in self.format:
            days, up = divmod(up, 86400)
            cache_timeout = 86400
        # Hours
        if '{hours}' in self.format:
            hours, up = divmod(up, 3600)
            cache_timeout = 3600
        # Minutes
        if '{minutes}' in self.format:
            minutes, up = divmod(up, 60)
            cache_timeout = 60
        # Seconds
        if '{seconds}' in self.format:
            seconds = up
            cache_timeout = None

        response = {}
        if cache_timeout:
            response['cached_until'] = time() + cache_timeout
        response['full_text'] = self.format.format(years=years,
                                                   days=days,
                                                   hours=hours,
                                                   minutes=minutes,
                                                   seconds=seconds)
        return response

if __name__ == "__main__":
    """
    Test this module by calling it directly.
    """
    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    while True:
        print(x.uptime([], config))
        sleep(1)
