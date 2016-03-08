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


def core_module_docstrings():
    '''
    Get docstrings for all core modules
    returns a dict of {<module_name>: <docstring>}
    '''
    docstrings = {}
    for file in os.listdir(modules_directory()):
        if file.endswith(".py"):
            name = file.split('.')[0]
            if name != '__init__':
                with open(os.path.join(modules_directory(), file)) as f:
                    module = ast.parse(f.read())
                    docstring = ast.get_docstring(module)
                    docstring = ['{}\n'.format(d) for d in str(docstring).strip().split('\n')]
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
        out.append('\n[{name}](#{name})  {desc}\n'.format(name=module, desc=desc))
    # details
    for module in sorted(data.keys()):
        out.append('\n---\n\n### <a name="{name}"></a>{name}\n\n{details}\n'.format(name=module, details=''.join(data[module]).strip()))
    return ''.join(out)


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
                    out = out + modules_dict[mod]
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


def check_docstrings(show_diff=False):
    readme = parse_readme()
    modules_readme = core_module_docstrings()
    if (create_readme(readme) != create_readme(modules_readme)):
        print_stderr('Documentation does not match!\n')
        for module in readme:
            if module not in modules_readme:
                print_stderr('\tModule {} in README but not in /modules'.format(module))
            elif ''.join(readme[module]).strip() != ''.join(modules_readme[module]).strip():
                print_stderr('\tModule {} docstring does not match README'.format(module))

        for module in modules_readme:
            if module not in readme:
                print_stderr('\tModule {} in /modules but not in README'.format(module))
        if show_diff:
            print_stderr('\n'.join(difflib.unified_diff(readme.split('\n'), modules_readme.split('\n'))))
        else:
            print_stderr('\nUse `py3satus docstring check diff` to view diff.')


def update_readme_for_modules(modules):
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
