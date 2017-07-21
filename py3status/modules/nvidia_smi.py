# -*- coding: utf-8 -*-
"""
Display NVIDIA GPU properties

NVSMI, short for NVIDIA System Management Interface, is a software that
provides monitoring information for most NVIDIA products starting with Fermi
or Kelper architecture.  The data is presented in either a plain text or an
XML format, via stdout or a file. NVSMI also provides several management
operations for changing the device state.

Configuration parameters:
    cache_timeout: refresh interval for this module (default 10)
    format: display format for this module (default '{format_properties}')
    format_not_supported: show this when properties are not supported
        (default '[\?color=bad&show NS]')
    format_properties: display format for NVIDIA GPU properties
        (default '[\?color=good {temperature.gpu}°C][\?soft  ]
        [\?color=degraded {memory.used} MB]')
    format_separator: show separator only if more than one (default ' ')

Format placeholders:
    {format_properties} format for NVIDIA GPU properties

Format_properties placeholders:
    {count} The number of NVIDIA GPUs in the system.
    {driver_version} The version of the installed NVIDIA display driver.
    {gpu_name} The official product name of the GPU.
    {gpu_uuid} Globally unique immutable identifier of the GPU.
    {memory.free} Total free memory.
    {memory.total} Total installed GPU memory.
    {memory.used} Total memory allocated by active contexts.
    {temperature.gpu} Core GPU temperature. in degrees C.
    {vbios_version} The BIOS of the GPU board.

    For more placeholders, see 'nvidia-smi --help-query-gpu' for an explicit
    list of valid properties to use. This module uses '--query-gpu` argument
    and with that argument, there are almost 140 GPU properties to choose from.
    Not all of NVIDIA GPU properties are supported with the installed GPU(s).

Color options:
    color_bad: NVIDIA GPU Properties Unavailable

Requires:
    nvidia-smi: NVIDIA System Management Interface program

@author lasers

SAMPLE OUTPUT
[
    {'color': '#00FF00', 'full_text': '64°C '}
    {'color': '#FFFF00', 'full_text': '98 MB'}
]
"""

NVIDIA_CMD = 'nvidia-smi --format=csv,noheader,nounits --query-gpu='
STRING_BAD_PROPERTIES = 'bad properties'
STRING_NOT_INSTALLED = "nvidia-smi: isn't installed"


class Py3status:
    """
    """
    # configuration parameters
    cache_timeout = 10
    format = '{format_properties}'
    format_not_supported = '[\?color=bad&show NS]'
    format_properties = u'[\?color=good {temperature.gpu}°C][\?soft  ]' +\
        u'[\?color=degraded {memory.used} MB]'
    format_separator = ' '

    def post_config_hook(self):
        if not self.py3.check_commands('nvidia-smi'):
            raise Exception(STRING_NOT_INSTALLED)
        try:
            self.properties = self.py3.get_placeholders_list(self.format_properties)
            self.nvidia_cmd = NVIDIA_CMD + '{}'.format(','.join(self.properties))
            self._get_nvidia_properties()
        except:
            raise Exception(STRING_BAD_PROPERTIES)

    def _get_nvidia_properties(self):
        return self.py3.command_output(self.nvidia_cmd)

    def nvidia_gpu(self):
        out = self._get_nvidia_properties()
        nv = []

        for line in out.splitlines():
            # split placeholders results
            line = [x.strip() for x in line.split(',')]
            gpu = dict(zip(self.properties, line))

            # overwrite [Not Supported] with formatted string
            for properties, value in gpu.items():
                if 'Not Supported' in value:
                    gpu[properties] = self.py3.safe_format(
                        self.format_not_supported)

            nv.append(self.py3.safe_format(self.format_properties, gpu))

        format_separator = self.py3.safe_format(self.format_separator)
        format_properties = self.py3.composite_join(format_separator, nv)

        return {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.py3.safe_format(
                self.format, {'format_properties': format_properties})
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
