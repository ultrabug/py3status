# Controlling py3status remotely

## Forcing an update

Just like i3status, you can force an update of your i3bar by sending a
`SIGUSR1` signal to py3status. Note that this will also send the same signal
to i3status.
```bash
$ killall -USR1 py3status
```

## The `py3-cmd` CLI

py3status can be controlled remotely via the `py3-cmd` cli utility.
It talks to the running py3status process over a Unix domain socket at
`{{ command_server_address() }}.<pid>`.

This utility allows you to click, list, or refresh matching modules.
```
# button numbers
{{ click_button_aliases() }}
```

### click

Send a click event to matching modules.
```bash
{{ command_help('click') }}
```

### list

Print a list of matching modules or module docstrings.
```bash
{{ command_help('list') }}
```

### refresh

Refresh the matching modules.
```bash
{{ command_help('refresh') }}
```

## Configuration file

`py3-cmd` can be used in your i3 or sway configuration file.

To send a click event to the whatismyip module when `Mod+x` is pressed
```
bindsym $mod+x exec py3-cmd click whatismyip
```

This example shows how volume control keys can be bound to change the
volume and then cause the `volume_status` module to be updated.
```
bindsym XF86AudioRaiseVolume  exec "amixer -q sset Master 5%+ unmute; py3-cmd refresh volume_status"
bindsym XF86AudioLowerVolume  exec "amixer -q sset Master 5%- unmute; py3-cmd refresh volume_status"
bindsym XF86AudioMute         exec "amixer -q sset Master toggle; py3-cmd refresh volume_status"
```
