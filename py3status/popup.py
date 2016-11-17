import shlex
import json

from subprocess import Popen, PIPE, check_output
from threading import Thread

# see if gtk/pango available for font measurement
# otherwise we will do a best guess
try:
    import gtk
    import pango
except ImportError:
    gtk = None


PADDING = 10
BORDER = 1
FG = '#FFFFFF'
BG = '#000000'
BORDER_COLOR = '#666666'

# FIXME get from config
BAR = 'bar-0'

SELECTOR_ON = u'\u25a0'
SELECTOR_OFF = u'\u25a1'


class PopupController:
    """
    This allows popups to be actioned via dzen2
    """

    def __init__(self, py3_wrapper):
        self.auto_update = False
        self.dzen2_available = None
        self.dzen2_xft = None
        self.event_x = 0
        self.module_name = None
        self.process = None
        self.py3_wrapper = py3_wrapper
        self.font_cache = {}

    def close(self, module_name=None):
        """
        Close the popup.
        """
        # prevent auto closing
        if module_name and module_name == self.module_name:
            return
        if self.process:
            try:
                self.process.kill()
                self.process = None
            except:
                pass

    def popup(self, module_name, lines, type, callback=None):
        """
        Show a popup
        """

        if not self.dzen2_available:
            if self.dzen2_available is False:
                # dzen2 is not available so no popups.
                return
            # check for dzen2
            if Popen(['which', 'dzen2'], stdout=PIPE, stderr=PIPE).wait() != 0:
                self.py3_wrapper.notify_user(
                    'dzen2 not installed, popups not available'
                )
                # not present
                self.dzen2_available = False
                return
            self.dzen2_available = True
            if 'XFT' not in self.get_output('dzen2 -v'):
                self.py3_wrapper.log('dzen2 does not support XFT')
                self.dzen2_xft = False
            else:
                self.dzen2_xft = True

        self.type = type
        self.callback = callback
        x = self.event_x
        # The popup will be shown in a thread
        self.thread = Thread(target=self.start_popup,
                             args=(module_name, x, lines, type))
        self.thread.daemon = True
        self.thread.start()

    def popup_toggle(self, module_name, lines, type, callback=None):
        """
        Close popup if open else show
        """

        if self.module_name == module_name:
            self.close()
        else:
            self.popup(module_name, lines, type, callback)

    def popup_update(self, module_name, data):
        """
        update the popup info
        """

        if self.module_name != module_name:
            return
        self.auto_update = False
        self.process_input(data, self.num_lines)
        if self.num_lines == 1:
            self.run_dzen2(module_name)
        else:
            self.write_lines(self.process)

    def process_input(self, lines, num_lines=None):
        """
        Process the info for the popup.
        converts string to list etc
        """
        if not isinstance(lines, list):
            lines = lines.splitlines()

        items = []

        for text in lines:
            value = None
            if isinstance(text, tuple):
                text, value = text
            full_text = u'{}{}'.format(self.selector.get(value, ''), text).rstrip()
            items.append(dict(full_text=full_text, value=value, text=text))
        # add blank lines to fill height of popup if needed.
        while num_lines and len(items) < num_lines:
            items.append(dict(full_text='', value=None, text=''))
        self.items = items

    def write_lines(self, process):
        """
        Writes the full info to the popup
        """

        if self.num_lines != 1:
            process.stdin.write('^cs()\n')
        for index, item in enumerate(self.items):
            if (self.type == 'menu' or
                    (self.down and index == self.num_lines - 1) or
                    (not self.down and index == 0)):
                line_break = self.line
            else:
                line_break = ''
            process.stdin.write(
                self.template.format(text=item['full_text'], line=line_break)
            )
        if self.num_lines != 1:
            process.stdin.write('^scrollhome()\n')
        process.stdin.flush()

    def get_output(self, cmd):
        """
        runs a command and gets the output as utf-8
        """

        output = check_output(shlex.split(cmd), universal_newlines=True).strip()
        try:
            output = output.decode('utf-8')
        except AttributeError:
            pass
        return output

    def calculate_width_fallback(self, font_size):
        """
        Do a best guess at calculating maximum text width
        """
        max_length = 0
        for item in self.items:
            length = len(item['full_text']) * font_size / 1.6
            max_length = max(max_length, length)
        width = int(max_length)
        return width

    def calculate_pango_size(self, font):
        """
        Calculate maximum text width using gtk and pango
        """
        label = gtk.Label()
        pango_layout = label.get_layout()
        pango_font_desc = pango.FontDescription(font)
        pango_layout.set_font_description(pango_font_desc)

        max_length = 0
        for item in self.items:
            pango_layout.set_markup(item['full_text'])
            length = pango_layout.get_pixel_size()[0]
            max_length = max(max_length, length)
        width = max_length
        return width

    def process_font(self, font):
        """
        Convert a font to one that dzen2 can understand.
        """
        if font in self.font_cache:
            return self.font_cache[font]
        if not font.startswith('pango:'):
            font = font.strip()
            self.font_cache[font] = font
            return font

        # pango font definition
        font = font[6:].strip()
        # size
        try:
            font_size = int(font.split()[-1])
        except:
            font_size = 12

        if not self.dzen2_xft:
            # we can't use a pango font
            # FIXME need a better way to choose font here using `xlsfonts`
            font_str = '-misc-fixed-medium-r-normal--13-120-75-75-c-70-iso10646-1'
            self.font_cache[font] = font_str
            return font_str

        # family find longest matching font string
        try:
            font_list = self.get_output('fc-list : family').splitlines()
        except:
            font_list = []
        fonts = []
        match = ''
        for font_name in font_list:
            fonts += font_name.split(',')
        for font_name in sorted(fonts):
            if font.startswith(font_name):
                if len(font_name) > len(match):
                    match = font_name

        if match:
            extras = u''.join(font.split()[:-1])[len(match):]
            if extras:
                font_str = u'{}-{} {}'.format(match, font_size, extras)
            else:
                font_str = u'{}-{}'.format(match, font_size)
            self.font_cache[font] = font_str
            return font_str

    def start_popup(self, module_name, x, lines, type='info'):
        """
        Helper to start a popup.  We log any exceptions here
        """
        try:
            self.action_popup(module_name, x, lines, type=type)
        except Exception:
            self.py3_wrapper.report_exception('Error processing event')

    def action_popup(self, module_name, x, lines, type):
        """
        Actually do the popup here
        """
        border = BORDER

        data = json.loads(self.get_output('i3-msg -t get_workspaces'))
        for workspace in data:
            if workspace['focused']:
                output = workspace['output']
                workspace_height = workspace['rect']['height']
                break

        data = json.loads(self.get_output('i3-msg -t get_outputs'))
        for output_info in data:
            if output_info['name'] == output:
                screen_width = output_info['rect']['width']
                screen_height = output_info['rect']['height']
                break

        # line height is based on the height of the i3bar
        line_height = screen_height - workspace_height
        # how many lines can we fit on the screen
        max_lines = (screen_height // line_height) - 1

        font_size = line_height - PADDING

        data = json.loads(self.get_output('i3-msg -t get_bar_config %s' % BAR))
        font = data['font']
        position = data['position']
        colors = data['colors']

        config_fn = self.py3_wrapper.get_config_attribute
        fg = config_fn(module_name, 'popup_fg') or colors.get('statusline', FG)
        bg = config_fn(module_name, 'popup_bg') or colors.get('background', BG)
        highlight_bg = config_fn(module_name, 'popup_highlight_bg') or fg
        highlight_fg = config_fn(module_name, 'popup_highlight_fg') or bg
        border_color = config_fn(module_name, 'popup_border') or BORDER_COLOR

        self.selector = {
            True: u'{} '.format(
                config_fn(module_name, 'popup_selector_on') or SELECTOR_ON
            ),
            False: u'{} '.format(
                config_fn(module_name, 'popup_selector_off') or SELECTOR_OFF
            ),
        }
        self.process_input(lines)

        if gtk:
            width = self.calculate_pango_size(font)
        else:
            width = self.calculate_width_fallback(font_size)

        # we want some padding in the popup
        width += (PADDING * 4)

        # limit to width of screen
        if width > screen_width:
            width = screen_width

        font = self.process_font(font)
        num_lines = len(self.items)
        self.num_lines = num_lines

        x = x - width // 2

        if x < 0:
            x = 0
        elif x > screen_width - width:
            x = screen_width - width

        events = [
            'button3=ungrabkeys,exit;',
            'button4=scrollup;',
            'button5=scrolldown;',
            'key_Escape=ungrabkeys,exit;',
        ]

        extra_options = ''
        if type == 'menu':
            if num_lines == 1:
                events.append('button1=exit:99;')
            else:
                extra_options = ' -m'
                events.append('button1=menuprint;')
        else:
            events.append('button1=exit;')

        if position == 'bottom':
            y = -line_height
            border_pos = 0
            self.down = False
            # if only one line then we will be using the dzen title
            if num_lines == 1:
                y *= 2
        else:
            y = 0
            if num_lines == 1:
                y = line_height
            border_pos = line_height - border
            self.down = True

        # if only one line then we will be using the dzen title
        if num_lines == 1:
            events.append('onstart=raise;')  # ,grabkeys;'
        else:
            events.append('onstart=uncollapse,hide,scrollhome;')  # ,grabkeys;'

        cmd = (
            'dzen2 -x {x} -y {y} -w {width}'
            ' {extra_options}'
            ' -p -ta l -sa l'
            ' -l {num_lines}'
            ' -bg "{bg}"'
            ' -fg "{highlight_bg}"'
            ' -fn \'{font}\''
            ' -h {line_height}'
            ' -e "{events}"'
        ).format(
            font=font,
            extra_options=extra_options,
            line_height=line_height,
            num_lines=min(max_lines, num_lines),
            x=x,
            y=y,
            bg=bg,
            highlight_bg=highlight_bg,
            width=width,
            events=''.join(events),
        )

        template = (
            '^ib(1)^pa({padding})'
            '^bg({highlight_fg})'
            '^fg({fg})'
            '{{text}}'
            '^fg({border_color})'
            '^pa(0;0)'
            '^r({border}x{line_height})'
            '{{line}}'
            '^pa({width};0)'
            '^r({border}x{line_height})'
            '^fg({fg})'
            '\n'
        )
        self.template = (template).format(
            border=border,
            padding=PADDING,
            width=width - border,
            line_height=line_height,
            border_color=border_color,
            fg=fg,
            highlight_fg=highlight_fg,
        )

        line = (
            '^pa(0;{border_pos})'
            '^r({width}x{border})'
        )

        self.line = (line).format(
            border=border,
            border_pos=border_pos,
            width=width - border,
        )

        self.dzen2_cmd = cmd
        self.run_dzen2(module_name)

    def run_dzen2(self, module_name):
        """
        Run the actual dzen2 command here.
        We do this because we need to be able to rerun the command to deal with
        single line popups as they use the title window not the slave window.
        """
        if self.py3_wrapper.config['debug']:
            self.py3_wrapper.log('popup command `{}`'.format(self.dzen2_cmd))
        command = shlex.split(self.dzen2_cmd)
        try:
            process = Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE,
                            universal_newlines=True)
        except:
            self.py3_wrapper.report_exception('popup dzen2 command failed')
            return

        self.write_lines(process)
        self.close()
        self.module_name = module_name
        self.process = process

        ignore = True

        while True:
            if not self.process:
                break
            nextline = self.process.stdout.readline()
            if nextline == '':
                if not self.process:
                    break
                err_no = self.process.poll()
                if err_no is not None:
                    # single line popup special case
                    if self.num_lines == 1 and err_no == 99:
                        item = self.items[0]
                        if item['value'] is not None:
                            item['value'] = not item['value']
                            self.auto_update = True
                        self.process = None
                        self.do_callback(item['text'])
                    break
            # ignore the first line of output
            if ignore:
                ignore = False
                continue

            # remove \n
            nextline = nextline[:-1]

            for item in self.items:
                if item['full_text'] == nextline:
                    if item['value'] is not None:
                        item['value'] = not item['value']
                        self.auto_update = True
                        # update the display text
                        item['full_text'] = u'{}{}'.format(
                            self.selector.get(item['value'], ''),
                            item['text']
                        ).rstrip()
                    self.do_callback(item['text'])
                    break
        self.process = None
        self.module_name = None

    def do_callback(self, clicked_item):
        """
        Run the callback if one has been set
        """
        if self.callback:
            module_name = self.module_name
            output = {}
            for item in self.items:
                if item['value'] is not None:
                    output[item['text']] = item['value']
            self.auto_update = True
            self.callback(clicked_item, output)
        if self.auto_update and self.process:
            if self.num_lines == 1:
                self.run_dzen2(module_name)
            else:
                self.write_lines(self.process)
