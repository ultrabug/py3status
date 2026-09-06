from py3status.autodoc import (
    _admonition_type,
    fence_prose,
    wrap_data_lines,
    wrap_listings,
    wrap_notes,
)


def test_fence_prose_wraps_plain_text():
    out = fence_prose("just some prose")
    assert out.startswith("````text\n")
    assert "just some prose" in out


def test_fence_prose_does_not_support_raw_admonition_fence():
    # a raw /// fence in a description isn't supported - just fenced as
    # plain text; a real admonition belongs in a Notes:/Warnings: section
    text = "before\n\n/// warning\nbe careful\n///\n\nafter"
    out = fence_prose(text)
    assert out == "````text\n" + text + "\n````"


def test_fence_prose_does_not_treat_header_shape_as_admonition():
    # regression guard for the old aws_bill special-case (fenced as plain text)
    text = "Warnings:\n    be careful\n"
    out = fence_prose(text)
    assert "/// warning" not in out
    assert "Warnings:" in out


def test_wrap_notes_renders_real_admonition_types():
    content = "Warnings:\n    be careful\n"
    out = wrap_notes(content)
    assert out == "/// warning\nbe careful\n///\n"


def test_wrap_notes_renders_plain_header_for_non_admonition():
    content = "Requires:\n    some-tool\n"
    out = wrap_notes(content)
    assert out == "**Requires:**\n\nsome-tool\n"


def test_admonition_type_requires_plural_form():
    assert _admonition_type("Warnings:") == "warning"
    # singular is not recognized as an admonition
    assert _admonition_type("Warning:") is None
    # not a blind rstrip("s") - "success" must not become "succe"
    assert _admonition_type("Success:") is None
    assert _admonition_type("Requires:") is None


def test_wrap_listings_groups_sub_heading_bullets():
    # a description-less bullet groups the bullets after it (weather_owm's shape)
    content = "Format placeholders:\n\n- `format_clouds`\n\n- `{coverage}` cloud coverage\n"
    out = wrap_listings(content)
    assert "**Format placeholders (format_clouds):**" in out
    assert "`{coverage}`" in out


def test_wrap_listings_flat_list_for_single_segment():
    content = "Configuration parameters:\n\n- `cache_timeout` how often *(default 10)*\n"
    out = wrap_listings(content)
    assert out.startswith("**Configuration parameters:**")
    assert "*Default: `10`*" in out


def test_wrap_data_lines_formats_metadata():
    content = "**author** someone\n**license** BSD\n"
    out = wrap_data_lines(content)
    assert "**Metadata:**" in out
    assert "**`author`**" in out
    assert ":   someone" in out
