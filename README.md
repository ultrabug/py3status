py3status
=========

py3status extends the mighty i3status for enhanced i3bar customization on i3wm

## Documentation
See the [wiki](https://github.com/ultrabug/py3status/wiki) for up to date documentation.

## Requirements
You must set the `output_format` to `i3bar` in the general section of your i3status.conf:

    general {
        output_format = "i3bar"
    }

## Installation
Just clone the repository:

    $ git clone git@github.com:ultrabug/py3status.git .py3status

Get into the cloned directory:

    $ cd .py3status

And run the setup.sh as root or via sudo:

    $ sudo sh setup.sh

## Usage
In your i3 config file, simply change the `status_command` with:

    status_command py3status

Usually you have your own i3status configuration, just point to it:

    status_command py3status -c ~/.i3/i3status.conf

## Options
You can see the help of py3status by issuing `py3status -h`:

    -c I3STATUS_CONF  path to i3status config file
    -n INTERVAL       polling interval in seconds (default 1 sec)
    -i INCLUDE_PATH   user-based class include directory
    -d                disable integrated transformations

## Update
Just pull on your local clone to get the latest py3status:

    $ cd .py3status
    $ git pull
