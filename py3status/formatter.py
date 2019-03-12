# -*- coding: utf-8 -*-
import re
import sys

from math import ceil
from numbers import Number

from py3status.composite import Composite

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl


python2 = sys.version_info < (3, 0)


class Formatter:
    """
    Formatter for processing format strings via the format method.
    """

    TOKENS = [
        r"(?P<block_start>\[)"
        r"|(?P<block_end>\])"
        r"|(?P<switch>\|)"
        r"|(\\\?(?P<command>\S*)\s)"
        r"|(?P<escaped>(\\.|\{\{|\}\}))"
        r"|(?P<placeholder>(\{(?P<key>([^}\\\:\!]|\\.)*)(?P<format>([^}\\]|\\.)*)?\}))"
        r"|(?P<literal>([^\[\]\\\{\}\|])+)"
        r"|(?P<lost_brace>([{}]))"
    ]

    reg_ex = re.compile(TOKENS[0], re.M | re.I)

    block_cache = {}
    format_string_cache = {}

    def __init__(self, py3_wrapper=None):
        self.py3_wrapper = py3_wrapper

    def tokens(self, format_string):
        """
        Get the tokenized format_string.
        Tokenizing is resource intensive so we only do it once and cache it
        """
        if format_string not in self.format_string_cache:
            if python2 and isinstance(format_string, str):
                format_string = format_string.decode("utf-8")
            tokens = list(re.finditer(self.reg_ex, format_string))
            self.format_string_cache[format_string] = tokens
        return self.format_string_cache[format_string]

    def get_placeholders(self, format_string):
        """
        Parses the format_string and returns a set of placeholders.
        """
        placeholders = set()
        # Tokenize the format string and process them
        for token in self.tokens(format_string):
            if token.group("placeholder"):
                placeholders.add(token.group("key"))
            elif token.group("command"):
                # get any placeholders used in commands
                commands = dict(parse_qsl(token.group("command")))
                # placeholders only used in `if`
                if_ = commands.get("if")
                if if_:
                    placeholders.add(Condition(if_).variable)
        return placeholders

    def get_placeholder_formats_list(self, format_string):
        """
        Parses the format_string and returns a list of tuples
        (placeholder, format).
        """
        placeholders = []
        # Tokenize the format string and process them
        for token in self.tokens(format_string):
            if token.group("placeholder"):
                placeholders.append((token.group("key"), token.group("format")))
        return placeholders

    def update_placeholders(self, format_string, placeholders):
        """
        Update a format string renaming placeholders.
        """
        # Tokenize the format string and process them
        output = []
        for token in self.tokens(format_string):
            if token.group("key") in placeholders:
                output.append(
                    "{%s%s}" % (placeholders[token.group("key")], token.group("format"))
                )
                continue
            elif token.group("command"):
                # update any placeholders used in commands
                commands = parse_qsl(token.group("command"), keep_blank_values=True)
                # placeholders only used in `if`
                if "if" in [x[0] for x in commands]:
                    items = []
                    for key, value in commands:
                        if key == "if":
                            # we have to rebuild from the parts we have
                            condition = Condition(value)
                            variable = condition.variable
                            if variable in placeholders:
                                variable = placeholders[variable]
                                # negation via `!`
                                not_ = "!" if not condition.default else ""
                                condition_ = condition.condition or ""
                                # if there is no condition then there is no
                                # value
                                if condition_:
                                    value_ = condition.value
                                else:
                                    value_ = ""
                                value = "{}{}{}{}".format(
                                    not_, variable, condition_, value_
                                )
                        if value:
                            items.append("{}={}".format(key, value))
                        else:
                            items.append(key)

                    # we cannot use urlencode because it will escape things
                    # like `!`
                    output.append(r"\?{} ".format("&".join(items)))
                    continue
            value = token.group(0)
            output.append(value)
        return u"".join(output)

    def update_placeholder_formats(self, format_string, placeholder_formats):
        """
        Update a format string adding formats if they are not already present.
        """
        # Tokenize the format string and process them
        output = []
        for token in self.tokens(format_string):
            if (
                token.group("placeholder")
                and (not token.group("format"))
                and token.group("key") in placeholder_formats
            ):
                output.append(
                    "{%s%s}"
                    % (token.group("key"), placeholder_formats[token.group("key")])
                )
                continue
            value = token.group(0)
            output.append(value)
        return u"".join(output)

    def build_block(self, format_string):
        """
        Parse the format string into blocks containing Literals, Placeholders
        etc that we can cache and reuse.
        """
        first_block = Block(None, py3_wrapper=self.py3_wrapper)
        block = first_block

        # Tokenize the format string and process them
        for token in self.tokens(format_string):
            value = token.group(0)
            if token.group("block_start"):
                # Create new block
                block = block.new_block()
            elif token.group("block_end"):
                # Close block setting any valid state as needed
                # and return to parent block to continue
                if not block.parent:
                    raise Exception("Too many `]`")
                block = block.parent
            elif token.group("switch"):
                # a new option has been created
                block = block.switch()
            elif token.group("placeholder"):
                # Found a {placeholder}
                key = token.group("key")
                format = token.group("format")
                block.add(Placeholder(key, format))
            elif token.group("literal"):
                block.add(Literal(value))
            elif token.group("lost_brace"):
                # due to how parsing happens we can get a lonesome }
                # eg in format_string '{{something}' this fixes that issue
                block.add(Literal(value))
            elif token.group("command"):
                # a block command has been found
                block.set_commands(token.group("command"))
            elif token.group("escaped"):
                # escaped characters add unescaped values
                if value[0] in ["\\", "{", "}"]:
                    value = value[1:]
                block.add(Literal(value))

        if block.parent:
            raise Exception("Block not closed")
        # add to the cache
        self.block_cache[format_string] = first_block

    def format(
        self,
        format_string,
        module=None,
        param_dict=None,
        force_composite=False,
        attr_getter=None,
    ):
        """
        Format a string, substituting place holders which can be found in
        param_dict, attributes of the supplied module, or provided via calls to
        the attr_getter function.
        """
        # fix python 2 unicode issues
        if python2 and isinstance(format_string, str):
            format_string = format_string.decode("utf-8")

        if param_dict is None:
            param_dict = {}

        # if the processed format string is not in the cache then create it.
        if format_string not in self.block_cache:
            self.build_block(format_string)

        first_block = self.block_cache[format_string]

        def get_parameter(key):
            """
            function that finds and returns the value for a placeholder.
            """
            if key in param_dict:
                # was a supplied parameter
                param = param_dict.get(key)
            elif module and hasattr(module, key):
                param = getattr(module, key)
                if hasattr(param, "__call__"):
                    # we don't allow module methods
                    raise Exception()
            elif attr_getter:
                # get value from attr_getter function
                try:
                    param = attr_getter(key)
                except:  # noqa e722
                    raise Exception()
            else:
                raise Exception()
            if isinstance(param, Composite):
                if param.text():
                    param = param.copy()
                else:
                    param = u""
            elif python2 and isinstance(param, str):
                param = param.decode("utf-8")
            return param

        # render our processed format
        valid, output = first_block.render(get_parameter, module)

        # clean things up a little
        if isinstance(output, list):
            output = Composite(output)
        if not output:
            if force_composite:
                output = Composite()
            else:
                output = ""

        return output


class Placeholder:
    """
    Class representing a {placeholder}
    """

    def __init__(self, key, format):
        self.key = key
        self.format = format

    def get(self, get_params, block):
        """
        return the correct value for the placeholder
        """
        value = "{%s}" % self.key
        try:
            value = value_ = get_params(self.key)
            if self.format.startswith(":"):
                # if a parameter has been set to be formatted as a numeric
                # type then we see if we can coerce it to be.  This allows
                # the user to format types that normally would not be
                # allowed eg '123' it also allows {:d} to be used as a
                # shorthand for {:.0f}.  Use {:g} to remove insignificant
                # trailing zeroes and the decimal point too if there are
                # no remaining digits following it.  If the parameter cannot
                # be successfully converted then the format will be removed.
                try:
                    if "ceil" in self.format:
                        value = int(ceil(float(value)))
                    if "f" in self.format:
                        value = float(value)
                    if "g" in self.format:
                        value = float(value)
                    if "d" in self.format:
                        value = int(float(value))
                    output = u"{[%s]%s}" % (self.key, self.format)
                    value = output.format({self.key: value})
                    value_ = float(value)
                except ValueError:
                    pass
            elif self.format.startswith("!"):
                output = u"{%s%s}" % (self.key, self.format)
                value = value_ = output.format(**{self.key: value})

            if block.commands.not_zero:
                valid = value_ not in ["", None, False, "0", "0.0", 0, 0.0]
            else:
                # '', None, and False are ignored
                # numbers like 0 and 0.0 are not.
                valid = not (value_ in ["", None] or value_ is False)
            enough = False
        except:  # noqa e722
            # Exception raised when we don't have the param
            enough = True
            valid = False

        return valid, value, enough

    def __repr__(self):
        return "<Placeholder {%s}>" % self.repr()

    def repr(self):
        if self.format:
            value = "%s%s" % (self.key, self.format)
        else:
            value = self.key
        return "{%s}" % value


class Literal:
    """
    Class representing some text
    """

    def __init__(self, text):
        self.text = text

    def __repr__(self):
        return "<Literal %s>" % self.text

    def repr(self):
        return self.text


class Condition:
    """
    This class represents the if condition of a block It allows us to compare
    the value of a parameter to a chosen value or just to see if it equates to
    True
    """

    condition = None
    value = True
    variable = None

    def __init__(self, info):
        # are we negated?
        self.default = info[0] != "!"
        if not self.default:
            info = info[1:]

        if "=" in info:
            self.variable, self.value = info.split("=")
            self.condition = "="
            self.check_valid = self._check_valid_condition
        elif ">" in info:
            self.variable, self.value = info.split(">")
            self.condition = ">"
            self.check_valid = self._check_valid_condition
        elif "<" in info:
            self.variable, self.value = info.split("<")
            self.condition = "<"
            self.check_valid = self._check_valid_condition
        else:
            self.variable = info
            self.check_valid = self._check_valid_basic

    def _check_valid_condition(self, get_params):
        """
        Check if the condition has been met.
        We need to make sure that we are of the correct type.
        """
        try:
            variable = get_params(self.variable)
        except:  # noqa e722
            variable = None
        value = self.value

        # if None, return oppositely
        if variable is None:
            return not self.default

        # convert the value to a correct type
        if isinstance(variable, bool):
            value = bool(self.value)
        elif isinstance(variable, Number):
            try:
                value = int(self.value)
            except:  # noqa e722
                try:
                    value = float(self.value)
                except:  # noqa e722
                    # could not parse
                    return not self.default

        # compare and return the result
        if self.condition == "=":
            return (variable == value) == self.default
        elif self.condition == ">":
            return (variable > value) == self.default
        elif self.condition == "<":
            return (variable < value) == self.default

    def _check_valid_basic(self, get_params):
        """
        Simple check that the variable is set
        """
        try:
            if get_params(self.variable):
                return self.default
        except:  # noqa e722
            pass
        return not self.default


class BlockConfig:
    r"""
    Block commands eg [\?color=bad ...] are stored in this object
    """

    REGEX_COLOR = re.compile("#[0-9A-F]{6}")
    INHERITABLE = ["color", "not_zero", "show"]

    # defaults
    _if = None
    color = None
    max_length = None
    min_length = 0
    not_zero = False
    show = False
    soft = False

    def __init__(self, parent):
        # inherit any commands from the parent block
        # inheritable commands are in self.INHERITABLE
        if parent:
            parent_commands = parent.commands
            for attr in self.INHERITABLE:
                setattr(self, attr, getattr(parent_commands, attr))

    def update_commands(self, commands_str):
        """
        update with commands from the block
        """
        commands = dict(parse_qsl(commands_str, keep_blank_values=True))
        _if = commands.get("if", self._if)
        if _if:
            self._if = Condition(_if)
        self._set_int(commands, "max_length")
        self._set_int(commands, "min_length")
        self.color = self._check_color(commands.get("color"))

        self.not_zero = "not_zero" in commands or self.not_zero
        self.show = "show" in commands or self.show
        self.soft = "soft" in commands or self.soft

    def _set_int(self, commands, name):
        """
        set integer value from commands
        """
        if name in commands:
            try:
                value = int(commands[name])
                setattr(self, name, value)
            except ValueError:
                pass

    def _check_color(self, color):
        if not color:
            return self.color
        # fix any hex colors so they are #RRGGBB
        if color.startswith("#"):
            color = color.upper()
            if len(color) == 4:
                color = (
                    "#"
                    + color[1]
                    + color[1]
                    + color[2]
                    + color[2]
                    + color[3]
                    + color[3]
                )
            # check color is valid
            if not self.REGEX_COLOR.match(color):
                return self.color
        return color


class Block:
    """
    class representing a [block] of a format string
    """

    def __init__(self, parent, base_block=None, py3_wrapper=None):

        self.base_block = base_block
        self.commands = BlockConfig(parent)
        self.content = []
        self.next_block = None
        self.parent = parent
        self.py3_wrapper = py3_wrapper

    def set_commands(self, command_str):
        """
        set any commands for this block
        """
        self.commands.update_commands(command_str)

    def add(self, item):
        self.content.append(item)

    def new_block(self):
        """
        create a new sub block to the current block and return it.
        the sub block is added to the current block.
        """
        child = Block(self, py3_wrapper=self.py3_wrapper)
        self.add(child)
        return child

    def switch(self):
        """
        block has been split via | so we need to start a new block for that
        option and return it to the user.
        """
        base_block = self.base_block or self
        self.next_block = Block(
            self.parent, base_block=base_block, py3_wrapper=self.py3_wrapper
        )
        return self.next_block

    def __repr__(self):
        return "<Block %s>" % self.repr()

    def repr(self):
        my_repr = [x.repr() for x in self.content]
        if self.next_block:
            my_repr.extend(["|"] + self.next_block.repr())
        return my_repr

    def check_valid(self, get_params):
        """
        see if the if condition for a block is valid
        """
        if self.commands._if:
            return self.commands._if.check_valid(get_params)

    def render(self, get_params, module, _if=None):
        """
        render the block and return the output.
        """
        enough = False
        output = []
        valid = None

        if self.commands.show:
            valid = True
        if self.parent and self.commands.soft and _if is None:
            return None, self
        if _if:
            valid = True
        elif self.commands._if:
            valid = self.check_valid(get_params)
        if valid is not False:
            for item in self.content:
                if isinstance(item, Placeholder):
                    sub_valid, sub_output, enough = item.get(get_params, self)
                    output.append(sub_output)
                elif isinstance(item, Literal):
                    sub_valid = None
                    enough = True
                    output.append(item.text)
                elif isinstance(item, Block):
                    sub_valid, sub_output = item.render(get_params, module)
                    if sub_valid is None:
                        output.append(sub_output)
                    else:
                        output.extend(sub_output)
                valid = valid or sub_valid
        if not valid:
            if self.next_block:
                valid, output = self.next_block.render(
                    get_params, module, _if=self.commands._if
                )
            elif self.parent is None and (
                (not self.next_block and enough) or self.base_block
            ):
                valid = True
            else:
                output = []

        # clean
        color = self.commands.color
        if color and color[0] != "#":
            color_name = "color_%s" % color
            threshold_color_name = "color_threshold_%s" % color
            # substitute color
            color = (
                getattr(module, color_name, None)
                or getattr(module, threshold_color_name, None)
                or getattr(module.py3, color_name.upper(), None)
            )
            if color == "hidden":
                return False, []

        text = u""
        out = []
        if isinstance(output, str):
            output = [output]

        # merge as much output as we can.
        # we need to convert values to unicode for concatination.
        if python2:
            conversion = unicode  # noqa
            convertables = (str, bool, int, float, unicode)  # noqa
        else:
            conversion = str
            convertables = (str, bool, int, float, bytes)

        first = True
        last_block = None
        for index, item in enumerate(output):
            is_block = isinstance(item, Block)
            if not is_block and item:
                last_block = None
            if isinstance(item, convertables) or item is None:
                text += conversion(item)
                continue
            elif text:
                if not first and (text == "" or out and out[-1].get("color") == color):
                    out[-1]["full_text"] += text
                else:
                    part = {"full_text": text}
                    if color:
                        part["color"] = color
                    out.append(part)
                text = u""
            if isinstance(item, Composite):
                if color:
                    item.composite_update(item, {"color": color}, soft=True)
                out.extend(item.get_content())
            elif is_block:
                # if this is a block then likely it is soft.
                if not out:
                    continue
                for x in range(index + 1, len(output)):
                    if output[x] and not isinstance(output[x], Block):
                        valid, _output = item.render(get_params, module, _if=True)
                        if _output and _output != last_block:
                            last_block = _output
                            out.extend(_output)
                        break
            else:
                if item:
                    out.append(item)
            first = False

        # add any left over text
        if text:
            part = {"full_text": text}
            if color:
                part["color"] = color
            out.append(part)

        # process any min/max length commands
        max_length = self.commands.max_length
        min_length = self.commands.min_length

        if max_length or min_length:
            for item in out:
                if max_length is not None:
                    item["full_text"] = item["full_text"][:max_length]
                    max_length -= len(item["full_text"])
                if min_length:
                    min_length -= len(item["full_text"])
            if min_length > 0:
                out[0]["full_text"] = u" " * min_length + out[0]["full_text"]
                min_length = 0

        return valid, out
