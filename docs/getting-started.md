# Getting Started

[Install py3status](user-guide/installation.md) then in your i3 config file,
simply **switch from `i3status` to `py3status`** in your `status_command`
option:

```
status_command py3status
```

Usually you have your own i3status configuration, just point to it:

``` 
status_command py3status -c ~/.config/i3status/config
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

Check out the [py3status user configuration guide](user-guide/configuration.md)
to learn how to add, order and configure modules!

## Py3status options

You can see the help of py3status by issuing `py3status --help`:

```bash
$ py3status --help

usage: py3status [-h] [-b] [-c FILE] [-d] [-g] [-i PATH] [-l FILE] [-s]
                 [-t INT] [-m] [-u PATH] [-v] [--wm WINDOW_MANAGER]

The agile, python-powered, i3status wrapper

optional arguments:
  -h, --help            show this help message and exit
  -b, --dbus-notify     send notifications via dbus instead of i3-nagbar
                        (default: False)
  -c, --config FILE     load config (default: /home/alexys/.i3/i3status.conf)
  -d, --debug           enable debug logging in syslog and --log-file
                        (default: False)
  -i, --include PATH    append additional user-defined module paths (default:
                        None)
  -l, --log-file FILE   enable logging to FILE (default: None)
  -s, --standalone      run py3status without i3status (default: False)
  -t, --timeout INT     default module cache timeout in seconds (default: 60)
  -m, --disable-click-events
                        disable all click events (default: False)
  -u, --i3status PATH   specify i3status path (default: /usr/bin/i3status)
  -v, --version         show py3status version and exit (default: False)
  --wm WINDOW_MANAGER   specify window manager i3 or sway (default: i3)
```

## Going further

Py3status is very open and flexible, check out the complete user guide to get
more intimate with it:

- [user configuration guide](user-guide/configuration.md)
- [available modules and options](user-guide/modules.md)
- [remote controlling py3status](user-guide/remote-control.md)
