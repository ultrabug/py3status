# -*- coding: utf-8 -*-
"""
Display NVIDIA properties currently exhibiting in the NVIDIA GPUs.

nvidia-smi, short for NVIDIA System Management Interface program, is a cross
platform tool that supports all standard NVIDIA driver-supported Linux distros.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{format_gpu}')
    format_gpu: display format for NVIDIA GPUs
        *(default '{gpu_name} [\?color=temperature.gpu {temperature.gpu}°C] '
        '[\?color=memory.used_percent {memory.used_percent}%]')*
    format_gpu_separator: show separator if more than one (default ' ')
    thresholds: specify color thresholds to use
        (default [(0, 'good'), (65, 'degraded'), (75, 'orange'), (85, 'bad')])

Format placeholders:
    {format_gpu} format for NVIDIA GPUs

format_gpu placeholders:
    {index}               Zero based index of the GPU.
    {count}               The number of NVIDIA GPUs in the system
    {driver_version}      The version of the installed NVIDIA display driver
    {gpu_name}            The official product name of the GPU
    {gpu_uuid}            Globally unique immutable identifier of the GPU
    {memory.free}         Total free memory
    {memory.total}        Total installed GPU memory
    {memory.used}         Total memory allocated by active contexts
    {memory.used_percent} Total memory allocated by active contexts percentage
    {temperature.gpu}     Core GPU temperature in degrees C

    Use `python /path/to/nvidia_smi.py --list-properties` for a full list of
    supported NVIDIA properties to use. Not all of supported NVIDIA properties
    will be usable. See `nvidia-smi --help-query-gpu` for more information.

Color thresholds:
    format_gpu:
        `xxx`: print a color based on the value of NVIDIA `xxx` property

Requires:
    nvidia-smi: command line interface to query NVIDIA devices

Examples:
```
# add {memory.used}
nvidia_smi {
    format_gpu = '{gpu_name} [\?color=temperature.gpu {temperature.gpu}°C] '
    format_gpu += '[\?color=memory.used_percent {memory.used} MiB'
    format_gpu += '[\?color=darkgray&show \|]{memory.used_percent:.1f}%]'
}
```

@author lasers

SAMPLE OUTPUT
[
    {'full_text': 'Quadro NVS 295 '},
    {'color': '#00ff00', 'full_text': '51°C '},
    {'color': '#00ff00', 'full_text': '60.8%'},
]

percent
[
    {'full_text': 'GPU '},
    {'full_text': '73°C ', 'color': '#ffff00'},
    {'full_text': '192 MiB', 'color': '#ffa500'},
    {'full_text': '|', 'color': '#a9a9a9'},
    {'full_text': '75.3%', 'color': '#ffa500'}
]
"""

STRING_NOT_INSTALLED = "not installed"


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 10
    format = "{format_gpu}"
    format_gpu = (
        u"{gpu_name} [\?color=temperature.gpu {temperature.gpu}°C] "
        "[\?color=memory.used_percent {memory.used_percent}%]"
    )
    format_gpu_separator = " "
    thresholds = [(0, "good"), (65, "degraded"), (75, "orange"), (85, "bad")]

    def post_config_hook(self):
        command = "nvidia-smi --format=csv,noheader,nounits --query-gpu="
        if not self.py3.check_commands(command.split()[0]):
            raise Exception(STRING_NOT_INSTALLED)
        self.properties = self.py3.get_placeholders_list(self.format_gpu)

        format_gpu = {x: ":.1f" for x in self.properties if "used_percent" in x}
        self.format_gpu = self.py3.update_placeholder_formats(
            self.format_gpu, format_gpu
        )

        for name in ["memory.used_percent"]:
            if name in self.properties:
                self.properties.remove(name)
        for name in ["memory.used", "memory.total"]:
            if name not in self.properties:
                self.properties.append(name)
        self.nvidia_command = command + ",".join(self.properties)

        self.thresholds_init = self.py3.get_color_names_list(self.format_gpu)

    def _get_nvidia_data(self):
        return self.py3.command_output(self.nvidia_command)

    def nvidia_smi(self):
        nvidia_data = self._get_nvidia_data()
        new_gpu = []

        for line in nvidia_data.splitlines():
            gpu = dict(zip(self.properties, line.split(", ")))
            gpu["memory.used_percent"] = (
                float(gpu["memory.used"]) / float(gpu["memory.total"]) * 100.0
            )
            for x in self.thresholds_init:
                if x in gpu:
                    self.py3.threshold_get_color(gpu[x], x)

            new_gpu.append(self.py3.safe_format(self.format_gpu, gpu))

        format_gpu_separator = self.py3.safe_format(self.format_gpu_separator)
        format_gpu = self.py3.composite_join(format_gpu_separator, new_gpu)

        return {
            "cached_until": self.py3.time_in(self.cache_timeout),
            "full_text": self.py3.safe_format(self.format, {"format_gpu": format_gpu}),
        }


if __name__ == "__main__":
    from sys import argv

    if "--list-properties" in argv:
        from sys import exit
        from json import dumps
        from subprocess import check_output

        help_cmd = "nvidia-smi --help-query-gpu"
        help_data = check_output(help_cmd.split()).decode()

        new_properties = []
        e = ["Default", "Exclusive_Thread", "Exclusive_Process", "Prohibited"]
        for line in help_data.splitlines():
            if line.startswith('"'):
                properties = line.split('"')[1::2]
                for name in properties:
                    if name not in e:
                        new_properties.append(name)

        properties = ",".join(new_properties)
        gpu_cmd = "nvidia-smi --format=csv,noheader,nounits --query-gpu="
        gpu_data = check_output((gpu_cmd + properties).split()).decode()

        new_gpus = []
        msg = "This GPU contains {} supported properties."
        for line in gpu_data.splitlines():
            gpu = dict(zip(new_properties, line.split(", ")))
            gpu = {k: v for k, v in gpu.items() if "[Not Supported]" not in v}
            gpu["= " + msg.format(len(gpu))] = ""
            gpu["=" * (len(msg) + 2)] = ""
            new_gpus.append(gpu)

        print(dumps(new_gpus, sort_keys=True, indent=4))
        exit()
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
