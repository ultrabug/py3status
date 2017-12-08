# -*- coding: utf-8 -*-
"""
Change brightness, gamma, reflect and more with xrandr... lmao.

Short description for my cool friends.
Right-click on the value to reset a value.
Right-click on the name to reset all values.
Middle-click on the value to randomize a value.
Middle-click on the name to randomize all values.
Scroll on the value to increase/decrease the value.
Scroll on the name doesn't do anything to the values.

Configuration parameters:
    button_next: mouse button to switch next value (default 4)
    button_previous: mouse button to switch previous value (default 5)
    button_random: mouse button to generate random values (default 2)
    button_reset: mouse button to reset values (default 3)
    format: display format for this module (default '{format_output}')
    format_output: display format for active outputs
        (default '{name} {brightness} {gamma_red} {gamma_green} {gamma_blue}')
    format_separator: show separator if more than one (default ' ')
    options: specify a dict of names and options to use (default {})
    outputs: specify a list of active outputs to use (default [])

Format placeholders:
    {output} number of active outputs, eg 2
    {format_output} format for active outputs

format_output placeholders:
    {brightness} brightness value, eg 1.0
    {delta} delta value, eg 0.05, 0.1, 0.25
    {gamma_blue} gamma blue value, eg 1.0
    {gamma_green} gamma green value, eg 1.0
    {gamma_red} gamma red value, eg 1.0
    {ignore} parameters to ignore, eg 'brightness, rotate'
    {name} output name, eg DP-2, DP-3
    {reflect} reflection value, eg normal, x, y, xy
    {rotate} rotation value, eg normal, left, right, inverted
    {scale} scale value, eg 1.0

Examples:
```
# default options
xrandr_lmao {
    options = {
        'brightness': 1.0,
        'delta': 0.05,
        'gamma_red': 1.0,
        'gamma_green': 1.0,
        'gamma_blue': 1.0,
        'ignore': [],
        'reflect': normal
        'rotate': normal
        'scale': 1.0,
    }
}

# we can configure per-output parameters too
xrandr_lmao {
    options = {
        'brightness': [0.75, 1.0],    # two outputs
        'rotate': ['normal', 'left']  # two outputs
    }
}

# start with few possilibities
xrandr_lmao {
    # adjust brightness
    format_output = '{name} {brightness}'

    # redshift alternative
    format_output = '{name} {brightness} {gamma_red}'

    # xrandr_rotate alternative
    format_output = '{rotate}'

    # chocolate brown gamma
    options = {
        'gamma_red': 1.70,
        'gamma_green': 1.20,
    }
}

# specify parameters to ignore when randomizing or setting all values
xrandr_lmao {
    options = {'ignore': 'delta'}  # ignore this on outputs
    options = {'ignore': ['rotate', 'reflect']}  # ignore this on outputs
    options = {
        'ignore': [
            ['brightness', 'rotate'],  # ignore this on output 1
            ['gamma_red', 'reflect'],  # ignore this on output 2
        ]
    }
}

# for best results, add this slew of parameters to your config. it is more
beautiful to randomize colors without brightness. randomizing the other
parameters too generally make your `xrandr_lmao` experience a bit more shitty.
xrandr_lmao {
    options = {'ignore': ['brightness', 'delta', 'rotate', 'reflect', 'scale']}
}

# start with few options
xrandr_lmao {
    # adjust brightness
    format_output = '{name} {brightness}'

    # redshift alternative
    format_output = '{name} {brightness} {gamma_red}'

    # xrandr_rotate alternative
    format_output = '{rotate}'
}

# we can configure per-output parameters too
xrandr_lmao {
    options = {
        'brightness': [0.75, 1.0],    # two outputs
        'rotate': ['normal', 'left']  # two outputs
    }
}

# adjust scale to zoom out by default
xrandr_lmao {
    format_output = '{scale}'
    options = {'scale': 1.25}
}

# add delta too so you can adjust the delta live. lmao.
xrandr_lmao {
    format_output = '{name} {brightness} {delta}'
}

# specify outputs to use
xrandr_lmao {
    outputs = ['LVDS-1', 'HDMI-1', 'DP-2', 'DP-3']
        OR
    outputs = ['DP-*']  # fnmatch
}

# it's always good to add arandr or a script
xrandr_lmao {
    on_click 8 = 'exec arandr'
}
```

@author lasers

SAMPLE OUTPUT
[
    {'full_text': 'DP-1 '},
    {'color': '#a9a9a9', 'full_text': '1.0 '},
    {'color': '#ff0000', 'full_text': '1.0 '},
    {'color': '#00ff00', 'full_text': '1.0 '},
    {'color': '#0000ff', 'full_text': '1.0 '},
    {'full_text': 'DP-2 '},
    {'color': '#a9a9a9', 'full_text': '1.0 '},
    {'color': '#ff0000', 'full_text': '1.0 '},
    {'color': '#00ff00', 'full_text': '1.0 '},
    {'color': '#0000ff', 'full_text': '1.0 '},
]
"""

from fnmatch import fnmatch
from operator import add as oper_add, sub as oper_sub
import random


class Py3status:
    """
    """
    # available configuration parameters
    button_next = 4
    button_previous = 5
    button_random = 2
    button_reset = 3
    format = '{format_output}'
    format_output = '{name} {brightness} {gamma_red} {gamma_green} {gamma_blue}'
    format_separator = ' '
    options = {}
    outputs = []

    def post_config_hook(self):
        self.random = (0, 5)
        active_outputs = self._get_xrandr_active_outputs()
        self.gamma_list = ['gamma_red', 'gamma_green', 'gamma_blue']
        delta_list = self.gamma_list + ['brightness', 'delta', 'scale']
        value_reset_list = delta_list + ['rotate', 'reflect']
        self.is_delta = self.py3.format_contains(self.format_output, 'delta')
        self.output_placeholders = sorted(list(set(['delta', 'ignore'] + (
            self.py3.get_placeholders_list(self.format_output)))))

        key = {}
        for index_output, output in enumerate(active_outputs):
            key[output] = {'ignore': []}

            # want a gamma? add all gamma. the command demands it.
            for rgb in self.gamma_list:
                if rgb not in self.output_placeholders:
                    key[output][rgb] = 1.0

            # check options for starting values, otherwise add ours.
            for x in self.output_placeholders:
                if x in self.options:
                    if x == 'ignore':
                        if any(isinstance(el, list) for el in self.options[x]):
                            key[output][x] = self.options[x][index_output]
                        else:
                            key[output][x] = self.options[x]
                    elif isinstance(self.options[x], list):
                        if len(self.options[x]) != len(active_outputs):
                            raise Exception('invalid value: %s' % x)
                        key[output][x] = self.options[x][index_output]
                    else:
                        key[output][x] = self.options[x]
                else:
                    if x in ['brightness', 'scale'] + self.gamma_list:
                        key[output][x] = 1.0
                    elif x in ['reflect', 'rotate']:
                        key[output][x] = 'normal'
                    elif x in ['delta']:
                        key[output][x] = 0.05
                    elif x in ['ignore']:
                        key[output][x] = []

        # initialize outputs in the cog with (contained) option names, their
        # starting or defined values, and the switching rules. simplified.
        self.cog = {}
        for output in active_outputs:
            self.cog[output] = {}
            update_gamma = True
            for name in self.output_placeholders:
                config = {}
                # gamma red, green, blue
                if name in self.gamma_list:
                    if update_gamma:
                        update_gamma = False
                        for rgb in self.gamma_list:
                            self.cog[output][rgb] = {
                                'switch': float(),
                                'value': key[output][rgb],
                                'reset': key[output][rgb],
                            }
                    continue
                # name, ignore
                if name in ['name', 'ignore']:
                    config['switch'] = None
                    if 'name' in name:
                        config['value'] = output
                    elif 'ignore' in name:
                        config['value'] = key[output][name]
                # number
                if name in delta_list:
                    config['switch'] = float()
                # value, reset
                if name in value_reset_list:
                    config['value'] = key[output][name]
                    config['reset'] = key[output][name]
                # rotate, reflect
                if name in ['rotate', 'reflect']:
                    config['index'] = 0
                    if 'rotate' in name:
                        config['switch'] = (
                            ['normal', 'right', 'inverted', 'left']
                        )
                    elif 'reflect' in name:
                        config['switch'] = ['normal', 'x', 'y', 'xy']

                self.cog[output][name] = config

    def _get_xrandr_active_outputs(self):
        data = self.py3.command_output(['xrandr']).splitlines()
        connected_outputs = [x.split() for x in data if ' connected' in x]
        active_outputs = []
        for output in connected_outputs:
            for x in output[2:]:
                if 'x' in x and '+' in x:
                    if self.outputs:
                        for _filter in self.outputs:
                            if fnmatch(output[0], _filter):
                                active_outputs.append(output[0])
                                break
                    else:
                        active_outputs.append(output[0])
                    break
                elif '(' in x:
                    break
        return active_outputs  # returns a list, eg ['DP-2', 'DP-3']

    def _manipulate(self, active_outputs):
        def _2f(value):
            return format(value, '.2f')  # convert 1.5501231 to 1.55

        # make composite to format and command to run
        new_output = []
        command = 'xrandr'
        for output in active_outputs:
            command += ' --output %s' % output
            composites = {}
            update_gamma = True
            for x in self.output_placeholders:
                if 'name' in x:
                    composites[x] = {
                        'full_text': output,
                        'index': '%s' % output,
                    }
                elif 'ignore' in x:
                    composites[x] = {
                        'full_text': ', '.join(self.cog[output][x]['value']),
                        'color': '#6a6a6a',
                    }
                elif 'delta' in x:
                    composites[x] = {
                        'full_text': _2f(self.cog[output][x]['value']),
                        'index': '%s/%s' % (output, x),
                        'color': '#fff000'
                    }
                elif 'brightness' in x:
                    command += ' --%s %s' % (x, self.cog[output][x]['value'])
                    composites[x] = {
                        'full_text': _2f(self.cog[output][x]['value']),
                        'index': '%s/%s' % (output, x),
                        'color': '#a9a9a9'
                    }
                elif 'gamma' in x and update_gamma:
                    update_gamma = False
                    command += ' --gamma %s:%s:%s' % (
                        self.cog[output]['gamma_red']['value'],
                        self.cog[output]['gamma_green']['value'],
                        self.cog[output]['gamma_blue']['value']
                    )
                    colors = ['#ff0000', '#00ff00', '#00bfff']
                    for rgb, color in zip(self.gamma_list, colors):
                        composites[rgb] = {
                            'full_text': _2f(self.cog[output][rgb]['value']),
                            'index': '%s/%s' % (output, rgb),
                            'color': color,
                        }
                elif 'rotate' in x:
                    command += ' --%s %s' % (x, self.cog[output][x]['value'])
                    composites[x] = {
                        'full_text': self.cog[output][x]['value'],
                        'index': '%s/%s' % (output, x),
                        'color': '#00ff00'
                    }
                elif 'reflect' in x:
                    command += ' --%s %s' % (x, self.cog[output][x]['value'])
                    composites[x] = {
                        'full_text': self.cog[output][x]['value'],
                        'index': '%s/%s' % (output, x),
                        'color': '#00ffff'
                    }
                elif 'scale' in x:
                    command += ' --%s %sx%s' % (
                        x, self.cog[output][x]['value'],
                        self.cog[output][x]['value']
                    )
                    composites[x] = {
                        'full_text': _2f(self.cog[output][x]['value']),
                        'index': '%s/%s' % (output, x),
                        'color': '#ff00ff'
                    }

            new_output.append(self.py3.safe_format(
                self.format_output, composites))

        format_separator = self.py3.safe_format(self.format_separator)
        format_output = self.py3.composite_join(format_separator, new_output)
        return format_output, command

    def _scroll_randomize(self, output, name, switch):
        # randomize a number value. for brightness, delta, gamma, scale.
        if isinstance(switch, float):
            self.cog[output][name]['value'] = random.uniform(
                self.random[0], self.random[1])
        # randomize a list value. for reflect and rotate.
        elif isinstance(switch, list):
            self.cog[output][name]['value'] = random.choice(switch)

    def _scroll_reset(self, output, name):
        # reset a number or list value.
        self.cog[output][name]['value'] = self.cog[output][name]['reset']

    def _scroll_values(self, output, name, switch, delta):
        # switch a number value. for brightness, delta, gamma, scale.
        if isinstance(switch, float):
            new_operator = oper_add if delta >= 0 else oper_sub
            self.cog[output][name]['value'] = new_operator(
                self.cog[output][name]['value'],
                self.cog[output]['delta']['value']
            )
        # switch a list of names. for reflect and rotate.
        elif isinstance(switch, list):
            switch = self.cog[output][name]['switch']
            self.cog[output][name]['index'] += delta
            self.cog[output][name]['index'] = (
                self.cog[output][name]['index'] % len(switch)
            )
            new_index = self.cog[output][name]['index']
            self.cog[output][name]['value'] = switch[new_index]

    def xrandr_lmao(self):
        active_outputs = self._get_xrandr_active_outputs()
        format_output, command = self._manipulate(active_outputs)
        self.py3.command_run(command)  # the only place to run a command

        return {
            'cached_until': self.py3.CACHE_FOREVER,
            'full_text': self.py3.safe_format(
                self.format, {
                    'format_output': format_output,
                    'output': len(active_outputs),
                }
            )
        }

    def on_click(self, event):
        if isinstance(event['index'], int):
            self.py3.prevent_refresh()  # ignore numbered indexes
            return
        elif '/' in event['index']:
            output, name = event['index'].split('/')  # users clicked values
        else:
            output, name = event['index'], None  # users clicked names

        button = event['button']
        switch = self.cog[output].get(name, {}).get('switch')

        if button == self.button_reset:
            # reset one thing
            if name:
                self._scroll_reset(output, name)
                return
            # reset all things
            for name in self.output_placeholders:
                switch = self.cog[output][name]['switch']
                if switch is None:
                    continue  # ignore ignore and name
                if name in self.cog[output]['ignore']['value']:
                    continue  # users wish to ignore this
                self._scroll_reset(output, name)

        elif button == self.button_random:
            # randomize one thing
            if name:
                self._scroll_randomize(output, name, switch)
                return
            # randomize all things
            for name in self.output_placeholders:
                switch = self.cog[output][name]['switch']
                if switch is None:
                    continue  # ignore ignore and name
                if name in self.cog[output]['ignore']['value']:
                    continue  # users wish to ignore this
                self._scroll_randomize(output, name, switch)
        elif name:
            if button == self.button_next:
                self._scroll_values(output, name, switch, +1)
            elif button == self.button_previous:
                self._scroll_values(output, name, switch, -1)
        else:
            self.py3.prevent_refresh()


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
