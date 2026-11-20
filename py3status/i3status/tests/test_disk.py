"""Tests for the disk i3status-compatible module."""

import os

from py3status.i3status.modules.disk import Py3status as Disk


class FakeStatvfs:
    def __init__(self, f_frsize=4096, f_blocks=1000, f_bfree=500, f_bavail=400):
        self.f_frsize = f_frsize
        self.f_blocks = f_blocks
        self.f_bfree = f_bfree
        self.f_bavail = f_bavail


def test_disk_default_format(make_module, monkeypatch):
    module = make_module(Disk)
    module.post_config_hook()
    monkeypatch.setattr(os, "statvfs", lambda path: FakeStatvfs())

    result = module.disk()

    # 500 free blocks * 4096 = 2048000 bytes = 1.95 MiB
    assert result["full_text"] == "2.0 MiB"


def test_disk_percentage_placeholders_no_collision(make_module, monkeypatch):
    module = make_module(Disk, format="%percentage_used_of_avail %percentage_used")
    module.post_config_hook()
    monkeypatch.setattr(os, "statvfs", lambda path: FakeStatvfs())

    result = module.disk()

    # used=500/1000=50%, used_of_avail=(1000-400)/1000=60%
    assert result["full_text"] == "60.0% 50.0%"


def test_disk_not_mounted(make_module, monkeypatch):
    module = make_module(Disk, format_not_mounted="NOT MOUNTED")
    module.post_config_hook()

    def raise_enoent(path):
        raise OSError("no such file")

    monkeypatch.setattr(os, "statvfs", raise_enoent)

    result = module.disk()

    assert result["full_text"] == "NOT MOUNTED"


def test_disk_low_threshold_colors_bad(make_module, monkeypatch):
    module = make_module(Disk, low_threshold=50, threshold_type="percentage_avail")
    module.post_config_hook()
    monkeypatch.setattr(os, "statvfs", lambda path: FakeStatvfs(f_bavail=100))

    result = module.disk()

    assert result["color"] == "#FF0000"
