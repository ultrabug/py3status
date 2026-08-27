"""Shared pytest fixtures for the i3status-compatible module tests."""

from unittest.mock import Mock

import pytest


@pytest.fixture
def make_module():
    def _make_module(cls, **config):
        module = cls()
        for key, value in config.items():
            setattr(module, key, value)
        module.py3 = Mock()
        module.py3.COLOR_BAD = "#FF0000"
        module.py3.CACHE_FOREVER = -1
        module.py3.time_in = Mock(return_value=1)
        return module

    return _make_module
