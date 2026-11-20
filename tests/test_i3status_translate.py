from py3status.config_types import ModuleDefinition
from py3status.i3status.translate import (
    DEFAULT_GENERAL_INTERVAL,
    DEFAULT_ITEMS,
    _flatten_container_items,
)
from py3status.parse_config import process_config


def write_config(tmp_path, text):
    path = tmp_path / "config"
    path.write_text(text)
    return path


def test_flatten_container_items_in_isolation():
    """
    Exercises _flatten_container_items() directly, on a hand-built
    container, with no config file or the rest of process_config() involved -
    the whole point of a small extracted helper is that this transformation
    can be understood and tested on its own.
    """
    load = ModuleDefinition({"format": "%1min", "on_click 1": "exec echo hi"})
    container = ModuleDefinition({"format_module_separator": " | ", "load": load})

    items = _flatten_container_items(container)

    # nested item replaced by a whole dict, name embedded, on_click left in
    # place, no longer a separate tree node
    assert "load" not in container
    assert items == [{"format": "%1min", "on_click 1": "exec echo hi", "name": "load"}]
    # unrelated (non-ModuleDefinition) keys are left alone
    assert container["format_module_separator"] == " | "


def test_consecutive_i3status_sections_share_one_container(tmp_path):
    config_path = write_config(
        tmp_path,
        """
general {
    interval = 5
}

order += "disk /"
order += "wireless _first_"
order += "load"

disk "/" {
    format = "%avail"
}

wireless _first_ {
    format_up = "W: %quality"
}

load {
    format = "%1min"
}
""",
    )
    config = process_config(config_path)

    assert config["order"] == [
        "i3status_proxy _generated_disk_0",
        "i3status_proxy _generated_wireless_first_0",
        "i3status_proxy _generated_load_0",
    ]
    # the container has no bar slot of its own and drives none of the old
    # i3status_wrapper.py subsystem, but must still be instantiated as a
    # real Module - that's driven by py3_modules, not order
    assert "i3status _generated" in config["py3_modules"]
    assert "i3status _generated" not in config["order"]
    container = config["i3status _generated"]
    assert [item["name"] for item in container["items"]] == ["disk /", "wireless _first_", "load"]
    assert container["items"][0] == {"name": "disk /", "format": "%avail"}
    # lets the container force-refresh its own proxies when it clears the
    # registry on death/reload, instead of them showing stale output until
    # their own cache_timeout happens to elapse - see i3status._cleanup()
    assert container["_proxies"] == [
        "i3status_proxy _generated_disk_0",
        "i3status_proxy _generated_wireless_first_0",
        "i3status_proxy _generated_load_0",
    ]


def test_auto_generated_container_logs_a_suggestion_not_a_deprecation(tmp_path, caplog):
    """
    Bare i3status modules are fully supported, not deprecated - the
    warning should nudge toward an explicit 'i3status <name> {}' section
    for finer control, without implying the bare form is going away.
    """
    config_path = write_config(
        tmp_path,
        """
order += "disk /"

disk "/" {
    format = "%avail"
}
""",
    )
    process_config(config_path)

    warnings = [r.message for r in caplog.records if r.levelname == "WARNING"]
    assert any("auto-generating an i3status container" in w for w in warnings)
    assert not any("legacy" in w.lower() or "deprecat" in w.lower() for w in warnings)


def test_no_generated_container_logs_no_suggestion(tmp_path, caplog):
    """
    A config with no bare i3status modules at all has nothing to
    auto-generate - the suggestion warning must not fire regardless.
    """
    config_path = write_config(
        tmp_path,
        """
order += "clock"

clock {
    format = "%H:%M"
}
""",
    )
    process_config(config_path)

    warnings = [r.message for r in caplog.records if r.levelname == "WARNING"]
    assert not any("auto-generating an i3status container" in w for w in warnings)


def test_run_interrupted_by_py3status_module_still_shares_one_container(tmp_path):
    """
    A py3status-native module in between two i3status runs used to split
    them into separate containers/subprocesses (_generated/_generated_2) - now, by
    default, every i3status section shares one container/subprocess
    regardless of how many separate runs exist, since a proxy's own
    position in `order` is independent of which container produced its
    data.
    """
    config_path = write_config(
        tmp_path,
        """
order += "disk /"
order += "battery_level"
order += "load"

disk "/" {
    format = "%avail"
}

load {
    format = "%1min"
}
""",
    )
    config = process_config(config_path)

    assert "i3status _generated" in config["py3_modules"]
    assert "i3status _generated_2" not in config["py3_modules"]
    assert config["order"] == [
        "i3status_proxy _generated_disk_0",
        "battery_level",
        "i3status_proxy _generated_load_0",
    ]
    assert [item["name"] for item in config["i3status _generated"]["items"]] == ["disk /", "load"]


def test_different_instances_of_same_type_get_distinct_generated_names(tmp_path):
    config_path = write_config(
        tmp_path,
        """
order += "disk /"
order += "disk /home"

disk "/" {
    format = "%avail root"
}

disk "/home" {
    format = "%avail home"
}
""",
    )
    config = process_config(config_path)

    assert config["order"] == [
        "i3status_proxy _generated_disk_0",
        "i3status_proxy _generated_disk_home_0",
    ]
    assert config["i3status_proxy _generated_disk_0"]["_item_instance"] == "/"
    assert config["i3status_proxy _generated_disk_home_0"]["_item_instance"] == "/home"


def test_exact_same_section_name_twice_gets_distinct_generated_names(tmp_path):
    """
    The same section can legitimately appear twice in order (eg shown on
    both sides of the bar). Each occurrence must read the original,
    unmodified config - not a version already consumed/deleted by the
    first occurrence - and get its own generated name.
    """
    config_path = write_config(
        tmp_path,
        """
order += "load"
order += "clock"
order += "load"

load {
    format = "%1min"
}

clock {
    format = "{Local}"
}
""",
    )
    config = process_config(config_path)

    assert config["order"] == [
        "i3status_proxy _generated_load_0",
        "clock",
        # every run shares one container now, so this second "load" just
        # gets the next index - the slug repeats, the index still disambiguates
        "i3status_proxy _generated_load_1",
    ]
    assert "format" not in config["i3status_proxy _generated_load_0"]
    assert config["i3status_proxy _generated_load_1"]["_item_name"] == "load"
    # both occurrences read the same original, undamaged config - neither
    # a KeyError from deleting it too early, nor an empty second read
    assert config["i3status _generated"]["items"][0]["format"] == "%1min"
    assert config["i3status _generated"]["items"][1]["format"] == "%1min"


def test_same_slug_reused_across_top_level_and_nested_group_shares_one_counter(tmp_path):
    """
    The per-slug counter in resolve_bare_i3status_modules() is global
    across the whole config, not scoped to wherever a bare item physically
    sits - three top-level "load" occurrences interleaved with other
    modules, plus a fourth "load" nested inside an ordinary group, must
    all draw from the same "load" counter in encounter order, landing on
    _0/_1/_2/_3 with no collisions.
    """
    config_path = write_config(
        tmp_path,
        """
order += "load"
order += "clock"
order += "load"
order += "group mygroup"
order += "battery_level"
order += "load"

load {
    format = "%1min"
}

clock {
    format = "{Local}"
}

group mygroup {
    load {
        format = "%1min nested"
    }
}

battery_level {
    format = "%percent"
}
""",
    )
    config = process_config(config_path)

    assert config["order"] == [
        "i3status_proxy _generated_load_0",
        "clock",
        "i3status_proxy _generated_load_1",
        "group mygroup",
        "battery_level",
        "i3status_proxy _generated_load_3",
    ]
    assert config["i3status _generated"]["_proxies"] == [
        "i3status_proxy _generated_load_0",
        "i3status_proxy _generated_load_1",
        "i3status_proxy _generated_load_2",
        "i3status_proxy _generated_load_3",
    ]
    # the group-nested occurrence renamed the group's own child key in
    # place, keeping its slot between the two top-level occurrences that
    # bracket it in encounter order
    assert config["group mygroup"]["items"] == ["i3status_proxy _generated_load_2"]


def test_repeated_bare_name_keeps_on_click_on_every_occurrence(tmp_path):
    """
    Every occurrence of a repeated top-level name reads the same shared
    raw dict - parse_onclick() pops on_click keys from it destructively,
    so without a copy per occurrence, only the first would keep its
    on_click handler and every later one would silently lose it.
    """
    config_path = write_config(
        tmp_path,
        """
order += "load"
order += "load"

load {
    format = "%1min"
    on_click 1 = "exec echo hi"
}
""",
    )
    config = process_config(config_path)

    proxies = [name for name in config["order"] if "i3status_proxy" in name]
    assert len(proxies) == 2
    for proxy_name in proxies:
        assert config["on_click"][proxy_name] == {1: "exec echo hi"}


def test_slug_collision_between_different_names_gets_distinct_generated_names(tmp_path):
    """
    "disk /mnt-a" and "disk /mnt_a" are different real mount paths but
    slugify() collapses both "-" and "_" to "_", producing the same slug -
    within a configured container (whose proxies are still slug-named,
    unlike a bare item's own plain sequential index), occurrence tracking
    must be keyed on the slug, not the original name, or the second one
    silently overwrites the first's generated config.
    """
    config_path = write_config(
        tmp_path,
        """
order += "i3status handconfig"

i3status handconfig {
    disk "/mnt-a" {
        format = "MNT-A"
    }
    disk "/mnt_a" {
        format = "MNT_A"
    }
}
""",
    )
    config = process_config(config_path)

    assert config["i3status handconfig"]["_proxies"] == [
        "i3status_proxy handconfig_disk_mnt_a",
        "i3status_proxy handconfig_disk_mnt_a_0",
    ]
    assert config["i3status_proxy handconfig_disk_mnt_a"]["_item_instance"] == "/mnt-a"
    assert config["i3status_proxy handconfig_disk_mnt_a_0"]["_item_instance"] == "/mnt_a"


def test_slug_collision_between_different_containers_gets_distinct_proxies(tmp_path):
    """
    "i3status hand-config" and "i3status hand_config" slugify to the same
    string - the claim set must be shared across containers, or the
    second one's proxy silently overwrites the first's config[name] entry.
    """
    config_path = write_config(
        tmp_path,
        """
order += "i3status hand-config"
order += "i3status hand_config"

i3status "hand-config" {
    load {
        format = "a"
    }
}

i3status "hand_config" {
    load {
        format = "b"
    }
}
""",
    )
    config = process_config(config_path)

    assert config["i3status hand-config"]["_proxies"] == ["i3status_proxy hand_config_load"]
    assert config["i3status hand_config"]["_proxies"] == ["i3status_proxy hand_config_load_0"]
    assert config["py3_modules"].count("i3status_proxy hand_config_load") == 1
    assert config["py3_modules"].count("i3status_proxy hand_config_load_0") == 1


def test_on_click_moves_to_top_level_dict_keyed_by_generated_name(tmp_path):
    config_path = write_config(
        tmp_path,
        """
order += "wireless _first_"

wireless _first_ {
    format_up = "W: %quality"
    on_click 1 = "exec nm-applet"
}
""",
    )
    config = process_config(config_path)

    generated_name = "i3status_proxy _generated_wireless_first_0"
    assert config["on_click"] == {generated_name: {1: "exec nm-applet"}}
    assert "on_click 1" not in config[generated_name]


def test_universal_options_hoisted_onto_proxy_not_container(tmp_path):
    config_path = write_config(
        tmp_path,
        """
order += "wireless _first_"

wireless _first_ {
    format_up = "W: %quality"
    border = "#FF0000"
    min_length = 20
}
""",
    )
    config = process_config(config_path)

    generated_name = "i3status_proxy _generated_wireless_first_0"
    assert config[generated_name]["border"] == "#FF0000"
    assert config[generated_name]["min_length"] == 20
    container = config["i3status _generated"]
    assert "border" not in container["items"][0]
    assert "min_length" not in container["items"][0]


def test_module_interval_is_rejected_not_aliased_to_cache_timeout(tmp_path, capsys):
    """
    "interval" is a general{}-only i3status setting (confirmed against
    the real binary: it hard-rejects a per-module "interval" with "no
    such option") - a module's own "interval" is ignored with a
    warning, not silently treated as its cache_timeout.
    """
    config_path = write_config(
        tmp_path,
        """
general {
    interval = 5
}

order += "load"

load {
    format = "%1min"
    interval = 30
}
""",
    )
    config = process_config(config_path)

    generated_name = "i3status_proxy _generated_load_0"
    assert config[generated_name]["cache_timeout"] == 5
    assert "interval" not in config[generated_name]
    assert "interval" not in config["i3status _generated"]["items"][0]
    assert "'interval' is not a module option" in capsys.readouterr().out


def test_time_module_stamps_explicit_flag_only_when_user_set_it(tmp_path):
    """
    _cache_timeout marks that the user explicitly asked for a tick rate
    on a time/tztime module (see proxy.py's _time_proxy()) - it must not
    appear just because the general_interval fallback filled in
    cache_timeout on its own.
    """
    config_path = write_config(
        tmp_path,
        """
general {
    interval = 5
}

order += "tztime local"
order += "tztime explicit"

tztime local {
    format = "%H:%M:%S"
}

tztime explicit {
    format = "%H:%M:%S"
    cache_timeout = 10
}
""",
    )
    config = process_config(config_path)

    assert "_cache_timeout" not in config["i3status_proxy _generated_tztime_local_0"]
    assert config["i3status_proxy _generated_tztime_explicit_0"]["_cache_timeout"] is True


def test_time_module_rejected_cache_timeout_does_not_stamp_explicit_flag(tmp_path):
    """
    cache_timeout=0 is lower than general.interval, so it gets rejected
    and replaced by general_interval same as any other module - _cache_timeout
    must not be set just because the key was present in the raw config,
    or the rejected value would still override the format's tick rate.
    """
    config_path = write_config(
        tmp_path,
        """
general {
    interval = 5
}

order += "tztime local"

tztime local {
    format = "%H:%M:%S"
    cache_timeout = 0
}
""",
    )
    config = process_config(config_path)

    proxy = config["i3status_proxy _generated_tztime_local_0"]
    assert proxy["cache_timeout"] == 5
    assert "_cache_timeout" not in proxy


def test_cache_timeout_is_a_py3status_only_option_not_leaked_to_i3status(tmp_path):
    """
    cache_timeout is not real i3status.conf syntax at the per-module
    level - it's py3status-only, so it becomes the generated proxy's
    real cache_timeout and never leaks into the native i3status.conf
    stanza the container hands its subprocess.
    """
    config_path = write_config(
        tmp_path,
        """
general {
    interval = 5
}

order += "load"

load {
    format = "%1min"
    cache_timeout = 30
}
""",
    )
    config = process_config(config_path)

    generated_name = "i3status_proxy _generated_load_0"
    assert config[generated_name]["cache_timeout"] == 30
    assert "cache_timeout" not in config["i3status _generated"]["items"][0]


def test_cache_timeout_is_unaffected_by_a_rejected_interval(tmp_path):
    """
    "interval" is rejected regardless of write order relative to
    cache_timeout - it never wins, and never interferes with
    cache_timeout actually applying, either way round.
    """
    config_path = write_config(
        tmp_path,
        """
order += "load"
order += "disk /"

load {
    format = "%1min"
    interval = 15
    cache_timeout = 30
}

disk "/" {
    format = "%avail"
    cache_timeout = 30
    interval = 15
}
""",
    )
    config = process_config(config_path)

    assert config["i3status_proxy _generated_load_0"]["cache_timeout"] == 30
    assert config["i3status_proxy _generated_disk_0"]["cache_timeout"] == 30


def test_cache_timeout_lower_than_general_interval_is_dropped(tmp_path):
    config_path = write_config(
        tmp_path,
        """
general {
    interval = 10
}

order += "load"

load {
    format = "%1min"
    cache_timeout = 1
}
""",
    )
    config = process_config(config_path)

    generated_name = "i3status_proxy _generated_load_0"
    # not the proxy class's own hardcoded default (1) - that would be the
    # exact too-low value that was just rejected; falls back to the general
    # interval it was compared against instead
    assert config[generated_name]["cache_timeout"] == 10


def test_no_interval_defaults_cache_timeout_to_general_interval(tmp_path):
    config_path = write_config(
        tmp_path,
        """
general {
    interval = 20
}

order += "load"

load {
    format = "%1min"
}
""",
    )
    config = process_config(config_path)

    generated_name = "i3status_proxy _generated_load_0"
    # no interval of its own configured - defaults to the container's own
    # poll rate (general.interval), not the proxy class's hardcoded 1, so
    # it keeps tracking general.interval if that ever changes
    assert config[generated_name]["cache_timeout"] == 20


def test_no_interval_at_all_defaults_cache_timeout_to_builtin_general_interval(tmp_path):
    """
    With no explicit `general { interval = ... }`, general_interval
    lands on DEFAULT_GENERAL_INTERVAL, and the generated proxy picks
    that default up.
    """
    config_path = write_config(
        tmp_path,
        """
order += "load"

load {
    format = "%1min"
}
""",
    )
    config = process_config(config_path)

    generated_name = "i3status_proxy _generated_load_0"
    assert config[generated_name]["cache_timeout"] == DEFAULT_GENERAL_INTERVAL


def test_no_i3status_sections_leaves_config_unchanged(tmp_path):
    config_path = write_config(
        tmp_path,
        """
order += "battery_level"

battery_level {
    format = "%percent"
}
""",
    )
    config = process_config(config_path)

    assert config["order"] == ["battery_level"]
    assert "i3status _generated" not in config


def test_configured_container_module_interval_is_rejected(tmp_path, capsys):
    """
    Same rejection as the bare-item case: a configured container's own
    item can't use "interval" as a cache_timeout alias either.
    """
    config_path = write_config(
        tmp_path,
        """
order += "i3status handconfig"

i3status handconfig {
    general {
        interval = 5
    }
    load {
        format = "%1min"
        interval = 30
    }
}
""",
    )
    config = process_config(config_path)

    generated_name = "i3status_proxy handconfig_load"
    assert config[generated_name]["cache_timeout"] == 5
    assert "interval" not in config[generated_name]
    assert "'interval' is not a module option" in capsys.readouterr().out
    assert "interval" not in config["i3status handconfig"]["items"][0]


def test_configured_container_strips_nested_py3status_modules(tmp_path, caplog):
    """
    A py3status-native module (eg clock) has no equivalent in the real
    i3status binary - nesting one inside an i3status container used to
    silently become a bogus proxy that could never receive real data,
    and threw off the container's own item count on every reading.
    Dropped, with a warning logged, instead of silently continuing.
    """
    config_path = write_config(
        tmp_path,
        """
order += "i3status handconfig"

i3status handconfig {
    load {
        format = "%1min"
    }
    clock {
        format = "{Local}"
    }
    battery_level {
    }
}
""",
    )
    config = process_config(config_path)

    assert config["i3status handconfig"]["items"] == [{"name": "load", "format": "%1min"}]
    assert not any(name.endswith("_clock") for name in config["py3_modules"])
    assert not any(name.endswith("_battery_level") for name in config["py3_modules"])

    warnings = [r.message for r in caplog.records if r.levelname == "WARNING"]
    assert any("ignoring non-i3status module 'clock'" in w for w in warnings)
    assert any("ignoring non-i3status module 'battery_level'" in w for w in warnings)


def test_configured_container_with_only_non_i3status_children_ends_up_empty(tmp_path, caplog):
    """
    Every child dropped as non-i3status must not fall back to
    DEFAULT_ITEMS (unrelated modules the user never asked for) - it's
    just left empty, same as none to begin with.
    """
    config_path = write_config(
        tmp_path,
        """
order += "i3status handconfig"

i3status handconfig {
    clock {
        format = "{Local}"
    }
}
""",
    )
    config = process_config(config_path)

    assert config["i3status handconfig"]["items"] == []
    warnings = [r.message for r in caplog.records if r.levelname == "WARNING"]
    assert any("ignoring non-i3status module 'clock'" in w for w in warnings)


def test_configured_container_cache_timeout_is_unaffected_by_a_rejected_interval(tmp_path):
    config_path = write_config(
        tmp_path,
        """
order += "i3status handconfig"

i3status handconfig {
    load {
        format = "%1min"
        interval = 15
        cache_timeout = 30
    }
}
""",
    )
    config = process_config(config_path)

    assert config["i3status_proxy handconfig_load"]["cache_timeout"] == 30


def test_configured_container_cache_timeout_lower_than_general_interval_is_dropped(tmp_path):
    config_path = write_config(
        tmp_path,
        """
order += "i3status handconfig"

i3status handconfig {
    general {
        interval = 10
    }
    load {
        format = "%1min"
        cache_timeout = 1
    }
}
""",
    )
    config = process_config(config_path)

    generated_name = "i3status_proxy handconfig_load"
    # falls back to the container's own general.interval it was compared
    # against, not the proxy class's hardcoded default (1) - that would be
    # the exact too-low value that was just rejected
    assert config[generated_name]["cache_timeout"] == 10


def test_configured_container_no_interval_defaults_to_its_own_general_interval(tmp_path):
    config_path = write_config(
        tmp_path,
        """
order += "i3status handconfig"

i3status handconfig {
    general {
        interval = 20
    }
    load {
        format = "%1min"
    }
}
""",
    )
    config = process_config(config_path)

    generated_name = "i3status_proxy handconfig_load"
    assert config[generated_name]["cache_timeout"] == 20


def test_configured_container_without_its_own_general_inherits_top_level_interval(tmp_path):
    """
    A configured container's own general{} falls back to the top-level
    one's explicit interval, same as it does for GENERAL_DEFAULTS keys -
    it only lands on the hardcoded default when neither sets one.
    """
    config_path = write_config(
        tmp_path,
        """
order += "disk /"
order += "i3status handconfig"

general {
    interval = 2
}

disk "/" {
    format = "%avail"
}

i3status handconfig {
    load {
        format = "%1min"
    }
}
""",
    )
    config = process_config(config_path)

    # the top-level container honors its own explicit general.interval
    assert config["general"]["interval"] == 2
    # the configured container's own general{} asked for nothing, so it
    # inherits the top-level one's explicit 2 instead of the hardcoded default
    assert config["i3status handconfig"]["general"]["interval"] == 2
    generated_name = "i3status_proxy handconfig_load"
    assert config[generated_name]["cache_timeout"] == 2


def test_configured_proxy_slug_drops_redundant_i3status_prefix(tmp_path):
    """
    A configured container's proxy slug is built from just its
    instance ("handconfig"), not the whole "i3status handconfig" name -
    the "i3status" part is already redundant with the i3status_proxy
    prefix every proxy name carries regardless.
    """
    config_path = write_config(
        tmp_path,
        """
order += "i3status handconfig"

i3status handconfig {
    load {
        format = "%1min"
    }
}
""",
    )
    config = process_config(config_path)

    assert "i3status_proxy handconfig_load" in config
    assert "i3status_proxy i3status_handconfig_load" not in config


def test_bare_unnamed_configured_container_uses_no_slug_prefix(tmp_path):
    """
    A bare "i3status { }" block (no instance at all) has nothing to
    slugify down to just an instance - and since there can only ever be
    one, there's nothing to disambiguate against either, so its items'
    proxy names get no container-derived prefix at all, not even
    "i3status_" (falling back to that would just reintroduce the same
    redundancy a named container's own prefix already had to drop).
    """
    config_path = write_config(
        tmp_path,
        """
order += "i3status"

i3status {
    load {
        format = "%1min"
    }
    disk "/" {
        format = "%avail"
    }
}
""",
    )
    config = process_config(config_path)

    assert "i3status_proxy load" in config
    assert "i3status_proxy disk" in config
    assert "i3status_proxy i3status_load" not in config


def test_bare_order_reference_with_no_block_at_all_gets_default_items(tmp_path):
    """
    order += "i3status" with no matching "i3status { }" block anywhere is
    valid i3status.conf syntax (same as any other bare item), but it never
    creates a config_info entry on its own - resolve_configured_i3status_containers()
    only iterates entries that already exist, so without synthesizing one,
    this container would resolve to an empty, item-less config and die on
    post_config_hook()'s "missing bare i3status modules" guard instead of
    falling back to DEFAULT_ITEMS like an explicit empty block does.
    """
    config_path = write_config(tmp_path, 'order += "i3status"\n')
    config = process_config(config_path)

    default_names = [item["name"] for item in DEFAULT_ITEMS]
    assert [item["name"] for item in config["i3status"]["items"]] == default_names


def test_configured_i3status_container_works_inside_a_group(tmp_path):
    """
    A configured "i3status name { }" container is itself just a real,
    container-typed Module - nothing about resolving it depends on being
    at the top level, so nesting one inside a group/frame (alongside an
    ordinary py3status module) must register and thread it exactly like
    any other child: in the group's own items, in py3_modules, and in
    module_groups so it force-updates its parent when a proxy updates.
    """
    config_path = write_config(
        tmp_path,
        """
order += "group mygroup"

group mygroup {
    i3status handconfig {
        load {
            format = "%1min"
        }
    }
    static_string hello {
        format = "hi"
    }
}
""",
    )
    config = process_config(config_path)

    assert config["group mygroup"]["items"] == ["i3status handconfig", "static_string hello"]
    assert "i3status handconfig" in config["py3_modules"]
    assert config[".module_groups"]["i3status handconfig"] == ["group mygroup"]
    proxy_name = config["i3status handconfig"]["_proxies"][0]
    assert config[".module_groups"][proxy_name] == ["i3status handconfig"]
