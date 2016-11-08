# -*- coding: utf-8 -*-
import re
import sys

from py3status.composite import Composite

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl


class BlockConfig:
    """
    Block commands eg [\?color=bad ...] are stored in this object
    """

    REGEX_COLOR = re.compile('#[0-9A-F]{6}')

    # defaults
    _if = None
    color = None
    has_commands = False
    max_length = None
    min_length = 0
    show = False

    def update_commands(self, commands_str):
        """
        update with commands from the block
        """
        commands = dict(parse_qsl(commands_str, keep_blank_values=True))

        self._if = commands.get('if', self._if)
        self.color = self._check_color(commands.get('color'))
        self._set_int(commands, 'max_length')
        self._set_int(commands, 'min_length')

        self.show = 'show' in commands or self.show

        self.has_commands = True

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
        if color.startswith('#'):
            color = color.upper()
            if len(color) == 4:
                color = ('#' + color[1] + color[1] + color[2] +
                         color[2] + color[3] + color[3])
            # check color is valid
            if not self.REGEX_COLOR.match(color):
                return self.color
        return color


class Block:
    """
    Represents a block of our format.  Block being contained inside [..]

    A block may contain options split by a pipe | and the first 'valid' block
    is the one that will be used.  blocks can contain other blocks and also
    know about their parent block (if they have one)
    """

    def __init__(self, param_dict, module, parent=None):
        self.block_config = BlockConfig()
        self.commands = {}
        self.content = []
        self.module = module
        self.options = []
        self.param_dict = param_dict
        self.parent = parent
        self.valid_blocks = set()

    def __repr__(self):
        return u'<Block {!r}>'.format(self.options)

    def add(self, item):
        """
        Add item to the block
        """
        if not isinstance(item, Block):
            item = Composite(item)
        self.content.append(item)

    def switch(self):
        """
        New option has been started
        """
        self.options.append(self.content)
        self.content = []

    def mark_valid(self, index=None):
        """
        Mark the current block as valid. Propogate this to any parent blocks
        """
        self.valid_blocks.add(index or len(self.options))
        if self.parent:
            self.parent.mark_valid()

    def set_commands(self, commands):
        """
        Process any commands into a dict and store
        commands are url query string encoded
        """
        self.block_config.update_commands(commands)

    def is_valid_by_command(self, index=None):
        """
        Check if we have a command forcing the block to be valid or not
        """
        # If this is not the first option in a block we ignore it.
        if index:
            return None
        if self.block_config._if:
            _if = self.block_config._if
            if _if and _if.startswith('!'):
                if not self.param_dict.get(_if[1:]):
                    return True
                else:
                    return False
            else:
                if self.param_dict.get(_if):
                    return True
                else:
                    return False
        if self.block_config.show:
            return True
        # explicitly return None to aid code readability
        return None

    def set_valid_state(self):
        """
        Mark block valid if a command requests
        """
        cmd_state = self.is_valid_by_command()
        if cmd_state is True:
            self.mark_valid()
        elif cmd_state is False:
            # This enables the second option in a block if \?if=.. is false.
            self.mark_valid(index=1)

    def process_composite_chunk_item(self, items):
        block_config = self.block_config
        if not block_config.has_commands:
            return
        for item in items:
            if block_config.max_length is not None:
                item['full_text'] = item['full_text'][:block_config.max_length]
                block_config.max_length -= len(item['full_text'])
            if block_config.min_length:
                block_config.min_length -= len(item['full_text'])
            if block_config.color and 'color' not in item:
                item['color'] = block_config.color
        if block_config.min_length > 0:
            items[0]['full_text'] = u' ' * block_config.min_length + items[0]['full_text']
            block_config.min_length = 0

    def show(self):
        """
        This is where we go output the content of a block and any valid child
        block that it contains.

        """
        # Start by finalising the block.
        # Any active content is added to self.options
        if self.content:
            self.options.append(self.content)

        output = Composite()

        for index, option in enumerate(self.options):
            if index in self.valid_blocks:
                # A block may be valid but has a command that causes this to be
                # disregarded.
                if self.is_valid_by_command(index) is False:
                    continue
                # add the content of the block and any children
                # to the output
                for item in option:
                    if isinstance(item, Block):
                        output.append(item.show())
                    else:
                        output.append(item)
                break

        # Build up our output.
        self.process_composite_chunk_item(output.get_content())
        return output


class Formatter:
    """
    Formatter for processing format strings via the format method.
    """

    TOKENS = [
        r'(?P<block_start>\[)'
        r'|(?P<block_end>\])'
        r'|(?P<switch>\|)'
        r'|(\\\?(?P<command>\S*)\s)'
        r'|(?P<escaped>(\\.|\{\{|\}\}))'
        r'|(?P<placeholder>(\{(?P<key>([^}\\\:\!]|\\.)*)(?P<format>([^}\\]|\\.)*)?\}))'
        r'|(?P<literal>([^\[\]\\\{\}\|])+)'
        r'|(?P<lost_brace>(\}))'
    ]

    python2 = sys.version_info < (3, 0)
    reg_ex = re.compile(TOKENS[0], re.M | re.I)

    def get_placeholders(self, format_string):
        """
        Parses the format_string and returns a set of placeholders.
        """
        placeholders = set()
        # Tokenize the format string and process them
        for token in re.finditer(self.reg_ex, format_string):
            if token.group('placeholder'):
                placeholders.add(token.group('key'))
        return placeholders

    def update_placeholders(self, format_string, placeholders):
        """
        Update a format string renaming placeholders.
        """

        # Tokenize the format string and process them
        output = []
        for token in re.finditer(self.reg_ex, format_string):
            if token.group('key') in placeholders:
                output.append('{%s%s}' % (
                    placeholders[token.group('key')],
                    token.group('format'))
                )
                continue
            value = token.group(0)
            output.append(value)
        return u''.join(output)

    def update_placeholder_formats(self, format_string, placeholder_formats):
        """
        Update a format string adding formats if they are not already present.
        """
        # Tokenize the format string and process them
        output = []
        for token in re.finditer(self.reg_ex, format_string):
            if (token.group('placeholder') and
                    (not token.group('format')) and
                    token.group('key') in placeholder_formats):
                output.append('{%s%s}' % (
                    token.group('key'),
                    placeholder_formats[token.group('key')])
                )
                continue
            value = token.group(0)
            output.append(value)
        return u''.join(output)

    def format(self, format_string, module=None, param_dict=None,
               force_composite=False, attr_getter=None):
        """
        Format a string, substituting place holders which can be found in
        param_dict, attributes of the supplied module, or provided via calls to
        the attr_getter function.
        """

        def set_param(param, value, key, format=''):
            """
            Converts a placeholder to a string value.
            We fix python 2 unicode issues and use string.format()
            to ensure that formatting is applied correctly
            """
            if self.python2 and isinstance(param, str):
                param = param.decode('utf-8')
            # '', None, and False are ignored
            # numbers like 0 and 0.0 are not.
            if not (param in ['', None] or param is False):
                if format.startswith(':'):
                    # if a parameter has been set to be formatted as a numeric
                    # type then we see if we can coerce it to be.  This allows
                    # the user to format types that normally would not be
                    # allowed eg '123' it also allows {:d} to be used as a
                    # shorthand for {:.0f}.  If the parameter cannot be
                    # successfully converted then the format is removed.
                    try:
                        if 'f' in format:
                            param = float(param)
                        if 'd' in format:
                            param = int(float(param))
                    except ValueError:
                        value = u'{%s}' % key
                value = value.format(**{key: param})
                block.add(value)
                block.mark_valid()

        # fix python 2 unicode issues
        if self.python2 and isinstance(format_string, str):
            format_string = format_string.decode('utf-8')

        if param_dict is None:
            param_dict = {}

        block = Block(param_dict, module)

        # Tokenize the format string and process them
        for token in re.finditer(self.reg_ex, format_string):
            value = token.group(0)
            if token.group('block_start'):
                # Create new block
                new_block = Block(param_dict, module, block)
                block.add(new_block)
                block = new_block
            elif token.group('block_end'):
                # Close block setting any valid state as needed
                # and return to parent block to continue
                block.set_valid_state()
                if not block.parent:
                    raise Exception('Too many `]`')
                block = block.parent
            elif token.group('switch'):
                # a new option has been created
                block.set_valid_state()
                block.switch()
            elif token.group('placeholder'):
                # Found a {placeholder}
                key = token.group('key')
                if key in param_dict:
                    # was a supplied parameter
                    param = param_dict.get(key)
                    if isinstance(param, Composite):
                        # supplied parameter is a composite
                        if param.get_content():
                            block.add(param.copy())
                            block.mark_valid()
                    else:
                        format = token.group('format')
                        set_param(param, value, key, format)
                elif module and hasattr(module, key):
                    # attribute of the module
                    param = getattr(module, key)
                    if not hasattr(param, '__call__'):
                        set_param(param, value, key)
                    else:
                        block.add(value)
                elif attr_getter:
                    # get value from attr_getter function
                    param = attr_getter(key)
                    set_param(param, value, key)
                else:
                    # substitution not found so add as a literal
                    block.add(value)
            elif token.group('literal'):
                block.add(value)
            elif token.group('lost_brace'):
                # due to how parsing happens we can get a lonesome }
                # eg in format_string '{{something}' this fixes that issue
                block.add(value)
            elif token.group('command'):
                # a block command has been found
                block.set_commands(token.group('command'))
            elif token.group('escaped'):
                # escaped characters add unescaped values
                if value[0] in ['\\', '{', '}']:
                    value = value[1:]
                block.add(value)

        if block.parent:
            raise Exception('Block not closed')

        # This is the main block if none of the sections are valid use the last
        # one for situations like '{placeholder}|Nothing'
        if not block.valid_blocks:
            block.mark_valid()
        output = block.show()

        # post format
        # swap color names to values
        for item in output:
            # ignore empty items
            if not item.get('full_text') and not item.get('separator'):
                continue
            # colors
            color_this = item.get('color')
            if color_this and color_this[0] != '#':
                color_name = 'color_%s' % color_this
                threshold_color_name = 'color_threshold_%s' % color_this
                # substitute color
                color_this = (
                    getattr(module, color_name, None) or
                    getattr(module, threshold_color_name, None) or
                    getattr(module.py3, color_name.upper(), None)
                )
                if color_this:
                        item['color'] = color_this
                else:
                    del item['color']
        output = Composite(output).simplify()
        # if only text then we can become a string
        if not force_composite:
            if len(output) == 0:
                return ''
            elif (len(output) == 1 and list(output[0].keys()) == ['full_text']):
                output = output[0]['full_text']

        return output
