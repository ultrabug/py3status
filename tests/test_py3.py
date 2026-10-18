from pprint import pformat

from py3status.py3 import Py3

py3 = Py3()


class MissingSetting:
    none_setting = True


class MockWrapper:
    config = {"py3_config": {"general": {}}}
    output_modules = {}

    def __init__(self, settings):
        self.settings = settings

    def get_config_attribute(self, module_name, name):
        return self.settings.get(name, MissingSetting())


class MockModule:
    module_full_name = "test_module"
    module_class = object()

    def __init__(self, settings):
        self._py3_wrapper = MockWrapper(settings)


def test_config_color_resolution(monkeypatch):
    monkeypatch.setattr(Py3, "_formatter", None)

    default_color = Py3(MockModule({})).COLOR_REBECCAPURPLE
    disabled_color = Py3(MockModule({"color_rebeccapurple": None})).COLOR_REBECCAPURPLE

    assert default_color == "#663399"
    assert disabled_color
    assert not py3.is_color(disabled_color)
    assert Py3(MockModule({})).COLOR_HIDDEN == "hidden"
    assert Py3(MockModule({})).COLOR_NOTACOLOR is None


def test_format_units():

    tests = [
        # basic unit guessing
        (dict(value=100), (100, "B")),
        (dict(value=999), (999, "B")),
        (dict(value=1000), (0.977, "KiB")),
        (dict(value=1024), (1.0, "KiB")),
        (dict(value=pow(1024, 2)), (1.0, "MiB")),
        (dict(value=pow(1024, 3)), (1.0, "GiB")),
        (dict(value=pow(1024, 4)), (1.0, "TiB")),
        (dict(value=pow(1024, 5)), (1.0, "PiB")),
        # no guessing
        (dict(value=pow(1024, 2), auto=False), (pow(1024, 2), "B")),
        (dict(value=pow(1024, 2), auto=False, unit="B"), (pow(1024, 2), "B")),
        (dict(value=pow(1024, 2), auto=False, unit="KiB"), (1024, "KiB")),
        # guess with si units
        (dict(value=100, si=True), (100, "B")),
        (dict(value=1000, si=True), (1.0, "kB")),
        (dict(value=pow(1000, 2), si=True), (1.0, "MB")),
        (dict(value=pow(1000, 3), si=True), (1.0, "GB")),
        (dict(value=pow(1000, 4), si=True), (1.0, "TB")),
        (dict(value=pow(1000, 5), si=True), (1.0, "PB")),
        # forced MiB
        (dict(value=pow(1024, 1), unit="MiB"), (0.000977, "MiB")),
        (dict(value=pow(1024, 2), unit="MiB"), (1.0, "MiB")),
        (dict(value=pow(1024, 3), unit="MiB"), (1024, "MiB")),
        (dict(value=pow(1024, 4), unit="MiB"), (pow(1024, 2), "MiB")),
        (dict(value=pow(1024, 5), unit="MiB"), (pow(1024, 3), "MiB")),
        # endings
        (dict(value=100, unit="b/s"), (100, "b/s")),
        (dict(value=1024, unit="b/s"), (1.0, "Kib/s")),
        (dict(value=pow(1024, 2), unit="b/s"), (1.0, "Mib/s")),
        (dict(value=pow(1000, 2), si=True, unit="b/s"), (1.0, "Mb/s")),
        (dict(value=pow(1024, 3), unit="Mib/sec"), (1024, "Mib/sec")),
        # optimal
        (dict(value=1234567890), (1.15, "GiB")),
        (dict(value=1234567890, optimal=None), (1.1497809458523989, "GiB")),
        (dict(value=1234567890, optimal=1), (1, "GiB")),
        (dict(value=1234567890, optimal=2), (1, "GiB")),
        (dict(value=1234567890, optimal=3), (1.1, "GiB")),
        (dict(value=1234567890, optimal=5), (1.15, "GiB")),
        (dict(value=1234567890, unit="MiB"), (1177, "MiB")),
        (dict(value=1234567890, unit="MiB", optimal=None), (1177.3756885528564, "MiB")),
        (dict(value=1234567890, unit="MiB", optimal=2), (1177, "MiB")),
        (dict(value=1234567890, unit="MiB", optimal=6), (1177.4, "MiB")),
        (dict(value=1234567890, unit="MiB", optimal=9), (1177.3757, "MiB")),
    ]

    for test in tests:
        print(test)
        # we use repr in the assert to ensure 1 and 1.0 are not treated the
        # same
        assert repr(py3.format_units(**test[0])) == repr(test[1])


def test_flatten_dict():
    data = {
        "fish_facts": {
            "sharks": "Most will drown if they stop moving",
            "skates": "More than 200 species",
        },
        "fruits": ["apple", "peach", "watermelon"],
        "number": 52,
    }
    expected = {
        "fish_facts-sharks": "Most will drown if they stop moving",
        "fish_facts-skates": "More than 200 species",
        "fruits-0": "apple",
        "fruits-1": "peach",
        "fruits-2": "watermelon",
        "number": 52,
    }

    returned = py3.flatten_dict(data, delimiter="-")
    print("returned data")
    print(pformat(returned))
    assert returned == expected


def test_flatten_dict_intermediates():
    data = {
        "fish_facts": {
            "sharks": "Most will drown if they stop moving",
            "skates": "More than 200 species",
        },
        "fruits": ["apple", "peach", "watermelon"],
        "number": 52,
    }
    expected = {
        "fish_facts": {
            "sharks": "Most will drown if they stop moving",
            "skates": "More than 200 species",
        },
        "fish_facts-sharks": "Most will drown if they stop moving",
        "fish_facts-skates": "More than 200 species",
        "fruits": ["apple", "peach", "watermelon"],
        "fruits-0": "apple",
        "fruits-1": "peach",
        "fruits-2": "watermelon",
        "number": 52,
    }

    returned = py3.flatten_dict(data, delimiter="-", intermediates=True)
    print("returned data")
    print(pformat(returned))
    assert returned == expected


def test_flatten_dict_deep():
    data = {
        "hash": {
            "dict": {"array": [1, 2, [1, 2, {"#": 123}]]},
            "list": [1, 2, [1, 2, {"mapping": 123}]],
        },
        "list": [1, 2, [1, 2, {"mapping": 123}]],
    }

    expected = {
        "hash-dict-array-0": 1,
        "hash-dict-array-1": 2,
        "hash-dict-array-2-0": 1,
        "hash-dict-array-2-1": 2,
        "hash-dict-array-2-2-#": 123,
        "hash-list-0": 1,
        "hash-list-1": 2,
        "hash-list-2-0": 1,
        "hash-list-2-1": 2,
        "hash-list-2-2-mapping": 123,
        "list-0": 1,
        "list-1": 2,
        "list-2-0": 1,
        "list-2-1": 2,
        "list-2-2-mapping": 123,
    }

    assert py3.flatten_dict(data, delimiter="-") == expected
    returned = py3.flatten_dict(data, delimiter="-")
    print("returned data")
    print(pformat(returned))
    assert returned == expected


def test_flatten_dict_deep_intermediates():
    data = {
        "hash": {
            "dict": {"array": [1, 2, [1, 2, {"#": 123}]]},
            "list": [1, 2, [1, 2, {"mapping": 123}]],
        },
        "list": [1, 2, [1, 2, {"mapping": 123}]],
    }

    expected = {
        "hash": {
            "dict": {"array": [1, 2, [1, 2, {"#": 123}]]},
            "list": [1, 2, [1, 2, {"mapping": 123}]],
        },
        "hash-dict": {"array": [1, 2, [1, 2, {"#": 123}]]},
        "hash-dict-array": [1, 2, [1, 2, {"#": 123}]],
        "hash-dict-array-0": 1,
        "hash-dict-array-1": 2,
        "hash-dict-array-2": [1, 2, {"#": 123}],
        "hash-dict-array-2-0": 1,
        "hash-dict-array-2-1": 2,
        "hash-dict-array-2-2": {"#": 123},
        "hash-dict-array-2-2-#": 123,
        "hash-list": [1, 2, [1, 2, {"mapping": 123}]],
        "hash-list-0": 1,
        "hash-list-1": 2,
        "hash-list-2": [1, 2, {"mapping": 123}],
        "hash-list-2-0": 1,
        "hash-list-2-1": 2,
        "hash-list-2-2": {"mapping": 123},
        "hash-list-2-2-mapping": 123,
        "list": [1, 2, [1, 2, {"mapping": 123}]],
        "list-0": 1,
        "list-1": 2,
        "list-2": [1, 2, {"mapping": 123}],
        "list-2-0": 1,
        "list-2-1": 2,
        "list-2-2": {"mapping": 123},
        "list-2-2-mapping": 123,
    }

    returned = py3.flatten_dict(data, delimiter="-", intermediates=True)
    print("returned data")
    print(pformat(returned))
    assert returned == expected


def test_flatten_dict_parent_key():
    data = {
        "fish_facts": {
            "sharks": "Most will drown if they stop moving",
            "skates": "More than 200 species",
        },
        "fruits": ["apple", "peach", "watermelon"],
        "number": 52,
    }
    expected = {
        "purple-fish_facts-sharks": "Most will drown if they stop moving",
        "purple-fish_facts-skates": "More than 200 species",
        "purple-fruits-0": "apple",
        "purple-fruits-1": "peach",
        "purple-fruits-2": "watermelon",
        "purple-number": 52,
    }

    returned = py3.flatten_dict(data, delimiter="-", parent_key="purple")
    print("returned data")
    print(pformat(returned))
    assert returned == expected


class FrozenClock:
    """time.time() and time.monotonic() that only move when told to."""

    def __init__(self):
        self.wall = 1_700_000_000.37
        self.mono = 50_000.37

    def time(self):
        return self.wall

    def monotonic(self):
        return self.mono

    def advance(self, seconds):
        self.wall += seconds
        self.mono += seconds


def time_in_with(monkeypatch, clock):
    monkeypatch.setattr("py3status.py3.time", clock)
    return Py3().time_in


def wall_at(clock, due):
    return clock.wall + due - clock.mono


def test_time_in_lands_on_the_second(monkeypatch):
    clock = FrozenClock()
    time_in = time_in_with(monkeypatch, clock)

    for seconds in (0, 1, 5, 10):
        due = time_in(seconds)
        assert due > clock.mono
        assert round(wall_at(clock, due) % 1, 6) in (0, 1)
    assert round(wall_at(clock, time_in(sync_to=60)) % 60, 6) in (0, 60)


def test_time_in_offset(monkeypatch):
    clock = FrozenClock()
    time_in = time_in_with(monkeypatch, clock)
    offset = clock.wall + 7.25  # e.g. when a countdown ends

    due = time_in(0, offset=offset)
    assert round((wall_at(clock, due) - offset) % 1, 6) in (0, 1)


def test_time_in_steady_gaps(monkeypatch):
    # a module asking again right after it ran gets exactly the gap it asked for
    for seconds in (0.1, 0.2, 0.25, 0.5, 1, 2, 5):
        clock = FrozenClock()
        time_in = time_in_with(monkeypatch, clock)
        gaps = []
        for _ in range(8):
            step = time_in(seconds) - clock.mono + 0.003  # runs a few ms late
            clock.advance(step)
            gaps.append(round(step, 2))
        assert set(gaps[3:]) == {seconds}, seconds


def test_time_in_cache_forever():
    assert py3.time_in(py3.CACHE_FOREVER) is py3.CACHE_FOREVER
