"""
mkdocs-macros-plugin hook (see zensical.toml's [project.plugins.macros]).
Macros pull live values from source instead of hand-typed docs content
that silently goes stale the moment the source changes.
"""

import contextlib
import os
import re
import tomllib
from pathlib import Path

from py3status.argparsers import (
    CONFIG_FILE_TEMPLATES,
    MODULE_SEARCH_PATH_TEMPLATES,
    build_parser,
)
from py3status.command import ALIAS_BUTTONS, SERVER_ADDRESS, build_command_parser
from py3status.constants import CACHE_TIMEOUT_DEFAULT, GENERAL_DEFAULTS, POSITIONS
from py3status.output import SUPPORTED_OUTPUT_FORMATS
from py3status.parse_config import CONVERSION_FUNCTIONS
from py3status.py3 import (
    REQUEST_RETRY_TIMES_DEFAULT,
    REQUEST_RETRY_WAIT_DEFAULT,
    REQUEST_TIMEOUT_DEFAULT,
)


def _numbered_list(templates):
    return "\n".join(f"{i} = {template}" for i, template in enumerate(templates, 1))


def _kv_list(mapping):
    return "\n".join(f"{key} = {value}" for key, value in mapping.items())


@contextlib.contextmanager
def _no_ansi_color():
    """
    argparse (Python 3.13+) auto-colorizes --help output based on the
    calling environment (FORCE_COLOR, isatty(), etc) - wrong here, since
    this output gets embedded as static docs text, never printed to a
    live terminal. PYTHON_COLORS=0 is argparse's own highest-precedence
    override (checked before NO_COLOR/FORCE_COLOR - see _colorize.
    can_colorize()), so it reliably disables colorizing regardless of
    whatever environment this build happens to run in.
    """
    previous = os.environ.get("PYTHON_COLORS")
    os.environ["PYTHON_COLORS"] = "0"
    try:
        yield
    finally:
        if previous is None:
            os.environ.pop("PYTHON_COLORS", None)
        else:
            os.environ["PYTHON_COLORS"] = previous


def _install_extras():
    # pyproject.toml's real optional-dependencies - not hand-copied
    pyproject = tomllib.loads(Path(__file__).parent.joinpath("pyproject.toml").read_text())
    extras = pyproject["project"]["optional-dependencies"]
    lines = []
    for name, deps in extras.items():
        pkgs = ", ".join(re.split(r"[=<>!~;]", dep)[0].strip() for dep in deps)
        lines.append(f"$ pip install py3status[{name}]  # {pkgs}")
    return "\n".join(lines)


def _click_button_aliases():
    # "leftclick" -> "left click", "scrollup" -> "scroll up", etc.
    by_button = sorted(ALIAS_BUTTONS.items(), key=lambda item: item[1])
    return "\n".join(
        f"{button} = {re.sub(r'(click|up|down)$', r' \1', alias)}"
        for alias, button in by_button
    )


def define_env(env):
    @env.macro
    def cli_help():
        with _no_ansi_color():
            return build_parser().format_help()

    @env.macro
    def config_search_paths():
        return _numbered_list(CONFIG_FILE_TEMPLATES)

    @env.macro
    def module_search_paths():
        return _numbered_list(MODULE_SEARCH_PATH_TEMPLATES)

    @env.macro
    def command_help(subcommand):
        with _no_ansi_color():
            _, sps = build_command_parser()
            return sps[subcommand].format_help()

    @env.macro
    def click_button_aliases():
        return _click_button_aliases()

    @env.macro
    def request_timeout_default():
        return str(REQUEST_TIMEOUT_DEFAULT)

    @env.macro
    def request_retry_times_default():
        return str(REQUEST_RETRY_TIMES_DEFAULT)

    @env.macro
    def request_retry_wait_default():
        return str(REQUEST_RETRY_WAIT_DEFAULT)

    @env.macro
    def cache_timeout_default():
        return str(CACHE_TIMEOUT_DEFAULT)

    @env.macro
    def align_positions():
        return ", ".join(f"`{position}`" for position in POSITIONS)

    @env.macro
    def general_defaults():
        return _kv_list(GENERAL_DEFAULTS)

    @env.macro
    def command_server_address():
        return SERVER_ADDRESS

    @env.macro
    def output_formats():
        return _numbered_list(sorted(SUPPORTED_OUTPUT_FORMATS))

    @env.macro
    def conversion_types():
        return ", ".join(f"`{name}`" for name in [*CONVERSION_FUNCTIONS, "auto"])

    @env.macro
    def install_extras():
        return _install_extras()
