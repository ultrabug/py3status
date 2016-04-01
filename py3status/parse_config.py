# -*- coding: utf-8 -*-
import codecs
import re
import glob
import os
import sys
import imp
from collections import OrderedDict
from string import Template
from subprocess import check_output

MAX_NESTING_LEVELS = 4

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
TZTIME_FORMAT = '%Y-%m-%d %H:%M:%S %Z'
TIME_MODULES = ['time', 'tztime']

I3STATUS_MODULES = [
    'battery', 'cpu_temperature', 'disk', 'ethernet', 'path_exists',
    'run_watch', 'tztime', 'volume', 'wireless'
]
I3S_SINGLE_NAMES = ['cpu_usage', 'ddate', 'ipv6', 'load', 'time']
ERROR_CONFIG = '''
general {colors = true interval = 60}

order += "static_string py3status"
order += "tztime local"
order += "group error"

static_string py3status {format = "py3status"}
tztime local {format = "%c"}
group error{
    button_next = 1
    button_prev = 0
    fixed_width = False
    format = "{output}"
    static_string error_min {format = "CONFIG ERROR" color = "#FF0000"}
    static_string error {format = "$error" color = "#FF0000"}
}
'''

GENERAL_DEFAULTS = {
    'color_bad': '#FF0000',
    'color_degraded': '#FFFF00',
    'color_good': '#00FF00',
    'color_separator': '#333333',
}


class ParseException(Exception):
    def __init__(self, error, line, line_no, position, token):
        self.error = error
        self.line = line
        self.line_no = line_no
        self.position = position
        self.token = token

    def one_line(self):
        return 'CONFIG ERROR: {} saw `{}` at line {} position {}'.format(
            self.error, self.token, self.line_no, self.position)

    def __str__(self):
        marker = ' ' * (self.position - 1) + '^'
        return '{}\n\nsaw `{}` at line {} position {}\n\n{}\n{}'.format(
            self.error, self.token, self.line_no, self.position, self.line,
            marker)


class ModuleDefinition(OrderedDict):
    '''Module definition in dict form'''
    pass


class ConfigParser:

    TOKENS = [
        '#.*$'  # comments
        '|(?P<operator>[()[\]{},:]|\+?=)'  # operators
        '|(?P<literal>'
        r'("(?:[^"\\]|\\.)*")'  # double quoted string
        r"|('(?:[^'\\]|\\.)*')"  # single quoted string
        '|([a-z_][a-z0-9_]*)'  # token
        '|(-?\d+\.\d*)|(-?\.\d+)'  # float
        '|(-?\d+)'  # int
        ')'
        r'|(?P<newline>\n)'  # newline
        '|(?P<unknown>\S+)'  # unknown token
    ]

    def __init__(self, config):
        self.tokenize(config)
        self.config = {}
        self.level = 0
        self.module_level = 0
        self.current_module = []
        self.current_token = 0
        self.line = 0
        self.raw = config.split('\n')
        self.modules()
        self.py3 = sys.version_info > (3, 0)

    def modules(self):
        modules = []
        root = os.path.dirname(os.path.realpath(__file__))
        module_path = os.path.join(root, 'modules', '*.py')
        for file in glob.glob(module_path):
            modules.append(os.path.basename(file)[:-3])
        self.module_names = modules + I3S_SINGLE_NAMES + I3STATUS_MODULES
        self.container_modules = []

    def check_child_friendly(self, name):
        name = name.split()[0]
        if name in self.container_modules:
            return
        root = os.path.dirname(os.path.realpath(__file__))
        module_path = os.path.join(root, 'modules')
        info = imp.find_module(name, [module_path])
        if not info:
            return
        (file, pathname, description) = info
        try:
            py_mod = imp.load_module(name, file, pathname, description)
        except:
            # We cannot load the module!  We could error out here but then the
            # user gets informed that the problem is with their config.  This
            # is not correct.  Better to say that all is well and then the
            # config can get parsed and py3status loads.  The error about the
            # failing module load is better handled at that point, and will be.
            return
        try:
            container = py_mod.Py3status.Meta.container
        except AttributeError:
            container = False
        # delete the module
        del py_mod
        if container:
            self.container_modules.append(name)
        else:
            self.error('Module `{}` cannot contain others'.format(name))

    def check_module_name(self, name, offset=0):
        if name in ['general']:
            return
        split_name = name.split()
        if split_name[0] not in self.module_names:
            self.current_token -= len(split_name) - offset
            self.error('Unknown module')
        if len(split_name) > 1 and split_name[0] in I3S_SINGLE_NAMES:
            self.current_token -= len(split_name) - 1 - offset
            self.error('Invalid name cannot have 2 tokens')
        if len(split_name) > 2:
            self.current_token -= len(split_name) - 2 - offset
            self.error('Invalid name cannot have more than 2 tokens')

    def error(self, msg, previous=False):
        '''
        Raise a ParseException.
        We provide information to help locate the error in the config to allow
        easy config debugging for users.  previous indicates that the error
        actually occurred at the end of the previous line.
        '''
        token = self.tokens[self.current_token - 1]
        line_no = self.line
        if previous:
            line_no -= 1
        line = self.raw[line_no]
        position = token['start'] - self.line_start
        if previous:
            position = len(line) + 2
        raise ParseException(msg, line, line_no + 1, position, token['value'])

    def tokenize(self, config):
        '''
        Break the config into a series of tokens
        '''
        tokens = []
        reg_ex = re.compile(self.TOKENS[0], re.M | re.I)

        for token in re.finditer(reg_ex, config):
            value = token.group(0)
            if token.group('operator'):
                t_type = 'operator'
            elif token.group('literal'):
                t_type = 'literal'
            elif token.group('newline'):
                t_type = 'newline'
            elif token.group('unknown'):
                t_type = 'unknown'
            else:
                continue
            tokens.append({'type': t_type,
                           'value': value,
                           'start': token.start()})
        self.tokens = tokens

    def next(self):
        '''
        Return the next token.  Keep track of our current position in the
        config for nice errors.
        '''
        if self.current_token == len(self.tokens):
            return None
        token = self.tokens[self.current_token]
        if token['type'] == 'newline':
            self.line += 1
            self.line_start = token['start']
        self.current_token += 1
        if token['type'] == 'unknown':
            self.error('Unknown token')
        return token

    def make_name(self, value):
        if value.startswith('"'):
            return value[1:-1].replace('\\"', '"')
        if value.startswith("'"):
            return value[1:-1].replace("\\'", "'")
        return value


    def make_value(self, value):
        '''
        Converts to actual value, or remains as string.
        '''

        if value.startswith('"'):
            return value[1:-1].replace('\\"', '"')
        if value.startswith("'"):
            return value[1:-1].replace("\\'", "'")
        try:
            return int(value)
        except:
            pass
        try:
            return float(value)
        except:
            pass
        if value.lower() == 'true':
            return True
        if value.lower() == 'false':
            return False
        if value.lower() == 'none':
            return None
        return value

    def separator(self, separator=',', end_token=None):
        '''
        Read through tokens till the required separator is found.  We ignore
        newlines.  If an end token is supplied raise a ParseEnd exception if it
        is found.
        '''
        while True:
            token = self.next()
            t_value = token['value']
            if end_token and t_value == end_token:
                raise self.ParseEnd()
            if t_value == separator:
                return
            if t_value == '\n':
                continue
            self.error('Unexpected character')

    def make_list(self, end_token=']'):
        '''
        We are in a list so get values until the end token.  This can also
        used to get tuples.
        '''
        out = []
        while True:
            try:
                value = self.value_assign(end_token=end_token)
                out.append(value)
                self.separator(end_token=end_token)
            except self.ParseEnd:
                return out

    def dict_key(self):
        '''
        Find the next key in a dict.  We skip any newlines and check for if the
        dict has ended.
        '''
        while True:
            token = self.next()
            t_value = token['value']
            if t_value == '\n':
                continue
            if t_value == '}':
                raise self.ParseEnd()
            if token['type'] == 'literal':
                return self.make_value(t_value)
            self.error('Invalid Key')

    def make_dict(self):
        '''
        We are in a dict so get key value pairs until the end token.
        '''
        out = {}
        while True:
            try:
                key = self.dict_key()
                self.separator(separator=':')
                value = self.value_assign(end_token=']')
                out[key] = value
                self.separator(end_token='}')
            except self.ParseEnd:
                return out

    def value_assign(self, end_token=None):
        '''
        We are expecting a value (literal, list, dict, tuple).
        If end_token then we are inside a list, dict or tuple so we are allow
        newlines and also check for the end token.
        '''
        while True:
            token = self.next()
            t_value = token['value']
            if end_token:
                if t_value == end_token:
                    raise self.ParseEnd()
                elif t_value == '\n':
                    continue
            if token['type'] == 'literal':
                return self.make_value(t_value)
            elif t_value == '[':
                return self.make_list()
            elif t_value == '{':
                return self.make_dict()
            elif t_value == '(':
                return tuple(self.make_list(end_token=')'))
            else:
                self.error('Value expected', previous=not (end_token))

    def module_def(self):
        '''
        This is a module definition so parse content till end.
        '''
        if self.module_level == MAX_NESTING_LEVELS:
            self.error('Module nested too deep')
        self.module_level += 1
        module = ModuleDefinition()
        self.parse(module, end_token='}')
        self.module_level -= 1
        self.current_module.pop()
        return module

    def assignment(self, token):
        '''
        We need to find a value to return.  If the token is `=` or `+=` we want
        a value.  If the token is `{` then we need to return a module
        definition.
        '''
        if token['value'] in ['=', '+=']:
            return self.value_assign()
        elif token['value'] in ['{']:
            return self.module_def()

    def parse(self, dictionary=None, end_token=None):
        '''
        Parse through the tokens. Finding names and values.
        This is called at the start of parsing the config but is
        also called to parse module definitions.
        '''
        self.level += 1
        name = []
        if dictionary is None:
            dictionary = self.config
        while True:
            token = self.next()
            if token is None:
                # we have got to the end of the config
                break
            t_type = token['type']
            t_value = token['value']
            if t_type == 'newline':
                if name:
                    self.error('Value expected', previous=True)
                continue
            elif t_value == end_token:
                self.level -= 1
                return
            elif t_type == 'literal':
                value = self.make_name(t_value)
                if not name and not re.match('[a-zA-Z_]', value):
                    self.error('Invalid name')
                name.append(value)
            elif t_type == 'operator':
                name = ' '.join(name)
                if not name:
                    self.error('Name expected')
                elif t_value == '+=' and name not in dictionary:
                    # order is treated specially
                    if not (self.level == 1 and name == 'order'):
                        self.error('{} does not exist'.format(name))
                if t_value in ['{']:
                    if self.current_module:
                        self.check_child_friendly(self.current_module[-1])
                    self.check_module_name(name)
                    self.current_module.append(name)
                value = self.assignment(token)
                # order is treated specially to create a list
                if self.level == 1 and name == 'order':
                    self.check_module_name(value, offset=1)
                    dictionary.setdefault(name, []).append(value)
                # assignment of value or module definition
                elif t_value in ['=', '{']:
                    dictionary[name] = value
                # appending to existing values
                elif t_value == '+=':
                    dictionary[name] += value
                else:
                    self.error('Unexpected character')
                name = []

    class ParseEnd(Exception):
        '''
        Used to signify the end of a dict, list, tuple, or module
        definition.
        '''
        pass


def process_config(config_path, py3_wrapper=None):
    """
    Parse i3status.conf so we can adapt our code to the i3status config.
    """

    def parse_config(config, user_modules=None):
        '''
        Parse text or file as a py3status config file.
        '''

        if hasattr(config, 'readlines'):
            config = ''.join(config.readlines())
        parser = ConfigParser(config)
        parser.parse()
        parsed = parser.config
        del parser
        return parsed

    config = {}

    if py3_wrapper:
        user_modules = py3_wrapper.get_user_modules()
    else:
        user_modules = None

    # get the file encoding this is important with multi-byte unicode chars
    encoding = check_output(['file', '-b', '--mime-encoding', config_path])
    encoding = encoding.strip().decode('utf-8')
    with codecs.open(config_path, 'r', encoding) as f:
        try:
            config_info = parse_config(f, user_modules=user_modules)
        except ParseException as e:

            error = e.one_line()
            if py3_wrapper:
                py3_wrapper.notify_user(error)
            error_config = Template(ERROR_CONFIG).substitute(
                error=error.replace('"', '\\"'))
            config_info = parse_config(error_config)

    # update general section with defaults
    general_defaults = GENERAL_DEFAULTS.copy()
    if 'general' in config_info:
        general_defaults.update(config_info['general'])
    config['general'] = general_defaults

    # get all modules
    modules = {}
    on_click = {}
    i3s_modules = []
    py3_modules = []
    module_groups = {}

    def process_onclick(key, value, group_name):
        try:
            button = int(key.split()[1])
            if button not in range(1, 6):
                raise ValueError('should be 1, 2, 3, 4 or 5')
        except IndexError as e:
            raise IndexError('missing "button id" for "on_click" '
                             'parameter in group {}'.format(group_name))
        except ValueError as e:
            raise ValueError('invalid "button id" '
                             'for "on_click" parameter '
                             'in group {} ({})'.format(group_name, e))
        clicks = on_click.setdefault(group_name, {})
        clicks[button] = value

    def get_module_type(name):
        if name.split()[0] in I3S_SINGLE_NAMES + I3STATUS_MODULES:
            return 'i3status'
        return 'py3status'

    def process_module(name, module, parent):
        if parent:
            modules[parent]['items'].append(name)
            mg = module_groups.setdefault(name, [])
            mg.append(parent)
            if get_module_type(name) == 'py3status':
                module['.group'] = parent

        # check module content
        for k, v in module.items():
            if k.startswith('on_click'):
                # on_click event
                process_onclick(k, v, name)
            if isinstance(v, ModuleDefinition):
                # we are a container
                module['items'] = []
        return module

    def get_modules(data, parent=None):
        for k, v in data.items():
            if isinstance(v, ModuleDefinition):
                module = process_module(k, v, parent)
                modules[k] = module
                get_modules(v, parent=k)

    get_modules(config_info)

    config['order'] = []

    def fix_module(module):
        fixed = {}
        for k, v in module.items():
            if not isinstance(v, ModuleDefinition):
                fixed[k] = v
        return fixed

    def add_container_items(module_name):
        module = modules.get(module_name, {})
        items = module.get('items', [])
        for item in items:
            if item in config:
                continue
            module_type = get_module_type(item)
            if module_type == 'i3status':
                if item not in i3s_modules:
                    i3s_modules.append(item)
            else:
                if item not in py3_modules:
                    py3_modules.append(item)
            module = modules.get(item, {})
            config[item] = fix_module(module)
            # add any children
            add_container_items(item)

    # create config for modules in order
    for name in config_info['order']:
        module = modules.get(name, {})
        module_type = get_module_type(name)
        config['order'].append(name)
        add_container_items(name)
        if module_type == 'i3status':
            if name not in i3s_modules:
                i3s_modules.append(name)
        else:
            if name not in py3_modules:
                py3_modules.append(name)
        config[name] = fix_module(module)

    config['on_click'] = on_click
    config['i3s_modules'] = i3s_modules
    config['py3_modules'] = py3_modules
    config['.module_groups'] = module_groups

    # time and tztime modules need a format for correct processing
    for name in config:
        if name.split()[0] in TIME_MODULES and 'format' not in config[name]:
            if name.split()[0] == 'time':
                config[name]['format'] = TIME_FORMAT
            else:
                config[name]['format'] = TZTIME_FORMAT

    return config


if __name__ == '__main__':
    pass
    config = '/home/toby/.i3/i3status.conf'
    import pprint
    pprint.pprint(process_config(config))
