import re
from pathlib import Path

from py3status.docstrings import core_module_docstrings
from py3status.screenshots import create_screenshots, get_samples


def file_sort(my_list):
    """
    Sort a list of files in a nice way.
    eg item-10 will be after item-9
    """

    def alphanum_key(key):
        """
        Split the key into str/int parts
        """
        return [int(s) if s.isdigit() else s for s in re.split("([0-9]+)", key)]

    my_list.sort(key=alphanum_key)
    return my_list


def screenshots(config, screenshots_data, module_name):
    """
    Create .md output for any screenshots a module may have.
    """
    shots = screenshots_data.get(module_name)
    if not shots:
        return ""

    out = []
    for index, shot in enumerate(file_sort(shots)):
        if not Path(f"{config['docs_dir']}/user-guide/screenshots/{shot}.png").exists():
            continue
        out.append(f"\n![{module_name} example {index}](screenshots/{shot}.png)\n")
    return "".join(out)


def create_module_docs(config):
    """
    Create documentation for modules.
    """
    data = core_module_docstrings(format="md")
    # get screenshot data
    screenshots_data = {}
    samples = get_samples()
    for sample in samples:
        module = sample.split("-")[0]
        if module not in screenshots_data:
            screenshots_data[module] = []
        screenshots_data[module].append(sample)

    out = ["# Available modules"]
    # details
    for module in sorted(data):
        out.append(
            "\n## {name}\n\n{screenshots}\n{details}\n".format(
                name=module,
                screenshots=screenshots(config, screenshots_data, module),
                details="".join(data[module]).strip(),
            )
        )
    # write include file
    path = f"{config['docs_dir']}/user-guide/modules.md"
    print(f"Writing modules documentation to {path}...")
    Path(path).write_text("".join(out))
    return config


def on_config(config):
    """
    Create any include files needed for sphinx documentation
    """
    create_screenshots(config)
    create_module_docs(config)
    return config
