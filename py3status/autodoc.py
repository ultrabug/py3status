# -*- coding: utf-8 -*-

import ast
import inspect
import os.path
import re

from docutils import nodes
from docutils.parsers.rst import Directive
from pygments.lexer import RegexLexer, bygroups
import pygments.token as pygments_token

from py3status.docstrings import core_module_docstrings
from py3status.screenshots import create_screenshots, get_samples, process
from py3status.py3 import Py3


# some Py3 methods have constants as defaults we need to identify them here
CONSTANT_PARAMS = [("log", "level"), ("notify_user", "level")]


class Py3statusLexer(RegexLexer):
    """
    A simple lexer for py3status configuration files.
    This helps make the documentation more beautiful
    """

    name = "Py3status"
    aliases = ["py3status"]
    filenames = ["*.conf"]

    tokens = {
        "root": [
            (r"#.*?$", pygments_token.Comment),  # comments
            (  # double quoted strings
                r'"(?:[^"\\]|\\.)*"',
                pygments_token.String.Double,
            ),
            (  # single quoted strings
                r"'(?:[^'\\]|\\.)*'",
                pygments_token.String.Single,
            ),
            (r"([0-9]+)|([0-9]*)\.([0-9]*)", pygments_token.Number),  # numbers
            (r"[Tt]rue|[Ff]alse|[Nn]one", pygments_token.Literal),  # True, False & None
            (r"(\+=)|=", pygments_token.Operator),  # = and +=
            (r"[{}\[\](),:]", pygments_token.Punctuation),  # other things like (){}[],:
            (  # config functions eg env(value, type)
                r"(\S+)([(])(([^)\\]|\\.)*)((\s*,\s*)(\w+))?([)])",
                bygroups(
                    pygments_token.Name.Function,
                    pygments_token.Punctuation,
                    pygments_token.Literal,
                    None,
                    None,
                    pygments_token.Punctuation,
                    pygments_token.Keyword.Type,
                    pygments_token.Punctuation,
                ),
            ),
            (  # module names
                r"(\S+)(\s*)([^=]*)(\s*)(\{)",
                bygroups(
                    pygments_token.Keyword.Reserved,
                    pygments_token.Whitespace,
                    pygments_token.Keyword.Reserved,
                    pygments_token.Whitespace,
                    pygments_token.Punctuation,
                ),
            ),
            (  # order += ....
                r"^(order)(\s+)(\+=)",
                bygroups(
                    pygments_token.Keyword.Reserved,
                    pygments_token.Whitespace,
                    pygments_token.Punctuation,
                ),
            ),
            (r"on_click\s*\d", pygments_token.Name.Variable),  # on_click x
            (  # module parameters
                r"(\w+)((:)(\S+))?",
                bygroups(
                    pygments_token.Name.Variable,
                    None,
                    pygments_token.Punctuation,
                    pygments_token.Keyword.Type,
                ),
            ),
            (r"\s+", pygments_token.Whitespace),  # whitespace
        ]
    }


def markdown_2_rst(lines):
    """
    Convert markdown to restructured text
    """
    out = []
    code = False
    for line in lines:
        # code blocks
        if line.strip() == "```":
            code = not code
            space = " " * (len(line.rstrip()) - 3)
            if code:
                out.append("\n\n%s.. code-block:: none\n\n" % space)
            else:
                out.append("\n")
        else:
            if code and line.strip():
                line = "    " + line
            else:
                # escape any backslashes
                line = line.replace("\\", "\\\\")
            out.append(line)
    return out


def file_sort(my_list):
    """
    Sort a list of files in a nice way.
    eg item-10 will be after item-9
    """

    def alphanum_key(key):
        """
        Split the key into str/int parts
        """
        return [int(s) if s.isdigit() else s for s in re.split("([0-9]+)", key)]

    my_list.sort(key=alphanum_key)
    return my_list


def screenshots(screenshots_data, module_name):
    """
    Create .rst output for any screenshots a module may have.
    """
    shots = screenshots_data.get(module_name)
    if not shots:
        return ""

    out = []
    for shot in file_sort(shots):
        if not os.path.exists("../doc/screenshots/%s.png" % shot):
            continue
        out.append(u"\n.. image:: screenshots/{}.png\n\n".format(shot))
    return u"".join(out)


def create_module_docs():
    """
    Create documentation for modules.
    """
    data = core_module_docstrings(format="rst")
    # get screenshot data
    screenshots_data = {}
    samples = get_samples()
    for sample in samples.keys():
        module = sample.split("-")[0]
        if module not in screenshots_data:
            screenshots_data[module] = []
        screenshots_data[module].append(sample)

    out = []
    # details
    for module in sorted(data.keys()):
        out.append("\n.. _module_%s:\n" % module)  # reference for linking
        out.append(
            "\n{name}\n{underline}\n\n{screenshots}{details}\n".format(
                name=module,
                screenshots=screenshots(screenshots_data, module),
                underline="-" * len(module),
                details="".join(markdown_2_rst(data[module])).strip(),
            )
        )
    # write include file
    with open("../doc/modules-info.inc", "w") as f:
        f.write("".join(out))


def get_variable_docstrings(filename):
    """
    Go through the file and find all documented variables.
    That is ones that have a literal expression following them.

    Also get a dict of assigned values so that we can substitute constants.
    """

    def walk_node(parent, values=None, prefix=""):
        """
        walk the ast searching for docstrings/values
        """
        docstrings = {}
        if values is None:
            values = {}
        key = None
        for node in ast.iter_child_nodes(parent):
            if isinstance(node, ast.ClassDef):
                # We are in a class so walk the class
                docs = walk_node(node, values, prefix + node.name + ".")[0]
                docstrings[node.name] = docs
            elif isinstance(node, ast.Assign):
                key = node.targets[0].id
                if isinstance(node.value, ast.Num):
                    values[key] = node.value.n
                if isinstance(node.value, ast.Str):
                    values[key] = node.value.s
                if isinstance(node.value, ast.Name):
                    if node.value.id in values:
                        values[prefix + key] = values[node.value.id]
            elif isinstance(node, ast.Expr) and key:
                docstrings[key] = node.value.s
            else:
                key = None
        return docstrings, values

    with open(filename, "r") as f:
        source = f.read()
    return walk_node(ast.parse(source))


def get_py3_info():
    """
    Inspect Py3 class and get constants, exceptions, methods
    along with their docstrings.
    """
    # get all documented constants and their values
    constants, values = get_variable_docstrings("../py3status/py3.py")
    # we only care about ones defined in Py3
    constants = constants["Py3"]
    # sort them alphabetically
    constants = [(k, v) for k, v in sorted(constants.items())]

    # filter values as we only care about values defined in Py3
    values = dict([(v, k[4:]) for k, v in values.items() if k.startswith("Py3.")])

    def make_value(attr, arg, default):
        """
        If the methods parameter is defined as a constant then do a
        replacement.  Otherwise return the values representation.
        """
        if (attr, arg) in CONSTANT_PARAMS and default in values:
            return values[default]
        return repr(default)

    # inspect Py3 to find it's methods etc
    py3 = Py3()
    # no private ones
    attrs = [x for x in dir(py3) if not x.startswith("_")]
    exceptions = []
    methods = []
    for attr in attrs:
        item = getattr(py3, attr)
        if "method" in str(item):
            # a method so we need to get the call parameters
            args, vargs, kw, defaults = inspect.getargspec(item)
            args = args[1:]
            len_defaults = len(defaults) if defaults else 0
            len_args = len(args)

            sig = []
            for index, arg in enumerate(args):
                # default values set?
                if len_args - index <= len_defaults:
                    default = defaults[len_defaults - len_args + index]
                    sig.append("%s=%s" % (arg, make_value(attr, arg, default)))
                else:
                    sig.append(arg)

            definition = "%s(%s)" % (attr, ", ".join(sig))
            methods.append((definition, item.__doc__))
            continue
        try:
            # find any exceptions
            if isinstance(item(), Exception):
                exceptions.append((attr, item.__doc__))
                continue
        except:  # noqa e722
            pass
    return {"methods": methods, "exceptions": exceptions, "constants": constants}


def auto_undent(string):
    """
    Unindent a docstring.
    """
    lines = string.splitlines()
    while lines[0].strip() == "":
        lines = lines[1:]
        if not lines:
            return []
    spaces = len(lines[0]) - len(lines[0].lstrip(" "))
    out = []
    for line in lines:
        num_spaces = len(line) - len(line.lstrip(" "))
        out.append(line[min(spaces, num_spaces) :])
    return out


def create_py3_docs():
    """
    Create the include files for py3 documentation.
    """
    # we want the correct .rst 'type' for our data
    trans = {"methods": "function", "exceptions": "exception", "constants": "attribute"}
    data = get_py3_info()
    for k, v in data.items():
        output = []
        for name, desc in v:
            output.append("")
            output.append(".. _%s:" % name)  # reference for linking
            output.append("")
            output.append(".. py:%s:: %s" % (trans[k], name))
            output.append("")
            output.extend(auto_undent(desc))
        with open("../doc/py3-%s-info.inc" % k, "w") as f:
            f.write("\n".join(output))


def create_auto_documentation():
    """
    Create any include files needed for sphinx documentation
    """
    create_screenshots()

    create_module_docs()
    create_py3_docs()


class ScreenshotDirective(Directive):
    """
    Adds the ability to add screenshots dynamically in sphinx documentation

    .. screenshot::

        {'color': '#00FF00', 'full_text': 'Example output'}

    """

    has_content = True

    def run(self):
        env = self.state.document.settings.env

        targetid = "screenshot-%d" % env.new_serialno("screenshot")
        targetnode = nodes.target("", "", ids=[targetid])

        image_name = "_%s" % targetid
        try:
            content = ast.literal_eval("\n".join(self.content))
        except:  # noqa e722
            content = {
                "color": "#990000",
                "background": "#FFFF00",
                "full_text": " IMAGE DATA ERROR ",
            }

        process(image_name, content, False)
        image_path = os.path.join("screenshots", image_name + ".png")
        screenshot_node = nodes.image(uri=image_path)
        return [targetnode, screenshot_node]


if __name__ == "__main__":
    create_auto_documentation()
