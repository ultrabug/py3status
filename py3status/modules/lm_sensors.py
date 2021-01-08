r"""
Display temperatures, voltages, fans, and more from hardware sensors.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    chips: specify a list of chips to use (default [])
    format: display format for this module (default '{format_chip}')
    format_chip: display format for chips (default '{name} {format_sensor}')
    format_chip_separator: show separator if more than one (default ' ')
    format_sensor: display format for sensors
        (default '[\?color=darkgray {name}] [\?color=auto.input&show {input}]')
    format_sensor_separator: show separator if more than one (default ' ')
    sensors: specify a list of sensors to use (default [])
    thresholds: specify color thresholds to use (default {'auto.input': True})

Format placeholders:
    {format_chip}   format for chips

Format_chip placeholders:
    {name}          chip name, eg coretemp-isa-0000, nouveau-pci-0500
    {adapter}       adapter type, eg ISA adapter, PCI adapter
    {format_sensor} format for sensors

Format_sensor placeholders:
    {name}          sensor name, eg core_0, gpu_core, temp1, fan1

    See `sensors -u` for a full list of placeholders for `format_chip`,
    `format_sensors` without the prefixes, `chips` and `sensors` options.

    See https://www.kernel.org/doc/Documentation/hwmon/sysfs-interface
    for more information on the sensor placeholders.

Color options for `auto.input` threshold:
    color_zero: zero value or less (color red)
    color_min: minimum value (color lightgreen)
    color_excl_input: input value excluded from threshold (color None)
    color_input: input value (color lime)
    color_near_max: input value near maximum value (color yellow)
    color_max: maximum value (color orange)
    color_near_crit: input value near critical value (color lightcoral)
    color_crit: critical value (color red)

Color thresholds:
    format_sensor:
        xxx: print a color based on the value of `xxx` placeholder
        auto.input: print a color based on the value of `input` placeholder
            against a customized threshold

Requires:
    lm_sensors: a tool to read temperature/voltage/fan sensors
    sensors-detect: see `man sensors-detect # --auto` to read about
        using defaults or to compile a list of kernel modules

Examples:
```
# identify possible chips, sensors, placeholders, etc
    [user@py3status ~] $ sensors -u
    ----------------------------- # ──────────────────────────────────────
    coretemp-isa-0000             # chip {name}         # chip: coretemp*
    Adapter: ISA adapter          #  ├── {adapter} type
    ----                          #  │------------------------------------
    Core 0:                       #  ├── sensor {name}  # sensor: core_0
      temp2_input: 48.000         #  │    ├── {input}
      temp2_max: 81.000           #  │    ├── {max}
      temp2_crit: 91.000          #  │    ├── {crit}
      temp2_crit_alarm: 0.000     #  │    └── {crit_alarm}
    Core 1:                       #  └── sensor {name}  # sensor: core_1
      temp3_input: 48.000         #       ├── {input}
      temp3_max: 81.000           #       ├── {max}
      temp3_crit: 91.000          #       ├── {crit}
      temp3_crit_alarm: 0.000     #       └── {crit_alarm}
                                  # ──────────────────────────────────────
    k10temp-pci-00c3              # chip {name}         # chip: k10temp*
    Adapter: PCI adapter          #  ├── {adapter} type
    ----                          #  │------------------------------------
    temp1:                        #  ├── sensor {name}  # sensor: temp1
      temp1_input: 30.000         #  │    ├── {input}
      temp1_max: -71.000          #  │    ├── {max}
      temp1_min: -15.000          #  │    ├── {min}
      temp1_alarm: 1.000          #  │    ├── {alarm}
      temp1_offset: 0.000         #  │    ├── {offset}
      temp1_beep: 0.000           #  │    └── {beep}
    intrusion0:                   #  └── sensor {name}  # sensor: intrusion0
      intrusion0_alarm: 0.000     #       └── {alarm}

    Solid lines denotes chips. Dashed lines denotes sensors.
    Sensor names are lowercased and its spaces replaced with underscores.
    The numbered prefixes, eg `temp1_*` are removed to keep names clean.

# specify chips to use
lm_sensors {
    chips = ['coretemp-isa-0000']  # full
        OR
    chips = ['coretemp*']  # fnmatch
}

# specify sensors to use
lm_sensors {
    sensors = ['core_0', 'core_1', 'core_2', 'core_3']  # full
        OR
    sensors = ['core_*']  # fnmatch
}

# show name per chip, eg CPU 35°C 36°C 37°C 39°C GPU 52°C
lm_sensors {
    format_chip = '[\?if=name=coretemp-isa-0000 CPU ]'
    format_chip += '[\?if=name=nouveau-pci-0500 GPU ]'
    format_chip += '{format_sensor}'
    format_sensor = '\?color=auto.input {input}°C'
    sensors = ['core*', 'temp*']
}

# show name per sensor, eg CPU1 35°C CPU2 36°C CPU3 37°C CPU4 39°C GPU 52°C
lm_sensors {
    format_chip = '{format_sensor}'
    format_sensor = '[\?if=name=core_0 CPU1 ]'
    format_sensor += '[\?if=name=core_1 CPU2 ]'
    format_sensor += '[\?if=name=core_2 CPU3 ]'
    format_sensor += '[\?if=name=core_3 CPU4 ]'
    format_sensor += '[\?if=name=gpu_core GPU ]'
    format_sensor += '[\?color=auto.input {input}°C]'
    sensors = ['core*', 'temp*']
}
```

@author lasers

SAMPLE OUTPUT
[
    {'full_text': 'coretemp-isa-000 '},
    {'full_text': 'core_0 ', 'color': '#a9a9a9'},
    {'full_text': '39 ', 'color': '#00ff00'},
    {'full_text': 'core_1 ', 'color': '#a9a9a9'},
    {'full_text': '40', 'color': '#00ff00'},
]

chip_names
[
    {'full_text': 'CPU '},
    {'full_text': '62°C ', 'color': '#00ff00'},
    {'full_text': '76°C ', 'color': '#ffff00'},
    {'full_text': '83°C ', 'color': '#ffa500'},
    {'full_text': '92°C ', 'color': '#ff0000'},
    {'full_text': 'GPU '},
    {'full_text': '52°C', 'color': '#00ff00'},
]

sensor_names
[
    {'full_text': 'CPU1 '},
    {'full_text': '62°C ', 'color': '#00ff00'},
    {'full_text': 'CPU2 '},
    {'full_text': '76°C ', 'color': '#ffff00'},
    {'full_text': 'TEMP1 '},
    {'full_text': '30 ', 'color': '#ffa500'},
    {'full_text': 'TEMP2 '},
    {'full_text': '27 ', 'color': '#ffa500'},
    {'full_text': 'GPU '},
    {'full_text': '52°C', 'color': '#00ff00'},
]
"""

from fnmatch import fnmatch
from collections import OrderedDict

STRING_NOT_INSTALLED = "not installed"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    chips = []
    format = "{format_chip}"
    format_chip = "{name} {format_sensor}"
    format_chip_separator = " "
    format_sensor = r"[\?color=darkgray {name}] [\?color=auto.input&show {input}]"
    format_sensor_separator = " "
    sensors = []
    thresholds = {"auto.input": True}

    def post_config_hook(self):
        if not self.py3.check_commands("sensors"):
            raise Exception(STRING_NOT_INSTALLED)

        placeholders = self.py3.get_placeholders_list(self.format_sensor)
        format_sensor = {x: ":g" for x in placeholders if x != "name"}
        self.sensor_placeholders = [x for x in placeholders if x != "name"]
        self.format_sensor = self.py3.update_placeholder_formats(
            self.format_sensor, format_sensor
        )

        self.first_run = True
        self.lm_sensors_command = "sensors -u"
        if not self.py3.format_contains(self.format_chip, "adapter"):
            self.lm_sensors_command += "A"  # don't print adapters

        if self.chips:
            lm_sensors_data = self._get_lm_sensors_data()
            chips = []
            for _filter in self.chips:
                for chunk in lm_sensors_data.split("\n\n")[:-1]:
                    for line in chunk.splitlines():
                        if fnmatch(line, _filter):
                            chips.append(line)
                        break
            self.lm_sensors_command += " {}".format(" ".join(chips))

        self.sensors = {"list": [], "name": {}, "sensors": self.sensors}

        self.thresholds_auto = False
        self.thresholds_man = self.py3.get_color_names_list(self.format_sensor)
        if (
            all("auto.input" in x for x in [self.thresholds, self.thresholds_man])
            and "input" in placeholders
        ):
            self.color_zero = self.py3.COLOR_ZERO or "red"
            self.color_input = self.py3.COLOR_INPUT or "lime"
            self.color_min = self.py3.COLOR_MIN or "lightgreen"
            self.color_excl_input = self.py3.COLOR_EXCL_INPUT or None
            self.color_near_max = self.py3.COLOR_NEAR_MAX or "yellow"
            self.color_max = self.py3.COLOR_MAX or "orange"
            self.color_near_crit = self.py3.COLOR_NEAR_CRIT or "lightcoral"
            self.color_crit = self.py3.COLOR_CRIT or "red"

            self.thresholds_auto = self.thresholds["auto.input"]
            del self.thresholds["auto.input"]

        if "auto.input" in self.thresholds_man:
            self.thresholds_man.remove("auto.input")

    def _get_lm_sensors_data(self):
        return self.py3.command_output(self.lm_sensors_command)

    def lm_sensors(self):
        lm_sensors_data = self._get_lm_sensors_data()
        new_chip = []

        for chunk in lm_sensors_data.split("\n\n")[:-1]:
            chip = {"sensors": OrderedDict()}
            first_line = True
            sensor_name = None
            new_sensor = []

            for line in chunk.splitlines():
                if line.startswith("  "):
                    if not sensor_name:
                        continue
                    key, value = line.split(": ")
                    prefix, key = key.split("_", 1)
                    chip["sensors"][sensor_name][key] = value
                elif first_line:
                    chip["name"] = line
                    first_line = False
                elif "Adapter:" in line:
                    chip["adapter"] = line[9:]
                else:
                    try:
                        sensor_name = self.sensors["name"][line]
                    except KeyError:
                        sensor_name = line[:-1].lower().replace(" ", "_")
                        self.sensors["name"][line] = sensor_name
                    if self.sensors["sensors"]:
                        if self.first_run:
                            for _filter in self.sensors["sensors"]:
                                if fnmatch(sensor_name, _filter):
                                    self.sensors["list"].append(sensor_name)
                        if sensor_name not in self.sensors["list"]:
                            sensor_name = None
                            continue
                    chip["sensors"][sensor_name] = {}

            for name, sensor in chip["sensors"].items():
                sensor["name"] = name

                for x in self.thresholds_man:
                    if x in sensor:
                        self.py3.threshold_get_color(sensor[x], x)

                if self.thresholds_auto:
                    auto_input = []
                    _input = sensor.get("input")
                    if self.first_run and _input is not None:
                        _input = float(_input)
                        _min = float(sensor.get("min", 0))
                        _max = float(sensor.get("max", 0))
                        _crit = float(sensor.get("crit", 0))
                        auto_input.append((0, self.color_zero))
                        if _min or _max or _crit:
                            _color_input = self.color_input
                        else:
                            _color_input = self.color_excl_input
                        auto_input.append((0.001, _color_input))
                        if _min >= _input:
                            auto_input.append((_min, self.color_min))
                        if _max:
                            _near_max = _max - _max / 100 * 10
                            auto_input.append((_near_max, self.color_near_max))
                            auto_input.append((_max, self.color_max))
                        if _crit:
                            _near_crit = _crit - _crit / 100 * 10
                            auto_input.append((_near_crit, self.color_near_crit))
                            auto_input.append((_crit, self.color_crit))

                    key = "{}/{}".format(chip["name"], sensor["name"])
                    self.py3.threshold_get_color(
                        _input, ("auto.input", key, auto_input)
                    )

                for x in self.sensor_placeholders:
                    if x not in sensor:
                        sensor[x] = None

                new_sensor.append(self.py3.safe_format(self.format_sensor, sensor))

            format_sensor_separator = self.py3.safe_format(self.format_sensor_separator)
            format_sensor = self.py3.composite_join(format_sensor_separator, new_sensor)

            chip["format_sensor"] = format_sensor
            del chip["sensors"]

            new_chip.append(self.py3.safe_format(self.format_chip, chip))

        format_chip_separator = self.py3.safe_format(self.format_chip_separator)
        format_chip = self.py3.composite_join(format_chip_separator, new_chip)
        self.first_run = False

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(
                self.format, {"format_chip": format_chip}
            ),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
