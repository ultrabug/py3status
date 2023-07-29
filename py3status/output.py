import sys
from json import dumps


class OutputFormat:
    """
    A base class for formatting the output of py3status for various
    different consumers
    """

    @classmethod
    def instance_for(cls, output_format):
        """
        A factory for OutputFormat objects
        """
        supported_output_formats = {
            "dzen2": Dzen2OutputFormat,
            "i3bar": I3barOutputFormat,
            "lemonbar": LemonbarOutputFormat,
            "none": NoneOutputFormat,
            "term": TermOutputFormat,
            "tmux": TmuxOutputFormat,
            "xmobar": XmobarOutputFormat,
        }

        if output_format in supported_output_formats:
            return supported_output_formats[output_format]()
        raise ValueError(
            f"Invalid `output_format` attribute, should be one of `{'`, `'.join(supported_output_formats.keys())}`. Got `{output_format}`."
        )

    def __init__(self):
        """
        Constructor
        """
        self.separator = None

    def format_separator(self, separator, color):
        """
        Produce a formatted and colorized separator for the output format,
        if the output_format requires it, and None otherwise.
        """
        pass

    def format(self, outputs):
        """
        Produce a line of output from a list of module output dictionaries
        """
        raise NotImplementedError()

    def write_header(self, header):
        """
        Write the header to output, if supported by the output_format
        """
        raise NotImplementedError()

    def write_line(self, output):
        """
        Write a line of py3status containing the given module output
        """
        raise NotImplementedError()


class I3barOutputFormat(OutputFormat):
    """
    Format the output for consumption by i3bar
    """

    def format(self, outputs):
        """
        Produce a line of output from a list of module outputs for
        consumption by i3bar. separator is ignored.
        """
        return ",".join(dumps(x) for x in outputs)

    def write_header(self, header):
        """
        Write the i3bar header to output
        """
        write = sys.__stdout__.write
        flush = sys.__stdout__.flush

        write(dumps(header))
        write("\n[[]\n")
        flush()

    def write_line(self, output):
        """
        Write a line of py3status output for consumption by i3bar
        """
        write = sys.__stdout__.write
        flush = sys.__stdout__.flush

        out = ",".join(x for x in output if x)
        write(f",[{out}]\n")
        flush()


class SeparatedOutputFormat(OutputFormat):
    """
    Base class for formatting output as an enriched string containing
    separators
    """

    def begin_color(self, color):
        """
        Produce a format string for a colorized output for the output format
        """
        raise NotImplementedError()

    def end_color(self):
        """
        Produce a format string for ending a colorized output for the output format
        """
        raise NotImplementedError()

    def end_color_quick(self):
        """
        Produce a format string for ending a colorized output, but only
        if it is syntactically required. (for example because a new color
        declaration immediately follows)
        """
        return self.end_color()

    def get_default_separator(self):
        """
        Produce the default separator for the output format
        """
        return " | "

    def format_separator(self, separator, color):
        """
        Format the given separator with the given color
        """
        if separator is None:
            separator = self.get_default_separator()
        if color is not None:
            separator = self.begin_color(color) + separator + self.end_color()
        self.separator = separator

    def format_color(self, block):
        """
        Format the given block of module output
        """
        full_text = block["full_text"]
        if "color" in block:
            full_text = self.begin_color(block["color"]) + full_text + self.end_color_quick()
        return full_text

    def format(self, outputs):
        """
        Produce a line of output from a list of module outputs by
        concatenating individual blocks of formatted output
        """
        return "".join(self.format_color(x) for x in outputs)

    def write_header(self, header):
        """
        Not supported in separated output formats
        """
        pass

    def write_line(self, output):
        """
        Write a line of py3status output separated by the formatted separator
        """
        write = sys.__stdout__.write
        flush = sys.__stdout__.flush

        out = self.separator.join(x for x in output if x)
        write(f"{out}\n")
        flush()


class Dzen2OutputFormat(SeparatedOutputFormat):
    """
    Format the output for consumption by dzen2
    """

    def begin_color(self, color):
        return f"^fg({color})"

    def end_color(self):
        return "^fg()"

    def end_color_quick(self):
        return ""

    def get_default_separator(self):
        """
        Produce the default separator for the output format
        """
        return "^p(5;-2)^ro(2)^p()^p(5)"


class XmobarOutputFormat(SeparatedOutputFormat):
    """
    Format the output for consumption by xmobar
    """

    def begin_color(self, color):
        return f"<fc={color}>"

    def end_color(self):
        return "</fc>"


class LemonbarOutputFormat(SeparatedOutputFormat):
    """
    Format the output for consumption by lemonbar
    """

    def begin_color(self, color):
        return f"%{{F{color}}}"

    def end_color(self):
        return "%{F-}"

    def end_color_quick(self):
        return ""


class TmuxOutputFormat(SeparatedOutputFormat):
    """
    Format the output for consumption by tmux
    """

    def begin_color(self, color):
        return f"#[fg={color.lower()}]"

    def end_color(self):
        return "#[default]"

    def end_color_quick(self):
        return ""


class TermOutputFormat(SeparatedOutputFormat):
    """
    Format the output using terminal escapes
    """

    def begin_color(self, color):
        col = int(color[1:], 16)
        r = (col & (0xFF << 0)) // 0x80
        g = (col & (0xFF << 8)) // 0x8000
        b = (col & (0xFF << 16)) // 0x800000
        col = (r << 2) | (g << 1) | b
        return f"\033[3{col};1m"

    def end_color(self):
        return "\033[0m"

    def end_color_quick(self):
        return ""


class NoneOutputFormat(SeparatedOutputFormat):
    """
    Format the output without colors
    """

    def begin_color(self, color):
        return ""

    def end_color(self):
        return ""
