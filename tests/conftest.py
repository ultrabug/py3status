import pytest

from py3status.i3status import registry


@pytest.fixture(autouse=True)
def reset_i3status_registry():
    """
    registry is in-process global state, shared across every test in the
    session - without this, one test marking eg "i3status gc0" dead (or
    publishing to it) leaks into any other test using that same
    conventional container name.
    """
    registry._registry.clear()
    registry._dead.clear()
    yield
    registry._registry.clear()
    registry._dead.clear()
