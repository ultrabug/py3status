import argparse
import importlib.metadata
from pathlib import Path

import pytest

import py3status
from py3status.core import ENTRY_POINT_KEY, Py3statusWrapper


@pytest.fixture(name="status_wrapper")
def make_status_wrapper():
    args = argparse.Namespace()
    status_wrapper = Py3statusWrapper(args)
    return status_wrapper


def test__get_path_included_modules(status_wrapper):
    """Use the list of inbuilt modules as reference to check against."""
    path_included_modules_path = Path(py3status.__file__).resolve().parent / "modules"
    status_wrapper.options.__dict__["include_paths"] = [path_included_modules_path]
    assert path_included_modules_path.exists()
    expected_keys = [n.stem for n in path_included_modules_path.iterdir() if n.suffix == ".py"]
    modules = status_wrapper._get_path_included_modules()
    assert sorted(modules) == sorted(expected_keys)


def test__get_entry_point_based_modules(status_wrapper, monkeypatch):
    def return_fake_entry_points(*args, **kwargs):
        class FakePy3status:
            Py3status = "I am a fake class"

            def __init__(self, name):
                self.name = name
                self.value = f"{name}.module"

            @staticmethod
            def load():
                from py3status.modules import air_quality

                return air_quality

        return [FakePy3status("spam"), FakePy3status("eggs")]

    monkeypatch.setattr(importlib.metadata, "entry_points", return_fake_entry_points)

    discoverable_modules = status_wrapper._get_entry_point_based_modules()
    assert len(discoverable_modules) == 2
    for name, info in discoverable_modules.items():
        assert any(n in name for n in ["spam", "eggs"])
        kind, klass = info
        assert kind == ENTRY_POINT_KEY
        assert klass.__name__ == "Py3status"
