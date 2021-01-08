import argparse
from pathlib import Path

import pkg_resources
import pytest

import py3status
from py3status.core import Py3statusWrapper, ENTRY_POINT_KEY


@pytest.fixture(name="status_wrapper")
def make_status_wrapper():
    args = argparse.Namespace()
    status_wrapper = Py3statusWrapper(args)
    return status_wrapper


def test__get_path_based_modules(status_wrapper):
    """Use the list of inbuilt modules as reference to check against."""
    included_modules_path = Path(py3status.__file__).resolve().parent / "modules"
    status_wrapper.options.__dict__["include_paths"] = [included_modules_path]
    assert included_modules_path.exists()
    expected_keys = [
        n.stem for n in included_modules_path.iterdir() if n.suffix == ".py"
    ]
    modules = status_wrapper._get_path_based_modules()
    assert sorted(modules) == sorted(expected_keys)


def test__get_entry_point_based_modules(status_wrapper, monkeypatch):
    def return_fake_entry_points(*_):
        class FakePy3status:
            Py3status = "I am a fake class"

            def __init__(self, name):
                self.name = name
                self.module_name = "module_name_" + self.name

            @staticmethod
            def load():
                from py3status.modules import air_quality

                return air_quality

        return [FakePy3status("spam"), FakePy3status("eggs")]

    monkeypatch.setattr(pkg_resources, "iter_entry_points", return_fake_entry_points)

    user_modules = status_wrapper._get_entry_point_based_modules()
    assert len(user_modules) == 2
    for name, info in user_modules.items():
        assert any(n in name for n in ["spam", "eggs"])
        kind, klass = info
        assert kind == ENTRY_POINT_KEY
        assert klass.__name__ == "Py3status"
