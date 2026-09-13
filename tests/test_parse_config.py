from codecs import BOM_UTF16_BE, BOM_UTF16_LE, BOM_UTF32_BE, BOM_UTF32_LE

import pytest

import py3status.parse_config as parse_config
from py3status.constants import GENERAL_DEFAULTS

CONFIG = '''\
order += "static_string"
static_string {
    format = "café"
}
'''

DETECTED_CONFIGS = [
    (CONFIG.encode("latin-1"), b"iso-8859-1"),
    (BOM_UTF16_LE + CONFIG.encode("utf-16-le"), b"utf-16le"),
    (BOM_UTF16_BE + CONFIG.encode("utf-16-be"), b"utf-16be"),
    (BOM_UTF32_LE + CONFIG.encode("utf-32-le"), b"utf-32le"),
    (BOM_UTF32_BE + CONFIG.encode("utf-32-be"), b"utf-32be"),
]


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        (CONFIG.replace("café", "cafe").encode("ascii"), "cafe"),
        (CONFIG.encode("utf-8"), "café"),
        (CONFIG.encode("utf-8-sig"), "café"),
    ],
)
def test_process_config_without_detection(tmp_path, monkeypatch, payload, expected):
    def unexpected_file_call(*args, **kwargs):
        raise AssertionError("file should not be called for ASCII or UTF-8 config")

    monkeypatch.setattr(parse_config, "check_output", unexpected_file_call)
    config_path = tmp_path / "py3status.conf"
    config_path.write_bytes(payload)

    config = parse_config.process_config(config_path)

    assert config["static_string"]["format"] == expected


@pytest.mark.parametrize(
    ("payload", "detected_encoding"),
    DETECTED_CONFIGS,
)
def test_process_config_detected_encoding(tmp_path, monkeypatch, payload, detected_encoding):
    def detect_encoding(command, timeout):
        assert command[:4] == ["file", "-b", "--mime-encoding", "--dereference"]
        assert timeout == 3
        return detected_encoding

    monkeypatch.setattr(parse_config, "check_output", detect_encoding)
    config_path = tmp_path / "py3status.conf"
    config_path.write_bytes(payload)

    config = parse_config.process_config(config_path)

    assert config["static_string"]["format"] == "café"


@pytest.mark.parametrize("payload", [payload for payload, _ in DETECTED_CONFIGS])
def test_process_config_file_detection(tmp_path, payload):
    config_path = tmp_path / "py3status.conf"
    config_path.write_bytes(payload)

    config = parse_config.process_config(config_path)

    assert config["static_string"]["format"] == "café"


def write_config(tmp_path, text):
    path = tmp_path / "config"
    path.write_text(text)
    return path


def test_configured_i3status_container_gets_whole_dicts_as_items(tmp_path):
    """
    Unlike a group/frame's children (separate Modules, so the generic
    walker only needs to remember their names), an i3status container's
    nested items are just settings dicts i3status.py writes straight into
    a generated i3status.conf - it needs the whole dict, with its own
    name embedded, not a bare name.
    """
    config_path = write_config(
        tmp_path,
        """
order += "i3status handconfig"

i3status handconfig {
    load {
        format = "%1min"
    }
    disk "/" {
        format = "%avail"
    }
}
""",
    )
    config = parse_config.process_config(config_path)

    items = config["i3status handconfig"]["items"]
    assert [dict(item) for item in items] == [
        {"name": "load", "format": "%1min"},
        {"name": "disk /", "format": "%avail"},
    ]
    # not top-level config entries - a group/frame's children would get
    # one each, but an i3status container's nested items aren't Modules
    assert "load" not in config
    assert "disk /" not in config


def test_configured_i3status_container_general_stays_general(tmp_path):
    """
    Regression: a nested general{} block used to get the same anonymous-
    instance treatment as any other unnamed nested module (becoming
    "general _anon_module_0", swept into items right along with real
    modules) - the container's own general.interval was silently
    dropped, and the fake "general ..." item made no sense as an
    i3status module. general/py3status are reserved names, not module
    types, and should never be anon-named or land in items.

    Also covers GENERAL_DEFAULTS (colors etc) getting merged in the same
    way the top-level general{} does - not just the explicitly-set keys.
    """
    config_path = write_config(
        tmp_path,
        """
order += "i3status handconfig"

i3status handconfig {
    general {
        interval = 2
    }
    load {
        format = "%1min"
    }
}
""",
    )
    config = parse_config.process_config(config_path)

    assert config["i3status handconfig"]["general"] == {**GENERAL_DEFAULTS, "interval": 2}
    items = config["i3status handconfig"]["items"]
    assert [dict(item) for item in items] == [{"name": "load", "format": "%1min"}]


def test_anon_naming_skips_a_user_typed_collision(tmp_path):
    """
    Regression: anon-naming used to hand out "name _anon_module_N" from a
    bare, unchecked counter - if a user happened to type that exact name
    themselves, the later auto-generated one silently clobbered it via
    plain dict assignment (dictionary[name] = value), losing the user's
    module entirely with no warning. It must now skip any name already
    claimed, same discipline as the reserved GENERATED_SLUG wipe.
    """
    config_path = write_config(
        tmp_path,
        """
order += "group mygroup"

group mygroup {
    clock _anon_module_0 {
        format = "user typed this"
    }
    clock {
        format = "auto anon"
    }
}
""",
    )
    config = parse_config.process_config(config_path)

    assert config["group mygroup"]["items"] == ["clock _anon_module_0", "clock _anon_module_1"]
    assert config["clock _anon_module_0"]["format"] == "user typed this"
    assert config["clock _anon_module_1"]["format"] == "auto anon"


def test_anon_naming_counter_is_global_across_containers(tmp_path):
    """
    Regression: the collision-check for anon-naming used to be scoped to
    only the current container's own dict, letting two separate groups'
    anon modules land on the identical name ("clock _anon_module_0" in
    both) - since the final flat config is keyed by that name at the top
    level (config[name] = module), the second group's clock silently
    overwrote the first's, and module_groups wrongly listed both groups
    against one shared module. The counter must persist across the whole
    parse, same as it did before collision-checking was ever added.
    """
    config_path = write_config(
        tmp_path,
        """
order += "group groupA"
order += "group groupB"

group groupA {
    clock {
        format = "a1"
    }
    clock {
        format = "a2"
    }
}

group groupB {
    clock {
        format = "b1"
    }
}
""",
    )
    config = parse_config.process_config(config_path)

    assert config["group groupA"]["items"] == ["clock _anon_module_0", "clock _anon_module_1"]
    assert config["group groupB"]["items"] == ["clock _anon_module_2"]
    assert config["clock _anon_module_0"]["format"] == "a1"
    assert config["clock _anon_module_1"]["format"] == "a2"
    assert config["clock _anon_module_2"]["format"] == "b1"
    assert config[".module_groups"]["clock _anon_module_2"] == ["group groupB"]


def test_generated_instance_name_gets_wiped_for_any_module_type(tmp_path):
    """
    The reserved GENERATED_SLUG marker is reserved for a machine-
    generated instance of any module type, not just i3status containers
    - a plain py3status module claiming it (bare, or "_generated_dog"-
    prefixed) gets it wiped the same way. Different types never collide
    with each other's own "_dog" fallback, since collisions are checked
    per module type.
    """
    config_path = write_config(
        tmp_path,
        """
order += "clock _generated"
order += "clock _dog"
order += "static_string _generated_dog"

clock _generated {
    format = "clock A"
}

clock _dog {
    format = "clock B"
}

static_string _generated_dog {
    format = "hi"
}
""",
    )
    config = parse_config.process_config(config_path)

    assert config["order"] == ["clock", "clock _dog", "static_string _dog"]
    assert config["clock"]["format"] == "clock A"
    assert config["clock _dog"]["format"] == "clock B"
    assert config["static_string _dog"]["format"] == "hi"


def test_generated_instance_name_falls_back_on_collision_for_any_type(tmp_path):
    """
    If the stripped name is already taken (by this same module type),
    fall back to "_2" instead of the two colliding.
    """
    config_path = write_config(
        tmp_path,
        """
order += "clock"
order += "clock _generated"

clock {
    format = "already here"
}

clock _generated {
    format = "needs to fall back"
}
""",
    )
    config = parse_config.process_config(config_path)

    assert config["order"] == ["clock", "clock _2"]
    assert config["clock"]["format"] == "already here"
    assert config["clock _2"]["format"] == "needs to fall back"


def test_configured_bare_generated_name_gets_wiped_to_unnamed(tmp_path):
    """
    The same GENERATED_SLUG reservation applies to i3status containers,
    exercised here as the real-world case that motivated it: the real
    auto-generated container always claims that exact name, so a
    configured section also claiming it (bare, no suffix) gets the word
    wiped instead of the two colliding - becoming a bare, unnamed
    "i3status", not a renumbered one.
    """
    config_path = write_config(
        tmp_path,
        """
order += "i3status _generated"
order += "load"

i3status _generated {
    disk "/" {
        format = "%avail"
    }
}

load {
    format = "%1min"
}
""",
    )
    config = parse_config.process_config(config_path)

    # the real generated container gets "_generated" and the bare
    # "load" section, with no order slot of its own
    assert [item["name"] for item in config["i3status _generated"]["items"]] == ["load"]
    assert "i3status _generated" not in config["order"]
    # the configured one, wiped, keeps its own items and its own
    # order slot - now bare and unnamed
    assert [item["name"] for item in config["i3status"]["items"]] == ["disk /"]
    assert "i3status" in config["order"]
    assert "i3status_proxy disk" in config


def test_configured_generated_prefixed_name_gets_wiped(tmp_path):
    """
    Only the literal GENERATED_SLUG marker is reserved, not anything it
    happens to be glued to - "i3status _generated_dog" becomes "i3status
    _dog" (keeping the rest of the instance the user actually chose),
    same rule as any other module type.
    """
    config_path = write_config(
        tmp_path,
        """
order += "i3status _generated_dog"

i3status _generated_dog {
    disk "/" {
        format = "%avail"
    }
}
""",
    )
    config = parse_config.process_config(config_path)

    assert "i3status _dog" in config
    assert [item["name"] for item in config["i3status _dog"]["items"]] == ["disk /"]
    assert "i3status _dog" in config["order"]
    assert "i3status_proxy dog_disk" in config


def test_wiped_i3status_name_falls_back_further_if_it_collides_too(tmp_path):
    """
    Wiping "_generated" off "i3status _generated_dog" produces "i3status
    _dog" - if a real, separate "i3status _dog" is also configured,
    that's a genuine second collision (unrelated to the reserved-name
    rule), so the wiped one falls back to "i3status _dog_2" instead of
    the two colliding. The real "i3status _dog" is left untouched.
    """
    config_path = write_config(
        tmp_path,
        """
order += "i3status _generated_dog"
order += "i3status _dog"

i3status _generated_dog {
    disk "/" {
        format = "%avail"
    }
}

i3status _dog {
    load {
        format = "%1min"
    }
}
""",
    )
    config = parse_config.process_config(config_path)

    assert [item["name"] for item in config["i3status _dog"]["items"]] == ["load"]
    assert [item["name"] for item in config["i3status _dog_2"]["items"]] == ["disk /"]
    assert "i3status _dog" in config["order"]
    assert "i3status _dog_2" in config["order"]


def test_configured_i3status_container_hoists_on_click_to_its_proxy(tmp_path):
    """
    A configured item's on_click never went through process_onclick()
    during the main parse (resolve_configured_i3status_containers() removes
    it from the tree before that walk ever runs) - it parses/hoists it
    to config["on_click"] itself, keyed by the item's own generated proxy
    name, same mechanism any other real module's on_click already uses (the
    proxy is a real, independently registered Module).
    """
    config_path = write_config(
        tmp_path,
        """
order += "i3status handconfig"

i3status handconfig {
    load {
        format = "%1min"
        on_click 1 = "exec echo clicked"
    }
}
""",
    )
    config = parse_config.process_config(config_path)

    item = config["i3status handconfig"]["items"][0]
    assert "on_click 1" not in item
    proxy_name = config["i3status handconfig"]["_proxies"][0]
    assert config["on_click"][proxy_name] == {1: "exec echo clicked"}
    assert "load" not in config["on_click"]


def test_group_container_children_are_still_bare_names(tmp_path):
    """
    Regression check: a real group/frame container (unrelated to
    i3status) must keep getting bare child names in items, and each
    child must still get its own top-level config entry - only
    i3status containers changed behavior.
    """
    config_path = write_config(
        tmp_path,
        """
order += "group mygroup"

group mygroup {
    static_string one {
        format = "one"
    }
    static_string two {
        format = "two"
    }
}
""",
    )
    config = parse_config.process_config(config_path)

    assert config["group mygroup"]["items"] == ["static_string one", "static_string two"]
    assert config["static_string one"]["format"] == "one"
    assert config["static_string two"]["format"] == "two"


def test_process_onclick_accepts_button_20(tmp_path):
    """
    1-20 inclusive - 20 is a valid button, not an off-by-one edge case to
    reject (range(1, 20) used to silently exclude it).
    """
    config_path = write_config(
        tmp_path,
        """
order += "static_string"

static_string {
    format = "hi"
    on_click 20 = "exec echo clicked"
}
""",
    )
    config = parse_config.process_config(config_path)

    assert config["on_click"]["static_string"] == {20: "exec echo clicked"}


def test_process_onclick_rejects_button_above_20(tmp_path, capsys):
    config_path = write_config(
        tmp_path,
        """
order += "static_string"

static_string {
    format = "hi"
    on_click 21 = "exec echo clicked"
}
""",
    )
    config = parse_config.process_config(config_path)

    assert "static_string" not in config["on_click"]
    assert "not in range 1-20" in capsys.readouterr().out


def test_module_never_taking_an_instance_with_one_is_a_config_error(tmp_path, capsys):
    """
    "memory" never takes a title in real i3status (unlike eg "disk") -
    confirmed against the real binary, which rejects it with "missing
    opening brace for section 'memory'" since it expects only one token.
    """
    config_path = write_config(
        tmp_path,
        """
order += "memory foo"

memory foo {
    format = "%used"
}
""",
    )
    config = parse_config.process_config(config_path)

    assert "cannot have 2 tokens" in capsys.readouterr().out
    assert "group error" in config
