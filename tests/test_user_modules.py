import argparse
import os
import sys

import pkg_resources
import pytest

import py3status
from py3status import core
from py3status.core import Py3statusWrapper


@pytest.fixture(name="status_wrapper")
def make_status_wrapper():
    args = argparse.Namespace()
    return Py3statusWrapper(args)


def test__get_path_based_modules(status_wrapper):
    """Use the list of inbuilt modules as reference to check against."""
    included_modules_path = os.path.join(os.path.dirname(py3status.__file__), "modules")
    status_wrapper.options.__dict__["include_paths"] = [included_modules_path]
    assert os.path.exists(included_modules_path)
    expected_keys = [
        n[:-3] for n in os.listdir(included_modules_path) if n.endswith(".py")
    ]
    modules = status_wrapper._get_path_based_modules()
    assert sorted(modules.keys()) == sorted(expected_keys)


@pytest.mark.xfail(reason="needs some work still ...")
def test__get_entry_point_based_modules(status_wrapper, monkeypatch):
    def return_fake_entry_points(*_):
        class FakeEntryPoint(object):
            Py3status = "I am a fake class"
            module_name = "fake module"

            def __init__(self, name):
                self.name = name

            @staticmethod
            def load():
                from py3status.modules import air_quality
                return air_quality

        return [FakeEntryPoint("spam"), FakeEntryPoint("eggs")]

    class FakeModule(object):
        EXPECTED_CLASS = "Py3status"
        methods = True

        def __init__(self, *args):
            if len(args) == 4:
                assert args[3].__class__.__name__ == self.EXPECTED_CLASS

    monkeypatch.setattr(pkg_resources, "iter_entry_points", return_fake_entry_points)
    monkeypatch.setattr(core, "Module", FakeModule)
    user_modules = status_wrapper._get_entry_point_based_modules()
    status_wrapper.load_modules(["spam", "eggs"], user_modules)
    assert len(user_modules) == 2
    assert user_modules["spam"] == py3status
    assert user_modules["eggs"] == py3status


# def test_explorative(monkeypatch):
#     from py3status import main
#     monkeypatch.setattr(sys, "argv", ["py3status", "-c", "/home/ob/.i3/config.d/i3bar.full.conf"])
#     main()
