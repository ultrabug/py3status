"""
Display static system information.

Configuration parameters:
    format: display format for this module
        *(default 'py3status {py3status_version} '
        '• python {python_version}')*

Format placeholders:
    User identity:
    {username} username, e.g. 'alex'

    Host/kernel:
    {hostname} hostname, e.g. 'toolbx'
    {machine} machine type, e.g. 'x86_64'
    {node} computer's network name, e.g. 'toolbx'
    {processor} processor name, e.g. 'amdk6' (often empty on Linux)
    {release} system's release, e.g. '7.1.4-200.fc44.x86_64'
    {system} system/OS name, e.g. 'Linux'
    {version} e.g. '#1 SMP PREEMPT_DYNAMIC Sat Jul 18 19:16:16 UTC 2026'

    OS/runtime:
    {os_id} distribution ID, e.g. "fedora"
    {os_name} distribution name, e.g. "Fedora Linux"
    {os_pretty_name} distribution pretty name, e.g. "Fedora Linux 44 (KDE Plasma)"
    {os_version} distribution version, e.g. "44 (KDE Plasma)"
    {os_version_id} distribution version ID, e.g. "44"

    Python/py3status:
    {py3status_version} py3status version, e.g. '3.64'
    {python_version} Python version, e.g. '3.14.6'
    {wm_name} py3status window manager, e.g. 'i3' or 'sway'

@author ultrabug, lasers

SAMPLE OUTPUT
{'full_text': 'py3status 3.64 • python 3.14.6'}

uname
{'full_text': 'Linux 4.8.15-300.fc25.x86_64'}

whoami
{'full_text': u'ultrabug'}
"""

from getpass import getuser
from platform import (
    freedesktop_os_release,
    python_version,
    uname,
)
from socket import gethostname

from py3status.version import version as py3status_version


class Py3status:
    """ """

    # available configuration parameters
    format = 'py3status {py3status_version} • python {python_version}'

    def post_config_hook(self):
        self.sysinfo_data = self._get_sysinfo_data()
        self.sysinfo_data["wm_name"] = self.py3._py3_wrapper.config.get("wm_name")

        if self.py3._py3_wrapper.config.get("testing"):
            width = max(map(len, self.sysinfo_data))
            for name, value in sorted(self.sysinfo_data.items()):
                self.py3.log(f"{name:<{width}}  {value}", level="debug")

    @staticmethod
    def _get_sysinfo_data():
        uname_data = uname()

        try:
            os_release = freedesktop_os_release()
        except OSError:
            os_release = {}

        return {
            "username": getuser(),
            "hostname": gethostname(),
            "system": uname_data.system,
            "node": uname_data.node,
            "release": uname_data.release,
            "version": uname_data.version,
            "machine": uname_data.machine,
            "processor": uname_data.processor,
            "python_version": python_version(),
            "py3status_version": py3status_version,
            "os_name": os_release.get("NAME"),
            "os_id": os_release.get("ID"),
            "os_version": os_release.get("VERSION"),
            "os_version_id": os_release.get("VERSION_ID"),
            "os_pretty_name": os_release.get("PRETTY_NAME"),
        }

    def sysinfo(self):
        return {
            "cached_until": self.py3.CACHE_FOREVER,
            "full_text": self.py3.safe_format(self.format, self.sysinfo_data),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
