import os
import time

from pathlib import Path
from pickle import dump, load
from tempfile import NamedTemporaryFile


class Storage:

    data = {}
    initialized = False

    def init(self, py3_wrapper):
        self.py3_wrapper = py3_wrapper
        self.config = py3_wrapper.config
        py3_config = self.config.get("py3_config", {})

        # check for legacy storage cache
        legacy_storage_path = self.get_legacy_storage_path()

        # cutting edge storage cache
        storage_config = py3_config.get("py3status", {}).get("storage")
        if storage_config:
            storage_file = os.path.expandvars(storage_config.expanduser())
            if "/" in storage_file:
                storage_dir = None
            else:
                storage_dir = os.environ.get("XDG_CACHE_HOME")
        else:
            storage_dir = os.environ.get("XDG_CACHE_HOME")
            storage_file = Path("py3status_cache.data")

        if not storage_dir:
            storage_dir = Path("~/.cache").expanduser()
        self.storage_path = storage_dir / storage_file

        # move legacy storage cache to new desired / default location
        if legacy_storage_path:
            self.py3_wrapper.log(
                "moving legacy storage_path {} to {}".format(
                    legacy_storage_path, self.storage_path
                )
            )
            legacy_storage_path.rename(self.storage_path)

        try:
            with self.storage_path.open("rb") as f:
                self.data = load(f, encoding="bytes")
        except OSError:
            pass

        self.py3_wrapper.log(f"storage_path: {self.storage_path}")
        if self.data:
            self.py3_wrapper.log(f"storage_data: {self.data}")
        self.initialized = True

    def get_legacy_storage_path(self):
        """
        Detect and return existing legacy storage path.
        """
        config_dir = Path(
            self.py3_wrapper.config.get("i3status_config_path", "/tmp")
        ).parent
        storage_path = config_dir / "py3status.data"
        if storage_path.exists():
            return storage_path
        else:
            return None

    def save(self):
        """
        Save our data to disk. We want to always have a valid file.
        """
        with NamedTemporaryFile(dir=self.storage_path.parent, delete=False) as f:
            # we use protocol=2 for python 2/3 compatibility
            dump(self.data, f, protocol=2)
            f.flush()
            os.fsync(f.fileno())
            tmppath = Path(f.name)
        tmppath.rename(self.storage_path)

    def storage_set(self, module_name, key, value):
        if key.startswith("_"):
            raise ValueError('cannot set keys starting with an underscore "_"')

        if self.data.get(module_name, {}).get(key) == value:
            return

        if module_name not in self.data:
            self.data[module_name] = {}
        self.data[module_name][key] = value
        ts = time.time()
        if "_ctime" not in self.data[module_name]:
            self.data[module_name]["_ctime"] = ts
        self.data[module_name]["_mtime"] = ts
        self.save()

    def storage_get(self, module_name, key):
        return self.data.get(module_name, {}).get(key, None)

    def storage_del(self, module_name, key=None):
        if module_name in self.data and key in self.data[module_name]:
            del self.data[module_name][key]
            self.save()

    def storage_keys(self, module_name):
        return list(self.data.get(module_name, {}))
