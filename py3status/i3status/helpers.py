"""
i3status name-classification and on_click parsing primitives, shared by
parse_config.py and translate.py without needing the full pipeline.
"""

from py3status.config_types import validate_onclick_button
from py3status.helpers import get_module_name
from py3status.i3status.constants import (
    I3S_CONTAINER_TYPE,
    I3S_MODULE_NAMES,
    I3S_PROXY_TYPE,
    I3S_SINGLE_NAMES,
)


def is_i3status_module_name(name):
    # is this an i3status.conf-style section name (eg "disk /")?
    return get_module_name(name) in I3S_MODULE_NAMES


def is_i3status_container_name(name):
    # is this an i3status container's own name (eg "i3status _generated")?
    return get_module_name(name) == I3S_CONTAINER_TYPE


def is_i3status_proxy_name(name):
    # is this a proxy's own name (eg "i3status_proxy _generated_disk")?
    return get_module_name(name) == I3S_PROXY_TYPE


def is_i3status_single_name(name):
    # i3status type that can never take an instance (eg "time", not "tztime")
    return get_module_name(name) in I3S_SINGLE_NAMES


def parse_onclick(module, name):
    """
    Pop and validate on_click <button> keys from a module config dict.
    Returns a dict of {button: command}, or None if none were configured.
    """
    clicks = {}
    # list(module) since we pop matched keys below while iterating
    for key in list(module):
        if not key.startswith("on_click"):
            continue
        try:
            button = validate_onclick_button(key)
        except ValueError as e:
            raise Exception(f"module '{name}': {e}")
        clicks[button] = module.pop(key)
    return clicks or None
