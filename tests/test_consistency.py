import ast
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent.parent / "py3status" / "modules"


def get_module_files(skip_files):
    for _file in sorted(MODULE_PATH.iterdir()):
        if _file.suffix == ".py" and _file.name not in skip_files:
            yield _file


def get_py3status_methods(_file):
    tree = ast.parse(_file.read_text(), filename=str(_file))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Py3status":
            return [item.name for item in node.body if isinstance(item, ast.FunctionDef)]
    return []


def test_authors():
    comment = "@author"
    skip_files = ["__init__.py"]
    errors = []

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            if comment not in f.read():
                errors.append((comment, _file))
    if errors:
        line = "Missing @author error(s) detected!\n\n"
        for error in errors:
            line += "`{}` is not in module `{}`\n".format(*error)
        print(line[:-1])
        assert False


def test_sample_output():
    comment = "SAMPLE OUTPUT"
    skip_files = ["__init__.py"]
    errors = []

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            if comment not in f.read():
                errors.append((comment, _file))
    if errors:
        line = "Missing sample error(s) detected!\n\n"
        for error in errors:
            line += "`{}` is not in module `{}`\n".format(*error)
        print(line[:-1])
        assert False


# def test_examples():
#     comment = "Examples:"
#     skip_files = ["__init__.py"]
#     errors = []
#
#     for _file in sorted(MODULE_PATH.iterdir()):
#         if _file.suffix == ".py" and _file.name not in skip_files:
#             with _file.open() as f:
#                 if comment not in f.read():
#                     errors.append((comment, _file))
#     if errors:
#         line = "Missing example error(s) detected!\n\n"
#         for error in errors:
#             line += "`{}` is not in module `{}`\n".format(*error)
#         print(line[:-1])
#         assert False


def test_available_configuration_parameters():
    comment = "# available configuration parameters"
    skip_files = ["__init__.py"]
    errors = []

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            if comment not in f.read():
                errors.append((comment, _file))
    if errors:
        line = "Missing comment error(s) detected!\n\n"
        for error in errors:
            line += "Comment `{}` is not in module `{}`\n".format(*error)
        print(line[:-1])
        assert False


def test_class_meta_before_parameters():
    line = "class Meta:"
    comment = "# available configuration parameters"
    errors = []
    skip_files = ["__init__.py"]

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            for x in f.readlines():
                if line in x:
                    errors.append((line, _file))
                    break
                elif comment in x:
                    break
    if errors:
        line = "Class Meta error(s) detected!\n\n"
        for error in errors:
            line += "`{}` is defined early in module `{}`\n".format(*error)
        print(line[:-1])
        assert False


def test_examples_before_requires():
    line = "Examples:"
    comment = "Requires:"
    errors = []
    skip_files = ["__init__.py"]

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            output = f.read()
            if line not in output or comment not in output:
                continue
            for x in output.splitlines():
                if x.startswith(line):
                    errors.append((line, _file))
                    break
                elif x.startswith(comment):
                    break
    if errors:
        line = "Examples error(s) detected!\n\n"
        for error in errors:
            line += "`{}` is defined early in module `{}`\n".format(*error)
        print(line[:-1])
        assert False


def test_authors_before_examples():
    line = "@author "
    comment = "Examples:"
    errors = []
    skip_files = ["__init__.py"]

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            output = f.read()
            if line not in output or comment not in output:
                continue
            for x in output.splitlines():
                if x.startswith(line):
                    errors.append((line, _file))
                    break
                elif x.startswith(comment):
                    break
    if errors:
        line = "Author error(s) detected!\n\n"
        for error in errors:
            line += "`{}` is defined early in module `{}`\n".format(*error)
        print(line[:-1])
        assert False


def test_format_placeholders():
    comment = "ormat placeholders:"
    comment2 = "ontrl placeholders:"
    skip_files = [
        "__init__.py",
        "i3pystatus.py",
        "keyboard_locks.py",
        "screenshot.py",
        "static_string.py",
        "wwan_status.py",
        "yubikey.py",
    ]
    errors = []

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            output = f.read()
            if comment not in output:
                if comment2 not in output:
                    errors.append((comment, _file))
    if errors:
        line = f"Missing `{comment}` error(s) detected!\n\n"
        for error in errors:
            line += "`{}` is not in module `{}`\n".format(*error)
        print(line[:-1])
        assert False


def test_module_method_order():
    skip_files = ["__init__.py", "i3pystatus.py"]
    errors = []

    for _file in get_module_files(skip_files):
        methods = get_py3status_methods(_file)
        module_method = _file.stem
        if module_method not in methods:
            errors.append(f"Module `{_file}` should define `{module_method}()`")
            continue

        if "post_config_hook" in methods and methods[0] != "post_config_hook":
            errors.append(
                f"Module `{_file}` should define `post_config_hook()` first when present"
            )

        expected_tail = [module_method]
        if "kill" in methods:
            expected_tail.append("kill")
        if "on_click" in methods:
            expected_tail.append("on_click")

        helper_methods = methods[1:] if methods[0] == "post_config_hook" else methods
        helper_methods = helper_methods[: -len(expected_tail)]
        for method in helper_methods:
            if not method.startswith("_"):
                errors.append(
                    f"Module `{_file}` should define `{method}()` before "
                    f"`{module_method}()` only if it is private"
                )

        if methods[-len(expected_tail) :] != expected_tail:
            expected_methods = " then ".join(f"`{name}()`" for name in expected_tail)
            errors.append(f"Module `{_file}` should end with {expected_methods}")

    if errors:
        line = "Module method ordering error(s) detected!\n\n"
        line += "\n".join(errors)
        print(line)
        assert False
