from py3status.core import Py3statusWrapper


class FakeModuleClass:
    def __init__(self, module_full_name=None, container=None):
        self._module_full_name = module_full_name
        self._container = container
        self.refreshed = 0

    def _refresh(self):
        self.refreshed += 1


class FakeModuleWrapper:
    def __init__(self, module_class):
        self.module_class = module_class
        self.forced = 0

    def force_update(self):
        self.forced += 1


def make_wrapper():
    # bypass __init__ - only exercises refresh_modules()/i3status_containers(),
    # which only touch modules/output_modules/last_refresh_ts
    wrapper = Py3statusWrapper.__new__(Py3statusWrapper)
    wrapper.last_refresh_ts = 0
    return wrapper


def test_refresh_modules_by_name_only_refreshes_the_owning_container():
    """
    Refreshing one specific i3status proxy by name used to SIGUSR1 every
    i3status container in the bar, not just the one that actually owns
    that proxy - wasteful with more than one container.
    """
    wrapper = make_wrapper()

    sc0 = FakeModuleClass(module_full_name="i3status generated")
    sc1 = FakeModuleClass(module_full_name="i3status generated_2")
    sc0_wrapper = FakeModuleWrapper(sc0)
    sc1_wrapper = FakeModuleWrapper(sc1)
    proxy_wrapper = FakeModuleWrapper(FakeModuleClass(container="i3status generated"))

    wrapper.modules = {
        "i3status generated": sc0_wrapper,
        "i3status generated_2": sc1_wrapper,
    }
    wrapper.output_modules = {
        "i3status generated": {"type": "py3status", "module": sc0_wrapper},
        "i3status generated_2": {"type": "py3status", "module": sc1_wrapper},
        "i3status_proxy generated_disk": {"type": "py3status", "module": proxy_wrapper},
    }

    wrapper.refresh_modules("i3status_proxy generated_disk")

    assert proxy_wrapper.forced == 1
    assert sc0.refreshed == 1
    assert sc1.refreshed == 0


def test_refresh_modules_by_container_name_refreshes_only_itself():
    wrapper = make_wrapper()

    sc0 = FakeModuleClass(module_full_name="i3status generated")
    sc1 = FakeModuleClass(module_full_name="i3status generated_2")
    sc0_wrapper = FakeModuleWrapper(sc0)
    sc1_wrapper = FakeModuleWrapper(sc1)

    wrapper.modules = {
        "i3status generated": sc0_wrapper,
        "i3status generated_2": sc1_wrapper,
    }
    wrapper.output_modules = {
        "i3status generated": {"type": "py3status", "module": sc0_wrapper},
        "i3status generated_2": {"type": "py3status", "module": sc1_wrapper},
    }

    wrapper.refresh_modules("i3status generated")

    assert sc0.refreshed == 1
    assert sc1.refreshed == 0
