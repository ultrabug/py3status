from py3status.module_test import MockPy3statusWrapper
from py3status.module import Module


class TestModule:
    static_variable = 123

    def __init__(self):
        self.instance_variable = 321

    def post_config_hook(self):
        pass

    @staticmethod
    def static_method(self):
        raise Exception("I don't want to be called!")

    @property
    def property(self):
        raise Exception("I don't want to be called!")

    def instance_method(self):
        raise Exception("I don't want to be called!")

    def _private_instance_method(self):
        raise Exception("I don't want to be called!")

    def on_click(self, event):
        raise Exception("I don't want to be called!")


def test_module_load():
    mock = MockPy3statusWrapper(
        {
            "general": {},
            "py3status": {},
            ".module_groups": {},
            "test_module": {},
        }
    )

    module = TestModule()
    m = Module("test_module", {}, mock, module)
    m.prepare_module()
    assert list(m.methods) == ["instance_method"]
