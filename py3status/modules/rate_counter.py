# -*- coding: utf-8 -*-
"""
Display days/hours/minutes spent and calculate the price of your service.

Configuration parameters:
    config_file: file path to store the time already spent
        and restore it the next session
    hour_price: your price per hour
    tax: tax value (1.02 = 2%)

@author Amaury Brisou <py3status AT puzzledge.org>
"""
import os
import time


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 5
    config_file = '%s%s' % (os.environ['HOME'],
                            '/.i3/py3status/counter-config.save')
    hour_price = 30
    tax = 1.02

    def __init__(self):
        self.current_time = time.time()
        self.diff_time = 0
        self.full_text = ''
        self.restarted = False
        self.saved_time = 0
        self.start_time = time.time()
        self.started = False
        try:
            # Use file to refer to the file object
            with open(self.config_file) as file:
                self.saved_time = float(file.read())
        except:
            pass

    def kill(self, i3s_output_list, i3s_config):
        if self.started is True:
            self.saved_time = self.current_time - self.start_time
        with open(self.config_file, 'w') as f:
            f.write(str(self.saved_time))

    def on_click(self, i3s_output_list, i3s_config, event):
        if event['button'] == 1:
            if self.started is True:
                self.saved_time = time.time() - self.start_time
                self.started = False
            else:
                self.start_time = time.time() - self.saved_time
                self.started = True
        elif event['button'] == 3:
            self._reset()

    def _reset(self):
        self.saved_time = 0
        with open(self.config_file, 'w') as f:
            f.write('0')

    def counter(self, i3s_output_list, i3s_config):
        if self.started:
            self.current_time = time.time()
            self.diff_time = time.gmtime(self.current_time - self.start_time)
            cost = (
                24 * float(self.hour_price) *
                float(self.diff_time.tm_mday - 1) +
                float(self.hour_price) * float(self.diff_time.tm_hour) +
                float(self.diff_time.tm_min) * float(self.hour_price) / 60 +
                float(self.diff_time.tm_sec) * float(self.hour_price) / 3600)
            self.full_text = 'Time: %d day %d:%d Cost: %.2f$' % (
                self.diff_time.tm_mday - 1, self.diff_time.tm_hour,
                self.diff_time.tm_min, float(cost) * float(self.tax))
            color = i3s_config['color_good']
        else:
            if self.full_text == '':
                if self.saved_time != 0:
                    t = time.gmtime(self.saved_time)
                    cost = float(self.hour_price) * float(
                        t.tm_mday - 1) * 24 + float(self.hour_price) * float(
                            t.tm_hour) + float(t.tm_min) * float(
                                self.hour_price) / 60 + float(
                                    t.tm_sec) * float(self.hour_price) / 3600
                    self.full_text = 'Time: %d day %d:%d Cost: %.2f$' % (
                        t.tm_mday - 1, t.tm_hour, t.tm_min, float(cost) *
                        float(self.tax))
                else:
                    self.full_text = "Time: 0 day 0:0 Cost: 0$"

            color = i3s_config['color_bad']

        response = {
            'cached_until': time.time() + self.cache_timeout,
            'full_text': self.full_text,
            'color': color,
        }
        return response


if __name__ == "__main__":

    from time import sleep
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00',
    }
    while True:
        print(x.counter([], config))
        sleep(1)
