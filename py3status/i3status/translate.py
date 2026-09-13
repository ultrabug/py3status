"""
Translate i3status.conf-style sections into a shared i3status container
plus one real proxy module per section - so on_click/border/markup/etc
come free from Module instead of being hand-rolled per item.
"""

import logging
import re
from collections import defaultdict
from itertools import count

from py3status.config_types import ModuleDefinition
from py3status.constants import GENERAL_DEFAULTS, GENERATED_SLUG, MODULE_OPTIONS
from py3status.helpers import get_instance_name, get_module_name, next_unclaimed_name
from py3status.i3status.constants import (
    DEFAULT_GENERAL_INTERVAL,
    DEFAULT_ITEMS,
    I3S_CONTAINER_TYPE,
    I3S_PROXY_TYPE,
    I3S_TIME_MODULES,
    I3S_TZTIME_FORMAT,
)
from py3status.i3status.helpers import (
    is_i3status_container_name,
    is_i3status_module_name,
    parse_onclick,
)

logger = logging.getLogger(__name__)


# --- deprecated: strip i3status entirely, or just bare items ---


def strip_i3status_sections(config_info):
    """
    Remove every i3status section/container, recursively - for deprecated
    --standalone: no i3status at all, not generated-but-unfed. Run before
    resolve_configured_i3status_containers() and resolve_bare_i3status_modules().
    """

    def is_i3status_related(name):
        # is this an i3status module or container?
        return is_i3status_module_name(name) or is_i3status_container_name(name)

    for name, value in list(config_info.items()):
        if is_i3status_related(name):
            del config_info[name]
        elif isinstance(value, ModuleDefinition):
            strip_i3status_sections(value)

    order = config_info.get("order")
    if order:
        config_info["order"] = [name for name in order if not is_i3status_related(name)]


def strip_bare_i3status_modules(config_info, notify_user):
    """
    Remove every bare i3status module section, recursively, with a
    warning per item - for disable_bare_i3status_modules. Leaves
    "i3status { }" containers alone. Run before resolve_bare_i3status_modules().
    """
    for name, value in list(config_info.items()):
        if is_i3status_container_name(name):
            continue
        if is_i3status_module_name(name):
            del config_info[name]
            notify_user(
                f"auto-generate is disabled; ignoring bare i3status module '{name}'"
                " - wrap it in an explicit 'i3status { }' container instead."
            )
        elif isinstance(value, ModuleDefinition):
            strip_bare_i3status_modules(value, notify_user)

    order = config_info.get("order")
    if order:
        config_info["order"] = [name for name in order if not is_i3status_module_name(name)]


# --- shared building blocks, used by both resolve steps below ---


def _slugify(name):
    # collapse non-alphanumeric runs into one "_" - avoids "wireless
    # _first_" becoming "wireless__first__0" via a naive replace.
    return re.sub(r"[^a-zA-Z0-9]+", "_", name).strip("_")


def _proxy_name(container_slug, slug, index):
    """
    Build one item's proxy name ("i3status_proxy <slug>"). No prefix if
    container_slug is "" (a bare block); no suffix on first occurrence
    (index 0) - a genuine collision counts up from "_0". Two different
    containers can slugify to the same container_slug, so the caller
    shares one `claimed` set across all of them, not just this one.
    """
    if container_slug:
        slug = f"{container_slug}_{slug}"
    if index:
        slug = f"{slug}_{index - 1}"
    return f"{I3S_PROXY_TYPE} {slug}"


def _next_proxy_name(claimed, container_slug, name):
    """Slugify name, then claim the first proxy name not already taken."""
    slug = _slugify(name)
    candidates = (_proxy_name(container_slug, slug, index) for index in count())
    proxy_name = next_unclaimed_name(candidates, claimed)
    claimed.add(proxy_name)
    return proxy_name


def _link_proxy_to_container(module_groups, proxy_name, container_name):
    # force-updates this container when a proxy updates, same as
    # a real group/frame's children
    module_groups.setdefault(proxy_name, []).append(container_name)


def _split_item_config(name, item_name, module_config, notify_user):
    """
    Split one item's config into (container_item, proxy_config):
    container_item keeps native i3status.conf keys; proxy_config gets
    the py3status-only options (universal options, resources,
    format_module, cache_timeout).
    """
    container_item = {"name": name}
    proxy_config = {}
    is_time_module = item_name in I3S_TIME_MODULES

    for key, value in module_config.items():
        if key in ("items",) or key.startswith("."):
            continue
        if key == "format_module":
            proxy_config["format_module"] = value
        elif key == "cache_timeout":
            proxy_config["cache_timeout"] = value
        elif key == "interval":
            # real i3status hard-rejects this at the per-module level
            # ("no such option") - "interval" is a general{}-only i3status
            # setting; use cache_timeout for a module's own refresh rate
            notify_user(
                f"module '{name}': 'interval' is not a module option; ignoring.",
                level="warning",
            )
        elif key == "resources" or key in MODULE_OPTIONS:
            proxy_config[key] = value
        elif is_time_module and key == "format":
            # the proxy renders this locally, at its own pace - the
            # container's own i3status.conf always gets I3S_TZTIME_FORMAT
            # instead (below), so timezone extraction always works
            # regardless of what the user wants to actually display
            proxy_config["format"] = value
        elif is_time_module and key == "format_time":
            if item_name != "tztime":
                # real i3status hard-rejects this for "time" ("no such
                # option") - format_time is documented as tztime-only
                notify_user(
                    f"module '{name}': format_time is a tztime-only option; ignoring.",
                    level="warning",
                )
            else:
                # the %time substitution below is done locally in Python,
                # not by i3status's own (native, but unreliable)
                # format_time - so this never goes into the container's
                # own i3status.conf
                proxy_config["format_time"] = value
        else:
            container_item[key] = value

    if is_time_module:
        # a fixed, reliably parseable format - never shown to the user,
        # only used to extract the timezone from i3status's own reading
        container_item["format"] = I3S_TZTIME_FORMAT
        proxy_config.setdefault("format", I3S_TIME_MODULES[item_name])
        if "format_time" in proxy_config:
            format_time = proxy_config.pop("format_time")
            if "%time" in proxy_config["format"]:
                proxy_config["format"] = proxy_config["format"].replace("%time", format_time)
            else:
                notify_user(
                    f"module '{name}' sets format_time, but its format has no "
                    "%time placeholder to substitute it into; ignoring.",
                    level="warning",
                )

    return container_item, proxy_config


def _resolve_proxy_config(name, module_config, container_name, general_interval, notify_user):
    """
    Split one item's config and resolve its cache_timeout against the
    container's own general_interval, stamping _container/_item_name/
    _item_instance. Returns (container_item, proxy_config).
    """
    item_name, _, item_instance = name.partition(" ")
    container_item, proxy_config = _split_item_config(name, item_name, module_config, notify_user)

    cache_timeout = proxy_config.get("cache_timeout")
    if (
        # skip: an obfuscated cache_timeout isn't comparable until runtime
        isinstance(cache_timeout, (int, float))
        and cache_timeout < general_interval
    ):
        notify_user(
            f"module '{name}' {{cache_timeout={cache_timeout}}} cannot be lower than "
            f"i3status general {{interval={general_interval}}}; ignoring.",
            level="warning",
        )
        del proxy_config["cache_timeout"]
        cache_timeout = None

    # falls back to the container's own poll rate, not the proxy's
    if "cache_timeout" not in proxy_config:
        proxy_config["cache_timeout"] = general_interval

    proxy_config["_container"] = container_name
    proxy_config["_item_name"] = item_name
    proxy_config["_item_instance"] = item_instance or None
    if item_name in I3S_TIME_MODULES:
        # TimeZoneTicker's own staleness heuristic - separate from
        # cache_timeout, which time/tztime proxies don't use for timing
        proxy_config["_interval"] = general_interval
        if cache_timeout is not None:
            # user's cache_timeout survived validation above - honor it
            # instead of the format string's own tick rate
            proxy_config["_cache_timeout"] = True

    return container_item, proxy_config


GENERATED_CONTAINER_NAME = f"{I3S_CONTAINER_TYPE} {GENERATED_SLUG}"


# --- step 1: explicitly-configured "i3status name { }" containers ---


def _only_general_defaults(source):
    """Keep only the GENERAL_DEFAULTS keys a general{}/py3status{} dict set."""
    return {k: v for k, v in source.items() if k in GENERAL_DEFAULTS}


def _resolve_interval(py3status_config, top_level_general, default=DEFAULT_GENERAL_INTERVAL):
    """py3status{} wins over an explicit interval in top_level_general, else default."""
    return py3status_config.get("interval", top_level_general.get("interval", default))


def _flatten_container_items(container):
    """
    A container's nested items are plain dicts, not Modules - flatten its
    children into a list of whole dicts (name embedded); "general" is
    merged separately as the container's own settings.
    """
    items = []
    for item_name, item_value in list(container.items()):
        if not isinstance(item_value, ModuleDefinition):
            continue
        if item_name == "general":
            container["general"] = dict(item_value)
            continue
        item_value["name"] = item_name
        items.append(item_value)
        del container[item_name]
    return items


def resolve_configured_i3status_containers(
    config_info, config, py3_modules, module_groups, on_click, notify_user, claimed=None
):
    """
    Recursively translate every explicitly-configured "i3status name { }"
    container into real proxy configs, against the raw tree, before
    parse_config.py's module-tree walk runs - that walk would never otherwise
    find proxies that only exist in `config`. Container names claiming
    GENERATED_SLUG are already wiped by wipe_generated_instance_names(),
    so nothing here can collide with the reserved auto-generated container.

    `claimed` is shared across every container, not just one's own
    siblings - two containers can slugify to the same name (eg
    "hand-config"/"hand_config").
    """
    if claimed is None:
        claimed = set()

    # a bare "order += name" reference to a container, with no matching
    # block at all, is as valid as an explicit empty one - synthesize the
    # same empty container so it gets the same DEFAULT_ITEMS fallback
    for name in config_info.get("order", []):
        if is_i3status_container_name(name) and name not in config_info:
            config_info[name] = ModuleDefinition()

    for name, value in list(config_info.items()):
        if not isinstance(value, ModuleDefinition):
            continue
        if is_i3status_container_name(name):
            _resolve_configured_container(
                name, value, config, py3_modules, module_groups, on_click, notify_user, claimed
            )
        else:
            resolve_configured_i3status_containers(
                value, config, py3_modules, module_groups, on_click, notify_user, claimed
            )


def _resolve_configured_container(
    container_name, container, config, py3_modules, module_groups, on_click, notify_user, claimed
):
    """
    Resolve one explicitly-configured "i3status name { }" container:
    split each of its items into (container_item, proxy_config) pairs,
    register each proxy into config/py3_modules/module_groups, and
    stamp the container's own resolved "items"/"_proxies".
    """
    items = _flatten_container_items(container)
    if not items:
        # bare "i3status { }" - use the defaults instead of an empty container
        items = [dict(item) for item in DEFAULT_ITEMS]

    # own general{} wins over config["general"], which is already fully
    # resolved (py3status{} > top-level general{} > hardcoded default);
    # an enclosing group's own settings are deliberately not consulted here
    general_defaults = dict(config["general"])
    general_defaults.update(container.get("general", {}))
    general_interval = general_defaults.get("interval", DEFAULT_GENERAL_INTERVAL)
    general_defaults["interval"] = general_interval
    container["general"] = general_defaults

    # get_config_attribute's group fallback needs these flat too
    container.update(_only_general_defaults(general_defaults))

    # just the instance, not "i3status <instance>" - redundant with
    # the i3status_proxy prefix every proxy already has
    instance = get_instance_name(container_name)
    container_slug = _slugify(instance)
    container_items = []
    proxy_names = []

    for item in items:
        name = item["name"]
        if not is_i3status_module_name(name):
            # a py3status-native module can't nest inside an i3status
            # container - the real binary has no such type, so it'd
            # silently skip emitting this block, throwing off the
            # reading count and erroring on every update from then on.
            logger.warning(
                "ignoring non-i3status module '%s' in container '%s'",
                get_module_name(name),
                container_name,
            )
            continue
        proxy_name = _next_proxy_name(claimed, container_slug, name)
        proxy_names.append(proxy_name)

        # still a raw "on_click <button>" key - hoist it to on_click
        clicks = parse_onclick(item, name)
        if clicks:
            on_click[proxy_name] = clicks

        container_item, proxy_config = _resolve_proxy_config(
            name, item, container_name, general_interval, notify_user
        )

        container_items.append(container_item)
        config[proxy_name] = proxy_config
        py3_modules.append(proxy_name)
        _link_proxy_to_container(module_groups, proxy_name, container_name)

    container["items"] = container_items
    container["_proxies"] = proxy_names


# --- step 2: bare i3status.conf-style items, not wrapped in a container ---


def _replace_keys_in_place(mapping, renames):
    # rename dict keys while preserving overall key order - a plain
    # pop+reinsert would move the renamed key to the end instead
    items = list(mapping.items())
    mapping.clear()
    for key, value in items:
        if key in renames:
            key, value = renames[key]
        mapping[key] = value


def _find_bare_i3status_runs(config_info):
    """
    Discover every maximal run of consecutive bare i3status names, walking
    order into every reachable group/frame (an orphaned group is never
    visited). Returns (owner, start_index, names) triples - owner is
    config_info for a top-level run (order needs positional replacement,
    since a name can repeat there) or a group's own dict (keys are
    unique); start_index only matters when owner is config_info.
    """
    runs = []
    seen = set()

    def walk(owner, candidates):
        current = []
        start = None
        for index, (name, module) in enumerate(candidates):
            if is_i3status_module_name(name):
                if not current:
                    start = index
                current.append(name)
                continue
            if current:
                runs.append((owner, start, current))
                current = []
            if module is not None and not is_i3status_container_name(name):
                if id(module) in seen:
                    continue
                seen.add(id(module))
                sub_candidates = [
                    (k, v) for k, v in module.items() if isinstance(v, ModuleDefinition)
                ]
                walk(module, sub_candidates)
        if current:
            runs.append((owner, start, current))

    top_candidates = [(name, config_info.get(name)) for name in config_info.get("order", [])]
    walk(config_info, top_candidates)
    return runs


def resolve_bare_i3status_modules(
    config_info, config, py3_modules, module_groups, on_click, notify_user
):
    """
    Translate every bare i3status.conf-style item into a real proxy,
    merged behind one shared auto-generated container. Each item is
    replaced in place by a ModuleDefinition under its new proxy name,
    so the module-tree walk discovers it like any other py3status
    module - no i3status-specific special-casing needed there.
    """
    runs = _find_bare_i3status_runs(config_info)

    config["general"]["interval"] = _resolve_interval(config["py3status"], config["general"])

    if not runs:
        return

    logger.warning("auto-generating an i3status container for bare i3status modules")

    container_name = GENERATED_CONTAINER_NAME
    container_slug = GENERATED_SLUG
    general_interval = config["general"]["interval"]
    container_items = []
    proxy_names = []
    # one ever-increasing counter per slug - each type starts at its own
    # "_0". No claim-checking needed: every name is prefixed with the one
    # fixed GENERATED_SLUG container, unlike a configured container's own
    # (variable) container_slug.
    slug_counters = defaultdict(count)
    order = list(config_info.get("order", []))
    translated_top_level_names = set()

    for owner, start, names in runs:
        renames = {}
        run_proxy_names = []
        for name in names:
            # top-level "order" may reference the same raw name more than
            # once (separate runs) - never consumed here, only at the end,
            # once every occurrence has read from it
            # a bare "order += name" with no name { } block at all is valid
            # copy it: a repeated name's every occurrence shares this same
            # dict, and parse_onclick() below pops from it destructively -
            # without the copy, only the first occurrence would keep its
            # on_click handlers
            item = dict(owner.get(name, ModuleDefinition()))
            clicks = parse_onclick(item, name)

            slug = _slugify(name)
            index = next(slug_counters[slug])
            proxy_name = f"{I3S_PROXY_TYPE} {container_slug}_{slug}_{index}"
            proxy_names.append(proxy_name)
            run_proxy_names.append(proxy_name)

            container_item, proxy_config = _resolve_proxy_config(
                name, item, container_name, general_interval, notify_user
            )
            container_items.append(container_item)
            _link_proxy_to_container(module_groups, proxy_name, container_name)

            if clicks:
                on_click[proxy_name] = clicks

            if owner is config_info:
                # a fresh top-level entry per occurrence - renaming the
                # shared raw one in place would break a repeated name's
                # other occurrence(s)
                config_info[proxy_name] = ModuleDefinition(proxy_config)
                translated_top_level_names.add(name)
            else:
                renames[name] = (proxy_name, ModuleDefinition(proxy_config))

        if owner is config_info:
            order[start : start + len(names)] = run_proxy_names
        else:
            _replace_keys_in_place(owner, renames)

    config_info["order"] = order
    for name in translated_top_level_names:
        config_info.pop(name, None)

    # config["general"] is already fully resolved: py3status{} > top-level
    # general{} > hardcoded default - the bare container has no "own"
    # general{} of its own to layer on top, unlike a configured container
    general = dict(config["general"])

    config[container_name] = {
        "items": container_items,
        "general": general,
        "_proxies": proxy_names,
        # no order slot of its own - i3status() checks this to skip
        # rendering entirely, since its items' proxies do have one
        "_generated": True,
    }
    # get_config_attribute's group fallback needs these flat too
    config[container_name].update(_only_general_defaults(general))
    py3_modules.append(container_name)
