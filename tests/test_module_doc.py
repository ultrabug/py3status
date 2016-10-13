"""
This tests module docstrings to ensure

* all the config options are documented

* correct default values are given

* config parameters listed in alphabetical order

Specific modules/config parameters are excluded but this should be discouraged.
"""

import re
from collections import OrderedDict

from py3status.docstrings import core_module_docstrings

IGNORE_MODULE = [
    # Cannot be imported due to missing libs
    'glpi',
    'mpd_status',
    'ns_checker',
    'rt',
    'scratchpad_counter',
]

IGNORE_ITEM = [
    ('screenshot', 'save_path'),  # home dir issue
    ('rate_counter', 'config_file'),  # home dir issue
    ('group', 'format'),  # dynamic depending on click_mode
    ('github', 'format'),  # dynamic
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


def check_docstrings():
    all_errors = []
    docstrings = core_module_docstrings()
    for module_name in sorted(docstrings.keys()):
        errors = []
        if module_name in IGNORE_MODULE:
            continue
        name = 'py3status.modules.{}'.format(module_name)
        try:
            py_mod = __import__(name)
            pass
        except ImportError as e:
            msg = 'Cannot import module `{}` {}'
            errors.append(msg.format(module_name, e))
            continue
        except Exception as e:
            msg = 'Cannot import module `{}` {}'
            errors.append(msg.format(module_name, e))
            continue

        try:
            py_mod = __import__(name)
            py3_mod = getattr(py_mod.modules, module_name).Py3status
        except AttributeError as e:
            msg = 'Module `{}` pas no Py3status class'
            errors.append(msg.format(module_name))
            continue
        mod_config = OrderedDict()
        for attribute_name in sorted(dir(py3_mod)):
            if attribute_name.startswith('_'):
                continue
            attribute = getattr(py3_mod, attribute_name)
            if repr(attribute).startswith('<'):
                continue
            if isinstance(attribute, str):
                try:
                    attribute = attribute.decode('utf-8')
                except AttributeError:
                    # python3
                    pass
            mod_config[attribute_name] = attribute
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
        for error in errors:
            print(error)
        assert(False)
