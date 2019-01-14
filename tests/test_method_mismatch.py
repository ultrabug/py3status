import os

MODULE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "py3status", "modules"
)
SKIP_FILES = ["__init__.py", "i3pystatus.py"]


def test_method_mismatch():
    errors = []
    for _file in sorted(os.listdir(MODULE_PATH)):
        if _file.endswith(".py") and _file not in SKIP_FILES:
            with open(os.path.join(MODULE_PATH, _file)) as f:
                name = _file[:-3]
                if "def {}(self".format(name) not in f.read():
                    errors.append((name, _file))
    if errors:
        line = "Method mismatched error(s) detected!\n\n"
        for error in errors:
            line += "Method `{}` is not in module `{}`\n".format(*error)
        print(line[:-1])
        assert False
