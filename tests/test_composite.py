from py3status.composite import Composite


# Composite initialize


def test_Composite_init_1():
    result = Composite("moo").get_content()
    assert result == [{"full_text": "moo"}]


def test_Composite_init_2():
    result = Composite({"full_text": "moo"}).get_content()
    assert result == [{"full_text": "moo"}]


def test_Composite_init_3():
    result = Composite([{"full_text": "moo"}]).get_content()
    assert result == [{"full_text": "moo"}]


def test_Composite_init_4():
    result = Composite(Composite("moo")).get_content()
    assert result == [{"full_text": "moo"}]


# Composite append


def test_Composite_append_1():
    c = Composite("moo")
    c.append("moo")
    result = c.get_content()
    assert result == [{"full_text": "moo"}, {"full_text": "moo"}]


def test_Composite_append_2():
    c = Composite("moo")
    c.append({"full_text": "moo"})
    result = c.get_content()
    assert result == [{"full_text": "moo"}, {"full_text": "moo"}]


def test_Composite_append_3():
    c = Composite("moo")
    c.append([{"full_text": "moo"}])
    result = c.get_content()
    assert result == [{"full_text": "moo"}, {"full_text": "moo"}]


def test_Composite_append_4():
    c = Composite("moo")
    c.append(Composite("moo"))
    result = c.get_content()
    assert result == [{"full_text": "moo"}, {"full_text": "moo"}]


# Composite __iadd__


def test_Composite_iadd_1():
    c = Composite("moo")
    c += "moo"
    result = c.get_content()
    assert result == [{"full_text": "moo"}, {"full_text": "moo"}]


def test_Composite_iadd_2():
    c = Composite("moo")
    c += {"full_text": "moo"}
    result = c.get_content()
    assert result == [{"full_text": "moo"}, {"full_text": "moo"}]


def test_Composite_iadd_3():
    c = Composite("moo")
    c += [{"full_text": "moo"}]
    result = c.get_content()
    assert result == [{"full_text": "moo"}, {"full_text": "moo"}]


def test_Composite_iadd_4():
    c = Composite("moo")
    c += Composite("moo")
    result = c.get_content()
    assert result == [{"full_text": "moo"}, {"full_text": "moo"}]


# Composite simplify


def test_Composite_simplify_separator():
    composite = Composite(
        [
            {"full_text": "one", "separator": True},
            {"full_text": "two", "separator": True},
        ]
    )
    assert composite.simplify().get_content() == [
        {"full_text": "one", "separator": True},
        {"full_text": "two", "separator": True},
    ]


def test_Composite_simplify_disabled_separator():
    composite = Composite(
        [
            {"full_text": "one", "separator": False},
            {"full_text": "two", "separator": False},
        ]
    )
    assert composite.simplify().get_content() == [
        {"full_text": "one", "separator": False},
        {"full_text": "two", "separator": False},
    ]


# Composite join


def test_Composite_simplify_whitespace_separator():
    composite = Composite(
        [
            {"full_text": "one"},
            {"full_text": " ", "separator": False, "separator_block_width": 0},
        ]
    )

    assert composite.simplify().get_content() == [
        {"full_text": "one"},
        {"full_text": " ", "separator": False, "separator_block_width": 0},
    ]


def test_Composite_join_native_separator():
    items = [
        Composite({"full_text": "one"}),
        Composite({"full_text": "two", "separator": False, "separator_block_width": 0}),
        Composite({"full_text": "three", "separator_block_width": 9}),
    ]
    result = Composite.composite_join(True, items)

    assert result.simplify().get_content() == [
        {"full_text": "one", "separator": True},
        {"full_text": "two", "separator": False, "separator_block_width": 0},
        {"full_text": "three", "separator_block_width": 9},
    ]
    assert items[0].get_content() == [{"full_text": "one"}]


def test_Composite_join_native_separator_trailing_empty_block():
    items = [
        Composite([{"full_text": "one"}, {"full_text": ""}]),
        Composite([{"full_text": "two"}, {"full_text": ""}]),
    ]

    assert Composite.composite_join(True, items).simplify().get_content() == [
        {"full_text": "one", "separator": True},
        {"full_text": "two"},
    ]


def test_Composite_join_disabled_native_separator():
    assert Composite.composite_join(False, ["one", "two"]).simplify().get_content() == [
        {"full_text": "one", "separator": False},
        {"full_text": "two"},
    ]
