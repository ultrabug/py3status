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

IGNORE_MODULE = [
]

# Ignored items will not have their default values checked or be included for
# alphabetical order purposes
IGNORE_ITEM = [
    ('screenshot', 'save_path'),  # home dir issue
    ('rate_counter', 'config_file'),  # home dir issue
    ('group', 'format'),  # dynamic depending on click_mode
    ('github', 'format'),  # dynamic
    ('kdeconnector', '_dev'),  # move to __init__ etc
    ('arch_updates', '_format_pacman_and_aur'),  # need moving into __init__ etc
    ('arch_updates', '_format_pacman_only'),  # need moving into __init__ etc
    ('arch_updates', '_line_separator'),  # need moving into __init__ etc
    ('arch_updates', 'format'),  # dynamic
]

# Obsolete parameters will not have alphabetical order checked
OBSELETE_PARAM = [
    ('battery_level', 'mode'),
    ('battery_level', 'show_percent_with_blocks'),
]

RE_PARAM = re.compile(
    '^  - `(?P<name>[^`]*)`.*?('
    '\*\(default (?P<value>('
    '("[^"]*")'  # double quote strings
    '|'
    "('[^']*')"  # quote strings
    '|'
    '([^)]*)'  # anything else
    '))\)\*)?$'
)

AST_LITERAL_TYPES = {
    'Num': 'n',
    'Str': 's',
    'NameConstant': 'value',
}

MODULE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                           '..', 'py3status', 'modules')


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
            if part == '\n':
                break
            if part.startswith('  - '):
                lines.append(part[:-1])
                continue
            lines[-1] += part[:-1]

        for line in lines:
            match = RE_PARAM.match(line)
            if match:
                if match.group('value'):
                    try:
                        value = eval(match.group('value'))
                        if isinstance(value, str):
                            try:
                                value = value.decode('utf-8')
                            except AttributeError:
                                # python3
                                pass
                        try:
                            value = value.replace('&amp;', '&')
                            value = value.replace('&lt;', '<')
                            value = value.replace('&gt;', '>')
                        except AttributeError:
                            pass
                        # wrap in tuple to distinguish None from missing
                        value = (value, )
                    except (SyntaxError, NameError):
                        value = '?Unknown?'
                else:
                    value = None
                params[match.group('name')] = value
        return params

    params = find_params(find_line('Configuration parameters:\n'))
    obsolete = find_params(find_line('Obsolete configuration parameters:\n'))
    return params, obsolete


def get_module_attributes(path):
    '''
    Get the attributes from the module from the ast.  We use ast because this
    way we can examine modules even if we do not have their required python
    modules installed.
    '''
    names = {}
    attributes = OrderedDict()
    python2_names = {
        'True': True,
        'False': False,
        'None': None,
    }

    def get_values(source, dest, extra=None):
        '''
        Get a list of the configuration parameters and their defaults.
        '''

        def get_value(value):
            '''
            Get the actual value from the ast allowing recursion
            '''
            class_name = value.__class__.__name__
            # if this is a literal then get its value
            value_type = AST_LITERAL_TYPES.get(class_name)
            if value_type:
                attr_value = getattr(value, value_type)
            else:
                if class_name == 'Dict':
                    attr_value = dict(zip(
                        list(map(get_value, value.keys)),
                        list(map(get_value, value.values))
                    ))
                elif class_name == 'List':
                    attr_value = list(map(get_value, value.elts))
                elif class_name == 'Name':
                    # in python 2 True, False, None are Names rather than
                    # NameConstant so we use them for the default
                    default = python2_names.get(value.id)
                    attr_value = extra.get(value.id, default)
                elif class_name == 'UnaryOp':
                    op = value.op.__class__.__name__
                    attr_value = get_value(value.operand)
                    # we only understand negation
                    if op == 'USub':
                        attr_value = -attr_value
                    else:
                        attr_value = 'UNKNOWN %s UnaryOp %s' % (class_name, op)
                elif class_name == 'BinOp':
                    left = get_value(value.left)
                    right = get_value(value.right)
                    op = value.op.__class__.__name__
                    try:
                        if op == 'Add':
                            attr_value = left + right
                        elif op == 'Mult':
                            attr_value = left * right
                        else:
                            attr_value = 'UNKNOWN %s BinOp %s' % (class_name,
                                                                  op)
                    except:
                        attr_value = 'UNKNOWN %s BinOp error' % class_name
                else:
                    attr_value = 'UNKNOWN %s' % class_name
            return attr_value

        if extra is None:
            extra = {}

        for line in source:
            if isinstance(line, ast.Assign):
                if (len(line.targets) == 1 and
                        isinstance(line.targets[0], ast.Name)):
                    attr = line.targets[0].id
                    value = line.value
                    dest[attr] = get_value(value)

    with open(path) as f:
        tree = ast.parse(f.read(), '')
        # some modules have constants defined we need to find these
        get_values(tree.body, names)
        for statement in tree.body:
            # look for the Py3status class and find it's attributes
            if (isinstance(statement, ast.ClassDef) and
                    statement.name == 'Py3status'):
                get_values(statement.body, attributes, names)
    return attributes


def check_docstrings():
    all_errors = []
    docstrings = core_module_docstrings()
    for module_name in sorted(docstrings.keys()):
        errors = []
        if module_name in IGNORE_MODULE:
            continue

        path = os.path.join(MODULE_PATH, '%s.py' % module_name)
        mod_config = get_module_attributes(path)

        params, obsolete = docstring_params(docstrings[module_name])

        if list(params.keys()) != list(sorted(params.keys())):
            keys = list(sorted(params.keys()))
            msg = 'config params not in alphabetical order should be\n{keys}'
            errors.append(msg.format(keys=keys))
        if list(obsolete.keys()) != list(sorted(obsolete.keys())):
            keys = list(sorted(obsolete.keys()))
            msg = 'obsolete params not in alphabetical order should be\n{keys}'
            errors.append(msg.format(keys=keys))

        # combine docstring parameters
        params.update(obsolete)

        # check attributes are in alphabetical order
        keys = list(mod_config.keys())
        for item in IGNORE_ITEM:
            if item[0] == module_name and item[1] in keys:
                keys.remove(item[1])
        for item in OBSELETE_PARAM:
            if item[0] == module_name and item[1] in keys:
                keys.remove(item[1])
        if keys != sorted(keys):
            errors.append('Attributes not in alphabetical order, should be')
            errors.append(sorted(mod_config.keys()))

        for param in sorted(mod_config.keys()):
            if (module_name, param) in IGNORE_ITEM:
                continue
            default = mod_config[param]
            if param not in params:
                msg = '{}: (default {!r}) not in module docstring'
                errors.append(msg.format(param, default))
                continue
            default_doc = params[param]
            if default_doc is None:
                msg = '`{}` default not in docstring add (default {!r})'
                errors.append(msg.format(param, default))
                del params[param]
                continue
            if default_doc[0] != default:
                msg = '`{}` (default {!r}) does not match docstring {!r}'
                errors.append(msg.format(param, default, default_doc[0]))
                del params[param]
                continue
            del params[param]

        for param in params:
            if (module_name, param) in IGNORE_ITEM:
                continue
            errors.append('{} in module docstring but not module'.format(param))
        if errors:
            all_errors += ['=' * 30, module_name, '=' * 30] + errors + ['\n']
    return all_errors


def test_docstrings():
    errors = check_docstrings()
    if errors:
        print('Docstring error(s) detected!\n\n')
        print('The tests may give incorrect errors for some configuration '
              'parameters that the tests do not understand. '
              'Such parameters can be excluded from the test by adding them '
              'to the IGNORE_ITEM list in tests/test_module_doc.py\n\n')
        for error in errors:
            print(error)
        assert(False)
