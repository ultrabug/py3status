# Getting Started

Install [py3status](/installation/), then set `status_command` to `py3status` in your config file.
```
status_command py3status
```

you can keep your configurations in different places.
```
status_command py3status -c ~/.config/py3status/top.conf
status_command py3status -c ~/.config/py3status/bottom.conf
```

## Check out all the available modules

You can get a list with short descriptions of all available modules by
using the CLI:
```bash
$ py3-cmd list --all
```

To get more details about all available modules and their configuration,
use:
```bash
$ py3-cmd list --all --full
```

All modules shipped with py3status are present as the Python source
files in the `py3status/modules` directory.

## Adding, ordering and configuring modules

Check out the [py3status user configuration guide](/configuration/)
to learn how to add, order and configure modules!

## Py3status options

You can get the py3status options by issuing `py3status --help`:
```bash
{{ cli_help() }}
```

## Going further

Py3status is very open and flexible, check out the rest of
our guide to get more intimate with it.
