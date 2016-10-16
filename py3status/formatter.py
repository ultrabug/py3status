# -*- coding: utf-8 -*-
import re
import sys

try:
    from urllib.parse import parse_qsl
except ImportError:
    from urlparse import parse_qsl


class Composite:
    """
    Helper class to identify a composite
    and store its content
    """

    def __init__(self, content, name='__Anon__'):
        self.content = content
        self.name = name

    def __repr__(self):
        return u'<Composite `{}`>'.format(self.name)


class BlockConfig:
    """
    Block commands eg [\?color=bad ...] are stored in this object
    """

    # defaults
    _if = None
    color = None
    max_length = None
    show = False

    def update(self, commands_str):
        """
        update with commands from the block
        """
        commands = dict(parse_qsl(commands_str, keep_blank_values=True))

        self._if = commands.get('if', self._if)
        self.color = commands.get('color', self.color)

        max_length = commands.get('max_length')
        if max_length is not None:
            self.max_length = int(max_length)

        self.show = 'show' in commands or self.show


class Block:
    """
    Represents a block of our format.  Block being contained inside [..]

    A block may contain options split by a pipe | and the first 'valid' block
    is the one that will be used.  blocks can contain other blocks and also
    know about their parent block (if they have one)
    """

    def __init__(self, param_dict, composites, module, parent=None):
        self.block_config = BlockConfig()
        self.commands = {}
        self.composites = composites
        self.content = []
        self.is_composite = False
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
        self.block_config.update(commands)

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

    def process_text_chunk(self, text):
        block_config = self.block_config
        if block_config.max_length is not None:
            text = text[:block_config.max_length]
            block_config.max_length -= len(text)
        if text and block_config.color or self.is_composite:
            text = {'full_text': text}
            if block_config.color:
                text['color'] = block_config.color
            if self.parent:
                text = Composite(text)
        return text

    def process_composite_chunk(self, composite):
        out = []
        for item in composite:
            self.process_composite_chunk_item(item)
            if item['full_text']:
                out.append(item)
        return out

    def process_composite_chunk_item(self, item):
        block_config = self.block_config
        if block_config.max_length is not None:
            item['full_text'] = item['full_text'][:block_config.max_length]
            block_config.max_length -= len(item['full_text'])
        if block_config.color and 'color' not in item:
            item['color'] = block_config.color

    def show(self):
        """
        This is where we go output the content of a block and any valid child
        block that it contains.

        """
        # Start by finalising the block.
        # Any active content is added to self.options
        if self.content:
            self.options.append(self.content)

        output = []

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
                        content = item.show()
                        if isinstance(content, list):
                            output.extend(content)
                        else:
                            output.append(content)
                        if item.is_composite:
                            self.is_composite = True
                    else:
                        output.append(item)
                break

        # if not building a composite then we can simply
        # build our output and return it here
        if not self.is_composite:
            data = ''.join(output)
            # apply our max length command
            if self.block_config.max_length is not None:
                data = data[:self.block_config.max_length]
            if self.block_config.color:
                block_composite = {
                    'full_text': data,
                    'color': self.block_config.color,
                }
                data = Composite(block_composite)
                self.is_composite = True
            return data

        # Build up our output.  We join any text pieces togeather and if we
        # have composites we keep them for final substitution in the main block
        data = []
        text = ''
        for item in output:
            if not isinstance(item, Composite):
                text += item
            else:
                if text:
                    data.append(self.process_text_chunk(text))
                text = ''
                if self.parent is None:
                    # This is the main block so we get the actual composites
                    composite = item.content
                    if not isinstance(composite, list):
                        composite = [composite]
                    data += self.process_composite_chunk(composite)
                else:
                    self.process_composite_chunk_item(item.content)
                    data.append(item)
        if text:
            data.append(self.process_text_chunk(text))

        return data


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
        r'|(?P<placeholder>(\{(?P<key>([^}\\\:\!]|\\.)*)(([^}\\]|\\.)*)?\}))'
        r'|(?P<literal>([^\[\]\\\{\}\|])+)'
        r'|(?P<lost_brace>(\}))'
    ]

    python2 = sys.version_info < (3, 0)
    reg_ex = re.compile(TOKENS[0], re.M | re.I)

    def format(self, format_string, module=None, param_dict=None,
               composites=None):
        """
        Format a string.
        substituting place holders which can be found in
        composites, param_dict or as attributes of the supplied module.
        """

        def set_param(param, value, key):
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
                value = value.format(**{key: param})
                block.add(value)
                block.mark_valid()

        # fix python 2 unicode issues
        if self.python2 and isinstance(format_string, str):
            format_string = format_string.decode('utf-8')

        if param_dict is None:
            param_dict = {}

        if composites is None:
            composites = {}

        block = Block(param_dict, composites, module)

        # Tokenize the format string and process them
        for token in re.finditer(self.reg_ex, format_string):
            value = token.group(0)
            if token.group('block_start'):
                # Create new block
                new_block = Block(param_dict, composites, module, block)
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
                if key in composites:
                    # Add the composite
                    if composites[key]:
                        block.add(Composite(composites[key], key))
                        block.is_composite = True
                        block.mark_valid()
                elif key in param_dict:
                    # was a supplied parameter
                    param = param_dict.get(key)
                    set_param(param, value, key)
                elif module and hasattr(module, key):
                    # attribute of the module
                    param = getattr(module, key)
                    if not hasattr(param, '__call__'):
                        set_param(param, value, key)
                    else:
                        block.add(value)
                else:
                    # substitution not found so add as a literal
                    block.add(value)
            elif token.group('literal'):
                block.add(value)
            elif token.group('lost_brace'):
                # due to how parsing happens we can get a lonesome }
                # eg in format_sting '{{something}' this fixes that issue
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
        if composites and not isinstance(output, list):
            if output == '':
                output = []
            else:
                output = [{'full_text': output}]

        # post format
        # swap color names to values
        # merge items if possible

        if isinstance(output, list):
            final_output = []
            diff_last = None
            item_last = None
            for item in output:
                # ignore empty items
                if not item['full_text'] and not item.get('separator'):
                    continue
                # colors
                color_this = item.get('color')
                if color_this and color_this[0] != '#':
                    color_name = 'color_%s' % color_this
                    # substitute color
                    color_this = (
                        getattr(module, color_name, None) or
                        getattr(module.py3, color_name.upper(), None)
                    )
                    if color_this:
                            item['color'] = color_this
                    else:
                        del item['color']
                # merge items if we can
                diff = (
                    item.get('index'),
                    item.get('instance'),
                    item.get('name'),
                    color_this,
                )
                if diff == diff_last:
                    item_last['full_text'] += item['full_text']
                else:
                    diff_last = diff
                    item_last = item.copy()  # copy item as we may change it
                    final_output.append(item_last)
            return final_output
        return output
