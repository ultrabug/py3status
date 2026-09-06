import ast
from pathlib import Path

MODULE_PATH = Path(__file__).resolve().parent.parent / "py3status" / "modules"


def get_module_files(skip_files):
    for _file in sorted(MODULE_PATH.iterdir()):
        if _file.suffix == ".py" and _file.name not in skip_files:
            yield _file


def get_py3status_methods(_file):
    tree = ast.parse(_file.read_text(), filename=str(_file))
    for node in tree.body:
        if isinstance(node, ast.ClassDef) and node.name == "Py3status":
            return [item.name for item in node.body if isinstance(item, ast.FunctionDef)]
    return []


def test_authors():
    comment = "@author"
    skip_files = ["__init__.py"]
    errors = []

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            if comment not in f.read():
                errors.append((comment, _file))
    if errors:
        line = "Missing @author error(s) detected!\n\n"
        for error in errors:
            line += "`{}` is not in module `{}`\n".format(*error)
        print(line[:-1])
        assert False


def test_sample_output():
    comment = "SAMPLE OUTPUT"
    skip_files = ["__init__.py"]
    errors = []

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            if comment not in f.read():
                errors.append((comment, _file))
    if errors:
        line = "Missing sample error(s) detected!\n\n"
        for error in errors:
            line += "`{}` is not in module `{}`\n".format(*error)
        print(line[:-1])
        assert False


# def test_examples():
#     comment = "Examples:"
#     skip_files = ["__init__.py"]
#     errors = []
#
#     for _file in sorted(MODULE_PATH.iterdir()):
#         if _file.suffix == ".py" and _file.name not in skip_files:
#             with _file.open() as f:
#                 if comment not in f.read():
#                     errors.append((comment, _file))
#     if errors:
#         line = "Missing example error(s) detected!\n\n"
#         for error in errors:
#             line += "`{}` is not in module `{}`\n".format(*error)
#         print(line[:-1])
#         assert False


def test_available_configuration_parameters():
    comment = "# available configuration parameters"
    skip_files = ["__init__.py"]
    errors = []

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            if comment not in f.read():
                errors.append((comment, _file))
    if errors:
        line = "Missing comment error(s) detected!\n\n"
        for error in errors:
            line += "Comment `{}` is not in module `{}`\n".format(*error)
        print(line[:-1])
        assert False


def test_class_meta_before_parameters():
    line = "class Meta:"
    comment = "# available configuration parameters"
    errors = []
    skip_files = ["__init__.py"]

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            for x in f.readlines():
                if line in x:
                    errors.append((line, _file))
                    break
                elif comment in x:
                    break
    if errors:
        line = "Class Meta error(s) detected!\n\n"
        for error in errors:
            line += "`{}` is defined early in module `{}`\n".format(*error)
        print(line[:-1])
        assert False


def test_examples_before_requires():
    line = "Examples:"
    comment = "Requires:"
    errors = []
    skip_files = ["__init__.py"]

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            output = f.read()
            if line not in output or comment not in output:
                continue
            for x in output.splitlines():
                if x.startswith(line):
                    errors.append((line, _file))
                    break
                elif x.startswith(comment):
                    break
    if errors:
        line = "Examples error(s) detected!\n\n"
        for error in errors:
            line += "`{}` is defined early in module `{}`\n".format(*error)
        print(line[:-1])
        assert False


def test_authors_before_examples():
    line = "@author "
    comment = "Examples:"
    errors = []
    skip_files = ["__init__.py"]

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            output = f.read()
            if line not in output or comment not in output:
                continue
            for x in output.splitlines():
                if x.startswith(line):
                    errors.append((line, _file))
                    break
                elif x.startswith(comment):
                    break
    if errors:
        line = "Author error(s) detected!\n\n"
        for error in errors:
            line += "`{}` is defined early in module `{}`\n".format(*error)
        print(line[:-1])
        assert False


def test_format_placeholders():
    comment = " placeholders:"
    skip_files = [
        "__init__.py",
        "i3pystatus.py",
        "keyboard_locks.py",
        "screenshot.py",
        "static_string.py",
        "wwan_status.py",
        "yubikey.py",
    ]
    errors = []

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            output = f.read()
            if comment not in output:
                errors.append((comment, _file))
    if errors:
        line = f"Missing `{comment}` error(s) detected!\n\n"
        for error in errors:
            line += "`{}` is not in module `{}`\n".format(*error)
        print(line[:-1])
        assert False


def test_sub_heading_names_are_real_values():
    # A sub-heading bullet (a `name:` bullet with no text of its own,
    # grouping the bullets that follow it - see
    # test_no_empty_listing_descriptions above) must name something real:
    # a value that actually appears elsewhere in the same module's
    # docstring (a real config parameter, or a value mentioned in its
    # own prose, eg xkb_input's `switcher` values) - not a vague phrase
    # like weather_owm's old `format only:`. An optional trailing
    # "(qualifier)" is allowed to disambiguate an otherwise-duplicate
    # name (eg xkb_input's two `swaymsg:` sections, one for its common
    # placeholders and one for its sway-only extras).
    import re

    from py3status.autodoc import BULLET_NAME_RE, LISTING_BLOCK_RE
    from py3status.docstrings import core_module_docstrings

    qualifier_re = re.compile(r"^(.*\S)\s+\([^()]*\)$")
    data = core_module_docstrings()
    errors = []
    for name, lines in data.items():
        content = "".join(lines).strip()
        for match in LISTING_BLOCK_RE.finditer(content):
            header = match.group(1).strip()
            rest_of_doc = content[: match.start()] + content[match.end() :]
            for bullet in BULLET_NAME_RE.finditer(match.group(2)):
                bullet_name, bullet_rest = bullet.group(1), bullet.group(2)
                if bullet_rest.strip():
                    continue
                sub_name = bullet_name
                qm = qualifier_re.match(sub_name)
                if qm:
                    sub_name = qm.group(1)
                for value in (v.strip() for v in sub_name.split(",")):
                    if value and value not in rest_of_doc:
                        errors.append((name, header, bullet_name, value))
    if errors:
        line = "Sub-heading name error(s) detected!\n\n"
        for module, header, bullet_name, value in errors:
            line += (
                f"`{bullet_name}` under `{header}` in module `{module}` names "
                f"`{value}`, which doesn't appear anywhere else in the docstring\n"
            )
        print(line[:-1])
        assert False


def test_no_admonition_header_before_first_listing():
    # An admonition-type header (Warning:/Note:/etc - see
    # autodoc.py's ADMONITION_TYPES) must not appear in the free-text
    # description before the first "Configuration parameters:"-style
    # listing (eg aws_bill.py used to open with a `Warnings:` section
    # before `Configuration parameters:`) - it belongs in its normal
    # position, after the structured reference sections, alongside
    # every other module's Notes/Warnings.
    from py3status.autodoc import LISTING_BLOCK_RE, NOTE_BLOCK_RE, _admonition_type
    from py3status.docstrings import core_module_docstrings

    data = core_module_docstrings()
    errors = []
    for name, lines in data.items():
        content = "".join(lines).strip()
        first_listing = LISTING_BLOCK_RE.search(content)
        split_at = first_listing.start() if first_listing else len(content)
        description = content[:split_at]
        for match in NOTE_BLOCK_RE.finditer(description):
            header = match.group(1).strip()
            if _admonition_type(header):
                errors.append((name, header))
    if errors:
        line = "Misplaced admonition header error(s) detected!\n\n"
        for module, header in errors:
            line += f"`{header}` in module `{module}` appears before its first listing\n"
        print(line[:-1])
        assert False


def test_no_colon_in_bullet_names():
    # A listing bullet's name (eg a Configuration parameters/Requires
    # entry) must never contain a colon - watson.py used to have a
    # `Requires:` line whose whole url ended up as the bullet's name
    # (`- \`https://github.com/...\` commandline time tracking tool`),
    # rendering as a broken-looking definition instead of plain prose.
    from py3status.autodoc import BULLET_NAME_RE, LISTING_BLOCK_RE
    from py3status.docstrings import core_module_docstrings

    data = core_module_docstrings()
    errors = []
    for name, lines in data.items():
        content = "".join(lines).strip()
        for match in LISTING_BLOCK_RE.finditer(content):
            header = match.group(1).strip()
            for bullet in BULLET_NAME_RE.finditer(match.group(2)):
                bullet_name = bullet.group(1)
                if ":" in bullet_name:
                    errors.append((name, header, bullet_name))
    if errors:
        line = "Colon in bullet name error(s) detected!\n\n"
        for module, header, bullet_name in errors:
            line += f"`{bullet_name}` under `{header}` in module `{module}` contains a colon\n"
        print(line[:-1])
        assert False


def test_format_placeholder_headers_name_the_real_parameter():
    # A "Format placeholders:"-shaped header whose bullets are all `{...}`
    # placeholders, and whose wording shares a root word with a real
    # `format_X` param (eg "player" for `format_player`), must actually be
    # spelled as that param's name(s) - case-insensitive. Also covers the
    # bare "format" case (catches scroll.py, whose `format` used to be
    # hardcoded rather than a real config parameter). Blind spot: a header
    # sharing no root word at all with its param (eg old "Stream format
    # placeholders:" for `format`/`format_offline`) isn't mechanically
    # catchable and has to be found by hand.
    import re

    from py3status.autodoc import BULLET_NAME_RE, LISTING_BLOCK_RE
    from py3status.docstrings import core_module_docstrings

    qualifier_re = re.compile(r"^(.*\S)\s+\([^()]*\)$")
    word_re = re.compile(r"[a-z]+")
    data = core_module_docstrings()
    errors = []
    for name, lines in data.items():
        content = "".join(lines).strip()
        matches = list(LISTING_BLOCK_RE.finditer(content))

        real_format_params = set()
        for match in matches:
            for bullet in BULLET_NAME_RE.finditer(match.group(2)):
                bullet_name = bullet.group(1)
                if not bullet_name.startswith("{") and (
                    bullet_name == "format" or bullet_name.startswith("format_")
                ):
                    real_format_params.add(bullet_name)
        suffixes = {p: p[len("format_") :] for p in real_format_params if p.startswith("format_")}

        for match in matches:
            header_full = match.group(1).strip()
            header = header_full.rstrip(":")
            bullets = list(BULLET_NAME_RE.finditer(match.group(2)))
            if not bullets or not all(b.group(1).startswith("{") for b in bullets):
                continue
            qm = qualifier_re.match(header)
            name_part = qm.group(1) if qm else header
            name_part = re.sub(r"(?i)\s*placeholders\s*$", "", name_part).strip()
            declared = {v.strip().lower() for v in name_part.split(",")}
            header_words = set(word_re.findall(header.lower()))
            matched = {p.lower() for p, suffix in suffixes.items() if suffix.lower() in header_words}
            if matched and not matched.issubset(declared):
                errors.append((name, header_full, sorted(matched)))
            elif "format" in declared and "format" not in {p.lower() for p in real_format_params}:
                errors.append((name, header_full, ["format (no such config parameter)"]))
    if errors:
        line = "Format-placeholder header naming error(s) detected!\n\n"
        for module, header, matched in errors:
            line += f"`{header}` in module `{module}` should name {matched}\n"
        print(line[:-1])
        assert False


def test_no_duplicate_section_headers():
    # same top-level header (eg "Configuration parameters:") twice in one
    # module's docstring is a copy-paste mistake, splitting one section in two
    from py3status.autodoc import LISTING_BLOCK_RE, NOTE_BLOCK_RE
    from py3status.docstrings import core_module_docstrings

    data = core_module_docstrings()
    errors = []
    for name, lines in data.items():
        content = "".join(lines).strip()
        headers = [m.group(1).strip() for m in LISTING_BLOCK_RE.finditer(content)]
        headers += [m.group(1).strip() for m in NOTE_BLOCK_RE.finditer(content)]
        dupes = {h for h in headers if headers.count(h) > 1}
        for header in sorted(dupes):
            errors.append((name, header))
    if errors:
        line = "Duplicate section header error(s) detected!\n\n"
        for module, header in errors:
            line += f"`{header}` appears more than once in module `{module}`\n"
        print(line[:-1])
        assert False


def test_no_empty_listing_descriptions():
    # every `- `name` ...` bullet inside a "Configuration parameters:"/
    # "Format placeholders:"/etc listing must end up with a real
    # description in the generated output. A bare `name` with nothing
    # after it is a valid sub-heading (eg weather_owm's `format_clouds:`
    # or xkb_input's `swaymsg:`) - wrap_listings() groups the bullets
    # that follow it into their own titled definition list rather than
    # rendering it as a confusing, description-less entry - so check
    # the real rendered output instead of just flagging every bare
    # bullet: each bullet's name must still appear somewhere in it, and
    # no definition may end up with a blank description.
    import re

    from py3status.autodoc import BULLET_NAME_RE, LISTING_BLOCK_RE, wrap_listings
    from py3status.docstrings import core_module_docstrings

    empty_definition_re = re.compile(r"`[^`]+`\*{0,2}\n:   *(\n|$)")

    data = core_module_docstrings()
    errors = []
    for name, lines in data.items():
        content = "".join(lines).strip()
        for match in LISTING_BLOCK_RE.finditer(content):
            header = match.group(1).strip()
            rendered = wrap_listings(match.group(0))
            if empty_definition_re.search(rendered):
                errors.append((name, header, "<empty definition in rendered output>"))
            for bullet in BULLET_NAME_RE.finditer(match.group(2)):
                if bullet.group(1) not in rendered:
                    errors.append((name, header, bullet.group(1)))
    if errors:
        line = "Empty listing description error(s) detected!\n\n"
        for module, header, bullet_name in errors:
            line += f"`{bullet_name}` under `{header}` in module `{module}` has no description\n"
        print(line[:-1])
        assert False


def test_no_singular_section_headers():
    # A docstring section header ("Examples:", "Configuration parameters:",
    # "Format placeholders:", "Color options:", "Color thresholds:",
    # "Requires:", "Notes:", and any "... parameters:"/"... placeholders:"
    # variant, eg "Dynamic format placeholders:") is always plural, never
    # singular ("Example:", "Configuration parameter:", etc), so every
    # module's docstring uses one consistent header spelling.
    singular_nouns = ("example", "note", "require", "parameter", "placeholder", "option", "threshold")
    # words that mark a header as a free-form sentence (eg "Color options
    # for `auto.input` threshold:") rather than a structured label like
    # "Configuration parameter:" - those are legitimately singular
    prose_words = ("for", "of", "in", "on", "with", "to", "a", "an", "the", "your")
    skip_files = ["__init__.py"]
    errors = []

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            lines = f.read().splitlines()
        for line in lines:
            if not line or line[0] in " \t" or not line.endswith(":"):
                continue
            words = line[:-1].split()
            if not words or words[-1].lower() not in singular_nouns:
                continue
            if any(word.lower() in prose_words for word in words[:-1]):
                continue
            errors.append((line, f"{line[:-1]}s:", _file))
    if errors:
        line = "Singular section header error(s) detected!\n\n"
        for error in errors:
            line += "`{}` in module `{}` should be `{}`\n".format(error[0], error[2], error[1])
        print(line[:-1])
        assert False


def test_examples_use_code_fence():
    # a docstring's "Examples:"/"Example:" section must open with a real
    # ```` ``` ```` fence, not plain indented text - the single-page docs
    # builder (py3status/autodoc.py) only recognizes multi-paragraph
    # indented sections up to their first blank line, so anything after
    # silently escapes as raw text; if a later line happens to start
    # with `#` (a shell/config comment), it gets misread as a markdown
    # heading and corrupts the whole page's table of contents (this
    # happened for real with prometheus.py's Examples section).
    headers = ("Examples:", "Example:")
    skip_files = ["__init__.py"]
    errors = []

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            lines = f.read().splitlines()
        for index, line in enumerate(lines):
            if line not in headers:
                continue
            rest = lines[index + 1 :]
            if not rest or not rest[0].startswith("```"):
                errors.append((line, _file))
            break
    if errors:
        line = "Examples not fenced with ``` error(s) detected!\n\n"
        for error in errors:
            line += "`{}` in module `{}` is not followed by a ``` code fence\n".format(*error)
        print(line[:-1])
        assert False


def test_code_fences_balanced():
    # every ``` opener needs its own ``` closer - an unmatched fence
    # doesn't just break syntax highlighting for the rest of the file,
    # it can throw off the single-page docs builder's own tracking of
    # what's inside a fence (py3status/autodoc.py's shift_headings),
    # letting unrelated text further down get misread as headings.
    skip_files = ["__init__.py"]
    errors = []

    for _file in get_module_files(skip_files):
        with _file.open() as f:
            count = sum(1 for line in f if line.startswith("```"))
        if count % 2:
            errors.append(_file)
    if errors:
        line = "Unbalanced ``` code fence error(s) detected!\n\n"
        for error in errors:
            line += f"Module `{error}` has an odd number of ``` fence markers\n"
        print(line[:-1])
        assert False


def test_module_method_order():
    skip_files = ["__init__.py", "i3pystatus.py"]
    errors = []

    for _file in get_module_files(skip_files):
        methods = get_py3status_methods(_file)
        module_method = _file.stem
        if module_method not in methods:
            errors.append(f"Module `{_file}` should define `{module_method}()`")
            continue

        if "post_config_hook" in methods and methods[0] != "post_config_hook":
            errors.append(
                f"Module `{_file}` should define `post_config_hook()` first when present"
            )

        expected_tail = [module_method]
        if "kill" in methods:
            expected_tail.append("kill")
        if "on_click" in methods:
            expected_tail.append("on_click")

        helper_methods = methods[1:] if methods[0] == "post_config_hook" else methods
        helper_methods = helper_methods[: -len(expected_tail)]
        for method in helper_methods:
            if not method.startswith("_"):
                errors.append(
                    f"Module `{_file}` should define `{method}()` before "
                    f"`{module_method}()` only if it is private"
                )

        if methods[-len(expected_tail) :] != expected_tail:
            expected_methods = " then ".join(f"`{name}()`" for name in expected_tail)
            errors.append(f"Module `{_file}` should end with {expected_methods}")

    if errors:
        line = "Module method ordering error(s) detected!\n\n"
        line += "\n".join(errors)
        print(line)
        assert False
