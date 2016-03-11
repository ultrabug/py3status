# -*- coding: utf-8 -*-
"""
Display uname information.

Configuration parameters:
    cache_timeout: how often we refresh this module in seconds (1h default)
    format: see placeholders below

Format of status string placeholders:
    {system} system/OS name, e.g. 'Linux', 'Windows', or 'Java'
    {node} computer’s network name (may not be fully qualified!)
    {release} system’s release, e.g. '2.2.0' or 'NT'
    {version} system’s release version, e.g. '#3 on degas'
    {machine} machine type, e.g. 'x86_64'
    {processor} the (real) processor name, e.g. 'amdk6'

@author ultrabug (inspired by ndalliard)
"""

from time import time
from platform import uname


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 3600
    format = '{system} {release} {machine}'

    def show_uname(self, i3s_output_list, i3s_config):
        system, node, release, version, machine, processor = uname()
        response = {
            'cached_until': time() + self.cache_timeout,
            'full_text': self.format.format(system=system,
                                            node=node,
                                            release=release,
                                            version=version,
                                            machine=machine,
                                            processor=processor)
        }
        return response


if __name__ == "__main__":
    x = Py3status()
    config = {
        'color_bad': '#FF0000',
        'color_degraded': '#FFFF00',
        'color_good': '#00FF00'
    }
    print(x.show_uname([], config))
