import ast
import re
import difflib

from pathlib import Path

from py3status.helpers import print_stderr


def modules_directory():
    """
    Get the core modules directory.
    """
    return Path(__file__).resolve().parent / "modules"


def parse_readme():
    """
    Crude parsing of modules/README.md
    returns a dict of {<module_name>: <documentation>}
    """
    name = None
    re_mod = re.compile(r'^### <a name="(?P<name>[a-z_0-9]+)"></a>')
    readme_file = modules_directory() / "README.md"
    modules_dict = {}
    with readme_file.open() as f:
        for row in f.readlines():
            match = re_mod.match(row)
            if match:
                name = match.group("name")
                modules_dict[name] = []
                continue
            if row.startswith("---"):
                name = None
                continue
            if name:
                modules_dict[name].append(row)
    return modules_dict


def core_module_docstrings(
    include_core=True, include_user=False, config=None, format="md"
):
    """
    Get docstrings for all core modules and user ones if requested
    returns a dict of {<module_name>: <docstring>}
    """
    paths = {}
    docstrings = {}
    if include_core:
        for file in modules_directory().iterdir():
            if file.suffix == ".py":
                if file.stem != "__init__":
                    paths[file.stem] = (file, "core")

    if include_user:
        # include user modules
        for include_path in sorted(config["include_paths"]):
            for file in sorted(include_path.iterdir()):
                if file.suffix != ".py":
                    continue
                paths[file.stem] = (file, "user")
    for name in paths:
        path, module_type = paths[name]
        with path.open() as f:
            try:
                module = ast.parse(f.read())
            except SyntaxError:
                # there is a syntax error so ignore module
                continue
            raw_docstring = ast.get_docstring(module)

            # prevent issue when no docstring exists
            if raw_docstring is None:
                continue

            # remove any sample outputs
            parts = re.split("^SAMPLE OUTPUT$", raw_docstring, flags=re.M)
            docstring = parts[0]

            if format == "md":
                docstring = [
                    d for d in _from_docstring_md(str(docstring).strip().split("\n"))
                ]
            elif format == "rst":
                docstring = [
                    d for d in _from_docstring_rst(str(docstring).strip().split("\n"))
                ]
            else:
                raise Exception("`md` and `rst` format supported only")

            docstrings[name] = docstring + ["\n"]
    return docstrings


def create_readme(data):
    """
    Create README.md text for the given module data.
    """
    out = ['<a name="top"></a>Modules\n========\n\n']
    # Links
    for module, lines in sorted(data.items()):
        desc = "".join(lines).strip().split("\n")[0]
        format_str = "\n**[{name}](#{name})** — {desc}\n"
        out.append(format_str.format(name=module, desc=desc))
    # details
    for module, lines in sorted(data.items()):
        out.append(
            '\n---\n\n### <a name="{name}"></a>{name}\n\n{details}\n'.format(
                name=module, details="".join(lines).strip()
            )
        )
    return "".join(out)


re_listing = re.compile(r"^\w.*:$")

# match in README.md
re_to_param = re.compile(r"^  - `([a-z]\S+)`($|[ \t])")
re_to_status = re.compile(r"^  - `({\S+})`($|[ \t])")
re_to_item = re.compile(r"^\s+-")
re_to_data = re.compile(r"^\*\*(author|license|source)\*\*($|[ \t])")
re_to_tag = re.compile("&lt;([^.]*)&gt;")
re_to_defaults = re.compile(r"\*(\(default.*\))\*")

# match in module docstring
re_from_param = re.compile(r"^    ([a-z<]\S+):($|[ \t])(.*)$")
re_from_status = re.compile(r"^\s+({\S+})($|[ \t])(.*)$")
re_from_item = re.compile(r"^\s+-(?=\s)")
re_from_data = re.compile("^@(author|license|source)($|[ \t])")
re_from_tag = re.compile("((`[^`]*`)|[<>&])")
re_from_defaults = re.compile(r"(\(default.*\))\s*$")

# for rst
re_lone_backtick = re.compile("(?<!`)`(?!`)")


def _reformat_docstring(doc, format_fn, code_newline=""):
    """
    Go through lines of file and reformat using format_fn
    """
    out = []
    status = {"listing": False, "add_line": False, "eat_line": False}
    code = False
    for line in doc:
        if status["add_line"]:
            out.append("\n")
        status["add_line"] = False
        if status["eat_line"]:
            status["eat_line"] = False
            if line.strip() == "":
                continue
        # check for start/end of code block
        if line.strip() == "```":
            code = not code
            out.append(line + code_newline)
            continue
        if not code:
            # if we are in a block listing a blank line ends it
            if line.rstrip() == "":
                status["listing"] = False
            # format the line
            line = format_fn(line, status)
            # see if block start
            if re_listing.match(line):
                status["listing"] = True
        out.append(line.rstrip() + "\n")
    return out


def _to_docstring(doc):
    """
    format from Markdown to docstring
    """

    def format_fn(line, status):
        """ format function """
        # swap &lt; &gt; to < >
        line = re_to_tag.sub(r"<\1>", line)
        if re_to_data.match(line):
            line = re_to_data.sub(r"@\1 ", line)
            status["eat_line"] = True
        line = re_to_defaults.sub(r"\1", line)
        if status["listing"]:
            # parameters
            if re_to_param.match(line):
                line = re_to_param.sub(r"    \1: ", line)
            # status items
            elif re_to_status.match(line):
                line = re_to_status.sub(r"    \1 ", line)
            # bullets
            elif re_to_item.match(line):
                line = re_to_item.sub(r"    -", line)
            # is continuation line
            else:
                line = " " * 8 + line.lstrip()
        return line

    return _reformat_docstring(doc, format_fn)


def _from_docstring_md(doc):
    """
    format from docstring to Markdown
    """

    def format_fn(line, status):
        """ format function """

        def fix_tags(line):
            # In markdown we need to escape < > and & for display
            # but we don't want to do this is the value is quoted
            # by backticks ``

            def fn(match):
                # swap matched chars
                found = match.group(1)
                if found == "<":
                    return "&lt;"
                if found == ">":
                    return "&gt;"
                if found == "&":
                    return "&amp;"
                return match.group(0)

            return re_from_tag.sub(fn, line)

        if re_from_data.match(line):
            line = re_from_data.sub(r"**\1** ", line)
            status["add_line"] = True
        line = re_from_defaults.sub(r"*\1*", line)
        if status["listing"]:
            # parameters
            if re_from_param.match(line):
                m = re_from_param.match(line)
                line = "  - `{}` {}".format(m.group(1), fix_tags(m.group(3)))
            # status items
            elif re_from_status.match(line):
                m = re_from_status.match(line)
                line = "  - `{}` {}".format(m.group(1), fix_tags(m.group(3)))
            # bullets
            elif re_from_item.match(line):
                line = re_from_item.sub(r"  -", fix_tags(line))
            # is continuation line
            else:
                line = fix_tags(line)
                line = " " * 4 + line.lstrip()
        else:
            line = fix_tags(line)
        return line

    return _reformat_docstring(doc, format_fn, code_newline="\n")


def _from_docstring_rst(doc):
    """
    format from docstring to ReStructured Text
    """

    def format_fn(line, status):
        """ format function """

        if re_from_data.match(line):
            line = re_from_data.sub(r"**\1** ", line)
            status["add_line"] = True
        line = re_from_defaults.sub(r"*\1*", line)
        if status["listing"]:
            # parameters
            if re_from_param.match(line):
                m = re_from_param.match(line)
                line = "  - ``{}`` {}".format(m.group(1), m.group(3))
            # status items
            elif re_from_status.match(line):
                m = re_from_status.match(line)
                line = "  - ``{}`` {}".format(m.group(1), m.group(3))
            # bullets
            elif re_from_item.match(line):
                line = re_from_item.sub(r"  -", line)
            # is continuation line
            else:
                line = " " * 4 + line.lstrip()
        # in .rst format code samples use double backticks vs single ones for
        # .md This converts them.
        line = re_lone_backtick.sub("``", line)
        return line

    return _reformat_docstring(doc, format_fn, code_newline="\n")


def update_docstrings():
    """
    update the docstring of each module using info in the
    modules/README.md file
    """
    modules_dict = parse_readme()
    files = {}
    # update modules
    for mod in modules_dict:
        mod_file = modules_directory() / f"{mod}.py"
        with mod_file.open() as f:
            files[mod] = f.readlines()

    for mod, rows in files.items():
        replaced = False
        done = False
        lines = False
        out = []
        quotes = None
        for row in rows:
            # deal with single or double quoted docstring
            if not quotes:
                if row.strip().startswith('"""'):
                    quotes = '"""'
                if row.strip().startswith("'''"):
                    quotes = "'''"
            if quotes and row.strip().startswith(quotes) and not done:
                out.append(row)
                if not replaced:
                    out = out + [
                        "".join(_to_docstring(modules_dict[mod])).strip() + "\n"
                    ]
                    replaced = True
                if lines:
                    done = True
                if not done and not lines:
                    lines = True
                continue
            if not lines or done:
                out.append(row)
        mod_file = modules_directory() / f"{mod}.py"
        with mod_file.open("w") as f:
            f.writelines(out)
    print_stderr("Modules updated from README.md")


def check_docstrings(show_diff=False, config=None, mods=None):
    """
    Check docstrings in module match the README.md
    """

    readme = parse_readme()
    modules_readme = core_module_docstrings(config=config)
    warned = False
    if create_readme(readme) != create_readme(modules_readme):
        for module, lines in sorted(readme.items()):
            if mods and module not in mods:
                continue
            err = None
            if module not in modules_readme:
                err = f"Module {module} in README but not in /modules"
            elif "".join(lines).strip() != "".join(modules_readme[module]).strip():
                err = f"Module {module} docstring does not match README"
            if err:
                if not warned:
                    print_stderr("Documentation does not match!\n")
                    warned = True
                print_stderr(err)

        for module in modules_readme:
            if mods and module not in mods:
                continue
            if module not in readme:
                print_stderr(f"Module {module} in /modules but not in README")
        if show_diff:
            print_stderr(
                "\n".join(
                    difflib.unified_diff(
                        create_readme(readme).split("\n"),
                        create_readme(modules_readme).split("\n"),
                    )
                )
            )
        else:
            if warned:
                print_stderr("\nUse `py3-cmd docstring --diff` to view diff.")


def update_readme_for_modules(modules):
    """
    Update README.md updating the sections for the module names listed.
    """
    readme = parse_readme()
    module_docstrings = core_module_docstrings()
    if modules == ["__all__"]:
        modules = list(core_module_docstrings())
    for module in modules:
        if module in module_docstrings:
            print_stderr(f"Updating README.md for module {module}")
            readme[module] = module_docstrings[module]
        else:
            print_stderr(f"Module {module} not in core modules")

    # write the file
    readme_file = modules_directory() / "README.md"
    readme_file.write_text(create_readme(readme))


def show_modules(config, modules_list):
    """
    List modules available optionally with details.
    """
    details = config["full"]
    core_mods = not config["user"]
    user_mods = not config["core"]

    modules = core_module_docstrings(
        include_core=core_mods, include_user=user_mods, config=config
    )

    new_modules = []
    if modules_list:
        from fnmatch import fnmatch

        for _filter in modules_list:
            for name in modules:
                if fnmatch(name, _filter):
                    if name not in new_modules:
                        new_modules.append(name)
    else:
        new_modules = list(modules)

    for name in sorted(new_modules):
        module = _to_docstring(modules[name])
        desc = module[0][:-1]
        if details:
            dash_len = len(name) + 4
            print("#" * dash_len)
            print(f"# {name} #")
            print("#" * dash_len)
            for description in module:
                print(description[:-1])
        else:
            print(f"{name:<22} {desc}")
