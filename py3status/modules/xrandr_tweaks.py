# -*- coding: utf-8 -*-
"""
Change Xrandr brightness, gamma, rotation, reflection, and more.

Right-click on the value to reset a value.
Right-click on the name to reset all values.
Middle-click on the value to randomize a value.
Middle-click on the name to randomize all values.
Scroll on the value to increase/decrease the value.
Scroll on the name doesn't do anything to the values.

Configuration parameters:
    button_next: mouse button to switch next values (default 4)
    button_previous: mouse button to switch previous values (default 5)
    button_random: mouse button to randomize values (default 2)
    button_reset: mouse button to reset values (default 3)
    button_update: mouse button to run last command (default 1)
    format: display format for this module (default '{format_output}')
    format_output: display format for active outputs
        (default '{name} {gamma_red} {gamma_green} {gamma_blue}')
    format_output_separator: show separator if more than one (default ' ')
    options: specify a dict consisting of option types and a dict
        consisting of output-related settings to use (default {})
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
    {ignore} parameters to ignore, eg brightness, rotate
    {name} output name, eg DP-2, DP-3
    {primary} primary output, eg 0.0, 1.0
    {reflection} reflection values, eg normal, x, y, xy
    {reflect} reflection value, eg normal
    {rotate} rotation value, eg normal
    {rotation} rotation values, eg normal, left, right, inverted
    {scale} scale value, eg 1.0
    {skip_update} values to skip on updates, eg rotate, reflect

format_output placeholders (randomizing ranges):
    {brightness_randomize} brightness randomizing range, eg (0, 5)
    {delta_randomize} delta randomizing range, eg (0, 5)
    {gamma_blue_randomize} gamma blue randomizing range, eg (0, 5)
    {gamma_green_randomize} gamma green randomizing range, eg (0, 5)
    {gamma_red_randomize} gamma red randomizing range, eg (0, 5)
    {scale_randomize} scale randomizing range, eg (0, 5)

format_output placeholders (scrolling ranges):
    {brightness_scroll} brightness scrolling range, eg (-100, 100)
    {delta_scroll} delta scrolling range, eg (-100, 100)
    {gamma_blue_scroll} gamma blue scrolling range, eg (-100, 100)
    {gamma_green_scroll} gamma green scrolling range, eg (-100, 100)
    {gamma_red_scroll} gamma red scrolling range, eg (-100, 100)
    {scale_scroll} scale scrolling range, eg (-100, 100)

format_output_option_{xxx} placeholders:
    {value} display format for this option

Examples:
```
# xrandr_tweaks comes with gamma colors by default. programming can be fun
# when we can repeatedly click on OUTPUT name to find a decent color scheme.

# adjust brightness
xrandr_tweaks {
    format_output = '{name} {brightness}'
}

# redshift alternative
xrandr_tweaks {
    format_output = '{name} {brightness} {gamma_red}'
}

# start with chocolate brown gamma
xrandr_tweaks {
    options = {
        'output': {
            'gamma_red': 1.70,
            'gamma_green': 1.20,
        }
    }
}

# we can also configure per-output parameters
xrandr_tweaks {
    options = {
        'output': {
            'brightness': [0.75, 1.0],      # two outputs
            'rotate': ['normal', 'left'],   # two outputs
            'ignore': [
                ['brightness', 'rotate'],
                ['brightness', 'reflect'],  # two outputs
            ]
        }
    }
}

# default options
xrandr_tweaks {
    # scroll down to OPTIONS to see all options. you can specify options
    # the same way here. we also support scrolling ranges and randomizing
    # ranges for floating values. the ranges should be a 2-tuple consisting
    # of minimal and maximum values, see examples below.
    format_output = '{name} {gamma_blue} {gamma_blue_scroll}'
    options = {
        'output': {
            'gamma_blue': 1.0,
            'gamma_blue_scroll': (-0.3, 3.3), # scrolling range example
            'gamma_blue_randomize': (-10, 10), # randomizing range example
        },
        'format_output': {
            'default': '\?color=lightblue {value:2f}',  # undefined format
            'gamma_blue': '\?color=#00bfff {value:.2f}',
            'gamma_blue_scroll': '\?color=skyblue {value:2f}',
            'gamma_blue_randomize': '\?color=skyblue {value:2f}',
        }
    }
}

# give gamma colors soft colors and hide the values
xrandr_tweaks {
    format_output = '{gamma_red} {gamma_green} {gamma_blue}'
    options = {
        'format_output': {
            'gamma_red': '\?color=tomato R',
            'gamma_green': '\?color=lightgreen G',
            'gamma_blue': '\?color=lightblue B',
        }
    }
}

# ignore parameters when randomizing or resetting all values (options)
xrandr_tweaks {
    options = {
        'output': {
            'ignore': 'delta',               # ignore one thing
                # OR
            'ignore': ['rotate', 'reflect'], # ignore two things
                # OR
            'ignore': [
                ['brightness', 'rotate'],    # ignore this on output 1
                ['gamma_red', 'reflect'],    # ignore this on output 2
            ]
        },
        'format_output': {
            'ignore': '\?color=#6a6a6a {value}',
        }
    }
}

# ignore parameters when randomizing or resetting all values (externals)
xrandr_tweak
    output_option_ignore = 'delta'                # ignore one thing
        # OR
    output_option_ignore = ['rotate', 'reflect']  # ignore two things
        # OR
    output_option_ignore = [
        ['brightness', 'rotate'],    # ignore this on output 1
        ['gamma_red', 'reflect'],    # ignore this on output 2
    ]
    format_output_option_ignore = '\?color=#6a6a6a {value}'
}

# for best results, add this slew of parameters to your config.
it is more practical to randomize colors without brightness and others.
xrandr_tweaks {
    format_output = '{name} {ignore}'
    output_option_ignore = [
        'brightness', 'delta', 'rotate', 'reflect', 'scale'
    ]
}

# adjust scale to zoom out by default
xrandr_tweaks {
    format_output = '{name} {scale}'
    output_option_scale = 1.25
}

# add delta too to adjust and/or randomize delta.
xrandr_tweaks {
    format_output = '{name} {brightness} {delta}'
}

# specify outputs to use
xrandr_tweaks {
    outputs = ['DP-1', 'DP-2', 'DP-3', 'DP-4'] # full
        OR
    outputs = ['DP-*']  # fnmatch
}

# rearrange the outputs
xrandr_tweaks {
    outputs = ['DP-2', 'DP-3']  # DP-2 first
        OR
    outputs = ['DP-3', 'DP-*']  # DP-3 first
}

# it's always good to add arandr or a script
xrandr_tweaks {
    on_click 8 = 'exec arandr'
}

# do you even name your outputs?
xrandr_tweaks {
    output_option_name = ['Timmy!', 'Jimmy!']
    format_output_separator = '\?color=bad  ~~Cripple Fight!~~ '
}

# xrandr_rotate alternative, live update
xrandr_tweaks {
    format_output = '{rotate}'
}

# xrandr_rotate minimal, rotate two ways
xrandr_tweaks {
    format_output = '{name} {rotate}'
    options = {
        'output': {
            'rotation': ['normal', 'left'], # rotate only normal, left
            'skip_update': ['rotate'],  # skip update on scroll
        }
    }
}

# xrandr_rotate maximum, rotate two ways, override values, set rotate layout
xrandr_tweaks {
    format_output = '{name} {rotate}'
    options = {
        'output': {
            'rotate': ['normal', 'left'],   # two outputs, start normal, left
            'rotation': ['normal', 'left'], # rotate only normal, left
            'skip_update': ['rotate'],  # skip update on scroll
        }
    }
    format_output_option_rotate = '\?color=lime '
    format_output_option_rotate += '[\?if=value=normal&show N]'
    format_output_option_rotate += '[\?if=value=inverted&show I]'
    format_output_option_rotate += '[\?if=value=left&show L]'
    format_output_option_rotate += '[\?if=value=right&show R]'
}

# invert screen color
xrandr_tweaks {
    format = 'INVERT {format_output}'
    format_output = '{brightness}'
    options = {
        'output': {
            'brightness_scroll': (-1.0, 1.0),
            'delta': 2.0,
        },
        'format_output': {
            'brightness': '\?if=value=1&color=bad OFF|\?color=good ON',
        }
    }
}

# set primary output
xrandr_tweaks {
    format_output = '{name} {primary} {brightness}'
}
```

@author lasers

SAMPLE OUTPUT
[
    {'full_text': 'DP-2 '},
    {'color': '#a9a9a9', 'full_text': '1.00 '},
    {'color': '#ff0000', 'full_text': '1.00 '},
    {'color': '#00ff00', 'full_text': '1.00 '},
    {'color': '#00bfff', 'full_text': '1.00 '},
    {'full_text': 'DP-3 '},
    {'color': '#a9a9a9', 'full_text': '1.00 '},
    {'color': '#ff0000', 'full_text': '1.00 '},
    {'color': '#00ff00', 'full_text': '1.00 '},
    {'color': '#00bfff', 'full_text': '1.00 '},
]
"""

from fnmatch import fnmatch
from random import choice, uniform


class Py3status:
    """
    """
    # available configuration parameters
    button_next = 4
    button_previous = 5
    button_random = 2
    button_reset = 3
    button_update = 1
    format = '{format_output}'
    format_output = '{name} {gamma_red} {gamma_green} {gamma_blue}'
    format_output_separator = ' '
    options = {}
    outputs = []

    def post_config_hook(self):
        # OPTIONS
        local_options = {
            'output': {
                'brightness': 1.0,
                'delta': 0.05,
                'gamma_blue': 1.0,
                'gamma_green': 1.0,
                'gamma_red': 1.0,
                'ignore': [],
                'name': None,
                'primary': False,
                'randomize': (0, 5),
                'reflect': 'normal',
                'reflection': ['normal', 'xy', 'x', 'y'],
                'rotate': 'normal',
                'rotation': ['normal', 'right', 'inverted', 'left'],
                'scale': 1.0,
                'scroll': (-100, 100),
                'skip_update': [],
            },
            'format_output': {
                'brightness': '\?color=#a9a9a9 {value:.2f}',
                'default': '\?color=lightblue {value:.2f}',
                'delta': '\?color=#fff000 {value:.2f}',
                'gamma_blue': '\?color=#00bfff {value:.2f}',
                'gamma_green': '\?color=#00ff00 {value:.2f}',
                'gamma_red': '\?color=#ff0000 {value:.2f}',
                'ignore': '\?color=#6a6a6a {value}',
                'name': '\?color=#ffffff {value}',
                'primary': '\?if=value&color=gold \[P\]|\?color=darkgray \[P\]',
                'reflect': '\?color=#00ffff {value}',
                'reflection': '\?color=#00a9a9 {value}',
                'rotate': '\?color=#00ff00 {value}',
                'rotation': '\?color=#00a900 {value}',
                'scale': '\?color=#ff00ff {value:.2f}',
                'skip_update': '\?color=#a90000 {value}',
            }
        }
        # update configs
        output_options = local_options['output']
        for key, value in local_options.items():
            local_options[key].update(self.options.get(key, {}))
            external = '{}_option_'.format(key)
            temporary = {}
            for name in value:
                option = getattr(self, external + name, None)
                if option:
                    temporary[name] = option
            local_options.setdefault(key, {}).update(temporary)
        self.options = local_options

        # init configs
        self.click = {'name': None, 'output': None}
        self.last_command = None
        self.gamma_list = ['gamma_red', 'gamma_green', 'gamma_blue']
        delta_list = self.gamma_list + ['brightness', 'delta', 'scale']
        self.is_delta = self.py3.format_contains(self.format_output, 'delta')
        self.is_primary = self.py3.format_contains(self.format_output, 'primary')
        defaults = ['delta', 'ignore', 'skip_update', 'scroll', 'randomize']
        placeholders = list(set(defaults + (
            self.py3.get_placeholders_list(self.format_output)))
        )
        self.format_output_placeholders = [
            x for x in placeholders if x in output_options
        ]
        xrandr_data = self._get_xrandr_data()
        active_outputs = self._get_active_outputs(xrandr_data)
        count_outputs = len(active_outputs)

        key = {}
        for index_output, output in enumerate(active_outputs):
            key[output] = {'ignore': []}

            # want a gamma? the command requires all numbers.
            for rgb in self.gamma_list:
                if rgb not in self.format_output_placeholders:
                    key[output][rgb] = 1.0

            # parse values
            def _parse_values(v):
                count_options = len(v)
                if count_options == count_outputs:
                    key[output][k] = v[index_output]
                if count_options == 0:
                    key[output][k] = v
                elif count_options > count_outputs:
                    key[output][k] = v[-count_outputs]
                elif count_options < count_outputs:
                    key[output][k] = v[-1]

            # check options for starting values, otherwise add ours.
            lists = ['ignore', 'rotation', 'reflection', 'skip_update']
            for k, v in self.options['output'].items():
                key[output][k] = v
                if k in lists:
                    if isinstance(v, list):
                        if any(isinstance(el, list) for el in v):
                            _parse_values(v)
                    else:
                        key[output][k] = [v]
                elif isinstance(v, list):
                    _parse_values(v)

            # add options from default config
            if not key[output].get('name'):
                key[output]['name'] = output
            for name, option in output_options.items():
                key[output].setdefault(name, option)
                if key[output][name] is None:
                    key[output][name] = option

        # debug key log
        # self.py3.log(key)

        # initialize outputs with options
        self.cog = {}
        for output in active_outputs:
            self.cog[output] = {}
            update_gamma = True
            for name in self.format_output_placeholders:
                # gamma red, green, blue
                if name in self.gamma_list:
                    if update_gamma:
                        update_gamma = False
                        for rgb in self.gamma_list:
                            _scroll = key[output].get(
                                '{}_scroll'.format(rgb),
                                key[output]['scroll']
                            )
                            _randomize = key[output].get(
                                '{}_randomize'.format(rgb),
                                key[output]['randomize']
                            )
                            self.cog[output][rgb] = {
                                'switch': float('inf'),
                                'value': key[output][rgb],
                                'reset': key[output][rgb],
                                'scroll': _scroll,
                                'randomize': _randomize,
                            }
                    continue
                config = {'value': key[output][name]}
                # primary
                if name in ['primary']:
                    switch = [True, False]
                    config['index'] = switch.index(key[output][name])
                    config['switch'] = switch
                    config['reset'] = key[output][name]
                # scrollable
                if name in delta_list:
                    config['switch'] = float('inf')
                    config['reset'] = key[output][name]
                    for x in ['scroll', 'randomize']:
                        config[x] = key[output].get(
                            '{}_{}'.format(name, x),
                            key[output][x]
                        )
                # delta ranges can't go under zero
                if 'delta' in name:
                    for x in ['scroll', 'randomize']:
                        new_key = 'delta_{}'.format(x)
                        _param = key[output].get(new_key)
                        if _param:
                            config[x] = _param = (0, _param[1])
                            if new_key in name:
                                config['value'] = _param = (0, _param[1])
                # rotate, reflect
                if name in ['rotate', 'reflect']:
                    if name == 'rotate':
                        new_key = 'rotation'
                    if name == 'reflect':
                        new_key = 'reflection'
                    switch = key[output][new_key]
                    config['index'] = switch.index(key[output][name])
                    if len(switch) > 1:
                        config['switch'] = switch
                        config['reset'] = key[output][name]
                # config
                self.cog[output][name] = config
        # debug cog log
        # self.py3.log(self.cog)

    def _get_xrandr_data(self):
        return self.py3.command_output(['xrandr'])

    def _get_active_outputs(self, xrandr_data):
        lines = xrandr_data.splitlines()
        connected_outputs = [x.split() for x in lines if ' connected' in x]
        active_outputs = []
        for output in connected_outputs:
            for x in output[2:]:
                if 'x' in x and '+' in x:
                    active_outputs.append(output[0])
                    break
                elif '(' in x:
                    break

        if self.outputs:
            matched_outputs = []
            for _filter in self.outputs:
                for output in active_outputs:
                    if fnmatch(output, _filter):
                        if output not in matched_outputs:
                            matched_outputs.append(output)
            return matched_outputs

        return active_outputs  # returns a list, eg ['DP-2', 'DP-3']

    def _manipulate(self, active_outputs):
        # make composites to format and command to run
        new_output = []
        command = 'xrandr'

        if self.is_primary:
            primary = None
            for output, v in self.cog.items():
                if v['primary']['value']:
                    primary = output
                self.cog[output]['primary']['value'] = False
            # if primary is None:
            #     command += ' --noprimary'

        for output in active_outputs:
            options = {}
            update_gamma = True
            command += ' --output {}'.format(output)
            for name in self.format_output_placeholders:
                # values
                value = self.cog[output][name]['value']
                if isinstance(value, list):
                    value = ', '.join(value)
                elif isinstance(value, tuple):
                    value = format(value)
                # primary
                elif 'primary' in name:
                    if output == primary:
                        value = True
                        command += ' --primary'
                # gamma red, green, blue
                elif 'gamma' in name:
                    if update_gamma:
                        update_gamma = False
                        command += ' --gamma {}'.format(':'.join(
                            [format(self.cog[output][rgb]['value'])
                             for rgb in self.gamma_list])
                        )
                # commands
                elif name in ['brightness', 'rotate', 'reflect', 'scale']:
                    command += ' --{} {}'.format(name, value)
                    if name in ['scale']:
                        command += 'x{}'.format(value)
                # composite
                format_output_option = self.py3.safe_format(
                    self.options['format_output'].get(
                        name, self.options['format_output']['default']
                    ),
                    {'value': value}
                )
                index = {'index': '{}/{}'.format(output, name)}
                self.py3.composite_update(format_output_option, index)
                options[name] = format_output_option

            new_output.append(
                self.py3.safe_format(self.format_output, options)
            )

        format_output_separator = self.py3.safe_format(
            self.format_output_separator)
        format_output = self.py3.composite_join(
            format_output_separator, new_output)

        return format_output, command

    def _scroll_randomize(self, output, name, switch):
        # randomize a number value. for brightness, delta, gamma, scale.
        # randomize a list value. for reflect, rotate.
        if isinstance(switch, float):
            value = self.cog[output][name]['randomize']
            self.cog[output][name]['value'] = uniform(value[0], value[1])
        elif isinstance(switch, list):
            self.cog[output][name]['value'] = choice(switch)

    def _scroll_reset(self, output, name, prevent_refresh=True):
        # reset a number or list value.
        reset = self.cog[output][name].get('reset')
        last_value = self.cog[output][name]['value']
        if reset is not None and reset != last_value:
            self.cog[output][name]['value'] = reset
        elif prevent_refresh:
            self.py3.prevent_refresh()

    def _scroll_values(self, output, name, switch, delta):
        # switch a number value. for brightness, delta, gamma, scale.
        # switch a list of names. for reflect and rotate.
        if isinstance(switch, float):
            _scroll = self.cog[output][name]['scroll']
            if delta > 0:
                self.cog[output][name]['value'] = (
                    self.cog[output][name]['value'] +
                    self.cog[output]['delta']['value']
                )
                self.cog[output][name]['value'] = min(
                    self.cog[output][name]['value'], _scroll[1]
                )
            elif delta < 0:
                self.cog[output][name]['value'] = (
                    self.cog[output][name]['value'] -
                    self.cog[output]['delta']['value']
                )
                self.cog[output][name]['value'] = max(
                    self.cog[output][name]['value'], _scroll[0]
                )
        elif isinstance(switch, list):
            switch = self.cog[output][name]['switch']
            self.cog[output][name]['index'] += delta
            self.cog[output][name]['index'] = (
                self.cog[output][name]['index'] % len(switch)
            )
            new_index = self.cog[output][name]['index']
            self.cog[output][name]['value'] = switch[new_index]

    def xrandr_tweaks(self):
        xrandr_data = self._get_xrandr_data()
        active_outputs = self._get_active_outputs(xrandr_data)
        format_output, command = self._manipulate(active_outputs)

        if self.last_command != command:
            name, output = self.click['name'], self.click['output']
            if (not name or
                    name not in self.cog[output]['skip_update']['value']):
                self.py3.command_run(command)
                # debug command log
                line = '============================\n'
                log = line
                for x in command.split('--output'):
                    log += '=== {}\n'.format(x)
                log += line
                self.py3.log(log.strip())
            self.last_command = command

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
            self.py3.prevent_refresh()
            return  # ignore unnamed indexes
        static_names = ['ignore', 'reflection', 'rotation']
        button = event['button']
        output, name = event['index'].split('/')  # eg DP-3/brightness
        switch = self.cog[output][name].get('switch')
        self.click.update({'output': output, 'name': name})

        if button == self.button_update:
            self.py3.command_run(self.last_command)
        elif button == self.button_reset:
            if name == 'name':
                # reset all things
                for name in self.format_output_placeholders:
                    switch = self.cog[output][name].get('switch')
                    if switch is None:
                        continue  # ignore ignore, name, etc
                    if name in self.cog[output]['ignore']['value']:
                        continue  # users wish to ignore this
                    self._scroll_reset(output, name, prevent_refresh=False)
            elif name not in static_names:
                self._scroll_reset(output, name)
            else:
                self.py3.prevent_refresh()
        elif button == self.button_random:
            if name == 'name':
                # randomize all things
                for name in self.format_output_placeholders:
                    if name in static_names:
                        continue  # ignore ignore, name, etc
                    if name in self.cog[output]['ignore']['value']:
                        continue  # users wish to ignore this
                    switch = self.cog[output][name].get('switch')
                    if switch is None:
                        continue  # maybe poor config.
                    self._scroll_randomize(output, name, switch)
            elif name not in static_names:
                # randomize one thing
                self._scroll_randomize(output, name, switch)
            else:
                self.py3.prevent_refresh()
            if not self.is_delta:
                self._scroll_reset(output, 'delta')
        elif switch:
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
