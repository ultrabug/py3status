# -*- coding: utf-8 -*-
import ast
import re
import os.path
import difflib

from py3status.helpers import print_stderr


def modules_directory():
    '''
    Get the core modules directory.
    '''
    return os.path.join(os.path.dirname(os.path.abspath(__file__)), 'modules')


def parse_readme():
    '''
    Crude parsing of modules/README.md
    returns a dict of {<module_name>: <documentation>}
    '''
    name = None
    re_mod = re.compile('^\#\#\# <a name="(?P<name>[a-z_0-9]+)"></a>')
    readme_file = os.path.join(modules_directory(), 'README.md')
    modules_dict = {}
    with open(readme_file) as f:
        for row in f.readlines():
            match = re_mod.match(row)
            if match:
                name = match.group('name')
                modules_dict[name] = []
                continue
            if row.startswith('---'):
                name = None
                continue
            if name:
                modules_dict[name].append(row)
    return modules_dict


def core_module_docstrings(include_core=True, include_user=False, config=None):
    '''
    Get docstrings for all core modules and user ones if requested
    returns a dict of {<module_name>: <docstring>}
    '''
    paths = {}
    docstrings = {}
    if include_core:
        for file in os.listdir(modules_directory()):
            if file.endswith(".py"):
                name = file[:-3]
                if name != '__init__':
                    paths[name] = (os.path.join(modules_directory(), file),
                                   'core')

    if include_user:
        # include user modules
        for include_path in sorted(config['include_paths']):
            include_path = os.path.abspath(include_path) + '/'
            if not os.path.isdir(include_path):
                continue
            for file in sorted(os.listdir(include_path)):
                if not file.endswith('.py'):
                    continue
                name = file[:-3]
                paths[name] = (os.path.join(include_path, file), 'user')
    for name in paths:
        path, module_type = paths[name]
        with open(path) as f:
            module = ast.parse(f.read())
            docstring = ast.get_docstring(module)
            docstring = [
                '{}\n'.format(d)
                for d in from_docstring(str(docstring).strip().split('\n'))
            ]
            docstrings[name] = docstring + ['\n']
    return docstrings


def create_readme(data):
    '''
    Create README.md text for the given module data.
    '''
    out = ['<a name="top"></a>Modules\n========\n\n']
    # Links
    for module in sorted(data.keys()):
        desc = ''.join(data[module]).strip().split('\n')[0]
        out.append('\n**[{name}](#{name})** — {desc}\n'.format(name=module,
                                                               desc=desc))
    # details
    for module in sorted(data.keys()):
        out.append(
            '\n---\n\n### <a name="{name}"></a>{name}\n\n{details}\n'.format(
                name=module,
                details=''.join(data[module]).strip()))
    return ''.join(out)


def to_docstring(doc):
    re_param = re.compile('^  - `([a-zA-Z0-9_{}]+)` ')
    out = []
    for line in doc:
        out.append(re_param.sub('    \\1 - ', line))
    return out


def from_docstring(doc):
    re_param = re.compile('^    ([a-zA-Z0-9_{}]+) - ')
    out = []
    for line in doc:
        out.append(re_param.sub('  - `\\1` ', line))
    return out


def update_docstrings():
    '''
    update the docstring of each module using info in the
    modules/README.md file
    '''
    modules_dict = parse_readme()
    files = {}
    # update modules
    for mod in modules_dict:
        mod_file = os.path.join(modules_directory(), mod + '.py')
        with open(mod_file) as f:
            files[mod] = f.readlines()

    for mod in files:
        replaced = False
        done = False
        lines = False
        out = []
        for row in files[mod]:
            if row.strip().startswith('"""') and not done:
                out.append(row)
                if not replaced:
                    out = out + [
                        ''.join(to_docstring(modules_dict[mod])).strip() + '\n'
                    ]
                    replaced = True
                if lines:
                    done = True
                if not done and not lines:
                    lines = True
                continue
            if not lines or done:
                out.append(row)
        mod_file = os.path.join(modules_directory(), mod + '.py')
        with open(mod_file, 'w') as f:
            f.writelines(out)
    print_stderr('Modules updated from README.md')


def check_docstrings(show_diff=False, config=None):
    '''
    Check docstrings in module match the README.md
    '''

    readme = parse_readme()
    modules_readme = core_module_docstrings(config=config)
    if (create_readme(readme) != create_readme(modules_readme)):
        print_stderr('Documentation does not match!\n')
        for module in readme:
            if module not in modules_readme:
                print_stderr(
                    '\tModule {} in README but not in /modules'.format(module))
            elif ''.join(readme[module]).strip() != ''.join(modules_readme[
                    module]).strip():
                print_stderr(
                    '\tModule {} docstring does not match README'.format(
                        module))

        for module in modules_readme:
            if module not in readme:
                print_stderr(
                    '\tModule {} in /modules but not in README'.format(module))
        if show_diff:
            print_stderr('\n'.join(difflib.unified_diff(
                create_readme(readme).split('\n'), create_readme(
                    modules_readme).split('\n'))))
        else:
            print_stderr('\nUse `py3satus docstring check diff` to view diff.')


def update_readme_for_modules(modules):
    '''
    Update README.md updating the sections for the module names listed.
    '''
    readme = parse_readme()
    module_docstrings = core_module_docstrings()
    for module in modules:
        if module in module_docstrings:
            print_stderr('Updating README.md for module {}'.format(module))
            readme[module] = module_docstrings[module]
        else:
            print_stderr('Module {} not in core modules'.format(module))

    # write the file
    readme_file = os.path.join(modules_directory(), 'README.md')
    with open(readme_file, 'w') as f:
        f.write(create_readme(readme))


def show_modules(config, params):
    '''
    List modules available optionally with details.
    '''
    details = params[0] == 'details'
    if details:
        modules_list = params[1:]
        core_mods = True
        user_mods = True
    else:
        user_mods = True
        core_mods = True
        modules_list = []
        if len(params) == 2:
            if params[1] == 'user':
                user_mods = True
                core_mods = False
            elif params[1] == 'core':
                user_mods = False
                core_mods = True
    if details:
        print_stderr('Module details:')
    else:
        print_stderr('Available modules:')
    modules = core_module_docstrings(include_core=core_mods,
                                     include_user=user_mods,
                                     config=config)
    for name in sorted(modules.keys()):
        if modules_list and name not in modules_list:
            continue
        module = to_docstring(modules[name])
        desc = module[0][:-1]
        if details:
            dash_len = len(name)
            print_stderr('=' * dash_len)
            print_stderr(name)
            print_stderr('=' * dash_len)
            for description in module:
                print_stderr(description[:-1])
        else:
            print_stderr('  %-22s %s' % (name, desc))
