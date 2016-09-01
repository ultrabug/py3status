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


class Block:
    """
    Represents a block of our format.  Block being contained inside [..]

    A block may contain options split by a pipe | and the first 'valid' block
    is the one that will be used.  blocks can contain other blocks and also
    know about their parent block (if they have one)
    """

    def __init__(self, param_dict, composites, module, parent=None):
        self.commands = {}
        self.composites = composites
        self.is_composite = False
        self.content = []
        self.module = module
        self.options = []
        self.param_dict = param_dict
        self.parent = parent
        self.valid_blocks = set()

    def __repr__(self):
        return repr(self.options)

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
        self.commands.update(parse_qsl(commands, keep_blank_values=True))

    def is_valid_by_command(self, index=None):
        """
        Check if we have a command forcing the block to be valid or not
        """
        # If this is not the first option in a block we ignore it.
        if index:
            return None
        if 'if' in self.commands:
            _if = self.commands['if']
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
        if 'show' in self.commands:
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
            if 'max_length' in self.commands:
                data = data[:int(self.commands['max_length'])]
            if 'color' in self.commands:
                block_composite = {
                    'full_text': data,
                    'color': self.commands['color'],
                }
                data = Composite(block_composite)
                self.is_composite = True
            return data

        # Build up our output.  We join any text pieces togeather and if we
        # have composites we keep them for final substitution in the main block
        class Options:
            max_length = self.commands.get('max_length')
            if max_length is not None:
                max_length = int(max_length)
            color = self.commands.get('color')

        def process_text_chunk(text, Options):
            if Options.max_length is not None:
                text = text[:Options.max_length]
                Options.max_length -= len(text)
            if text and Options.color or self.is_composite:
                text = {'full_text': text}
                if Options.color:
                    text['color'] = Options.color
                if self.parent:
                    text = Composite(text)
            return text

        def process_composite_chunk(composite, Options):
            out = []
            for item in composite:
                process_composite_chunk_item(item, Options)
                if item['full_text']:
                    out.append(item)
            return out

        def process_composite_chunk_item(item, Options):
            if Options.max_length is not None:
                item['full_text'] = item['full_text'][:Options.max_length]
                Options.max_length -= len(item['full_text'])
            if Options.color and not 'color' in item:
                item['color'] = Options.color

        data = []
        text = ''
        for item in output:
            if not isinstance(item, Composite):
                text += item
            else:
                if text:
                    data.append(process_text_chunk(text, Options))
                text = ''
                if self.parent is None:
                    # This is the main block so we get the actual composites
                    composite = item.content
                    if not isinstance(composite, list):
                        composite = [composite]
                    data += process_composite_chunk(composite, Options)
                else:
                    process_composite_chunk_item(item.content, Options)
                    data.append(item)
        if text:
            data.append(process_text_chunk(text, Options))

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

        is_composite = composites is not None

        def set_param(param, value, key):
            """
            Converts a placeholder to a string value.
            We fix python 2 unicode issues and use string.format()
            to ensure that formatting is applied correctly
            """
            if self.python2 and isinstance(param, str):
                param = param.decode('utf-8')
            if param or param is 0:
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


if __name__ == '__main__':

    """
    Run formatter tests
    """

    f = Formatter()

    param_dict = {
        'name': u'Björk',
        'number': 42,
        'pi': 3.14159265359,
        'yes': True,
        'no': False,
        'empty': '',
        'None': None,
        '?bad name': 'evil',
        u'☂ Very bad name ': u'☂ extremely evil',
        'long_str': 'I am a long string though not too long',
        'python2_unicode': u'Björk',
        'python2_str': 'Björk',
        'zero': 0,
    }

    composites = {
        'complex': [{'full_text': 'LA 09:34'}, {'full_text': ' NY 12:34'}],
        'simple': {'full_text': 'NY 12:34'},
        'indexed': {'full_text': 'NY 12:34'},
        'empty': [],
    }

    class Module:
        module_param = 'something'

        def module_method(self):
            return 'method'

        @property
        def module_property(self):
            return 'property'

        class py3:
            COLOR_BAD = '#FF0000'
            COLOR_DEGRADED = '#FF00'
            COLOR_GOOD = '#00FF00'


    tests = [
        {
            'format': u'hello ☂',
            'expected': u'hello ☂',
        },
        {
            'format': 'hello ☂',
            'expected': u'hello ☂',
        },
        {
            'format': '[hello]',
            'expected': '',
        },
        {
            'format': r'\\ \[ \] \{ \}',
            'expected': r'\ [ ] { }',
        },
        {
            'format': '{{hello}}',
            'expected': '{hello}',
        },
        {
            'format': '{{hello}',
            'expected': '{hello}',
        },
        {
            'format': '{?bad name}',
            'expected': 'evil',
        },
        {
            'format': '{☂ Very bad name }',
            'expected': '☂ extremely evil',
        },
        {
            'format': '{missing} {name} {number}',
            'expected': '{missing} Björk 42',
        },
        {
            'format': '{missing}|{name}|{number}',
            'expected': 'Björk',
        },
        {
            'format': '{missing}|empty',
            'expected': 'empty',
        },
        {
            'format': '[{missing}|empty]',
            'expected': '',
        },
        {
            'format': 'pre [{missing}|empty] post',
            'expected': 'pre  post',
        },
        {
            'format': 'pre [{missing}|empty] post|After',
            'expected': 'After',
        },
        {
            'format': '{module_param}',
            'expected': 'something',
        },
        {
            'format': '{module_method}',
            'expected': '{module_method}',
        },
        {
            'format': '{module_property}',
            'expected': 'property',
        },
        {
            'format': 'Hello {name}!',
            'expected': 'Hello Björk!',
        },
        {
            'format': '[Hello {name}!]',
            'expected': 'Hello Björk!',
        },
        {
            'format': '[Hello {missing}|Anon!]',
            'expected': '',
        },
        {
            'format': 'zero [one [two [three [no]]]]|Numbers',
            'expected': 'Numbers',
        },
        {
            'format': 'zero [one [two [three [{yes}]]]]|Numbers',
            'expected': 'zero one two three True',
        },
        {
            'format': 'zero [one [two [three [{no}]]]]|Numbers',
            'expected': 'Numbers',
        },
        # zero/False/None etc
        {
            'format': '{zero}',
            'expected': '0',
        },
        {
            'format': '[{zero}] hello',
            'expected': '0 hello',
        },
        {
            'format': '[{zero} ping] hello',
            'expected': '0 ping hello',
        },
        {
            'format': '{None}',
            'expected': '',
        },
        {
            'format': '[{None}] hello',
            'expected': ' hello',
        },
        {
            'format': '[{None} ping] hello',
            'expected': ' hello',
        },
        {
            'format': '{no}',
            'expected': '',
        },
        {
            'format': '[{no}] hello',
            'expected': ' hello',
        },
        {
            'format': '[{no} ping] hello',
            'expected': ' hello',
        },
        {
            'format': '{yes}',
            'expected': 'True',
        },
        {
            'format': '[{yes}] hello',
            'expected': 'True hello',
        },
        {
            'format': '[{yes} ping] hello',
            'expected': 'True ping hello',
        },
        {
            'format': '{empty}',
            'expected': '',
        },
        {
            'format': '[{empty}] hello',
            'expected': ' hello',
        },
        {
            'format': '[{empty} ping] hello',
            'expected': ' hello',
        },
        # python 2 unicode
        {
            'format': 'Hello {python2_unicode}! ☂',
            'expected': 'Hello Björk! ☂',
        },
        {
            'format': u'Hello {python2_unicode}! ☂',
            'expected': 'Hello Björk! ☂',
        },
        {
            'format': 'Hello {python2_str}! ☂',
            'expected': 'Hello Björk! ☂',
        },
        {
            'format': u'Hello {python2_str}! ☂',
            'expected': 'Hello Björk! ☂',
        },
        # formatting
        {
            'format': '{name}',
            'expected': 'Björk',
        },
        {
            'format': '{name!s}',
            'expected': 'Björk',
        },
        {
            'format': '{name!r}',
            'expected': "'Björk'",
            'py3only': True,
        },
        {
            'format': '{name:7}',
            'expected': 'Björk  ',
        },
        {
            'format': '{name:<7}',
            'expected': 'Björk  ',
        },
        {
            'format': '{name:>7}',
            'expected': '  Björk',
        },
        {
            'format': '{name:*^9}',
            'expected': '**Björk**',
        },
        {
            'format': '{long_str}',
            'expected': 'I am a long string though not too long',
        },
        {
            'format': '{long_str:.6}',
            'expected': 'I am a',
        },
        {
            'format': '{number}',
            'expected': '42',
        },
        {
            'format': '{number:04d}',
            'expected': '0042',
        },
        {
            'format': '{pi}',
            'expected': '3.14159265359',
        },
        {
            'format': '{pi:05.2f}',
            'expected': '03.14',
        },
        # commands
        {
            'format': '{missing}|\?show Anon',
            'expected': 'Anon',
        },
        {
            'format': 'Hello [{missing}|[\?show Anon]]!',
            'expected': 'Hello Anon!',
        },
        {
            'format': '[\?if=yes Hello]',
            'expected': 'Hello',
        },
        {
            'format': '[\?if=no Hello]',
            'expected': '',
        },
        {
            'format': '[\?if=missing Hello]',
            'expected': '',
        },
        {
            'format': '[\?if=!yes Hello]',
            'expected': '',
        },
        {
            'format': '[\?if=!no Hello]',
            'expected': 'Hello',
        },
        {
            'format': '[\?if=!missing Hello]',
            'expected': 'Hello',
        },
        {
            'format': '[\?if=yes Hello[ {name}]]',
            'expected': 'Hello Björk',
        },
        {
            'format': '[\?if=no Hello[ {name}]]',
            'expected': '',
        },
        {
            'format': '[\?if=!yes Hello|Goodbye|Something else]',
            'expected': 'Goodbye',
        },
        {
            'format': '[\?if=!no Hello|Goodbye]',
            'expected': 'Hello',
        },
        {
            'format': '[\?max_length=10 Hello {name} {number}]',
            'expected': 'Hello Björ',
        },
        {
            'format': '\?max_length=9 Hello {name} {number}',
            'expected': 'Hello Bjö',
        },
        # Errors
        {
            'format': 'hello]',
            'exception': 'Too many `]`',
        },
        {
            'format': '[hello',
            'exception': 'Block not closed',
        },
        # Composites
        {
            'format': '{empty}',
            'expected': [],
            'composite': True,
        },
        {
            'format': '{simple}',
            'expected': [{'full_text': 'NY 12:34'}],
            'composite': True,
        },
        {
            'format': '{complex}',
            'expected': [{'full_text': 'LA 09:34 NY 12:34'}],
            'composite': True,
        },
        {
            'format': 'TEST {simple}',
            'expected': [{'full_text': u'TEST NY 12:34'}],
            'composite': True,
        },
        {
            'format': '[{empty}]',
            'expected': [],
            'composite': True,
        },
        {
            'format': '[{simple}]',
            'expected': [{'full_text': 'NY 12:34'}],
            'composite': True,
        },
        {
            'format': '[{complex}]',
            'expected': [{'full_text': 'LA 09:34 NY 12:34'}],
            'composite': True,
        },
        {
            'format': 'test [{simple}]',
            'expected': [{'full_text': u'test NY 12:34'}],
            'composite': True,
        },
        {
            'format': '{simple} TEST [{name}[ {number}]]',
            'expected': [
                {'full_text': 'NY 12:34 TEST Björk 42'}
            ],
            'composite': True,
        },
        # block colors
        {
            'format': '[\?color=bad {name}]',
            'expected':  [{'full_text': 'Björk', 'color': '#FF0000'}],
        },
        {
            'format': '[\?color=good Name [\?color=bad {name}] hello]',
            'expected':  [
                {'full_text': 'Name ', 'color': '#00FF00'},
                {'full_text': 'Björk', 'color': '#FF0000'},
                {'full_text': ' hello', 'color': '#00FF00'}
            ],
        },
        {
            'format': '[\?max_length=20&color=good Name [\?color=bad {name}] hello]',
            'expected':  [
                {'full_text': 'Name ', 'color': '#00FF00'},
                {'full_text': 'Björk', 'color': '#FF0000'},
                {'full_text': ' hello', 'color': '#00FF00'}
            ],
        },
        {
            'format': '[\?max_length=8&color=good Name [\?color=bad {name}] hello]',
            'expected':  [
                {'full_text': 'Name ', 'color': '#00FF00'},
                {'full_text': 'Bjö', 'color': '#FF0000'}
            ],

        },
        {
            'format': '[\?color=bad {name}][\?color=good {name}]',
            'expected': [
                {'full_text': 'Björk', 'color': '#FF0000'},
                {'full_text': 'Björk', 'color': '#00FF00'}
            ],
        },
        {
            'format': '[\?color=bad {name}] [\?color=good {name}]',
            'expected': [
                {'full_text': 'Björk', 'color': '#FF0000'},
                {'full_text': ' '},
                {'full_text': 'Björk', 'color': '#00FF00'}
            ],
        },
    ]

    passed = 0
    failed = 0
    module = Module()

    for test in tests:
        if test.get('py3only') and f.python2:
            continue
        try:
            if test.get('composite'):
                result = f.format(
                    test['format'],
                    module,
                    param_dict,
                    composites,
                )
            else:
                result = f.format(test['format'], module, param_dict)
        except Exception as e:
            if test.get('exception') == str(e):
                passed += 1
                continue
            else:
                print('Fail %r' % test['format'])
                print('exception raised %r' % e)
                print('')
                failed += 1
        expected = test.get('expected')
        if f.python2 and isinstance(expected, str):
            expected = expected.decode('utf-8')
        if result == expected:
            passed += 1
        else:
            print('Fail %r' % test['format'])
            print('expected %r' % expected)
            print('got      %r' % result)
            print('')
            failed += 1

    print('Tests complete: %s passed %s failed' % (passed, failed))
