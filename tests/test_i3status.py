from pathlib import Path

import py3status.modules.i3status as i3status_module
from py3status.i3status import registry


class FakePy3:
    _module_full_name = "i3status gc0"
    CACHE_FOREVER = -1
    LOG_ERROR = "error"
    LOG_INFO = "info"
    LOG_WARNING = "warning"

    def __init__(self):
        self.updated = []
        self.logged = []

    def update(self, module_name=None):
        self.updated.append(module_name)

    def log(self, message, level="info"):
        self.logged.append((level, message))

    def get_config(self, name, default=None):
        if name == "module_full_name":
            return self._module_full_name
        assert name == "i3status"
        return default


def make_module(items=None):
    module = i3status_module.Py3status()
    module.py3 = FakePy3()
    # normally set once by post_config_hook() - tests call the container's
    # methods directly, bypassing it, so set it here instead
    module._module_full_name = module.py3.get_config("module_full_name")
    module.items = items if items is not None else []
    return module


def test_publish_to_registry_stores_each_output_item_by_name_instance():
    module = make_module(items=[{"name": "disk /"}, {"name": "wireless _first_"}])
    module.output = [
        {"name": "disk_info", "instance": "/", "full_text": "42%"},
        {"name": "wireless", "instance": "_first_", "full_text": "WIFI"},
    ]

    module._publish_to_registry()

    assert registry.read("i3status gc0", ("disk_info", "/")) is None
    assert registry.read("i3status gc0", ("disk", "/")) == {
        "name": "disk_info",
        "instance": "/",
        "full_text": "42%",
    }
    assert registry.read("i3status gc0", ("wireless", "_first_")) == {
        "name": "wireless",
        "instance": "_first_",
        "full_text": "WIFI",
    }


def test_publish_to_registry_ignores_disk_info_name_from_i3status(tmp_path):
    """
    Real i3status names the disk block 'disk_info' in its JSON output even
    though the config section (and the name a generated proxy looks up)
    is 'disk' - confirmed against the real binary. Matching is positional
    (zip against self.items), so the item's own reported name is never
    consulted and this is a non-issue by construction.
    """
    module = make_module(items=[{"name": "disk /"}])
    module.output = [{"name": "disk_info", "instance": "/", "full_text": "29.2 GiB"}]

    module._publish_to_registry()

    assert registry.read("i3status gc0", ("disk", "/")) == {
        "name": "disk_info",
        "instance": "/",
        "full_text": "29.2 GiB",
    }


def test_publish_to_registry_uses_the_containers_own_full_name():
    module = make_module(items=[{"name": "load"}])
    module._module_full_name = "i3status gc5"
    module.output = [{"name": "load", "instance": None, "full_text": "0.2"}]

    module._publish_to_registry()

    assert registry.read("i3status gc5", ("load", None)) == {
        "name": "load",
        "instance": None,
        "full_text": "0.2",
    }


def test_publish_to_registry_keys_by_configured_instance_not_i3status_own():
    """
    Real i3status substitutes a config's "_first_"/"all"/index-style
    sentinel instance with a runtime-discovered identifier in its own JSON
    output (eg wireless "_first_" -> the real interface name "wlp2s0",
    battery "all" -> a sysfs path) - confirmed against the real binary.
    A generated proxy's lookup key always uses the *configured* instance
    (translate.py parses it straight from the section name), so publishing
    under i3status's own reported instance would never match - the proxy
    would silently stay empty forever. Positional matching keys by the
    configured item regardless of what i3status itself reports.
    """
    module = make_module(items=[{"name": "wireless _first_"}, {"name": "battery all"}])
    module.output = [
        {"name": "wireless", "instance": "wlp2s0", "full_text": "W 44%"},
        {"name": "battery", "instance": "/sys/class/power_supply/BAT0/uevent", "full_text": "80%"},
    ]

    module._publish_to_registry()

    assert registry.read("i3status gc0", ("wireless", "_first_")) == {
        "name": "wireless",
        "instance": "wlp2s0",
        "full_text": "W 44%",
    }
    assert registry.read("i3status gc0", ("battery", "all")) == {
        "name": "battery",
        "instance": "/sys/class/power_supply/BAT0/uevent",
        "full_text": "80%",
    }
    # the raw i3status-reported instances were never used as registry keys
    assert registry.read("i3status gc0", ("wireless", "wlp2s0")) is None
    assert registry.read("i3status gc0", ("battery", "/sys/class/power_supply/BAT0/uevent")) is None


def test_publish_to_registry_disambiguates_two_sections_of_the_same_type():
    """
    Real i3status reports the same resolved-path-style instance scheme for
    every section of a given type - two "battery N" sections both report
    their own sysfs path, never "0"/"1" - confirmed against the real
    binary. Matching by (name, instance) content can't tell them apart;
    only position can, since i3status always emits its array in the same
    order as the order += directives the container wrote.
    """
    module = make_module(items=[{"name": "battery 0"}, {"name": "battery 1"}])
    module.output = [
        {"name": "battery", "instance": "/sys/class/power_supply/BAT0/uevent", "full_text": "80%"},
        {
            "name": "battery",
            "instance": "/sys/class/power_supply/BAT1/uevent",
            "full_text": "No battery",
        },
    ]

    module._publish_to_registry()

    assert registry.read("i3status gc0", ("battery", "0"))["full_text"] == "80%"
    assert registry.read("i3status gc0", ("battery", "1"))["full_text"] == "No battery"


class _FakeStdout:
    def __init__(self, lines, on_exhausted):
        self._lines = list(lines)
        self._on_exhausted = on_exhausted

    def readline(self):
        if self._lines:
            return self._lines.pop(0)
        self._on_exhausted()
        return ""


class _FakeProcess:
    def __init__(self, lines, on_exhausted):
        self.stdout = _FakeStdout(lines, on_exhausted)

    def poll(self):
        return None

    def wait(self, timeout=None):
        return 0


def test_spawn_errors_instead_of_publishing_on_a_module_count_mismatch(monkeypatch, tmp_path):
    """
    An installed i3status that doesn't recognize one configured module type
    silently emits zero blocks for it instead of erroring - confirmed
    against the real binary (order += "bogus_type" just gets skipped).
    Matching is positional, so a shorter reading would otherwise attribute
    every later item to the wrong proxy. Must error and skip publishing
    that reading entirely instead of ever zipping mismatched lists.
    """
    module = make_module(items=[{"name": "load"}, {"name": "disk /"}])
    module.running = True
    module.tmpfile = type("T", (), {"name": str(tmp_path / "fake.conf")})()
    module.i3status_command = ["i3status", "-c", module.tmpfile.name]

    lines = [
        '{"version":1}\n',
        "[\n",
        # only 1 block for 2 declared items - the "load" slot silently
        # dropped, same as a real installed i3status would for an
        # unrecognized module type
        ',[{"name": "disk_info", "instance": "/", "full_text": "42%"}]\n',
    ]
    fake_process = _FakeProcess(lines, on_exhausted=lambda: setattr(module, "running", False))
    monkeypatch.setattr(i3status_module, "Popen", lambda *a, **k: fake_process)

    module._spawn_i3status()

    assert module.error == "expected 2 modules, but i3status produced 1 module"
    assert registry.read("i3status gc0", ("disk", "/")) is None
    assert registry.read("i3status gc0", ("load", None)) is None


def test_spawn_accumulates_a_multiline_error(monkeypatch, tmp_path):
    """
    A validation error can print across two lines - keep both, not
    just the last one seen.
    """
    module = make_module(items=[{"name": "load"}])
    module.running = True
    module.line = ""
    module.tmpfile = type("T", (), {"name": str(tmp_path / "fake.conf")})()
    module.i3status_command = ["i3status", "-c", module.tmpfile.name]

    lines = [
        "Invalid interval attribute found in section general, line 3: -5\n",
        "Expected positive integer\n",
    ]
    fake_process = _FakeProcess(lines, on_exhausted=lambda: None)
    monkeypatch.setattr(i3status_module, "Popen", lambda *a, **k: fake_process)

    module._spawn_i3status()

    assert (
        module.error
        == "Invalid interval attribute found in section general: -5 Expected positive integer"
    )


def test_spawn_keeps_a_real_error_that_starts_with_i3status(monkeypatch, tmp_path):
    """
    A genuine per-module read failure (eg print_load.c's own error) also
    starts with "i3status: " - confirmed real, must still surface.
    """
    module = make_module(items=[{"name": "load"}])
    module.running = True
    module.line = ""
    module.tmpfile = type("T", (), {"name": str(tmp_path / "fake.conf")})()
    module.i3status_command = ["i3status", "-c", module.tmpfile.name]

    lines = ["i3status: Cannot read system load using getloadavg()\n"]
    fake_process = _FakeProcess(lines, on_exhausted=lambda: None)
    monkeypatch.setattr(i3status_module, "Popen", lambda *a, **k: fake_process)

    module._spawn_i3status()

    assert module.error == "Cannot read system load using getloadavg()"


def test_i3status_skips_real_rendering_for_generated_containers():
    """
    A generated container has no order slot of its own - core only ever
    writes a module's output into the bar for the index(es) it has in
    order (see core.py's create_output_modules()/output[index] = out), so
    this container's own full_text is never displayed no matter what.
    Returns immediately, without ever reading self._proxies/get_output().
    """
    module = make_module()
    module._generated = True
    module._render_full_text = module._generated_full_text
    module.error = None

    result = module.i3status()

    assert result == {"cached_until": -1, "full_text": ""}


def test_i3status_renders_normally_by_combining_its_proxies_output():
    """
    A configured container's own items are real proxy Modules too
    now (resolve_configured_i3status_containers), but the container itself
    still has its own order slot and must keep rendering a real combined
    output - reading each proxy's own latest rendered output via
    get_output() and joining them, same as frame.py/group.py already do
    for their own real child modules. Only an generated container
    (_generated) is invisible - _proxies alone isn't enough to tell them
    apart, since both kinds have it.
    """
    module = make_module()
    module._proxies = ["i3status_proxy handconfig_load", "i3status_proxy handconfig_disk"]
    module._render_full_text = module._configured_full_text
    module.error = None
    module.py3.get_output = lambda name: [{"full_text": name}]
    module.py3.safe_join = lambda separator, outputs: outputs
    module.py3.safe_format = lambda fmt, subs: subs.get("format_module", "")

    result = module.i3status()

    assert result == {
        "cached_until": -1,
        "full_text": [
            [{"full_text": "i3status_proxy handconfig_load"}],
            [{"full_text": "i3status_proxy handconfig_disk"}],
        ],
    }


def test_cleanup_force_refreshes_its_own_proxies(tmp_path):
    """
    A dead/killed container must not leave its proxies showing stale
    output until their own cache_timeout happens to elapse - it force-
    refreshes each one immediately after clearing the registry, so they
    pick up the "no data" state right away.
    """
    module = make_module()
    module.process = None
    module.tmpfile = type("T", (), {"name": str(tmp_path / "nonexistent.conf")})()
    module._proxies = ["i3status_proxy gc0_disk", "i3status_proxy gc0_load"]
    registry.publish("i3status gc0", ("disk", "/"), {"full_text": "stale"})

    module._cleanup()

    assert registry.read("i3status gc0", ("disk", "/")) is None
    assert module.py3.updated == [
        "i3status_proxy gc0_disk",
        "i3status_proxy gc0_load",
        None,
    ]


def test_cleanup_on_configured_container_updates_only_itself():
    """
    A configured container (no py3status/i3status/translate.py
    metadata) has no proxies to force-refresh - it renders its own
    combined output directly, so only its own self.py3.update() applies.
    """
    module = make_module()
    module.process = None
    module.tmpfile = type("T", (), {"name": "/tmp/nonexistent-i3status-cleanup-test"})()

    module._cleanup()

    assert module.py3.updated == [None]


def _make_respawn_module():
    module = make_module()
    module.running = True
    module.ready = False
    module.process = None
    module.tmpfile = type("T", (), {"name": "/tmp/nonexistent-i3status-respawn-test"})()
    return module


def test_respawn_gives_up_immediately_if_never_ready(monkeypatch):
    """
    A subprocess that never produces a single valid line (broken config,
    missing binary) isn't going to fix itself by retrying - give up after
    one attempt instead of spending the whole respawn budget on it.
    """
    module = _make_respawn_module()
    calls = []
    sleeps = []
    monkeypatch.setattr(module, "_spawn_i3status", lambda: calls.append(1))
    monkeypatch.setattr(i3status_module, "sleep", lambda seconds: sleeps.append(seconds))

    module._start_loop()

    assert len(calls) == 1
    assert sleeps == []
    assert module.running is False
    assert module.py3.logged == [("warning", "giving up: never started successfully")]


def test_respawn_exhausts_budget_on_repeated_quick_crashes(monkeypatch):
    """
    Once it has worked at least once, a crash gets retried - but a genuine
    crash loop (each attempt dying quickly) still gives up for good once
    RESPAWN_ATTEMPTS is used up, same as the old i3status_wrapper.py.
    """
    module = _make_respawn_module()
    calls = []
    clock = [0]

    def fake_spawn():
        calls.append(1)
        module.ready = True
        clock[0] += 1  # each attempt starts well within RESPAWN_INTERVAL of the last

    monkeypatch.setattr(module, "_spawn_i3status", fake_spawn)
    monkeypatch.setattr(i3status_module, "monotonic", lambda: clock[0])
    monkeypatch.setattr(i3status_module, "sleep", lambda seconds: None)

    module._start_loop()

    assert len(calls) == i3status_module.RESPAWN_ATTEMPTS
    assert module.running is False
    restarts = [msg for level, msg in module.py3.logged if msg.startswith("restarting")]
    assert restarts == [
        f"restarting (attempt {n}/{i3status_module.RESPAWN_ATTEMPTS})"
        for n in range(1, i3status_module.RESPAWN_ATTEMPTS + 1)
    ]
    assert module.py3.logged[-1] == (
        "warning",
        f"giving up: {i3status_module.RESPAWN_ATTEMPTS} restarts "
        f"within {i3status_module.RESPAWN_INTERVAL}s",
    )


def test_respawn_never_gives_up_when_crashes_are_spread_out(monkeypatch):
    """
    Same idea as systemd's StartLimitIntervalSec/StartLimitBurst: a start
    only counts against the burst if it falls within RESPAWN_INTERVAL of
    the RESPAWN_ATTEMPTS-th-most-recent one. Attempts spaced further apart
    than that age out of the window instead of ever accumulating toward
    it - a long-lived container with rare, unrelated crashes keeps
    respawning indefinitely, unlike a genuine crash loop.
    """
    module = _make_respawn_module()
    calls = []
    clock = [0]
    stop_after = i3status_module.RESPAWN_ATTEMPTS + 5

    def fake_spawn():
        calls.append(1)
        module.ready = True
        clock[0] += i3status_module.RESPAWN_INTERVAL  # always outside the window
        if len(calls) == stop_after:
            module.running = False  # stop the test well past the original budget

    monkeypatch.setattr(module, "_spawn_i3status", fake_spawn)
    monkeypatch.setattr(i3status_module, "monotonic", lambda: clock[0])
    monkeypatch.setattr(i3status_module, "sleep", lambda seconds: None)

    module._start_loop()

    # more calls happened than RESPAWN_ATTEMPTS - proves spread-out
    # restarts never accumulate toward the burst limit, rather than the
    # loop stopping dead once it reached the original attempt count
    assert len(calls) == stop_after
    assert module.running is False
    # no "giving up" message - it never actually exhausted the burst
    assert not any(msg.startswith("giving up") for _, msg in module.py3.logged)
    assert len(module.py3.logged) == stop_after - 1


def test_set_error_strips_its_own_generated_config_path_and_line_number(tmp_path):
    """
    Our own throwaway tmpfile path and its line number are noise -
    strip both, leaving just i3status's real message.
    """
    module = make_module()
    module.tmpfile = type("T", (), {"name": str(tmp_path / "py3status-i3status-extras.conf")})()

    module._set_error(f"{module.tmpfile.name}:16: missing title for section 'volume'")

    assert module.error == "missing title for section 'volume'"


def test_write_i3status_config_starts_with_a_comment_identifying_the_container(tmp_path):
    """
    Matching a PID or a /tmp/py3status-i3status_*.conf path back to its
    container otherwise means cross-referencing logs or grepping the
    file's own `order` lines against the config.
    """
    module = make_module(items=[{"name": "load", "format": "%1min"}])
    module.general = {}

    module._write_i3status_config()

    tmpfile_path = Path(module.tmpfile.name)
    try:
        assert tmpfile_path.read_text().startswith("# i3status gc0\n\ngeneral {\n")
    finally:
        tmpfile_path.unlink()


def test_write_i3status_config_expands_named_colors_to_hex(tmp_path):
    """
    Real i3status only accepts strict #rrggbb for color_good/bad/degraded
    (both in general{} and per-section overrides) - it dies outright on
    anything else, confirmed against the real binary. py3status's usual
    named colors ("lime", "red", ...) must be resolved to hex before they
    ever reach the generated config, or the whole container dies on
    startup the moment a user writes a color the way they would anywhere
    else in py3status.
    """
    module = make_module(items=[{"name": "disk /", "format": "%avail", "color_bad": "red"}])
    module.general = {"color_good": "lime"}

    module._write_i3status_config()

    tmpfile_path = Path(module.tmpfile.name)
    try:
        content = tmpfile_path.read_text()
        assert 'color_good = "#00FF00"' in content
        assert 'color_bad = "#FF0000"' in content
    finally:
        tmpfile_path.unlink()


def test_write_i3status_config_drops_alpha_channel_from_colors(tmp_path):
    """
    Real i3status dies outright on anything but strict 6-digit #rrggbb,
    confirmed against the real binary - an 8-digit #rrggbbaa (or a 4-digit
    #rgba shorthand that expand_color() expands to 8 digits) must have its
    alpha channel dropped before it ever reaches the generated config, or
    the whole container dies on startup.
    """
    module = make_module(items=[{"name": "disk /", "format": "%avail", "color_bad": "#F008"}])
    module.general = {"color_good": "#FF000080"}

    module._write_i3status_config()

    tmpfile_path = Path(module.tmpfile.name)
    try:
        content = tmpfile_path.read_text()
        assert 'color_good = "#FF0000"' in content
        assert 'color_bad = "#FF0000"' in content
    finally:
        tmpfile_path.unlink()


def test_write_i3status_config_ends_with_exactly_one_trailing_newline(tmp_path):
    module = make_module(items=[{"name": "load", "format": "%1min"}])
    module.general = {}

    module._write_i3status_config()

    tmpfile_path = Path(module.tmpfile.name)
    try:
        content = tmpfile_path.read_text()
        assert content.endswith("\n")
        assert not content.endswith("\n\n")
    finally:
        tmpfile_path.unlink()


class _HandConfigFakePy3(FakePy3):
    def check_commands(self, cmd):
        return "i3status"


def test_post_config_hook_accepts_a_bare_native_item():
    """
    Every item's own universal py3status options (cache_timeout/color/
    border/on_click/resources/...) are split off onto its own real proxy
    Module before this container is even instantiated now (see
    translate.py's resolve_bare_i3status_modules()/
    resolve_configured_i3status_containers()) - post_config_hook() itself
    has nothing left to resolve per item beyond basic shape, for either a
    configured or a generated container's items.
    """
    module = i3status_module.Py3status()
    module.py3 = _HandConfigFakePy3()
    module.general = {}
    module.items = [{"name": "load", "format": "%1min"}]
    module._proxies = ["i3status_proxy handconfig_load"]

    try:
        module.post_config_hook()
        assert module.items == [{"name": "load", "format": "%1min"}]
    finally:
        module.kill()
