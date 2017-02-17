# -*- coding: utf-8 -*-
"""
Allow modules to be enabled/disabled whilst py3status is running

Configuration parameters:
    format: format to display
        (default '⚙[\?color=good  {enabled}][\?color=bad&if=disabled  {disabled}]')

Format placeholders:
    {count} total number of modules.
    {disabled} number of modules currently disabled.
    {enabled} number of modules currently enabled.

@author tobes
@license BSD
"""


class Py3status:

    format = u'⚙[\?color=good  {enabled}][\?color=bad&if=disabled  {disabled}]'

    def post_config_hook(self):
        module_data = self.py3.py3status_function('module_info') or []
        keys = self.py3.storage_keys()
        for module in module_data:
            module_name = module['name']
            if module_name in keys and not self.py3.storage_get(module_name):
                self.py3.py3status_function('module_disable', module_name)
                self.py3.log(u'Disabling module %s' % module_name)

    def select(self):
        module_info = self.py3.py3status_function('module_info') or []
        count = len(module_info) - 1  # we don't count this module
        enabled = sum(1 for x in module_info if x['enabled']) - 1
        disabled = count - enabled

        return {
            'full_text': self.py3.safe_format(
                self.format, dict(count=count,
                                  enabled=enabled,
                                  disabled=disabled)
            ),
            'cached_until': self.py3.CACHE_FOREVER,
        }

    def _callback(self, module_name, output):
        if output[module_name]:
            self.py3.py3status_function('module_enable', module_name)
        else:
            self.py3.py3status_function('module_disable', module_name)
        self.py3.storage_set(module_name, output[module_name])
        self.py3.update()

    def on_click(self, event):
        module_data = self.py3.py3status_function('module_info')
        data = [(x['name'], x['enabled'])
                for x in module_data
                if x['name'] != self.py3.module_name()]
        self.py3.popup_toggle(data, type='menu', callback=self._callback)


if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test
    module_test(Py3status)
