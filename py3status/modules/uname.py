# -*- coding: utf-8 -*-
"""
Display system information.

Configuration parameters:
    format: display format for this module (default '{system} {release}')

Format placeholders:
    {system} system/OS name, e.g. 'Linux', 'Windows', or 'Java'
    {node} computer’s network name (may not be fully qualified!)
    {release} system’s release, e.g. '2.2.0' or 'NT'
    {version} system’s release version, e.g. '#3 on degas'
    {machine} machine type, e.g. 'x86_64'
    {processor} the (real) processor name, e.g. 'amdk6'

@author ultrabug (inspired by ndalliard)

SAMPLE OUTPUT
{'full_text': 'Linux 4.8.15-300.fc25.x86_64'}
"""

from platform import uname


class Py3status:
    """
    """

    # available configuration parameters
    format = "{system} {release}"

    class Meta:
        deprecated = {
            "remove": [{"param": "cache_timeout", "msg": "obsolete parameter"}]
        }

    def uname(self):
        keys = ["system", "node", "release", "version", "machine", "processor"]
        full_text = self.py3.safe_format(self.format, dict(zip(keys, uname())))

        return {"cached_until": self.py3.CACHE_FOREVER, "full_text": full_text}


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
