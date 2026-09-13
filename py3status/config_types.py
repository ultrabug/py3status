"""
Small, dependency-free primitives shared by parse_config.py and the
i3status translation layer (translate.py/helpers.py) - kept out of
parse_config.py itself so neither side needs a deferred import to
avoid a cycle.
"""

from collections import OrderedDict


class ModuleDefinition(OrderedDict):
    """Module definition in OrderedDict form"""

    pass


def validate_onclick_button(key):
    """
    Parse and validate the button number from an on_click <button> key.
    Returns the validated int, or raises ValueError.
    """
    try:
        button = int(key.split()[1])
    except (ValueError, IndexError):
        raise ValueError(f"invalid '{key}'")
    if button not in range(1, 21):
        raise ValueError(f"'{key}' not in range 1-20")
    return button
