# -*- coding: utf-8 -*-
"""
Display which graphics device is in use using prime-select


Configuration parameters:
    cache_timeout: how often to update the bar (default 60)
    format: (default 'GPU: {device}')

Format placeholders:
    {device} Name of device currently in use

Requires:
    nvidia-prime: nvidia's tool to switch graphics device (nvidia or intel)

Example:
```
nvidia_prime {
    format = "GPU: {device}"
    cache_timeout: 600
}

```

@author Jørn Sandvik Nilsson

SAMPLE_OUTPUT
{'full_text': 'GPU: intel'}

"""

from py3status import exceptions


class Py3status:
    """
    """

    # available configuration parameters
    cache_timeout = 60
    format = "GPU: {device}"

    def nvidia_prime(self):

        device = "unknown"
        try:
            device = self.py3.command_output(["prime-select", "query"]).strip()
        except exceptions.CommandError:
            pass

        return {
            'full_text': self.py3.safe_format(
                self.format,
                dict(device=device)),
            'cached_until': self.py3.time_in(self.cache_timeout)
        }

if __name__ == "__main__":
    """
    Run module in test mode.
    """
    from py3status.module_test import module_test

    module_test(Py3status)
