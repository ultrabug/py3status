# -*- coding: utf-8 -*-
"""
Display system information from uname.

Configuration parameters:
    format: see placeholders below (default '{system} {release} {machine}')

Format placeholders:
    {system} system/OS name, e.g. 'Linux', 'Windows', or 'Java'
    {node} computer’s network name (may not be fully qualified!)
    {release} system’s release, e.g. '2.2.0' or 'NT'
    {version} system’s release version, e.g. '#3 on degas'
    {machine} machine type, e.g. 'x86_64'
    {processor} the (real) processor name, e.g. 'amdk6'

@author ultrabug (inspired by ndalliard)

SAMPLE OUTPUT
{'full_text': 'Linux 4.8.15-300.fc25.x86_64 x86_64'}
"""

from platform import uname


class Py3status:
    """
    """
    # available configuration parameters
    format = '{system} {release} {machine}'

    class Meta:
        deprecated = {
            'remove': [
                {
                    'param': 'cache_timeout',
                    'msg': 'obsolete parameter',
                },
            ],
        }

    def show_uname(self):
        system, node, release, version, machine, processor = uname()
        response = {
            'cached_until': self.py3.CACHE_FOREVER,
            'full_text': self.py3.safe_format(
                self.format,
                dict(system=system,
                     node=node,
                     release=release,
                     version=version,
                     machine=machine,
                     processor=processor))
        }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
