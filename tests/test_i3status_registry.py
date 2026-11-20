from py3status.i3status import registry


def test_publish_then_read_returns_latest_value():
    registry.publish("i3status gc0", ("disk", "/"), {"full_text": "42%"})

    assert registry.read("i3status gc0", ("disk", "/")) == {"full_text": "42%"}


def test_read_missing_key_returns_none():
    assert registry.read("i3status gc0", ("nonexistent", None)) is None


def test_publish_overwrites_previous_value():
    key = ("wireless", "_first_")
    registry.publish("i3status gc1", key, {"full_text": "old"})
    registry.publish("i3status gc1", key, {"full_text": "new"})

    assert registry.read("i3status gc1", key) == {"full_text": "new"}


def test_different_containers_do_not_collide():
    key = ("load", None)
    registry.publish("i3status gc0", key, {"full_text": "container 0"})
    registry.publish("i3status gc1", key, {"full_text": "container 1"})

    assert registry.read("i3status gc0", key) == {"full_text": "container 0"}
    assert registry.read("i3status gc1", key) == {"full_text": "container 1"}
