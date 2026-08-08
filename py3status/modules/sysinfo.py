"""
Display system information.

Configuration parameters:
    format: display format for this module, otherwise random (default None)

Format placeholders:
    Identify:
    {username} username, eg ultrabug
    {hostname} hostname, eg thinkpad

    Platform:
    {system} system/OS name, eg Linux
    {node} computer's network name, eg thinkpad
    {release} system's release, eg 7.1.5-200.fc44.x86_64
    {version} version, eg #1 SMP PREEMPT_DYNAMIC Fri Jul 24 20:44:56 UTC 2026
    {machine} machine type, eg x86_64
    {processor} processor name (often empty on Linux)

    Distribution:
    {os_id} distro ID, eg arch
    {os_name} distro name, eg Arch Linux
    {os_pretty_name} distro pretty name, eg Arch Linux
    {os_version} distro version (based on distro)
    {os_version_id} distro version ID (based on distro)

    Runtime:
    {py3status_version} py3status version, eg 3.64
    {python_version} Python version, eg 3.14.6
    {wm_name} window manager, eg i3 or sway

Notes:
    whoami: Inspired by ndalliard
    uname: Inspired by i3 FAQ
        https://faq.i3wm.org/question/1618/add-user-name-to-status-bar.1.html

Examples:
```
# display platform information
sysinfo uname {
    format = '{system} {release}'
}

# display distribution information
sysinfo distro {
    format = "{os_name} {os_version_id}"
}

# display logged-in username
sysinfo whoami {
    format = "{username}"
}
```

@author ultrabug

SAMPLE OUTPUT
[
    {'full_text': 'release '},
    {'full_text': '7.1.5-200.fc44.x86_64', 'color': '#A9A9A9'},
]

uname
{'full_text': 'Linux 4.8.15-300.fc25.x86_64'}

whoami
{'full_text': 'ultrabug'}
"""

from getpass import getuser
from platform import (
    freedesktop_os_release,
    python_version,
    uname,
)
from random import choice
from socket import gethostname

from py3status.version import version as py3status_version


class Py3status:
    """ """

    # available configuration parameters
    format = None

    def post_config_hook(self):
        # platform
        self.sys = uname()._asdict()

        # distribution
        os_release = freedesktop_os_release()
        for key in ("NAME", "ID", "VERSION", "VERSION_ID", "PRETTY_NAME"):
            self.sys[f"os_{key.lower()}"] = os_release.get(key)

        # runtime/identify
        self.sys.update(
            username=getuser(),
            hostname=gethostname(),
            python_version=python_version(),
            py3status_version=py3status_version,
            wm_name=self.py3.get_wm_msg().removesuffix("msg").removesuffix("-"),
        )

        if not self.format:
            keys, values = (("version",), (None, ""))
            key, value = choice(
                [(k, v) for k, v in self.sys.items() if k not in keys and v not in values]
            )
            self.format = r"{key} [\?color=darkgray {value}]"
            self.sys.update(key=key, value=value)

        if self.py3._py3_wrapper.config.get("testing"):
            width = max(map(len, self.sys))
            for name, value in sorted(self.sys.items()):
                self.py3.log(f"{name:<{width}}  {value}", level="debug")

    def sysinfo(self):
        return {
            "cached_until": self.py3.CACHE_FOREVER,
            "full_text": self.py3.safe_format(self.format, self.sys),
        }


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
