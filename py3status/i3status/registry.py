"""
In-process shared state between an i3status container and its proxies.
A plain dict is safe here - simple get/set are GIL-covered, no lock needed.
"""

_registry = {}
_dead = {}


def publish(container_instance, item_key, output):
    # latest rendered output for one item of a container
    _registry[(container_instance, item_key)] = output


def read(container_instance, item_key):
    # latest published output for one item, or None if not published yet
    return _registry.get((container_instance, item_key))


def clear(container_instance):
    # remove everything published by one container - once it's done for
    # good (killed/reloaded, or respawn budget exhausted), not per-crash
    for key in [key for key in _registry if key[0] == container_instance]:
        del _registry[key]


def mark_dead(container_instance, reason):
    # never coming back - separate from clear() and never cleared itself,
    # so a late proxy still sees why instead of polling forever
    _dead[container_instance] = reason


def dead_reason(container_instance):
    # why a container is never coming back, or None if it isn't (yet)
    return _dead.get(container_instance)
