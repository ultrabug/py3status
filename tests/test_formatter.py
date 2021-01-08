"""
Run formatter tests
"""

import platform

from pprint import pformat

import pytest

from py3status.composite import Composite
from py3status.formatter import Formatter
from py3status.py3 import NoneColor

is_pypy = platform.python_implementation() == "PyPy"
f = Formatter()

param_dict = {
    "name": "Björk",
    "number": 42,
    "pi": 3.14159265359,
    "yes": True,
    "no": False,
    "empty": "",
    "None": None,
    "?bad name": "evil",
    "☂ Very bad name ": "☂ extremely evil",
    "long_str": "I am a long string though not too long",
    "python2_unicode": "Björk",
    "python2_str": "Björk",
    "zero": 0,
    "zero_str": "0",
    "zero_float": 0.0,
    "zero_almost": 0.0001,
    "str_int": "123",
    "str_float": "123.456",
    "str_nan": "I'm not a number",
    "trailing_zeroes_1": "50.000",
    "trailing_zeroes_2": "5.500",
    "composite_basic": Composite(
        [
            {"full_text": "red ", "color": "#FF0000"},
            {"full_text": "green ", "color": "#00FF00"},
            {"full_text": "blue", "color": "#0000FF"},
        ]
    ),
    "complex": Composite([{"full_text": "LA 09:34"}, {"full_text": "NY 12:34"}]),
    "complex2": Composite(
        [{"full_text": "LA 09:34", "color": "#FF0000"}, {"full_text": "NY 12:34"}]
    ),
    "simple": Composite({"full_text": "NY 12:34"}),
    "empty_composite": Composite(),
    "comp_bad_color": Composite({"full_text": "BAD", "color": NoneColor()}),
    "composite_looks_empty": Composite([{"color": "#FFF", "full_text": ""}]),
}


class Module:
    module_param = "something"
    module_true = True
    module_false = False

    class py3:
        COLOR_BAD = "#FF0000"
        COLOR_DEGRADED = "#FFFF00"
        COLOR_GOOD = "#00FF00"

    def module_method(self):
        return "method"

    @property
    def module_property(self):
        return "property"


def attr_getter_fn(attr):
    """
    test attr_getter function
    """
    return f"*{attr}*"


def run_formatter(test_dict):
    __tracebackhide__ = True

    if not test_dict.get("pypy", True) and is_pypy:
        return
    if test_dict.get("attr_getter"):
        attr_getter = attr_getter_fn
    else:
        attr_getter = None
    try:
        module = Module()
        result = f.format(
            test_dict["format"],
            module,
            param_dict,
            force_composite=test_dict.get("composite"),
            attr_getter=attr_getter,
        )
    except Exception as e:
        if test_dict.get("exception") == str(e):
            return
        print("Format\n{}\n".format(test_dict["format"]))
        raise e

    # simplify the composite and convert to text if possible
    if isinstance(result, Composite):
        result.simplify()
        if not test_dict.get("composite") and len(result) == 1 and len(result[0]) == 1:
            result = result[0]["full_text"]

    if hasattr(result, "get_content"):
        result = result.get_content()

    expected = test_dict.get("expected")
    if result != expected:
        print("Format\n{}\n".format(test_dict["format"]))
        print("Expected\n{}".format(pformat(expected)))
        print("Got\n{}".format(pformat(result)))
    if result != expected:
        pytest.fail("Results not as expected")


def get_placeholders(test_dict):
    __tracebackhide__ = True

    result = f.get_placeholders(test_dict["format"])
    expected = test_dict.get("expected")

    if result != expected:
        print("Format\n{}\n".format(test_dict["format"]))
        print("Expected\n{}".format(pformat(expected)))
        print("Got\n{}".format(pformat(result)))
    if result != expected:
        pytest.fail("Results not as expected")


def update_placeholders(test_dict):
    __tracebackhide__ = True

    result = f.update_placeholders(test_dict["format"], test_dict["updates"])
    expected = test_dict.get("expected")

    if result != expected:
        print("Format\n{}\n".format(test_dict["format"]))
        print("Expected\n{}".format(pformat(expected)))
        print("Got\n{}".format(pformat(result)))
    if result != expected:
        pytest.fail("Results not as expected")


def get_color_names(test_dict):
    __tracebackhide__ = True

    result = f.get_color_names(test_dict["format"])
    expected = test_dict.get("expected")

    if result != expected:
        print("Format\n{}\n".format(test_dict["format"]))
        print("Expected\n{}".format(pformat(expected)))
        print("Got\n{}".format(pformat(result)))
    if result != expected:
        pytest.fail("Results not as expected")


def test_1():
    run_formatter({"format": "hello ☂", "expected": "hello ☂"})


def test_2():
    run_formatter({"format": "hello ☂", "expected": "hello ☂"})


def test_3():
    run_formatter({"format": "[hello]", "expected": ""})


def test_4():
    run_formatter({"format": r"\\ \[ \] \{ \}", "expected": r"\ [ ] { }"})


def test_5():
    run_formatter({"format": "{{hello}}", "expected": "{hello}"})


def test_6():
    run_formatter({"format": "{{hello}", "expected": "{hello}"})


def test_7():
    run_formatter({"format": "{?bad name}", "expected": "evil"})


def test_8():
    run_formatter(
        {
            "format": "{☂ Very bad name }",
            "expected": "☂ extremely evil",
            # unicode.format({<unicode>: ..}) is broken in pypy
            "pypy": False,
        }
    )


def test_9():
    run_formatter(
        {"format": "{missing} {name} {number}", "expected": "{missing} Björk 42"}
    )


def test_10():
    run_formatter({"format": "{missing}|{name}|{number}", "expected": "Björk"})


def test_11():
    run_formatter({"format": "{missing}|empty", "expected": "empty"})


def test_12():
    run_formatter({"format": "[{missing}|empty]", "expected": ""})


def test_13():
    run_formatter({"format": "pre [{missing}|empty] post", "expected": "pre  post"})


def test_14():
    run_formatter({"format": "pre [{missing}|empty] post|After", "expected": "After"})


def test_15():
    run_formatter({"format": "{module_param}", "expected": "something"})


def test_16():
    run_formatter({"format": "{module_method}", "expected": "{module_method}"})


def test_16a():
    run_formatter({"format": "x {module_method}", "expected": "x {module_method}"})


def test_16b():
    run_formatter({"format": "[x {module_method}]", "expected": ""})


def test_17():
    run_formatter({"format": "{module_property}", "expected": "property"})


def test_18():
    run_formatter({"format": "Hello {name}!", "expected": "Hello Björk!"})


def test_19():
    run_formatter({"format": "[Hello {name}!]", "expected": "Hello Björk!"})


def test_20():
    run_formatter({"format": "[Hello {missing}|Anon!]", "expected": ""})


def test_21():
    run_formatter(
        {"format": "zero [one [two [three [no]]]]|Numbers", "expected": "Numbers"}
    )


def test_22():
    run_formatter(
        {
            "format": "zero [one [two [three [{yes}]]]]|Numbers",
            "expected": "zero one two three True",
        }
    )


def test_23():
    run_formatter(
        {"format": "zero [one [two [three [{no}]]]]|Numbers", "expected": "Numbers"}
    )


# zero/False/None etc


def test_24():
    run_formatter({"format": "{zero}", "expected": "0"})


def test_24a():
    run_formatter({"format": "{zero_str}", "expected": "0"})


def test_24b():
    run_formatter({"format": "{zero_float}", "expected": "0.0"})


def test_25():
    run_formatter({"format": "[{zero}] hello", "expected": "0 hello"})


def test_26():
    run_formatter({"format": "[{zero} ping] hello", "expected": "0 ping hello"})


def test_27():
    run_formatter({"format": "{None}", "expected": ""})


def test_28():
    run_formatter({"format": "[{None}] hello", "expected": " hello"})


def test_29():
    run_formatter({"format": "[{None} ping] hello", "expected": " hello"})


def test_30():
    run_formatter({"format": "{no}", "expected": ""})


def test_31():
    run_formatter({"format": "[{no}] hello", "expected": " hello"})


def test_32():
    run_formatter({"format": "[{no} ping] hello", "expected": " hello"})


def test_33():
    run_formatter({"format": "{yes}", "expected": "True"})


def test_34():
    run_formatter({"format": "[{yes}] hello", "expected": "True hello"})


def test_35():
    run_formatter({"format": "[{yes} ping] hello", "expected": "True ping hello"})


def test_36():
    run_formatter({"format": "{empty}", "expected": ""})


def test_37():
    run_formatter({"format": "[{empty}] hello", "expected": " hello"})


def test_38():
    run_formatter({"format": "[{empty} ping] hello", "expected": " hello"})


def test_39():
    run_formatter(
        # python 2 unicode
        {"format": "Hello {python2_unicode}! ☂", "expected": "Hello Björk! ☂"}
    )


def test_40():
    run_formatter(
        {"format": "Hello {python2_unicode}! ☂", "expected": "Hello Björk! ☂"}
    )


def test_41():
    run_formatter({"format": "Hello {python2_str}! ☂", "expected": "Hello Björk! ☂"})


def test_42():
    run_formatter({"format": "Hello {python2_str}! ☂", "expected": "Hello Björk! ☂"})


def test_43():
    run_formatter(
        # formatting
        {"format": "{name}", "expected": "Björk"}
    )


def test_44():
    run_formatter({"format": "{name!s}", "expected": "Björk"})


def test_45():
    # the representation is different in python2 "u'Björk'"
    run_formatter({"format": "{name!r}", "expected": "'Björk'", "py3only": True})


def test_46():
    run_formatter({"format": "{name:7}", "expected": "Björk  "})


def test_47():
    run_formatter({"format": "{name:<7}", "expected": "Björk  "})


def test_48():
    run_formatter({"format": "{name:>7}", "expected": "  Björk"})


def test_49():
    run_formatter({"format": "{name:*^9}", "expected": "**Björk**"})


def test_50():
    run_formatter(
        {"format": "{long_str}", "expected": "I am a long string though not too long"}
    )


def test_51():
    run_formatter({"format": "{long_str:.6}", "expected": "I am a"})


def test_52():
    run_formatter({"format": "{number}", "expected": "42"})


def test_53():
    run_formatter({"format": "{number:04d}", "expected": "0042"})


def test_54():
    run_formatter({"format": "{pi}", "expected": "3.14159265359"})


def test_55():
    run_formatter({"format": "{pi:05.2f}", "expected": "03.14"})


def test_56():
    run_formatter(
        # commands
        {"format": r"{missing}|\?show Anon", "expected": "Anon"}
    )


def test_57():
    run_formatter(
        {"format": r"Hello [{missing}|[\?show Anon]]!", "expected": "Hello Anon!"}
    )


def test_58():
    run_formatter({"format": r"[\?if=yes Hello]", "expected": "Hello"})


def test_58a():
    run_formatter({"format": r"\?if=yes Hello", "expected": "Hello"})


def test_59():
    run_formatter({"format": r"[\?if=no Hello]", "expected": ""})


def test_59a():
    run_formatter({"format": r"\?if=no Hello", "expected": ""})


def test_60():
    run_formatter({"format": r"[\?if=missing Hello]", "expected": ""})


def test_61():
    run_formatter({"format": r"[\?if=!yes Hello]", "expected": ""})


def test_62():
    run_formatter({"format": r"[\?if=!no Hello]", "expected": "Hello"})


def test_63():
    run_formatter({"format": r"[\?if=!missing Hello]", "expected": "Hello"})


def test_64():
    run_formatter({"format": r"[\?if=yes Hello[ {name}]]", "expected": "Hello Björk"})


def test_65():
    run_formatter({"format": r"[\?if=no Hello[ {name}]]", "expected": ""})


def test_66():
    run_formatter(
        {"format": r"[\?max_length=10 Hello {name} {number}]", "expected": "Hello Björ"}
    )


def test_67():
    run_formatter(
        {"format": r"\?max_length=9 Hello {name} {number}", "expected": "Hello Bjö"}
    )


def test_68():
    run_formatter(
        # Errors
        {"format": "hello]", "exception": "Too many `]`"}
    )


def test_69():
    run_formatter({"format": "[hello", "exception": "Block not closed"})


def test_70():
    run_formatter(
        # Composites
        {"format": "{empty_composite}", "expected": [], "composite": True}
    )


def test_70a():
    run_formatter(
        # Composites
        {"format": "[{empty_composite} hello]", "expected": [], "composite": True}
    )


def test_71():
    run_formatter(
        {
            "format": "{simple}",
            "expected": [{"full_text": "NY 12:34"}],
            "composite": True,
        }
    )


def test_72():
    run_formatter(
        {
            "format": "{complex}",
            "expected": [{"full_text": "LA 09:34NY 12:34"}],
            "composite": True,
        }
    )


def test_73():
    run_formatter(
        {
            "format": "TEST {simple}",
            "expected": [{"full_text": "TEST NY 12:34"}],
            "composite": True,
        }
    )


def test_74():
    run_formatter({"format": "[{empty}]", "expected": [], "composite": True})


def test_75():
    run_formatter(
        {
            "format": "[{simple}]",
            "expected": [{"full_text": "NY 12:34"}],
            "composite": True,
        }
    )


def test_76():
    run_formatter(
        {
            "format": "[{complex}]",
            "expected": [{"full_text": "LA 09:34NY 12:34"}],
            "composite": True,
        }
    )


def test_77():
    run_formatter(
        {
            "format": "TEST [{simple}]",
            "expected": [{"full_text": "TEST NY 12:34"}],
            "composite": True,
        }
    )


def test_78():
    run_formatter(
        {
            "format": "{simple} TEST [{name}[ {number}]]",
            "expected": [{"full_text": "NY 12:34 TEST Björk 42"}],
            "composite": True,
        }
    )


def test_else_true():
    run_formatter({"format": r"[\?if=yes Hello|Goodbye]", "expected": "Hello"})


def test_else_false():
    run_formatter(
        {"format": r"[\?if=no Hello|Goodbye|Something else]", "expected": "Goodbye"}
    )


def test_composite_looks_empty():
    run_formatter({"format": "[ {composite_looks_empty}]", "expected": ""})


# block colors


def test_color_name_1():
    run_formatter(
        {
            "format": r"\?color=bad color",
            "expected": [{"full_text": "color", "color": "#FF0000"}],
        }
    )


def test_color_name_2():
    run_formatter({"format": r"\?color=no_name color", "expected": "color"})


def test_color_name_3():
    run_formatter(
        {
            "format": r"\?color=#FF00FF color",
            "expected": [{"full_text": "color", "color": "#FF00FF"}],
        }
    )


def test_color_name_4():
    run_formatter(
        {
            "format": r"\?color=#ff00ff color",
            "expected": [{"full_text": "color", "color": "#FF00FF"}],
        }
    )


def test_color_name_4a():
    run_formatter(
        {
            "format": r"[\?color=#ff00ff&show color]",
            "expected": [{"full_text": "color", "color": "#FF00FF"}],
        }
    )


def test_color_name_5():
    run_formatter(
        {
            "format": r"\?color=#F0F color",
            "expected": [{"full_text": "color", "color": "#FF00FF"}],
        }
    )


def test_color_name_5a():
    run_formatter(
        {
            "format": r"[\?color=#F0F&show color]",
            "expected": [{"full_text": "color", "color": "#FF00FF"}],
        }
    )


def test_color_name_6():
    run_formatter(
        {
            "format": r"\?color=#f0f color",
            "expected": [{"full_text": "color", "color": "#FF00FF"}],
        }
    )


def test_color_name_7():
    run_formatter({"format": r"\?color=#BADHEX color", "expected": "color"})


def test_color_name_7a():
    run_formatter({"format": r"[\?color=#BADHEX&show color]", "expected": "color"})


def test_color_1():
    run_formatter(
        {
            "format": r"[\?color=bad {name}]",
            "expected": [{"full_text": "Björk", "color": "#FF0000"}],
        }
    )


def test_color_1a():
    run_formatter(
        {
            "format": r"\?color=bad {name}",
            "expected": [{"full_text": "Björk", "color": "#FF0000"}],
        }
    )


def test_color_2():
    run_formatter(
        {
            "format": r"[\?color=good Name [\?color=bad {name}] hello]",
            "expected": [
                {"full_text": "Name ", "color": "#00FF00"},
                {"full_text": "Björk", "color": "#FF0000"},
                {"full_text": " hello", "color": "#00FF00"},
            ],
        }
    )


def test_color_3():
    run_formatter(
        {
            "format": r"[\?max_length=20&color=good Name [\?color=bad {name}] hello]",
            "expected": [
                {"full_text": "Name ", "color": "#00FF00"},
                {"full_text": "Björk", "color": "#FF0000"},
                {"full_text": " hello", "color": "#00FF00"},
            ],
        }
    )


def test_color_4():
    run_formatter(
        {
            "format": r"[\?max_length=8&color=good Name [\?color=bad {name}] hello]",
            "expected": [
                {"full_text": "Name ", "color": "#00FF00"},
                {"full_text": "Bjö", "color": "#FF0000"},
            ],
        }
    )


def test_color_5():
    run_formatter(
        {
            "format": r"[\?color=bad {name}][\?color=good {name}]",
            "expected": [
                {"full_text": "Björk", "color": "#FF0000"},
                {"full_text": "Björk", "color": "#00FF00"},
            ],
        }
    )


def test_color_6():
    run_formatter(
        {
            "format": r"[\?color=bad {name}] [\?color=good {name}]",
            "expected": [
                {"full_text": "Björk ", "color": "#FF0000"},
                {"full_text": "Björk", "color": "#00FF00"},
            ],
        }
    )


def test_color_7():
    run_formatter(
        {
            "format": r"\?color=bad {simple}",
            "expected": [{"full_text": "NY 12:34", "color": "#FF0000"}],
        }
    )


def test_color_7a():
    run_formatter(
        {
            "format": r"[\?color=bad {simple}]",
            "expected": [{"full_text": "NY 12:34", "color": "#FF0000"}],
        }
    )


def test_color_8():
    run_formatter(
        {
            "format": r"\?color=bad {complex}",
            "expected": [{"full_text": "LA 09:34NY 12:34", "color": "#FF0000"}],
        }
    )


def test_color_8a():
    run_formatter(
        {
            "format": r"[\?color=#FF00FF {complex}]",
            "expected": [{"full_text": "LA 09:34NY 12:34", "color": "#FF00FF"}],
        }
    )


def test_color_9():
    run_formatter(
        {
            "format": r"\?color=good {complex2}",
            "expected": [
                {"color": "#FF0000", "full_text": "LA 09:34"},
                {"color": "#00FF00", "full_text": "NY 12:34"},
            ],
        }
    )


def test_color_9a():
    run_formatter(
        {
            "format": r"[\?color=good {complex2}]",
            "expected": [
                {"color": "#FF0000", "full_text": "LA 09:34"},
                {"color": "#00FF00", "full_text": "NY 12:34"},
            ],
        }
    )


def test_color_10():
    # correct, but code is py3 instead of composite/formatter. same w/ color=hidden.
    run_formatter(
        {
            "format": r"[\?color=None&show None][\?color=degraded&show degraded]",
            "expected": [
                {"full_text": "None"},
                {"full_text": "degraded", "color": "#FFFF00"},
            ],
        }
    )


def test_color_11():
    # one would say it's right, but maybe one would say it's wrong too.
    run_formatter(
        {
            "format": r"[\?color=ORANGE&show orange] [\?color=bLuE&show blue]",
            "expected": "orange blue",  # wrong imho
            # "expected": [
            #     {"full_text": "orange", "color": "#FFA500"},
            #     {"full_text": "blue", "color": "#0000FF"},
            # ],
        }
    )


def test_color_12():
    run_formatter(
        {
            "color_test": "#FFA500",
            "format": r"\?color=test test",
            "expected": "test",  # wrong
            # "expected": [{"full_text": "test", "color": "#FFA500"}]
        }
    )


# Composite tests


def test_composite_1():
    run_formatter(
        {
            "format": "{composite_basic}",
            "expected": [
                {"color": "#FF0000", "full_text": "red "},
                {"color": "#00FF00", "full_text": "green "},
                {"color": "#0000FF", "full_text": "blue"},
            ],
        }
    )


def test_composite_2():
    run_formatter(
        {
            "format": "{composite_basic}",
            "expected": [
                {"color": "#FF0000", "full_text": "red "},
                {"color": "#00FF00", "full_text": "green "},
                {"color": "#0000FF", "full_text": "blue"},
            ],
            "composite": True,
        }
    )


def test_composite_3():
    run_formatter(
        {
            "format": "RGB: {composite_basic}",
            "expected": [
                {"full_text": "RGB: "},
                {"color": "#FF0000", "full_text": "red "},
                {"color": "#00FF00", "full_text": "green "},
                {"color": "#0000FF", "full_text": "blue"},
            ],
        }
    )


def test_composite_4():
    run_formatter(
        {
            "format": r"\?color=good {simple} {composite_basic} {complex}",
            "expected": [
                {"full_text": "NY 12:34 ", "color": "#00FF00"},
                {"color": "#FF0000", "full_text": "red "},
                {"color": "#00FF00", "full_text": "green "},
                {"color": "#0000FF", "full_text": "blue "},
                {"full_text": "LA 09:34NY 12:34", "color": "#00FF00"},
            ],
            "composite": True,
        }
    )


def test_composite_5():
    run_formatter(
        {
            "format": r"[\?color=#FF00FF {simple} {composite_basic} {complex2}]",
            "expected": [
                {"full_text": "NY 12:34 ", "color": "#FF00FF"},
                {"color": "#FF0000", "full_text": "red "},
                {"color": "#00FF00", "full_text": "green "},
                {"color": "#0000FF", "full_text": "blue "},
                {"color": "#FF0000", "full_text": "LA 09:34"},
                {"color": "#FF00FF", "full_text": "NY 12:34"},
            ],
            "composite": True,
        }
    )


def test_composite_6():
    run_formatter(
        {"format": "hello", "expected": [{"full_text": "hello"}], "composite": True}
    )


def test_attr_getter():
    run_formatter(
        {
            "format": "{test_attr_getter}",
            "expected": "*test_attr_getter*",
            "attr_getter": True,
        }
    )


def test_min_length_1():
    run_formatter({"format": r"\?min_length=9 Hello", "expected": "    Hello"})


def test_min_length_2():
    run_formatter({"format": r"[\?min_length=9&show Hello]", "expected": "    Hello"})


def test_min_length_3():
    run_formatter({"format": r"[\?min_length=9 [{name}]]", "expected": "    Björk"})


def test_min_length_4():
    run_formatter(
        {
            "format": r"[\?min_length=9 [\?color=good {name}]]",
            "expected": [{"color": "#00FF00", "full_text": "    Björk"}],
        }
    )


def test_min_length_5():
    run_formatter(
        {
            "format": r"\?min_length=9 [\?color=bad {number}][\?color=good {name}]",
            "expected": [
                {"full_text": "  42", "color": "#FF0000"},
                {"full_text": "Björk", "color": "#00FF00"},
            ],
        }
    )


def test_min_length_6():
    run_formatter(
        {
            "format": r"[\?min_length=9 [\?color=bad {number}][\?color=good {name}]]",
            "expected": [
                {"full_text": "  42", "color": "#FF0000"},
                {"full_text": "Björk", "color": "#00FF00"},
            ],
        }
    )


def test_numeric_strings_1():
    run_formatter({"format": "{str_int: d}", "expected": " 123"})


def test_numeric_strings_2():
    run_formatter({"format": "{str_int:.2f}", "expected": "123.00"})


def test_numeric_strings_3():
    run_formatter({"format": "{str_float: d}", "expected": " 123"})


def test_numeric_strings_4():
    run_formatter({"format": "{str_float:.1f}", "expected": "123.5"})


def test_numeric_strings_5():
    run_formatter({"format": "{str_nan: d}", "expected": "I'm not a number"})


def test_numeric_strings_6():
    run_formatter({"format": "{str_nan:.1f}", "expected": "I'm not a number"})


def test_not_zero_1():
    run_formatter({"format": r"[\?not_zero {zero}]", "expected": ""})


def test_not_zero_2():
    run_formatter({"format": r"[\?not_zero {zero_str}]", "expected": ""})


def test_not_zero_3():
    run_formatter({"format": r"[\?not_zero {zero_float}]", "expected": ""})


def test_not_zero_4():
    run_formatter({"format": r"[\?not_zero {yes}]", "expected": "True"})


def test_not_zero_5():
    run_formatter({"format": r"[\?not_zero {no}]", "expected": ""})


def test_not_zero_6():
    run_formatter({"format": r"[\?not_zero {number}]", "expected": "42"})


def test_not_zero_7():
    run_formatter({"format": r"[\?not_zero {pi}]", "expected": "3.14159265359"})


def test_not_zero_8():
    run_formatter({"format": r"[\?not_zero {name}]", "expected": "Björk"})


def test_not_zero_9():
    run_formatter({"format": r"[\?not_zero {str_nan}]", "expected": "I'm not a number"})


def test_not_zero_10():
    run_formatter(
        {"format": r"[\?not_zero {zero} {str_nan}]", "expected": "0 I'm not a number"}
    )


def test_not_zero_11():
    run_formatter({"format": r"[\?not_zero {zero_str} {zero}]", "expected": ""})


def test_bad_composite_color():
    run_formatter({"format": "{comp_bad_color}", "expected": "BAD"})


def test_soft_1():
    run_formatter({"format": r"{name}[\?soft  ]{name}", "expected": "Björk Björk"})


def test_soft_2():
    run_formatter({"format": r"{name}[\?soft  ]{empty}", "expected": "Björk"})


def test_soft_3():
    run_formatter({"format": r"{empty}[\?soft  ]{empty}", "expected": ""})


def test_soft_4():
    run_formatter({"format": r"[\?soft  ]", "expected": ""})


def test_soft_5():
    run_formatter(
        {"format": r"{number}[\?soft  {name} ]{number}", "expected": "42 Björk 42"}
    )


def test_soft_6():
    run_formatter({"format": r"{number}[\?soft  {name} ]{empty}", "expected": "42"})


def test_soft_7():
    run_formatter({"format": r"\?soft {number}", "expected": "42"})


def test_module_true():
    run_formatter({"format": r"[\?if=module_true something]", "expected": "something"})


def test_module_false():
    run_formatter({"format": r"[\?if=module_false something]", "expected": ""})


def test_module_true_value():
    run_formatter({"format": "{module_true}", "expected": "True"})


def test_module_false_value():
    run_formatter({"format": "{module_false}", "expected": ""})


def test_zero_format_1():
    run_formatter({"format": r"[\?not_zero {zero_almost}]", "expected": "0.0001"})


def test_zero_format_2():
    run_formatter({"format": r"[\?not_zero {zero_almost:d}]", "expected": ""})


def test_zero_format_3():
    run_formatter({"format": r"[\?not_zero {zero_almost:.3f}]", "expected": ""})


def test_zero_format_4():
    run_formatter({"format": r"[\?not_zero {zero_almost:.4f}]", "expected": "0.0001"})


def test_inherit_not_zero_1():
    run_formatter({"format": r"\?not_zero [{zero}]", "expected": ""})


def test_inherit_not_zero_2():
    run_formatter({"format": r"[\?not_zero [{zero}]]", "expected": ""})


def test_inherit_not_zero_3():
    run_formatter({"format": r"[\?not_zero [[[{zero}]]]]", "expected": ""})


def test_inherit_show_1():
    run_formatter({"format": r"\?show [[[hello]]]", "expected": "hello"})


def test_inherit_color_1():
    run_formatter(
        {
            "format": r"\?color=#F0F [[[{number}]]]",
            "expected": [{"color": "#FF00FF", "full_text": "42"}],
        }
    )


def test_inherit_color_2():
    run_formatter(
        {
            "format": r"\?color=#F0F [[\?color=good [{number}]]]",
            "expected": [{"color": "#00FF00", "full_text": "42"}],
        }
    )


def test_conditions_1():
    run_formatter({"format": r"\?if=number=42 cool beans", "expected": "cool beans"})


def test_conditions_2():
    run_formatter({"format": r"\?if=number=4 cool beans", "expected": ""})


def test_conditions_3():
    run_formatter({"format": r"\?if=!number=42 cool beans", "expected": ""})


def test_conditions_4():
    run_formatter({"format": r"\?if=!number=4 cool beans", "expected": "cool beans"})


def test_conditions_5():
    run_formatter({"format": r"\?if=missing=4 cool beans", "expected": ""})


def test_conditions_6():
    run_formatter({"format": r"\?if=name=Björk cool beans", "expected": "cool beans"})


def test_conditions_7():
    run_formatter({"format": r"\?if=name=Jimmy cool beans", "expected": ""})


def test_conditions_8():
    run_formatter({"format": r"\?if=name= cool beans", "expected": ""})


def test_conditions_9():
    run_formatter({"format": r"\?if=number= cool beans", "expected": ""})


def test_conditions_10():
    run_formatter(
        {"format": r"\?if=pi=3.14159265359 cool beans", "expected": "cool beans"}
    )


def test_conditions_11():
    run_formatter({"format": r"\?if=pi=3 cool beans", "expected": ""})


def test_conditions_12():
    run_formatter({"format": r"\?if=yes=3 cool beans", "expected": "cool beans"})


def test_conditions_13():
    run_formatter({"format": r"\?if=no=3 cool beans", "expected": ""})


def test_conditions_14():
    run_formatter({"format": r"\?if=number>3 cool beans", "expected": "cool beans"})


def test_conditions_15():
    run_formatter({"format": r"\?if=number<50 cool beans", "expected": "cool beans"})


def test_conditions_16():
    run_formatter({"format": r"\?if=number>50 cool beans", "expected": ""})


def test_conditions_17():
    run_formatter({"format": r"\?if=number<3 cool beans", "expected": ""})


def test_conditions_18():
    run_formatter({"format": r"\?if=name<Andrew cool beans", "expected": ""})


def test_conditions_19():
    run_formatter({"format": r"\?if=name>Andrew cool beans", "expected": "cool beans"})


def test_conditions_20():
    run_formatter({"format": r"\?if=name<John cool beans", "expected": "cool beans"})


def test_conditions_21():
    run_formatter({"format": r"\?if=name>John cool beans", "expected": ""})


def test_conditions_22():
    run_formatter({"format": r"\?if=missing>John cool beans", "expected": ""})


def test_conditions_23():
    run_formatter({"format": r"[\?if=None=None cool] beans", "expected": " beans"})


def test_trailing_zeroes_1():
    run_formatter(
        {
            "format": "{trailing_zeroes_1} becomes {trailing_zeroes_1:g}",
            "expected": "50.000 becomes 50",
        }
    )


def test_trailing_zeroes_2():
    run_formatter(
        {
            "format": "{trailing_zeroes_2} becomes {trailing_zeroes_2:g}",
            "expected": "5.500 becomes 5.5",
        }
    )


def test_ceiling_numbers_1():
    run_formatter(
        {"format": "{pi} becomes {pi:ceil}", "expected": "3.14159265359 becomes 4"}
    )


def test_ceiling_numbers_2():
    run_formatter(
        {
            "format": "{zero_almost} becomes {zero_almost:ceil}",
            "expected": "0.0001 becomes 1",
        }
    )


# get placeholder tests


def test_placeholders_1():
    get_placeholders({"format": "{placeholder}", "expected": {"placeholder"}})


def test_placeholders_2():
    get_placeholders(
        {
            "format": "[{placeholder}]{placeholder2:%d}",
            "expected": {"placeholder", "placeholder2"},
        }
    )


def test_placeholders_3():
    get_placeholders(
        {
            "format": r"{placeholder}[\?if=test something]",
            "expected": {"placeholder", "test"},
        }
    )


def test_placeholders_4():
    get_placeholders(
        {
            "format": r"{placeholder}[\?if=!test=42&color=red something]",
            "expected": {"placeholder", "test"},
        }
    )


def test_placeholders_5():
    get_placeholders(
        {
            "format": r"\{placeholder\}[\?if=test&color=red something]",
            "expected": {"test"},
        }
    )


# Placeholder update tests


def test_update_placeholders_1():
    update_placeholders(
        {"format": "{placeholder}", "updates": {}, "expected": "{placeholder}"}
    )


def test_update_placeholders_2():
    update_placeholders(
        {
            "format": "[{placeholder}]{placeholder2:%d}",
            "updates": {
                "placeholder": "new_placeholder",
                "placeholder2": "new_placeholder2",
            },
            "expected": "[{new_placeholder}]{new_placeholder2:%d}",
        }
    )


def test_update_placeholders_3():
    update_placeholders(
        {
            "format": r"{placeholder}[\?if=test something]",
            "updates": {"test": "new_test"},
            "expected": r"{placeholder}[\?if=new_test something]",
        }
    )


def test_update_placeholders_4():
    update_placeholders(
        {
            "format": r"{placeholder}[\?if=!test=42&color=red something]",
            "updates": {"red": "blue"},
            "expected": r"{placeholder}[\?if=!test=42&color=red something]",
        }
    )


def test_update_placeholders_5():
    update_placeholders(
        {
            "format": r"\{placeholder\}{placeholder}[\?if=placeholder&color=red something]",
            "updates": {"placeholder": "new_placeholder"},
            "expected": r"\{placeholder\}{new_placeholder}[\?if=new_placeholder&color=red something]",
        }
    )


def test_get_color_names_1():
    get_color_names(
        {
            "format": r"\?color=red \?color=#0f0 green \?color=#0000ff blue",
            "expected": set(),
        }
    )


def test_get_color_names_2():
    get_color_names(
        {
            "format": r"[\?color=tobias funke|\?color=bluemangroup troupe]",
            "expected": {"tobias", "bluemangroup"},
        }
    )


def test_get_color_names_3():
    get_color_names(
        {
            "format": r"[\?color=good bonsai tree][\?color=None Saibot]",
            "expected": set(),
        }
    )


def test_get_color_names_4():
    get_color_names(
        {
            "format": r"\?color=rebeccapurple \?color=rebecca \?color=purple",
            "expected": {"rebecca"},
        }
    )


if __name__ == "__main__":
    # run tests
    import sys

    this_module = sys.modules[__name__]
    for _ in range(10):
        for name in dir(this_module):
            if not name.startswith("test_"):
                continue
            getattr(this_module, name)()
