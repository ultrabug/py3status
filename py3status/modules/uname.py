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

from platform import uname


class Py3status:
    """
    """
    # available configuration parameters
    cache_timeout = 3600
    format = '{system} {release} {machine}'

    def show_uname(self):
        system, node, release, version, machine, processor = uname()
        response = {
            'cached_until': self.py3.time_in(self.cache_timeout),
            'full_text': self.format.format(system=system,
                                            node=node,
                                            release=release,
                                            version=version,
                                            machine=machine,
                                            processor=processor)
        }
        return response


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
