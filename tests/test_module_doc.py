"""
This tests module docstrings to ensure

* all the config options are documented

* correct default values are given

* config parameters listed in alphabetical order

Specific modules/config parameters are excluded but this should be discouraged.
"""

import ast
import os.path
import re

from collections import OrderedDict

from py3status.docstrings import core_module_docstrings

IGNORE_MODULE = []

ILLEGAL_CONFIG_OPTIONS = ["min_width", "separator", "separator_block_width", "align"]

IGNORE_ILLEGAL_CONFIG_OPTIONS = [("group", "align")]

# Ignored items will not have their default values checked or be included for
# alphabetical order purposes
IGNORE_ITEM = []

# Obsolete parameters will not have alphabetical order checked
OBSOLETE_PARAM = []

RE_PARAM = re.compile(r"^  - `(?P<name>[^`]*)`.*?(\*\(default (?P<value>(.*))\)\*)?$")

AST_LITERAL_TYPES = {"Num": "n", "Str": "s", "NameConstant": "value"}

MODULE_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "py3status", "modules"
)


def docstring_params(docstring):
    """
    Crudely parse the docstring and get parameters and their defaults
    """

    def find_line(text):
        for index, line in enumerate(docstring):
            if line == text:
                return index + 1

    def find_params(start):
        """
        find documented parameters and add them to params dict
        """
        params = OrderedDict()
        if start is None:
            return params
        lines = []
        for part in docstring[start:]:
            if part == "\n":
                break
            if part.startswith("  - "):
                lines.append(part[:-1])
                continue
            lines[-1] += part[:-1]

        for line in lines:
            match = RE_PARAM.match(line)
            if match:
                if match.group("value"):
                    try:
                        value = eval(match.group("value"))
                        if isinstance(value, str):
                            try:
                                value = value.decode("utf-8")
                            except AttributeError:
                                # python3
                                pass
                        try:
                            value = value.replace("&amp;", "&")
                            value = value.replace("&lt;", "<")
                            value = value.replace("&gt;", ">")
                        except AttributeError:
                            pass
                        # wrap in tuple to distinguish None from missing
                        value = (value,)
                    except (SyntaxError, NameError):
                        value = "?Unknown?"
                else:
                    value = None
                params[match.group("name")] = value
        return params

    params = find_params(find_line("Configuration parameters:\n"))
    obsolete = find_params(find_line("Obsolete configuration parameters:\n"))
    return params, obsolete


def get_module_attributes(path):
    """
    Get the attributes from the module from the ast.  We use ast because this
    way we can examine modules even if we do not have their required python
    modules installed.
    """
    names = {}
    attributes = OrderedDict()
    python2_names = {"True": True, "False": False, "None": None}

    def get_values(source, dest, extra=None):
        """
        Get a list of the configuration parameters and their defaults.
        """

        def get_value(value):
            """
            Get the actual value from the ast allowing recursion
            """
            class_name = value.__class__.__name__
            # if this is a literal then get its value
            value_type = AST_LITERAL_TYPES.get(class_name)
            if value_type:
                attr_value = getattr(value, value_type)
            else:
                if class_name == "Dict":
                    attr_value = dict(
                        zip(
                            list(map(get_value, value.keys)),
                            list(map(get_value, value.values)),
                        )
                    )
                elif class_name == "List":
                    attr_value = list(map(get_value, value.elts))
                elif class_name == "Name":
                    # in python 2 True, False, None are Names rather than
                    # NameConstant so we use them for the default
                    default = python2_names.get(value.id)
                    attr_value = extra.get(value.id, default)
                elif class_name == "Tuple":
                    attr_value = tuple(map(get_value, value.elts))
                elif class_name == "UnaryOp":
                    op = value.op.__class__.__name__
                    attr_value = get_value(value.operand)
                    # we only understand negation
                    if op == "USub":
                        attr_value = -attr_value
                    else:
                        attr_value = "UNKNOWN %s UnaryOp %s" % (class_name, op)
                elif class_name == "BinOp":
                    left = get_value(value.left)
                    right = get_value(value.right)
                    op = value.op.__class__.__name__
                    try:
                        if op == "Add":
                            attr_value = left + right
                        elif op == "Mult":
                            attr_value = left * right
                        else:
                            attr_value = "UNKNOWN %s BinOp %s" % (class_name, op)
                    except Exception:
                        attr_value = "UNKNOWN %s BinOp error" % class_name
                else:
                    attr_value = "UNKNOWN %s" % class_name
            return attr_value

        if extra is None:
            extra = {}

        for line in source:
            if isinstance(line, ast.Assign):
                if len(line.targets) == 1 and isinstance(line.targets[0], ast.Name):
                    attr = line.targets[0].id
                    value = line.value
                    dest[attr] = get_value(value)

    with open(path) as f:
        tree = ast.parse(f.read(), "")
        # some modules have constants defined we need to find these
        get_values(tree.body, names)
        for statement in tree.body:
            # look for the Py3status class and find it's attributes
            if isinstance(statement, ast.ClassDef) and statement.name == "Py3status":
                get_values(statement.body, attributes, names)
    return attributes


def _gen_diff(source, target, source_label="Source", target_label="Target"):
    # Create a unique object for determining if the list is missing an entry
    blank = object()

    # Make both lists the same length
    max_len = max(len(source), len(target))
    for lst in (source, target):
        lst.extend([blank for i in range(max_len - len(lst))])

    # Determine the length of the longest item in the list
    max_elem_len = max([len(str(elem)) for elem in source])
    padding = "    "
    format_str = padding + ("%%%ds %%s %%s" % max_elem_len)

    # Set up initial output contents
    middle_orig = "  "
    out = [
        format_str % (source_label, middle_orig, target_label),
        # Length of dashes is enough for the longest element on both sides,
        # plus the size of the middle symbol(s), plus two spaces for separation
        padding + ("-" * (2 * max_elem_len + len(middle_orig) + 2)),
    ]

    for (have, want) in zip(source, target):
        # Determine the mark
        middle = middle_orig

        # The current version is missing this line
        if have == blank:
            middle = "<<"
            have = ""

        # The target version is missing this line
        elif want == blank:
            middle = ">>"
            want = ""

        # Both lines exist, but are different
        elif have != want:
            middle = "!!"

        # Place the diff into the output
        out.append(format_str % (str(have), middle, str(want)))

    return "\n".join(out) + "\n"


def check_docstrings():
    all_errors = []
    docstrings = core_module_docstrings()
    for module_name in sorted(docstrings.keys()):
        errors = []
        if module_name in IGNORE_MODULE:
            continue

        path = os.path.join(MODULE_PATH, "%s.py" % module_name)
        mod_config = get_module_attributes(path)

        params, obsolete = docstring_params(docstrings[module_name])

        if list(params.keys()) != list(sorted(params.keys())):
            keys = list(params.keys())
            msg = "config params not in alphabetical order should be\n{keys}"
            errors.append(msg.format(keys=_gen_diff(keys, sorted(keys))))
        if list(obsolete.keys()) != list(sorted(obsolete.keys())):
            keys = list(obsolete.keys())
            msg = "obsolete params not in alphabetical order should be\n{keys}"
            errors.append(msg.format(keys=_gen_diff(keys, sorted(keys))))

        # combine docstring parameters
        params.update(obsolete)

        # bad config params - these have reserved usage
        allowed_bad_config_params = [
            x[1] for x in IGNORE_ILLEGAL_CONFIG_OPTIONS if x[0] == module_name
        ]
        bad_config_params = set(ILLEGAL_CONFIG_OPTIONS) & set(params)
        bad_config_params -= set(allowed_bad_config_params)

        if bad_config_params:
            msg = "The following config parameters are reserved and"
            msg += "should not be used by modules:\n    {}"
            errors.append(msg.format(", ".join(bad_config_params)))

        # check attributes are in alphabetical order
        keys = list(mod_config.keys())
        for item in IGNORE_ITEM:
            if item[0] == module_name and item[1] in keys:
                keys.remove(item[1])
        for item in OBSOLETE_PARAM:
            if item[0] == module_name and item[1] in keys:
                keys.remove(item[1])
        if keys != sorted(keys):
            errors.append("Attributes not in alphabetical order, should be")
            errors.append(_gen_diff(keys, sorted(keys)))

        for param in sorted(mod_config.keys()):
            if (module_name, param) in IGNORE_ITEM:
                continue
            default = mod_config[param]
            if param not in params:
                msg = "{}: (default {!r}) not in module docstring"
                errors.append(msg.format(param, default))
                continue
            default_doc = params[param]
            if default_doc is None:
                msg = "`{}` default not in docstring add (default {!r})"
                errors.append(msg.format(param, default))
                del params[param]
                continue
            if default_doc[0] != default:
                msg = "`{}` (default {!r}) does not match docstring {!r}"
                errors.append(msg.format(param, default, default_doc[0]))
                del params[param]
                continue
            del params[param]

        for param in params:
            if (module_name, param) in IGNORE_ITEM:
                continue
            errors.append("{} in module docstring but not module".format(param))
        if errors:
            all_errors += ["=" * 30, module_name, "=" * 30] + errors + ["\n"]
    return all_errors


def test_docstrings():
    errors = check_docstrings()
    if errors:
        print("Docstring error(s) detected!\n\n")
        print(
            "The tests may give incorrect errors for some configuration "
            "parameters that the tests do not understand. "
            "Such parameters can be excluded from the test by adding them "
            "to the IGNORE_ITEM list in tests/test_module_doc.py\n\n"
        )
        for error in errors:
            print(error)
        assert False
