r"""
Display AMD information currently exhibiting in the AMD GPUs.

amdsmi, short for AMD System Management Interface, is a cross platform
tool that supports all standard AMD driver-supported Linux distros.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{format_gpu}')
    format_gpu: display format for AMD GPUs
        *(default '{market_name} [\?color=temperature_edge '
        '{temperature_edge}°C] [\?color=vram_used_percent '
        '{vram_used_percent}%]')*
    format_gpu_separator: show separator if more than one (default ' ')
    memory_unit: specify memory unit, eg 'KiB', 'MiB', 'GiB', otherwise auto,
        or None to leave values/units as-is (default 'B')
    thresholds: specify color thresholds to use
        (default [(0, 'good'), (65, 'degraded'), (75, 'orange'), (85, 'bad')])

Format placeholders:
    {format_gpu} format for AMD GPUs

format_gpu placeholders:
    {market_name}       official product name
    {temperature_edge}  core GPU temperature
    {vram_used}         VRAM used
    {vram_used_unit}    VRAM used unit
    {vram_used_percent} VRAM used percentage
    {vram_total}        total VRAM
    {vram_total_unit}   total VRAM unit

    Run `python /path/to/amd_smi.py --list-fields` for a full list of
    supported field names. Not all supported field names will be usable.

Color thresholds:
    format_gpu:
        `xxx`: print a color based on the value of AMD `xxx` field

Requires:
    amdsmi: python library to query AMD devices

Examples:
```
# display used/total VRAM
amd_smi {
    format_gpu = '{market_name} [\?color=temperature_edge '
    format_gpu += '{temperature_edge}°C] '
    format_gpu += '[\?color=vram_used_percent {vram_used_percent:.1f}%] '
    format_gpu += '[{vram_used} {vram_used_unit}/{vram_total} {vram_total_unit}]'
}
```

@author lasers

SAMPLE OUTPUT
[
    {'full_text': 'AMD Radeon 780M Graphics '},
    {'color': '#00ff00', 'full_text': '58°C 26.6%'},
]

raw_vram
[
    {'full_text': 'AMD Radeon 780M Graphics '},
    {'color': '#00ff00', 'full_text': '58°C 26.6% '},
    {'full_text': '1091 MB/4096 MB'},
]
"""

import inspect

import amdsmi

DERIVED_FIELDS = {
    "vram_used_percent": ("vram_used", "vram_total"),
    "vram_used_unit": ("vram_used",),
    "vram_total_unit": ("vram_total",),
}


class Py3status:
    """ """

    # available configuration parameters
    cache_timeout = 10
    format = "{format_gpu}"
    format_gpu = (
        r"{market_name} [\?color=temperature_edge "
        r"{temperature_edge}°C] "
        r"[\?color=vram_used_percent "
        r"{vram_used_percent}%]"
    )
    format_gpu_separator = " "
    memory_unit = "B"
    thresholds = [(0, "good"), (65, "degraded"), (75, "orange"), (85, "bad")]

    def post_config_hook(self):
        amdsmi.amdsmi_init()
        self._handles = amdsmi.amdsmi_get_processor_handles()

        # apply :.1f to *_percent placeholders
        placeholders = self.py3.get_placeholders_list(self.format_gpu)
        format_gpu = {x: ":.1f" for x in placeholders if x.endswith("_percent")}
        self.format_gpu = self.py3.update_placeholder_formats(self.format_gpu, format_gpu)
        self.thresholds_init = self.py3.get_color_names_list(self.format_gpu)

        # collect every field name format_gpu needs
        needed = set(placeholders) | set(self.thresholds_init)
        for field, sources in DERIVED_FIELDS.items():
            if field in needed:
                needed.update(sources)
        self._need_temperature = any(x.startswith("temperature_") for x in needed)

        # narrow every discovered call down to what's actually needed
        all_calls = self._discover_calls()
        self._calls = all_calls
        if self._handles:
            handle = self._handles[0]
            self._calls = []
            for call in all_calls:
                try:
                    keys = self._call_flat(call, handle)
                except Exception:
                    continue
                if needed & keys.keys():
                    self._calls.append(call)

    @staticmethod
    def _discover_calls():
        calls = []
        for name in dir(amdsmi):
            if not name.startswith("amdsmi_get_"):
                continue
            func = getattr(amdsmi, name)
            try:
                signature = inspect.signature(func)
            except (TypeError, ValueError):
                continue
            required = [
                p for p in signature.parameters.values() if p.default is inspect.Parameter.empty
            ]
            if len(required) == 1:
                calls.append(func)
        return calls

    @staticmethod
    def _call_flat(call, handle):
        value = call(handle)
        if isinstance(value, dict):
            return Py3status._flatten(value)
        return Py3status._flatten(value, call.__name__.replace("amdsmi_get_", ""))

    @staticmethod
    def _flatten(value, prefix=""):
        if not isinstance(value, (dict, list)):
            if not isinstance(value, (str, int, float, bool, type(None))):
                return {}
            if value == "N/A":
                return {}
            return {prefix: value}
        pairs = value.items() if isinstance(value, dict) else enumerate(value)
        flat = {}
        for key, sub_value in pairs:
            flat.update(Py3status._flatten(sub_value, f"{prefix}_{key}" if prefix else str(key)))
        return flat

    @staticmethod
    def _fetch(calls, handle, need_temperature=True):
        entry = {}
        for call in calls:
            try:
                entry.update(Py3status._call_flat(call, handle))
            except Exception:
                continue
        if need_temperature:
            sensors = {
                "edge": amdsmi.AmdSmiTemperatureType.EDGE,
                "hotspot": amdsmi.AmdSmiTemperatureType.HOTSPOT,
                "vram": amdsmi.AmdSmiTemperatureType.VRAM,
            }
            temperatures = {}
            for name, sensor in sensors.items():
                try:
                    temperatures[name] = amdsmi.amdsmi_get_temp_metric(
                        handle, sensor, amdsmi.AmdSmiTemperatureMetric.CURRENT
                    )
                except Exception:
                    continue
            entry.update(Py3status._flatten(temperatures, "temperature"))
        return entry

    def amd_smi(self):
        new_gpu = []
        for handle in self._handles:
            gpu = self._fetch(self._calls, handle, self._need_temperature)

            used = gpu.get("vram_used")
            total = gpu.get("vram_total")
            if used is not None and total:
                gpu["vram_used_percent"] = used / total * 100
                for key in ("vram_used_unit", "vram_total_unit"):
                    gpu[key] = "MB"

            threshold_gpu = gpu.copy()

            if self.memory_unit:
                for key in ("vram_used", "vram_total"):
                    if key not in gpu:
                        continue
                    value = gpu[key] * (1024**2)
                    gpu[key], gpu[f"{key}_unit"] = self.py3.format_units(value, self.memory_unit)

            for x in self.thresholds_init:
                if x in threshold_gpu:
                    self.py3.threshold_get_color(threshold_gpu[x], x)

            new_gpu.append(self.py3.safe_format(self.format_gpu, gpu))

        format_gpu_separator = self.py3.safe_format(self.format_gpu_separator)
        format_gpu = self.py3.composite_join(format_gpu_separator, new_gpu)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, {"format_gpu": format_gpu}),
        }

    def kill(self):
        amdsmi.amdsmi_shut_down()


if __name__ == "__main__":
    if "--list-fields" in __import__("sys").argv:
        from json import dumps
        from sys import exit

        amdsmi.amdsmi_init()
        handles = amdsmi.amdsmi_get_processor_handles()
        calls = Py3status._discover_calls()

        new_gpus = []
        msg = "This GPU contains {} supported fields."
        for handle in handles:
            fields = Py3status._fetch(calls, handle)
            gpu = dict(sorted(fields.items()))
            gpu["= " + msg.format(len(fields))] = ""
            gpu["=" * (len(msg) + 2)] = ""
            new_gpus.append(gpu)

        print(dumps(new_gpus, sort_keys=True, indent=4))
        amdsmi.amdsmi_shut_down()
        exit()
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
