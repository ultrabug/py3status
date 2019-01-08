# -*- coding: utf-8 -*-
import codecs
import imp
import os
import re

from collections import OrderedDict
from string import Template
from subprocess import check_output, CalledProcessError

from py3status.constants import (
    CONFIG_FILE_SPECIAL_SECTIONS,
    I3S_SINGLE_NAMES,
    I3S_MODULE_NAMES,
    MAX_NESTING_LEVELS,
    ERROR_CONFIG,
    GENERAL_DEFAULTS,
    RETIRED_MODULES,
    TIME_MODULES,
    TIME_FORMAT,
    TZTIME_FORMAT,
)

from py3status.private import PrivateHide, PrivateBase64


class ParseException(Exception):
    """
    Exception raised when a parse exception occurs.
    This exception receives information on the error so that helpful error
    messages can be provided to the user.
    """

    def __init__(self, error, line, line_no, position, token):
        self.error = error
        self.line = line
        self.line_no = line_no
        self.position = position
        self.token = token.replace("\n", "\\n")

    def one_line(self, config_path):
        filename = os.path.basename(config_path)
        notif = "CONFIG ERROR: {} saw `{}` at line {} position {} in file {}"
        return notif.format(
            self.error, self.token, self.line_no, self.position, filename
        )

    def __str__(self):
        marker = " " * (self.position - 1) + "^"
        return "{}\n\nsaw `{}` at line {} position {}\n\n{}\n{}".format(
            self.error, self.token, self.line_no, self.position, self.line, marker
        )


class ModuleDefinition(OrderedDict):
    """Module definition in OrderedDict form"""

    pass


class ConfigParser:
    """
    A basic top down parser.

    We break the config into a list of tokens and travel through them to build
    up a dict that corresponds to the config.

    The parser allows:

    * containers

        container {
            included_module 1 {}
            included_module 2 {}
        }

    * nesting of containers

        container 1 {
            container 2 {
                included_module 1 {}
            }
            included_module 2 {}
        }

    * many types including lists, dict and tuple values

        my_module {
            my_str = 'hello'
            my_int = 23
            my_bool = true
            my_list = [1, 2, 3]
            my_dict = {'x': 1, 'y': 2}
            my_tuple = (1, 'something')
            my_complex = {
                'list' : [1, 2, 3],
                'dict' : {'x': 1, 'y': 2}
            }
        }

    * environment variable support

        order += env(ORDER_VAR)

        my_module {
            my_guessed_type = env(MY_VAR)
            my_str = env(MY_VAR, str)
            my_int = env(MY_INT_VAR, int)
            my_bool = env(MY_FLAG, bool)
            my_complex = {
                'list' : [1, 2, env(MY_LIST_ENTRY, int)],
                'dict' : {'x': env(MY_DICT_VAL), 'y': 2}
            }
        }

    * execute shell code

        my_module {
            my_guessed_type = shell(pass show git|head -n1)
            my_str = shell(pass show git|head -n1, str)
            my_int = shell(pass show git|head -n1, int)
            my_bool = shell(pass show git|head -n1, bool)
        }

        (shell code may not include any parenthesis!)

    * quality feedback on parse errors.
        details include error description, line number, position.

    """

    CONVERSIONS = "(auto|bool|int|float|str)"
    FUNCTIONS = "(base64|env|hide|shell)"

    TOKENS = [
        "#.*$"  # comments
        "|(?P<function>"  # functions of the form `name(payload[,type])`
        "" + FUNCTIONS + r"\(\s*(([^)\\]|\\.)*?)"  # nasty '' but flake8
        r"(\s*,\s*" + CONVERSIONS + r")?\s*\))"
        r"|(?P<operator>[()[\]{},:]|\+?=)"  # operators
        "|(?P<literal>"
        r'("(?:[^"\\]|\\.)*")'  # double quoted string
        r"|('(?:[^'\\]|\\.)*')"  # single quoted string
        r"|([a-z_][a-z0-9_\-]*(:[a-z0-9_]+)?)"  # token
        r"|(-?\d+\.\d*)|(-?\.\d+)"  # float
        r"|(-?\d+)"  # int
        ")"
        r"|(?P<newline>\n)"  # newline
        r"|(?P<unknown>\S+)"  # unknown token
    ]

    def __init__(self, config, py3_wrapper):
        self.tokenize(config)
        self.config = {}
        self.level = 0
        self.module_level = 0
        self.current_module = []
        self.current_token = 0
        self.line = 0
        self.line_start = 0
        self.py3_wrapper = py3_wrapper
        self.raw = config.split("\n")
        self.container_modules = []
        self.anon_count = 0

    def notify_user(self, error):
        if self.py3_wrapper:
            self.py3_wrapper.notify_user(error)
        else:
            print(error)

    class ParseEnd(Exception):
        """
        Used to signify the end of a dict, list, tuple, or module
        definition.
        """

        pass

    def check_child_friendly(self, name):
        """
        Check if a module is a container and so can have children
        """
        name = name.split()[0]
        if name in self.container_modules:
            return
        root = os.path.dirname(os.path.realpath(__file__))
        module_path = os.path.join(root, "modules")
        try:
            info = imp.find_module(name, [module_path])
        except ImportError:
            return
        if not info:
            return
        (file, pathname, description) = info
        try:
            py_mod = imp.load_module(name, file, pathname, description)
        except Exception:
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
            self.error("Module `{}` cannot contain others".format(name))

    def check_module_name(self, name, offset=0):
        """
        Checks a module name eg. some i3status modules cannot have an instance
        name.
        """
        if name in ["general"]:
            return
        split_name = name.split()
        if len(split_name) > 1 and split_name[0] in I3S_SINGLE_NAMES:
            self.current_token -= len(split_name) - 1 - offset
            self.error("Invalid name cannot have 2 tokens")
        if len(split_name) > 2:
            self.current_token -= len(split_name) - 2 - offset
            self.error("Invalid name cannot have more than 2 tokens")

    def error(self, msg, previous=False):
        """
        Raise a ParseException.
        We provide information to help locate the error in the config to allow
        easy config debugging for users.  previous indicates that the error
        actually occurred at the end of the previous line.
        """
        token = self.tokens[self.current_token - 1]
        line_no = self.line
        if previous:
            line_no -= 1
        line = self.raw[line_no]
        position = token["start"] - self.line_start
        if previous:
            position = len(line) + 2
        raise ParseException(msg, line, line_no + 1, position, token["value"])

    def tokenize(self, config):
        """
        Break the config into a series of tokens
        """
        tokens = []
        reg_ex = re.compile(self.TOKENS[0], re.M | re.I)

        for token in re.finditer(reg_ex, config):
            value = token.group(0)
            if token.group("operator"):
                t_type = "operator"
            elif token.group("literal"):
                t_type = "literal"
            elif token.group("newline"):
                t_type = "newline"
            elif token.group("function"):
                t_type = "function"
            elif token.group("unknown"):
                t_type = "unknown"
            else:
                continue
            tokens.append(
                {"type": t_type, "value": value, "match": token, "start": token.start()}
            )
        self.tokens = tokens

    def next(self):
        """
        Return the next token.  Keep track of our current position in the
        config for nice errors.
        """
        if self.current_token == len(self.tokens):
            return None
        token = self.tokens[self.current_token]
        if token["type"] == "newline":
            self.line += 1
            self.line_start = token["start"]
        self.current_token += 1
        if token["type"] == "unknown":
            self.error("Unknown token")
        return token

    def remove_quotes(self, value):
        """
        Remove any surrounding quotes from a value and unescape any contained
        quotes of that type.
        """
        # beware the empty string
        if not value:
            return value

        if value[0] == value[-1] == '"':
            return value[1:-1].replace('\\"', '"')
        if value[0] == value[-1] == "'":
            return value[1:-1].replace("\\'", "'")
        return value

    def unicode_escape_sequence_fix(self, value):
        """
        It is possible to define unicode characters in the config either as the
        actual utf-8 character or using escape sequences the following all will
        show the Greek delta character.
        Δ \N{GREEK CAPITAL LETTER DELTA} \U00000394  \u0394
        """

        def fix_fn(match):
            # we don't escape an escaped backslash
            if match.group(0) == r"\\":
                return r"\\"
            return match.group(0).encode("utf-8").decode("unicode-escape")

        return re.sub(r"\\\\|\\u\w{4}|\\U\w{8}|\\N\{([^}\\]|\\.)+\}", fix_fn, value)

    def make_value(self, value):
        """
        Converts to actual value, or remains as string.
        """
        # ensure any escape sequences are converted to unicode
        value = self.unicode_escape_sequence_fix(value)

        if value and value[0] in ['"', "'"]:
            return self.remove_quotes(value)

        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        if value.lower() == "none":
            return None
        return value

    def config_function(self, token):
        """
        Process a config function from a token
        """
        match = token["match"]
        function = match.group(2).lower()
        param = match.group(3) or ""
        value_type = match.group(6) or "auto"

        # fix any escaped closing parenthesis
        param = param.replace(r"\)", ")")

        CONFIG_FUNCTIONS = {
            "base64": self.make_function_value_private,
            "env": self.make_value_from_env,
            "hide": self.make_function_value_private,
            "shell": self.make_value_from_shell,
        }

        return CONFIG_FUNCTIONS[function](param, value_type, function)

    def value_convert(self, value, value_type):
        """
        convert string into type used by `config functions`
        """
        CONVERSION_OPTIONS = {
            "str": str,
            "int": int,
            "float": float,
            # Treat booleans specially
            "bool": (lambda val: val.lower() in ("true", "1")),
            # Auto-guess the type
            "auto": self.make_value,
        }

        try:
            return CONVERSION_OPTIONS[value_type](value)
        except (TypeError, ValueError):
            self.notify_user("Bad type conversion")
            return None

    def make_value_from_env(self, param, value_type, function):
        """
        get environment variable
        """
        value = os.getenv(param)
        if value is None:
            self.notify_user("Environment variable `%s` undefined" % param)
        return self.value_convert(value, value_type)

    def make_value_from_shell(self, param, value_type, function):
        """
        run command in the shell
        """
        try:
            value = check_output(param, shell=True).rstrip()
        except CalledProcessError:
            # for value_type of 'bool' we return False on error code
            if value_type == "bool":
                value = False
            else:
                if self.py3_wrapper:
                    self.py3_wrapper.report_exception(
                        msg="shell: called with command `%s`" % param
                    )
                self.notify_user("shell script exited with an error")
                value = None
        else:
            # if the value_type is 'bool' then we return True for success
            if value_type == "bool":
                value = True
            else:
                # convert bytes to unicode
                value = value.decode("utf-8")
                value = self.value_convert(value, value_type)
        return value

    def make_function_value_private(self, value, value_type, function):
        """
        Wraps converted value so that it is hidden in logs etc.
        Note this is not secure just reduces leaking info

        Allows base 64 encode stuff using base64() or plain hide() in the
        config
        """
        # remove quotes
        value = self.remove_quotes(value)

        if function == "base64":
            try:
                import base64

                value = base64.b64decode(value).decode("utf-8")
            except TypeError as e:
                self.notify_user("base64(..) error %s" % str(e))

        # check we are in a module definition etc
        if not self.current_module:
            self.notify_user("%s(..) used outside of module or section" % function)
            return None

        module = self.current_module[-1].split()[0]
        if module in CONFIG_FILE_SPECIAL_SECTIONS + I3S_MODULE_NAMES:
            self.notify_user(
                "%s(..) cannot be used outside of py3status module "
                "configuration" % function
            )
            return None

        value = self.value_convert(value, value_type)
        module_name = self.current_module[-1]
        return PrivateHide(value, module_name)

    def separator(self, separator=",", end_token=None):
        """
        Read through tokens till the required separator is found.  We ignore
        newlines.  If an end token is supplied raise a ParseEnd exception if it
        is found.
        """
        while True:
            token = self.next()
            t_value = token["value"]
            if end_token and t_value == end_token:
                raise self.ParseEnd()
            if t_value == separator:
                return
            if t_value == "\n":
                continue
            self.error("Unexpected character")

    def make_list(self, end_token="]"):
        """
        We are in a list so get values until the end token.  This can also
        used to get tuples.
        """
        out = []
        while True:
            try:
                value = self.value_assign(end_token=end_token)
                out.append(value)
                self.separator(end_token=end_token)
            except self.ParseEnd:
                return out

    def dict_key(self):
        """
        Find the next key in a dict.  We skip any newlines and check for if the
        dict has ended.
        """
        while True:
            token = self.next()
            t_value = token["value"]
            if t_value == "\n":
                continue
            if t_value == "}":
                raise self.ParseEnd()
            if token["type"] == "literal":
                return self.make_value(t_value)
            self.error("Invalid Key")

    def make_dict(self):
        """
        We are in a dict so get key value pairs until the end token.
        """
        out = {}
        while True:
            try:
                key = self.dict_key()
                self.separator(separator=":")
                value = self.value_assign(end_token="]")
                out[key] = value
                self.separator(end_token="}")
            except self.ParseEnd:
                return out

    def value_assign(self, end_token=None):
        """
        We are expecting a value (literal, list, dict, tuple).
        If end_token then we are inside a list, dict or tuple so we are allow
        newlines and also check for the end token.
        """
        while True:
            token = self.next()
            t_value = token["value"]
            if end_token:
                if t_value == end_token:
                    raise self.ParseEnd()
                elif t_value == "\n":
                    continue
            if token["type"] == "literal":
                return self.make_value(t_value)
            if token["type"] == "function":
                return self.config_function(token)
            elif t_value == "[":
                return self.make_list()
            elif t_value == "{":
                return self.make_dict()
            elif t_value == "(":
                return tuple(self.make_list(end_token=")"))
            else:
                self.error("Value expected", previous=not (end_token))

    def module_def(self):
        """
        This is a module definition so parse content till end.
        """
        if self.module_level == MAX_NESTING_LEVELS:
            self.error("Module nested too deep")
        self.module_level += 1
        module = ModuleDefinition()
        self.parse(module, end_token="}")
        self.module_level -= 1
        self.current_module.pop()
        return module

    def assignment(self, token):
        """
        We need to find a value to return.  If the token is `=` or `+=` we want
        a value.  If the token is `{` then we need to return a module
        definition.
        """
        if token["value"] in ["=", "+="]:
            return self.value_assign()
        elif token["value"] in ["{"]:
            return self.module_def()

    def process_value(self, name, value, module_name):
        """
        This method allow any encodings to be dealt with.
        Currently only base64 is supported.

        Note: If other encodings are added then this should be split so that
        there is a method for each encoding.
        """
        # if we have a colon in the name of a setting then it
        # indicates that it has been encoded.
        if ":" in name:

            if module_name.split(" ")[0] in I3S_MODULE_NAMES + ["general"]:
                self.error("Only py3status modules can use obfuscated")

            if type(value).__name__ not in ["str", "unicode"]:
                self.error("Only strings can be obfuscated")

            (name, scheme) = name.split(":")
            if scheme == "base64":
                value = PrivateBase64(value, module_name)
            elif scheme == "hide":
                value = PrivateHide(value, module_name)
            else:
                self.error("Unknown scheme {} for data".format(scheme))

        return name, value

    def parse(self, dictionary=None, end_token=None):
        """
        Parse through the tokens. Finding names and values.
        This is called at the start of parsing the config but is
        also called to parse module definitions.
        """
        self.level += 1
        name = []
        if dictionary is None:
            dictionary = self.config
        while True:
            token = self.next()
            if token is None:
                # we have got to the end of the config
                break
            t_type = token["type"]
            t_value = token["value"]
            if t_type == "newline":
                continue
            elif t_value == end_token:
                self.level -= 1
                return
            elif t_type == "literal":
                value = self.remove_quotes(t_value)
                if not name and not re.match("[a-zA-Z_]", value):
                    self.error("Invalid name")
                name.append(value)
            elif t_type == "function":
                self.error("Name expected")
            elif t_type == "operator":
                name = " ".join(name)
                if not name:
                    self.error("Name expected")
                elif t_value == "+=" and name not in dictionary:
                    # deal with encoded names
                    if name.split(":")[0] not in dictionary:
                        # order is treated specially
                        if not (self.level == 1 and name == "order"):
                            self.error("{} does not exist".format(name))
                if t_value in ["{"]:
                    if self.current_module:
                        self.check_child_friendly(self.current_module[-1])
                    self.check_module_name(name)
                    self.current_module.append(name)
                value = self.assignment(token)
                # order is treated specially to create a list
                if self.level == 1 and name == "order":
                    if not value:
                        self.error("Invalid module")
                    self.check_module_name(value, offset=1)
                    dictionary.setdefault(name, []).append(value)
                # assignment of  module definition
                elif t_value == "{":
                    # If this is an py3status module and in a container and has
                    # no instance name then give it an anon one.  This allows
                    # us to have multiple non-instance named modules defined
                    # without them clashing.
                    if (
                        self.level > 1
                        and " " not in name
                        and name not in I3S_MODULE_NAMES
                    ):
                        name = "{} _anon_module_{}".format(name, self.anon_count)
                        self.anon_count += 1
                    dictionary[name] = value
                # assignment of value
                elif t_value == "=":
                    try:
                        name, value = self.process_value(
                            name, value, self.current_module[-1]
                        )
                    except IndexError:
                        self.error("Missing {", previous=True)
                    dictionary[name] = value
                # appending to existing values
                elif t_value == "+=":
                    dictionary[name] += value
                else:
                    self.error("Unexpected character")
                name = []


def process_config(config_path, py3_wrapper=None):
    """
    Parse i3status.conf so we can adapt our code to the i3status config.
    """

    def notify_user(error):
        if py3_wrapper:
            py3_wrapper.notify_user(error)
        else:
            print(error)

    def parse_config(config):
        """
        Parse text or file as a py3status config file.
        """

        if hasattr(config, "readlines"):
            config = "".join(config.readlines())
        parser = ConfigParser(config, py3_wrapper)
        parser.parse()
        parsed = parser.config
        del parser
        return parsed

    def parse_config_error(e, config_path):
        # There was a problem use our special error config
        error = e.one_line(config_path)
        notify_user(error)
        # to display correctly in i3bar we need to do some substitutions
        for char in ['"', "{", "|"]:
            error = error.replace(char, "\\" + char)
        error_config = Template(ERROR_CONFIG).substitute(error=error)
        return parse_config(error_config)

    config = {}

    # get the file encoding this is important with multi-byte unicode chars
    try:
        encoding = check_output(
            ["file", "-b", "--mime-encoding", "--dereference", config_path]
        )
        encoding = encoding.strip().decode("utf-8")
    except CalledProcessError:
        # bsd does not have the --mime-encoding so assume utf-8
        encoding = "utf-8"
    try:
        with codecs.open(config_path, "r", encoding) as f:
            try:
                config_info = parse_config(f)
            except ParseException as e:
                config_info = parse_config_error(e, config_path)
    except LookupError:
        with codecs.open(config_path) as f:
            try:
                config_info = parse_config(f)
            except ParseException as e:
                config_info = parse_config_error(e, config_path)

    # update general section with defaults
    general_defaults = GENERAL_DEFAULTS.copy()
    if "general" in config_info:
        general_defaults.update(config_info["general"])
    config["general"] = general_defaults

    config["py3status"] = config_info.get("py3status", {})
    modules = {}
    on_click = {}
    i3s_modules = []
    py3_modules = []
    module_groups = {}

    def process_onclick(key, value, group_name):
        """
        Check on_click events are valid.  Store if they are good
        """
        button_error = False
        button = ""
        try:
            button = key.split()[1]
            if int(button) not in range(1, 20):
                button_error = True
        except (ValueError, IndexError):
            button_error = True

        if button_error:
            err = "Invalid on_click for `{}`. Number not in range 1-20: `{}`."
            notify_user(err.format(group_name, button))
            return False
        clicks = on_click.setdefault(group_name, {})
        clicks[button] = value
        return True

    def get_module_type(name):
        """
        i3status or py3status?
        """
        if name.split()[0] in I3S_MODULE_NAMES:
            return "i3status"
        return "py3status"

    def process_module(name, module, parent):
        if parent:
            modules[parent]["items"].append(name)
            mg = module_groups.setdefault(name, [])
            mg.append(parent)
            if get_module_type(name) == "py3status":
                module[".group"] = parent

        # check module content
        for k, v in list(module.items()):
            if k.startswith("on_click"):
                # on_click event
                process_onclick(k, v, name)
                # on_click should not be passed to the module via the config.
                del module[k]
            if isinstance(v, ModuleDefinition):
                # we are a container
                module["items"] = []
        return module

    def get_modules(data, parent=None):
        for k, v in data.items():
            if isinstance(v, ModuleDefinition):
                module = process_module(k, v, parent)
                modules[k] = module
                get_modules(v, parent=k)

    get_modules(config_info)

    config["order"] = []

    def remove_any_contained_modules(module):
        """
        takes a module definition and returns a dict without any modules that
        may be defined with it.
        """
        fixed = {}
        for k, v in module.items():
            if not isinstance(v, ModuleDefinition):
                fixed[k] = v
        return fixed

    def append_modules(item):
        module_type = get_module_type(item)
        if module_type == "i3status":
            if item not in i3s_modules:
                i3s_modules.append(item)
        else:
            if item not in py3_modules:
                py3_modules.append(item)

    def add_container_items(module_name):
        module = modules.get(module_name, {})
        items = module.get("items", [])
        for item in items:
            if item in config:
                continue

            append_modules(item)
            module = modules.get(item, {})
            config[item] = remove_any_contained_modules(module)
            # add any children
            add_container_items(item)

    # create config for modules in order
    for name in config_info.get("order", []):
        module_name = name.split(" ")[0]
        if module_name in RETIRED_MODULES:
            notify_user(
                "Module `{}` is no longer available".format(module_name)
                + ". Alternative modules are: {}.".format(
                    ", ".join("`{}`".format(x) for x in RETIRED_MODULES[module_name])
                )
            )
            continue
        module = modules.get(name, {})
        config["order"].append(name)
        add_container_items(name)
        append_modules(name)

        config[name] = remove_any_contained_modules(module)

    config["on_click"] = on_click
    config["i3s_modules"] = i3s_modules
    config["py3_modules"] = py3_modules
    config[".module_groups"] = module_groups

    # time and tztime modules need a format for correct processing
    for name in config:
        if name.split()[0] in TIME_MODULES and "format" not in config[name]:
            if name.split()[0] == "time":
                config[name]["format"] = TIME_FORMAT
            else:
                config[name]["format"] = TZTIME_FORMAT

    if not config["order"]:
        notify_user(
            "Your configuration file does not list any module"
            ' to be loaded with the "order" directive.'
        )
    return config


if __name__ == "__main__":
    # process a config file and display output
    # file name user supplied or ~/.i3/i3status.conf
    import sys
    import pprint

    if len(sys.argv) > 1:
        file_name = sys.argv[1]
    else:
        file_name = os.path.join(os.path.expanduser("~"), ".i3/i3status.conf")
    print("\nPARSING CONFIG FILE %s\n\n" % file_name)
    pprint.pprint(process_config(file_name))
