from py3status.constants import CONFIG_RESERVED_SECTIONS

# fmt: off
I3STATUS_INSTANCE_MODULE_NAMES = {
    "battery", "cpu_temperature", "disk", "ethernet", "memory", "path_exists",
    "read_file", "run_watch", "tztime", "volume", "wireless",
}
I3STATUS_SINGLE_NAME_MODULES = {"cpu_usage", "ddate", "ipv6", "load", "time"}
I3STATUS_COLOR_OPTION_NAMES = {"color_bad", "color_good", "color_degraded"}
I3STATUS_MODULE_COLOR_NAMES = {"general", "battery", "cpu_temperature", "disk", "load"}
I3STATUS_WRAPPER_SETTING_NAMES = {
    "align", "allow_urgent", "background", "border", "border_bottom", "border_left",
    "border_right", "border_top", "color", "min_length", "min_width", "markup",
    "on_error", "position", "separator", "separator_block_width", "urgent_background",
    "urgent_border", "urgent_border_bottom", "urgent_border_left", "urgent_border_right",
    "urgent_border_top", "urgent_foreground",
}
# fmt: on


def is_i3status_wrapper_section(name):
    split_name = name.split()
    return bool(split_name) and split_name[0] in (
        I3STATUS_SINGLE_NAME_MODULES | I3STATUS_INSTANCE_MODULE_NAMES
    )


def get_i3status_wrapper_section_name_error(name):
    split_name = name.split()
    if len(split_name) > 1 and split_name[0] in I3STATUS_SINGLE_NAME_MODULES:
        return "Invalid name cannot have 2 tokens"
    return None


def _get_generated_name(name):
    return f"i3status {'-'.join(name.split())}_generated"


def _rewrite_section_references(section_config, get_generated_name):
    rewritten_config = dict(section_config)
    items = rewritten_config.get("items")
    if isinstance(items, list) and all(isinstance(item, str) for item in items):
        rewritten_config["items"] = [get_generated_name(item) for item in items]
    group_name = rewritten_config.get(".group")
    if isinstance(group_name, str):
        rewritten_config[".group"] = get_generated_name(group_name)
    return rewritten_config


def _is_wrapper_config_key(module_name, key):
    if key.startswith(".") or key in I3STATUS_WRAPPER_SETTING_NAMES:
        return True
    if key not in I3STATUS_COLOR_OPTION_NAMES:
        return False
    return module_name not in I3STATUS_MODULE_COLOR_NAMES


def _make_wrapper_config(name, section_config, user_general_config):
    module_name = name.split()[0]
    wrapper_config = {}
    if user_general_config:
        wrapper_config["general"] = dict(user_general_config)
    module_config = {"name": name}

    for key, value in section_config.items():
        if _is_wrapper_config_key(module_name, key):
            wrapper_config[key] = value
        else:
            module_config[key] = value

    wrapper_config["modules"] = [module_config]
    return wrapper_config


def convert_i3status_wrapper_config(config, user_general_config):
    config_sections = {
        name: section_config
        for name, section_config in config.items()
        if name not in CONFIG_RESERVED_SECTIONS
    }
    rename_map = {
        name: _get_generated_name(name)
        for name in config_sections
        if is_i3status_wrapper_section(name)
    }
    if not rename_map:
        return config

    generated_config = {
        "general": config["general"],
        "py3status": config["py3status"],
        "order": [rename_map.get(name, name) for name in config["order"]],
        "on_click": {},
        "py3_modules": [],
        ".module_groups": {},
    }

    def get_generated_name(name):
        return rename_map.get(name, name)

    for name, section_config in config_sections.items():
        generated_name = get_generated_name(name)
        rewritten_section_config = _rewrite_section_references(section_config, get_generated_name)
        if generated_name == name:
            resolved_section_config = rewritten_section_config
        else:
            resolved_section_config = _make_wrapper_config(
                name, rewritten_section_config, user_general_config
            )
        if generated_name not in generated_config["py3_modules"]:
            generated_config["py3_modules"].append(generated_name)
        generated_config[generated_name] = resolved_section_config

    generated_config["on_click"] = {
        get_generated_name(name): clicks for name, clicks in config.get("on_click", {}).items()
    }

    for name, parents in config.get(".module_groups", {}).items():
        generated_name = get_generated_name(name)
        generated_config[".module_groups"].setdefault(generated_name, [])
        for parent in parents:
            generated_parent = get_generated_name(parent)
            if generated_parent not in generated_config[".module_groups"][generated_name]:
                generated_config[".module_groups"][generated_name].append(generated_parent)

    return generated_config
