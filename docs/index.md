# Introduction

Using py3status, you can take control of your i3bar easily by:

- using one of the available modules shipped with py3status
- grouping multiple modules and automatically or manually cycle their display
- writing your own modules and have their output displayed on your bar
- handling click events on your i3bar and play with them in no time
- seeing your clock tick every second whatever your i3status interval

No extra configuration file needed, just install & enjoy!

## About

You will love py3status if you're using [i3wm](https://i3wm.org) (or
[sway](https://swaywm.org)) and are frustrated by the i3status
limitations on your i3bar such as:

- you cannot hack into it easily
- you want more than the built-in modules and their limited configuration
- you cannot pipe the result of one of more scripts or commands in your bar easily

## Philosophy

- no added configuration file, use the standard i3status.conf
- rely on i3status' strengths and its existing configuration as much as possible
- be extensible, it must be easy for users to add their own
  stuff/output by writing a simple python class which will be loaded
  and executed dynamically - easily allow interactivity with the i3bar
- add some built-in enhancement/transformation of basic i3status modules output
- support Python 3

We apply the zen to improve this project and encourage everyone to read it!

## Need help?

Get help, share ideas or feedback, join community, report bugs, or
others, see:

### GitHub

- [Issues](https://github.com/ultrabug/py3status/issues) /
- [Pull requests](https://github.com/ultrabug/py3status/pulls)

### Live IRC Chat

Join us on \#py3status at [oftc.net](https://www.oftc.net)
