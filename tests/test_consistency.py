from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent.parent / "py3status" / "modules"


def test_method_mismatch():
    line = "def {}(self"
    skip_files = ["__init__.py", "i3pystatus.py"]
    errors = []

    for _file in sorted(MODULE_PATH.iterdir()):
        if _file.suffix == ".py" and _file.name not in skip_files:
            with _file.open() as f:
                if f"def {_file.stem}(self" not in f.read():
                    errors.append((_file.stem, _file))
    if errors:
        line = "Method mismatched error(s) detected!\n\n"
        for error in errors:
            line += "Method `{}` is not in module `{}`\n".format(*error)
        print(line[:-1])
        assert False


def test_authors():
    comment = "@author"
    skip_files = ["__init__.py"]
    errors = []

    for _file in sorted(MODULE_PATH.iterdir()):
        if _file.suffix == ".py" and _file.name not in skip_files:
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

    for _file in sorted(MODULE_PATH.iterdir()):
        if _file.suffix == ".py" and _file.name not in skip_files:
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

    for _file in sorted(MODULE_PATH.iterdir()):
        if _file.suffix == ".py" and _file.name not in skip_files:
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

    for _file in sorted(MODULE_PATH.iterdir()):
        if _file.suffix == ".py" and _file.name not in skip_files:
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

    for _file in sorted(MODULE_PATH.iterdir()):
        if _file.suffix == ".py" and _file.name not in skip_files:
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

    for _file in sorted(MODULE_PATH.iterdir()):
        if _file.suffix == ".py" and _file.name not in skip_files:
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

    for _file in sorted(MODULE_PATH.iterdir()):
        if _file.suffix == ".py" and _file.name not in skip_files:
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
