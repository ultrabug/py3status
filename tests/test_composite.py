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
