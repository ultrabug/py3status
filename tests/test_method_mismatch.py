import os

MODULE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "py3status", "modules"
)
SKIP_FILES = ["__init__.py", "i3pystatus.py"]


def check_method_mismatch():
    files = [x for x in os.listdir(MODULE_PATH) if x not in SKIP_FILES]
    errors = []

    for _file in sorted(files):
        if _file.endswith(".py"):
            with open(os.path.join(MODULE_PATH, _file)) as f:
                _self = "def {}(self".format(_file[:-3])
                if _self not in f.read():
                    errors.append((_self[4:-5], _file))
    return errors


def test_method_mismatch():
    errors = check_method_mismatch()
    if errors:
        line = "Method mismatched error(s) detected!\n\n"
        for error in errors:
            line += "Method `{}` is not in module `{}`\n".format(*error)
        print(line[:-1])
        assert False
