"""
Shared helpers for the native i3status-compatible modules.
"""


def resolve_cache_timeout(py3, cache_timeout):
    """
    Resolve a module's effective cache_timeout.

    Real i3status has no per-module interval - a single `general { interval }`
    (default 1 second) ticks every configured module together. If the user
    has explicitly set this module's own cache_timeout, that wins (a py3status
    module-level override real i3status doesn't have, but is backwards
    compatible with it). Otherwise fall back to `general { interval }` if
    set, then to 1 to match i3status's own default.

    cache_timeout must default to None on the class for this to distinguish
    "user configured this module's cache_timeout" from "still the default".
    """
    if cache_timeout is not None:
        return cache_timeout
    return py3._get_config_setting("interval", 1)


def format_placeholders(format_string, placeholders):
    """
    Replace %placeholder occurrences in format_string.

    placeholders is an ordered sequence of (name, value) pairs, eg
    [("%percentage_used_of_avail", "42.0%"), ("%percentage_used", "12.0%")].

    Matches i3status's own format_placeholders(): a single left-to-right
    scan, checking placeholder names in the given order at each '%' and
    using the first one that matches as a prefix. The order matters when
    one placeholder name is itself a prefix of another (eg %percentage_used
    is a prefix of %percentage_used_of_avail) - the more specific name must
    come first or it will never be reached.
    """
    out = []
    i = 0
    length = len(format_string)
    while i < length:
        char = format_string[i]
        if char != "%":
            out.append(char)
            i += 1
            continue
        for name, value in placeholders:
            if format_string.startswith(name, i):
                out.append(value)
                i += len(name)
                break
        else:
            out.append(char)
            i += 1
    return "".join(out)


# module name -> the i3status-compatible module's config key implied by
# its instance
_INSTANCE_CONFIG_KEYS = {
    "battery": "number",
    "cpu_temperature": "zone",
    "disk": "path",
    "ethernet": "interface",
    "path_exists": "title",
    "read_file": "title",
    "run_watch": "title",
    "wireless": "interface",
}

# keys that must be an actual int, matching real i3status's atoi(title) -
# used in %d-style formatting downstream, unlike eg battery's number
# (also atoi'd in real i3status, but the i3status-compatible module
# coerces it with int() at use time regardless, so it's fine left as a
# string here)
_INT_KEYS = {"zone"}

# py3status-only config keys that are never valid real i3status options on
# ANY of the 16 i3status-compatible modules - unlike _INSTANCE_CONFIG_KEYS
# (which is per-module and tied to a section's title/instance), these apply
# across the board. parse_config.py strips each of these, alongside the
# section's own instance-derived key (if any), whenever it resolves to the
# real i3status wrapper rather than the native module - real i3status has
# no per-module cache_timeout/interval override, only the single general
# { interval } setting, so a leftover cache_timeout would otherwise crash
# the wrapper exactly like a leftover instance-only key does.
#
# `python` (py3status's own native-vs-wrapper resolution directive) is
# NOT in this set even though it's also never a real i3status option -
# it's stripped separately, unconditionally in BOTH resolution paths (see
# parse_config.py's remove_any_contained_modules), since no module ever
# reads self.python either way.
WRAPPER_INVALID_KEYS = ("cache_timeout",)


def instance_config_key(module_name):
    """
    Return the i3status-compatible-only config key this module derives
    from its instance/title (eg 'path' for 'disk', 'title' for
    'run_watch'), or None if this module has no such key.

    This key is never a real i3status config option - real i3status
    hard-errors ("no such option") if it appears in a section delegated
    to it, so parse_config.py strips it from any section resolving to
    the real i3status wrapper rather than the native module.
    """
    return _INSTANCE_CONFIG_KEYS.get(module_name)


def translate_instance(name):
    """
    Given a real i3status order-entry (eg 'disk /home', 'battery 0',
    'load'), return a dict of the i3status-compatible config key(s)
    implied by its instance/title portion - eg {'path': '/home'},
    {'number': '0'}.

    Several i3status modules derive part of their behavior from the
    config section's own title/instance rather than a separate config
    key - eg `disk "/home" { }` implies path="/home", `battery 0 { }`
    implies number=0 (confirmed against i3status.c's CASE_SEC_TITLE
    blocks: .path = title, .number = atoi(title), etc). py3status
    modules have no way to discover this on their own - py3status
    doesn't tell a module what section name it was configured under,
    unlike i3status's C code. This fills that gap, so an unmodified
    real i3status.conf section's instance can be translated into the
    equivalent config key without the user having to duplicate it by
    hand.

    Returns {} for modules with no title-derived config key (eg 'load',
    'tztime', 'volume' - the latter two do have a title in real
    i3status, but it's only used for i3bar instance metadata there, not
    derived into any actual config value), or if name has no
    instance/title at all.
    """
    module_name, _, instance = name.partition(" ")
    if not instance:
        return {}
    key = instance_config_key(module_name)
    if key is None:
        return {}
    if key in _INT_KEYS:
        try:
            return {key: int(instance)}
        except ValueError:
            return {key: 0}
    return {key: instance}
