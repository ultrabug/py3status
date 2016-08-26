<a name="top"></a>Modules
========


**[arch_updates](#arch_updates)** — Displays the number of package updates pending for an Arch Linux installation.

**[aws_bill](#aws_bill)** — Display the current AWS bill.

**[battery_level](#battery_level)** — Display the battery level.

**[bitcoin_price](#bitcoin_price)** — Display bitcoin prices using bitcoincharts.com.

**[bluetooth](#bluetooth)** — Display bluetooth status.

**[clementine](#clementine)** — Display the current "artist - title" playing in Clementine.

**[deadbeef](#deadbeef)** — Display track currently playing in deadbeef.

**[dpms](#dpms)** — Activate or deactivate DPMS and screen blanking.

**[dropboxd_status](#dropboxd_status)** — Display dropboxd status.

**[exchange_rate](#exchange_rate)** — Display foreign exchange rates.

**[external_script](#external_script)** — Display output of given script.

**[fedora_updates](#fedora_updates)** — The number of package updates pending for a Fedora Linux installation.

**[file_status](#file_status)** — Display if a file or dir exists.

**[github](#github)** — Display Github notifications and issue/pull requests for a repo.

**[glpi](#glpi)** — Display the total number of open tickets from GLPI.

**[gpmdp](#gpmdp)** — Display currently playing song from Google Play Music Desktop Player.

**[graphite](#graphite)** — Display Graphite metrics.

**[group](#group)** — Group a bunch of modules together and switch between them.

**[hamster](#hamster)** — Display current tasks from project Hamster.

**[icinga2](#icinga2)** — Display Icinga2 service status information.

**[imap](#imap)** — Display the unread messages count from your IMAP account.

**[insync](#insync)** — Get current insync status

**[kdeconnector](#kdeconnector)** — Display information of your android device over KDEConnector.

**[keyboard_layout](#keyboard_layout)** — Display the current active keyboard layout.

**[mpd_status](#mpd_status)** — Display information from mpd.

**[net_rate](#net_rate)** — Display the current network transfer rate.

**[netdata](#netdata)** — Display network speed and bandwidth usage.

**[ns_checker](#ns_checker)** — Display DNS resolution success on a configured domain.

**[nvidia_temp](#nvidia_temp)** — Display NVIDIA GPU temperature.

**[online_status](#online_status)** — Display if a connection to the internet is established.

**[pingdom](#pingdom)** — Display the latest response time of the configured Pingdom checks.

**[player_control](#player_control)** — Control music/video players.

**[pomodoro](#pomodoro)** — Display and control a Pomodoro countdown.

**[process_status](#process_status)** — Display if a process is running.

**[rainbow](#rainbow)** — Add color cycling fun to your i3bar.

**[rate_counter](#rate_counter)** — Display days/hours/minutes spent and calculate the price of your service.

**[rt](#rt)** — Display the number of ongoing tickets from selected RT queues.

**[scratchpad_async](#scratchpad_async)** — Display the amount of windows and indicate urgency hints on scratchpad (async).

**[scratchpad_counter](#scratchpad_counter)** — Display the amount of windows in your i3 scratchpad.

**[screenshot](#screenshot)** — Take a screenshot and optionally upload it to your online server.

**[selinux](#selinux)** — Display the current selinux state.

**[spaceapi](#spaceapi)** — Display if your favorite hackerspace is open or not.

**[spotify](#spotify)** — Display information about the current song playing on Spotify.

**[static_string](#static_string)** — Display static text.

**[sysdata](#sysdata)** — Display system RAM and CPU utilization.

**[taskwarrior](#taskwarrior)** — Display currently active (started) taskwarrior tasks.

**[timer](#timer)** — A simple countdown timer.

**[twitch_streaming](#twitch_streaming)** — Checks if a Twitch streamer is online.

**[uname](#uname)** — Display uname information.

**[vnstat](#vnstat)** — Display vnstat statistics.

**[volume_status](#volume_status)** — Display current sound volume using amixer.

**[vpn_status](#vpn_status)** — Drop-in replacement for i3status run_watch VPN module.

**[weather_yahoo](#weather_yahoo)** — Display Yahoo! Weather forecast as icons.

**[whatismyip](#whatismyip)** — Display your public/external IP address and toggle to online status on click.

**[whoami](#whoami)** — Display the currently logged in user.

**[wifi](#wifi)** — Display WiFi bit rate, quality, signal and SSID using iw.

**[window_title](#window_title)** — Display the current window title.

**[window_title_async](#window_title_async)** — Display the current window title with async update.

**[wwan_status](#wwan_status)** — Display current network and ip address for newer Huwei modems.

**[xrandr](#xrandr)** — Control your screen(s) layout easily.

**[xrandr_rotate](#xrandr_rotate)** — Switch between horizontal and vertical screen rotation on a single click.

**[xsel](#xsel)** — Display the X selection.

**[yandexdisk_status](#yandexdisk_status)** — Display Yandex.Disk status.

---

### <a name="arch_updates"></a>arch_updates

Displays the number of package updates pending for an Arch Linux installation.

This will display a count of how many 'pacman' updates are waiting
to be installed and optionally a count of how many 'aur' updates are
also waiting.

Configuration parameters:
  - `cache_timeout` How often we refresh this module in seconds *(default 600)*
  - `format` Display format to use
    *(default 'UPD: {pacman}' or 'UPD: {pacman}/{aur}')*
  - `include_aur` Set to True to use 'cower' to check for AUR updates
    *(default False)*

Format of status string parameters:
  - `{aur}` Number of pending aur updates
  - `{pacman}` Number of pending pacman updates

Requires:
  - `cower` Needed to display pending 'aur' updates

**author** Iain Tatch <iain.tatch@gmail.com>

**license** BSD

---

### <a name="aws_bill"></a>aws_bill

Display the current AWS bill.

**WARNING: This module generate some costs on the AWS bill.
Take care about the cache_timeout to limit these fees!**

Configuration parameters:
  - `aws_access_key_id` Your AWS access key
  - `aws_account_id` The root ID of the AWS account.
    Can be found here` https://console.aws.amazon.com/billing/home#/account
  - `aws_secret_access_key` Your AWS secret key
  - `billing_file` Csv file location
  - `cache_timeout` How often we refresh this module in seconds
  - `s3_bucket_name` The bucket where billing files are sent by AWS.
    Follow this article to activate this feature:
    http://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/detailed-billing-reports.html

Format of status string placeholders:
  - `{bill_amount}` AWS bill amount

Requires:
  - `boto`

**author** nawadanp

---

### <a name="battery_level"></a>battery_level

Display the battery level.

Configuration parameters:
  - `battery_id` id of the battery to be displayed
    set to 'all' for combined display of all batteries
    default is 0
  - `blocks` a string, where each character represents battery level
    especially useful when using icon fonts (e.g. FontAwesome)
    default is "_▁▂▃▄▅▆▇█"
  - `cache_timeout` a timeout to refresh the battery state
    default is 30
  - `charging_character` a character to represent charging battery
    especially useful when using icon fonts (e.g. FontAwesome)
    default is "⚡"
  - `color_bad` a color to use when the battery level is bad
    None means get it from i3status config
    default is None
  - `color_charging` a color to use when the battery is charging
    None means get it from i3status config
    default is "#FCE94F"
  - `color_degraded` a color to use when the battery level is degraded
    None means get it from i3status config
    default is None
  - `color_good` a color to use when the battery level is good
    None means get it from i3status config
    default is None
  - `format` string that formats the output. See placeholders below.
    default is "{icon}"
  - `format_notify_charging` format of the notification received when you click
    on the module while your computer is plugged
    default is "Charging ({percent}%)"
  - `format_notify_discharging` format of the notification received when you
    click on the module while your comupter is not plugged
    default is "{time_remaining}"
  - `hide_when_full` hide any information when battery is fully charged (when
    the battery level is greater than or equal to 'threshold_full')
    default is False
  - `hide_seconds` hide seconds in remaining time
    default is False
  - `notification` show current battery state as notification on click
    default is False
  - `notify_low_level` display notification when battery is running low (when
    the battery level is less than 'threshold_degraded')
    default is False
  - `threshold_bad` a percentage below which the battery level should be
    considered bad
    default is 10
  - `threshold_degraded` a percentage below which the battery level should be
    considered degraded
    default is 30
  - `threshold_full` a percentage at or above which the battery level should
    should be considered full
    default is 100

Format of status string placeholders:
  - `{ascii_bar}` - a string of ascii characters representing the battery level,
    an alternative visualization to '{icon}' option
  - `{icon}` - a character representing the battery level,
    as defined by the 'blocks' and 'charging_character' parameters
  - `{percent}` - the remaining battery percentage (previously '{}')
  - `{time_remaining}` - the remaining time until the battery is empty

Obsolete configuration parameters:
  - `mode` an old way to define `format` parameter. The current behavior is:
    if 'format' is not "{icon}", this parameter is completely ignored
    if 'format' is "{icon}" and 'mode' is "ascii_bar", the `format` is
    set to "{ascii_bar}"
    if 'format' is "{icon}" and 'mode' is "text", the `format` is set to
    "Battery: {percent}"
    all other values are ignored
    default is None
  - `show_percent_with_blocks` an old way to define `format` parameter. The
    current behavior is:
    if 'format' is not "{icon}", this parameter is completely ignored
    if 'format' is "{icon}" and 'mode' is "ascii_bar" or "text", this
    parameter is completely ignored
    if the value is True, the `format` is set to "{icon} {percent}%"
    default is None

Requires:
  - the `acpi` command line

**author** shadowprince, AdamBSteele, maximbaz, 4iar

**license** Eclipse Public License

---

### <a name="bitcoin_price"></a>bitcoin_price

Display bitcoin prices using bitcoincharts.com.

Configuration parameters:
  - `cache_timeout` Should be at least 15 min according to bitcoincharts.
  - `color_index` Index of the market responsible for coloration,
    meaning that the output is going to be green if the
    price went up and red if it went down.
    default: -1 means no coloration,
    except when only one market is selected
  - `field` Field that is displayed per market,
    see http://bitcoincharts.com/about/markets-api/
  - `hide_on_error` Display empty response if True, else an error message
  - `markets` Comma-separated list of markets. Supported markets can
    be found at http://bitcoincharts.com/markets/list/
  - `symbols` Try to match currency abbreviations to symbols,
    e.g. USD -> $, EUR -> € and so on

**author** Andre Doser <doser.andre AT gmail.com>

---

### <a name="bluetooth"></a>bluetooth

Display bluetooth status.

Confiuration parameters:
  - `format` format when there is a connected device
  - `format_no_conn` format when there is no connected device
  - `format_no_conn_prefix` prefix when there is no connected device
  - `format_prefix` prefix when there is a connected device
  - `device_separator` the separator char between devices (only if more than one
    device)

Format of status string placeholders
  - `{name}`  device name
  - `{mac}`  device MAC address

Requires:
  - `hcitool`

**author** jmdana <https://github.com/jmdana>

**license** GPLv3 <http://www.gnu.org/licenses/gpl-3.0.txt>

---

### <a name="clementine"></a>clementine

Display the current "artist - title" playing in Clementine.

Requires:
  - `clementine`

**author** Francois LASSERRE <choiz@me.com>

**license** GNU GPL http://www.gnu.org/licenses/gpl.html

---

### <a name="deadbeef"></a>deadbeef

Display track currently playing in deadbeef.

Configuration parameters:
  - `cache_timeout` how often we refresh usage in seconds *(default: 1s)*
  - `format` see placeholders below
  - `delimiter` delimiter character for parsing *(default: ¥)*

Format of status string placeholders:
  - `{artist}` artist
  - `{title}` title
  - `{elapsed}` elapsed time
  - `{length}` total length
  - `{year}` year
  - `{tracknum}` track number


Requires:
    deadbeef:

**author** mrt-prodz

---

### <a name="dpms"></a>dpms

Activate or deactivate DPMS and screen blanking.

This module allows activation and deactivation
of DPMS (Display Power Management Signaling)
by clicking on 'DPMS' in the status bar.

Configuration parameters:
  - `format_off` string to display when DPMS is disabled
  - `format_on` string to display when DPMS is enabled

Color options:
  - `color_on` when dpms is enabled, defaults to color_good
  - `color_off` when dpms is disabled, defaults to color_bad

**author** Andre Doser <dosera AT tf.uni-freiburg.de>

---

### <a name="dropboxd_status"></a>dropboxd_status

Display dropboxd status.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds (10s default)
  - `format` prefix text for the dropbox status

Valid status values include:
  - Dropbox isn't running!
  - Starting...
  - Downloading file list...
  - Syncing "filename"
  - Up to date

Requires:
  - `dropbox-cli` command line tool

**author** Tjaart van der Walt (github:tjaartvdwalt)

**license** BSD

---

### <a name="exchange_rate"></a>exchange_rate

Display foreign exchange rates.

The exchange rate data comes from Yahoo Finance.

For a list of three letter currency codes please see
https://en.wikipedia.org/wiki/ISO_4217 NOTE: Not all listed currencies may be
available

Configuration parameters:
  - `base` Base currency used for exchange rates *(default 'EUR')*
  - `cache_timeout` How often we refresh this module in seconds *(default 600)*
  - `format` Format of the output.  This is also where requested currencies are
    configured. Add the currency code surrounded by curly braces and it
    will be replaced by the current exchange rate.
    *(default '${USD} £{GBP} ¥{JPY}')*

Requires:
  - `requests` python lib

**author** tobes

**license** BSD

---

### <a name="external_script"></a>external_script

Display output of given script.

Display output of any executable script set by `script_path`.
Pay attention. The output must be one liner, or will break your i3status !
The script should not have any parameters, but it could work.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds
  - `color` color of printed text
  - `format` see placeholders below
  - `script_path` script you want to show output of (compulsory)
  - `strip_output` shall we strip leading and trailing spaces from output
    *(default False)*

Format of status string placeholders:
  - `{output}` output of script given by "script_path"

i3status.conf example:

```
external_script {
    color = "#00FF00"
    format = "my name is {output}"
    script_path = "/usr/bin/whoami"
}
```

**author** frimdo ztracenastopa@centrum.cz

---

### <a name="fedora_updates"></a>fedora_updates

The number of package updates pending for a Fedora Linux installation.

This will display a count of how many `dnf` updates are waiting
to be installed.
Additionally check if any update security notices.

Configuration parameters:
  - `cache_timeout` How often we refresh this module in seconds
    *(default 600)*
  - `color_bad` Color when security notice
    *(default global color_bad)*
  - `color_degraded` Color when upgrade available
    *(default global color_degraded)*
  - `color_good` Color when no upgrades needed
    *(default global color_good)*
  - `format` Display format to use
    *(default 'DNF: {updates}')*

Format status string parameters:
  - `{updates}` number of pending dnf updates

**author** Toby Dacre

**license** BSD

---

### <a name="file_status"></a>file_status

Display if a file or dir exists.

Configuration parameters:
  - `cache_timeout` how often to run the check
  - `format_available` what to display when available
  - `format_unavailable` what to display when unavailable
  - `path` the path to a file or dir to check if it exists

**author** obb, Moritz Lüdecke

---

### <a name="github"></a>github

Display Github notifications and issue/pull requests for a repo.

To check notifications a Github `username` and `personal access token` are
required.  You can create a personal access token at
https://github.com/settings/tokens The only `scope` needed is `notifications`,
which provides readonly access to notifications.

The Github API is rate limited so setting `cache_timeout` too small may cause
issues see https://developer.github.com/v3/#rate-limiting for details


Configuration parameters:
  - `auth_token` Github personal access token, needed to check notifications
    see above.
    *(default None)*
  - `button_action` Button that when clicked opens the Github notification page
    if notifications, else the project page for the repository . Setting to
    `0` disables.
    *(default 3)*
  - `cache_timeout` How often we refresh this module in seconds
    *(default 60)*
  - `format` Format of output
    (default '{repo} {issues}/{pull_requests}{notifications}'
    if username and auth_token provided else
    '{repo} {issues}/{pull_requests}')
  - `format_notifications` Format of `{notification}` status placeholder.
    *(default ' N{notifications_count}')*
  - `notifications` Type of notifications can be `all` for all notifications or
    `repo` to only get notifications for the repo specified.  If repo is
    not provided then all notifications will be checked.
    *(default 'all')*
  - `repo` Github repo to check
    *(default 'ultrabug/py3status')*
  - `username` Github username, needed to check notifications.
    *(default None)*

Format of status string placeholders:
  - `{repo}` the short name of the repository being checked.
    eg py3status
  - `{repo_full}` the full name of the repository being checked.
    eg ultrabug/py3status
  - `{issues}` Number of open issues.
  - `{pull_requests}` Number of open pull requests
  - `{notifications}` Notifications.  If no notifications this will be empty.
  - `{notifications_count}` Number of notifications.  This is also the __Only__
    status string available to `format_notifications`.

Requires:
  - `requests` python module from pypi https://pypi.python.org/pypi/requests

Examples:

```
# set github access credentials
github {
    auth_token = '40_char_hex_access_token'
    username = 'my_username'
}

# just check for any notifications
github {
    auth_token = '40_char_hex_access_token'
    username = 'my_username'
    format = 'Github {notifications_count}'
}
```

**author** tobes

---

### <a name="glpi"></a>glpi

Display the total number of open tickets from GLPI.

Configuration parameters:
  - `critical` set bad color above this threshold
  - `db` database to use
  - `host` database host to connect to
  - `password` login password
  - `user` login user
  - `warning` set degraded color above this threshold

It features thresholds to colorize the output and forces a low timeout to
limit the impact of a server connectivity problem on your i3bar freshness.

---

### <a name="gpmdp"></a>gpmdp

Display currently playing song from Google Play Music Desktop Player.

Configuration parameters:
  - `cache_timeout`  how often we refresh this module in seconds *(default 5)*
  - `format`         specify the items and ordering of the data in the status bar.
    These area 1:1 match to gpmdp-remote's options *(default is '♫ {info}')*.

Format of status string placeholders:
    See `gpmdp-remote help`. Simply surround the items you want displayed (i.e. `album`)
    with curly braces (i.e. `{album}`) and place as-desired in the format string.

    {info}            Print info about now playing song
    {title}           Print current song title
    {artist}          Print current song artist
    {album}           Print current song album
    {album_art}       Print current song album art URL
    {time_current}    Print current song time in milliseconds
    {time_total}      Print total song time in milliseconds
    {status}          Print whether GPMDP is paused or playing
    {current}         Print now playing song in "artist - song" format
    {help}            Print this help message


Requires:
  - `gpmdp` http://www.googleplaymusicdesktopplayer.com/
  - `gpmdp-remote` https://github.com/iandrewt/gpmdp-remote

**author** Aaron Fields https://twitter.com/spirotot

**license** BSD

---

### <a name="graphite"></a>graphite

Display Graphite metrics.

Confiuration parameters:
  - `cache_timeout` how often we refresh this module in seconds.
    *(default 10)*
  - `datapoint_selection` when multiple data points are returned,
    use "max" or "min" to determine which one to display.
    *(default "max")*
  - `format` you MUST use placeholders here to display data, see below.
  - `graphite_url` URL to your graphite server.
  - `http_timeout` HTTP query timeout to graphite.
    *(default 10)*
  - `targets` semicolon separated list of targets to query graphite for.
  - `threshold_bad` numerical threshold,
    if set will send a notification and colorize the output.
    *(default None means no notification and color)*
  - `threshold_degraded` numerical threshold,
    if set will send a notification and colorize the output.
    *(default None means no notification and color)*
  - `timespan` time range to query graphite for.
    *(default "-2minutes")*
  - `value_comparator` choose between "max" and "min" to compare thresholds
    to the data point value.
    *(default "max")*
  - `value_format` pretty format long numbers with "K", "M" etc.
    *(default True)*
  - `value_round` round values so they're not displayed as floats.
    *(default True)*

Dynamic format placeholders:
    The "format" parameter placeholders are dynamically based on the data points
    names returned by the "targets" query to graphite.

    For example if your target is "carbon.agents.localhost-a.memUsage", you'd get
    a JSON result like this:
        {"target": "carbon.agents.localhost-a.memUsage", "datapoints": [[19693568.0, 1463663040]]}

    So the placeholder you could use on your "format" config is:
        format = "{carbon.agents.localhost-a.memUsage}"

    TIP: use aliases !
        targets = "alias(carbon.agents.localhost-a.memUsage, 'local_memuse')"
        format = "local carbon mem usage: {local_memuse} bytes"

**author** ultrabug

---

### <a name="group"></a>group

Group a bunch of modules together and switch between them.

In `i3status.conf` groups can be configured. The active one of these groups is
shown in the i3bar.  The active group can be changed by a user click.  If the
click is not used by the group module then it will be passed down to the
displayed module.

Modules can be i3status core modules or py3status modules.  The active group
can be cycled through automatically.

The group can handle clicks by reacting to any that are made on it or its
content or it can use a button and only respond to clicks on that.
The way it does this is selected via the `click_mode` option.

Configuration parameters:
  - `align` Text alignment when fixed_width is set
    can be 'left', 'center' or 'right' *(default 'center')*
  - `button_next` Button that when clicked will switch to display next module.
    Setting to `0` will disable this action. *(default 5)*
  - `button_prev` Button that when clicked will switch to display previous
    module.  Setting to `0` will disable this action. *(default 4)*
  - `button_toggle` Button that when clicked toggles the group content being
    displayed between open and closed.
    This action is ignored if `{button}` is not in the format.
    Setting to `0` will disable this action *(default 1)*
  - `click_mode` This defines how clicks are handled by the group.
    If set to `all` then the group will respond to all click events.  This
    may cause issues with contained modules that use the same clicks that
    the group captures.  If set to `button` then only clicks that are
    directly on the `{button}` are acted on.  The group
    will need `{button}` in its format.
    *(default 'all')*
  - `cycle` Time in seconds till changing to next module to display.
    Setting to `0` will disable cycling. *(default 0)*
  - `fixed_width` Reduce the size changes when switching to new group
    *(default False)*
  - `format` Format for module output.
    (default "{output}" if click_mode is 'all',
    "{output} {button}" if click_mode 'button')
  - `format_button_open` Format for the button when group closed
    *(default '+')*
  - `format_button_closed` Format for the button when group open
    *(default  '-')*
  - `format_closed` Format for module output when closed.
    *(default "{button}")*
  - `open` Is the group open and displaying its content. Has no effect if
    `{button}` not in format *(default True)*


Format of status string placeholders:
  - `{button}` The button to open/close or change the displayed group
  - `{output}` Output of current active module

Example:

```
# Create a disks group that will show space on '/' and '/home'
# Change between disk modules every 30 seconds
...
order += "group disks"
...

group disks {
    cycle = 30
    format = "Disks: {output} {button}"
    click_mode = "button"

    disk "/" {
        format = "/ %avail"
    }

    disk "/home" {
        format = "/home %avail"
    }
}
```

**author** tobes

---

### <a name="hamster"></a>hamster

Display current tasks from project Hamster.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds (5s default)
  - `format` see placeholders below

Format of status string placeholders:
  - `{current}` hamster current

Requires:
  - `hamster`

**author** Aaron Fields (spirotot [at] gmail.com)

**license** BSD

---

### <a name="icinga2"></a>icinga2

Display Icinga2 service status information.

Configuration Parameters:
  - `base_url` the base url to the icinga-web2 services list
  - `cache_timeout` how often the data should be updated
  - `color` define a color for the output
  - `disable_acknowledge` enable or disable counting of acknowledged
    service problems
  - `format` define a format string like "CRITICAL: %d"
  - `password` password to authenticate against the icinga-web2 interface
  - `status` set the status you want to obtain
    (0=OK,1=WARNING,2=CRITICAL,3=UNKNOWN)
  - `user` username to authenticate against the icinga-web2 interface

**author** Ben Oswald <ben.oswald@root-space.de>

**license** BSD License <https://opensource.org/licenses/BSD-2-Clause>

**source** https://github.com/nazco/i3status-modules

---

### <a name="imap"></a>imap

Display the unread messages count from your IMAP account.

Configuration parameters:
  - `cache_timeout` how often to run this check
  - `criterion` status of emails to check for
  - `format` format to display
  - `hide_if_zero` don't show on bar if 0
  - `imap_server` IMAP server to connect to
  - `mailbox` name of the mailbox to check
  - `new_mail_color` what color to output on new mail
  - `password` login password
  - `port` IMAP server port
  - `user` login user
  - `base64` use base64 encoded password (bool) *(default: False)*

Format of status string placeholders:
  - `{unseen}` number of unread emails

**author** obb

---

### <a name="insync"></a>insync

Get current insync status

Thanks to Iain Tatch <iain.tatch@gmail.com> for the script that this is based on.

Configuration parameters:
  - `cache_timeout` How often we refresh this module in seconds
    *(default 10)*
  - `format` Display format to use *(default '{status} {queued}')*

Format status string parameters:
  - `{status}` Status of Insync
  - `{queued}` Number of files queued

Requires:
  - `insync` command line tool

**author** Joshua Pratt <jp10010101010000@gmail.com>

**license** BSD

---

### <a name="kdeconnector"></a>kdeconnector

Display information of your android device over KDEConnector.

Configuration parameters:
  - `device` the device name, you need this if you have more than one device
    connected to your PC
  - `device_id` alternatively to the device name you can set your device id here
  - `format` see placeholders below
  - `format_disconnected` text if device is disconnected
  - `low_threshold` percentage value when text is twitch to color_bad
  - `status_bat` text when battery is discharged
  - `status_chr` text when device is charged
  - `status_full` text when battery is full
  - `status_no_notif` text when you have no notifications
  - `status_notif` text when notifications are available

Format of status string placeholders:
  - `{bat_status}` battery state
  - `{charge}` the battery charge
  - `{name}` name of the device
  - `{notif_size}` number of notifications
  - `{notif_status}` shows if a notification is available or nor

i3status.conf example:

```
kdeconnector {
    device_id = "aa0844d33ac6ca03"
    format = "{name} {battery} ⚡ {state}"
    low_battery = "10"
}
```

Requires:
    pydbus
    kdeconnect

**author** Moritz Lüdecke

---

### <a name="keyboard_layout"></a>keyboard_layout

Display the current active keyboard layout.

Configuration parameters:
  - `cache_timeout` check for keyboard layout change every seconds
  - `colors` a comma separated string of color values for each layout,
    eg: "us=#FCE94F, fr=#729FCF". (deprecated use color options)
  - `format` see placeholders below

Format of status string placeholders:
  - `{layout}` currently active keyboard layout

Color options:
  - `color_&lt;layout&gt;` color for the layout
    eg color_fr = '#729FCF'

Requires:
  - `xkblayout-state`
    or
  - `setxkbmap` and `xset` (works for the first two predefined layouts.)

**author** shadowprince, tuxitop

**license** Eclipse Public License

---

### <a name="mpd_status"></a>mpd_status

Display information from mpd.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds (2s default)
  - `color` enable coloring output *(default False)*
  - `color_pause` custom pause color *(default i3status color degraded)*
  - `color_play` custom play color *(default i3status color good)*
  - `color_stop` custom stop color *(default i3status color bad)*
  - `format` template string (see below)
  - `hide_when_paused` hide the status if state is paused
  - `hide_when_stopped` hide the status if state is stopped
  - `host` mpd host
  - `max_width` maximum status length
  - `password` mpd password
  - `port` mpd port
  - `state_pause` label to display for "paused" state
  - `state_play` label to display for "playing" state
  - `state_stop` label to display for "stopped" state

Requires:
  - `python-mpd2` (NOT python2-mpd2)
```
# pip install python-mpd2
```

Refer to the mpc(1) manual page for the list of available placeholders to be
used in `format`.
You can also use the %state% placeholder, that will be replaced with the state
label (play, pause or stop).
Every placeholder can also be prefixed with `next_` to retrieve the data for
the song following the one currently playing.

You can also use {} instead of %% for placeholders (backward compatibility).

Examples of `format`
```
# Show state and (artist -) title, if no title fallback to file:
%state% [[[%artist% - ]%title%]|[%file%]]

# Alternative legacy syntax:
{state} [[[{artist} - ]{title}]|[{file}]]

# Show state, [duration], title (or file) and next song title (or file):
%state% \[%time%\] [%title%|%file%] → [%next_title%|%next_file%]
```

**author** shadowprince, zopieux

**license** Eclipse Public License

---

### <a name="net_rate"></a>net_rate

Display the current network transfer rate.

Configuration parameters:
  - `all_interfaces` ignore self.interfaces, but not self.interfaces_blacklist
  - `devfile` location of dev file under /proc
  - `format_no_connection` when there is no data transmitted from the
    start of the plugin
  - `hide_if_zero` hide indicator if rate == 0
  - `interfaces` comma separated list of interfaces to track
  - `interfaces_blacklist` comma separated list of interfaces to ignore
  - `precision` amount of numbers after dot

Format of status string placeholders:
  - `{down}` download rate
  - `{interface}` name of interface
  - `{total}` total rate
  - `{up}` upload rate

**author** shadowprince

**license** Eclipse Public License

---

### <a name="netdata"></a>netdata

Display network speed and bandwidth usage.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds (2s default)
  - `low_*` / `med_*` coloration thresholds
  - `nic` the network interface to monitor *(defaults to eth0)*

**author** Shahin Azad &lt;ishahinism at Gmail&gt;

---

### <a name="ns_checker"></a>ns_checker

Display DNS resolution success on a configured domain.

This module launch a simple query on each nameservers for the specified domain.
Nameservers are dynamically retrieved. The FQDN is the only one mandatory
parameter.  It's also possible to add additional nameservers by appending them
in nameservers list.

The default resolver can be overwritten with my_resolver.nameservers parameter.

Configuration parameters:
  - `domain` domain name to check
  - `lifetime` resolver lifetime
  - `nameservers` comma separated list of reference DNS nameservers
  - `resolvers` comma separated list of DNS resolvers to use

**author** nawadanp

---

### <a name="nvidia_temp"></a>nvidia_temp

Display NVIDIA GPU temperature.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds
  - `color_bad` the color used if the temperature can't be read.
  - `color_good` the color used if everything is OK.
  - `format_prefix` a prefix for the output.
  - `format_units` the temperature units. Will appear at the end.
  - `temp_separator` the separator char between temperatures (only if more than
    one GPU)

Requires:
  - `nvidia-smi`

**author** jmdana <https://github.com/jmdana>

**license** BSD

---

### <a name="online_status"></a>online_status

Display if a connection to the internet is established.

Configuration parameters:
  - `cache_timeout` how often to run the check
  - `format_offline` what to display when offline
  - `format_online` what to display when online
  - `timeout` how long before deciding we're offline
  - `url` connect to this url to check the connection status

**author** obb

---

### <a name="pingdom"></a>pingdom

Display the latest response time of the configured Pingdom checks.

We also verify the status of the checks and colorize if needed.
Pingdom API doc : https://www.pingdom.com/features/api/documentation/

Configuration parameters:
  - `app_key` create an APP KEY on pingdom first
  - `cache_timeout` how often to refresh the check from pingdom
  - `checks` comma separated pindgom check names to display
  - `login` pingdom login
  - `max_latency` maximal latency before coloring the output
  - `password` pingdom password
  - `request_timeout` pindgom API request timeout

Requires:
  - `requests` python module from pypi
    https://pypi.python.org/pypi/requests

---

### <a name="player_control"></a>player_control

Control music/video players.

Provides an icon to control simple functions of audio/video players:
  - start (left click)
  - stop  (left click)
  - pause (middle click)

Configuration parameters:
  - `debug` enable verbose logging (bool) *(default: False)*
  - `supported_players` supported players (str) (comma separated list)
  - `volume_tick` percentage volume change on mouse wheel (int) (positive number
    or None to disable it)

**author** Federico Ceratto <federico.ceratto@gmail.com>, rixx

**license** BSD

---

### <a name="pomodoro"></a>pomodoro

Display and control a Pomodoro countdown.

Button 1 starts/pauses countdown.
Button 2 switch Pomodoro/Break.
Button 3 resets timer.

Configuration parameters:
  - `display_bar` display time in bars when True, otherwise in seconds
  - `format` define custom display format. See placeholders below
  - `format_separator` separator between minutes:seconds
  - `max_breaks` maximum number of breaks
  - `num_progress_bars` number of progress bars
  - `sound_break_end` break end sound (file path) (requires pyglet
    or pygame)
  - `sound_pomodoro_end` pomodoro end sound (file path) (requires pyglet
    or pygame)
  - `sound_pomodoro_start` pomodoro start sound (file path) (requires pyglet
    od pygame)
  - `timer_break` normal break time (seconds)
  - `timer_long_break` long break time (seconds)
  - `timer_pomodoro` pomodoro time (seconds)

Format of status string placeholders:
  - `{bar}` display time in bars
  - `{ss}` display time in total seconds (1500)
  - `{mm}` display time in total minutes (25)
  - `{mmss}` display time in (hh-)mm-ss (25:00)

i3status.conf example:
```
pomodoro {
    format = "{mmss} {bar}"
}
```

**author** Fandekasp (Adrien Lemaire), rixx, FedericoCeratto, schober-ch

---

### <a name="process_status"></a>process_status

Display if a process is running.

Configuration parameters:
  - `cache_timeout` how often to run the check
  - `format_running` what to display when process running
  - `format_not_running` what to display when process is not running
  - `process` the process name to check if it is running

**author** obb, Moritz Lüdecke

---

### <a name="rainbow"></a>rainbow

Add color cycling fun to your i3bar.

This is the most pointless yet most exciting module you can imagine.

It allows color cycling of modules. Imagine the joy of having the current time
change through the colors of the rainbow.

If you were completely insane you could also use it to implement the i3bar
equivalent of the &lt;blink&gt; tag and cause yourself endless headaches and the
desire to vomit.

The color for the contained module(s) is changed and cycles through your chosen
gradient by default this is the colors of the rainbow.  This module will
increase the amount of updates that py3status needs to do so should be used
sparingly.


Configuration parameters:
  - `cycle_time` How often we cdo a color change in seconds
    *(default 1)*
  - `force` If True then the color will always be set.  If false the color will
    only be changed if it has not been set by a module.
    *(default False)*
  - `gradient` The colors we will cycle through, This is a list of hex values
    (default [ '#FF0000', '#FFFF00', '#00FF00', '#00FFFF',
    '#0000FF', '#FF00FF', '#FF0000', ])
  - `steps` Number of steps between each color in the gradient
    *(default 10)*

Example config:

```
order += "rainbow time"

# show time colorfully
rainbow time {
    time {}
}
```

Example blinking config:

```
order += "rainbow blink_time"

# blinking text black/white
rainbow blink_time{
    gradient = [
        '#FFFFFF',
        '#000000',
    ]
    steps = 1

    time {}
}
```

**author** tobes

---

### <a name="rate_counter"></a>rate_counter

Display days/hours/minutes spent and calculate the price of your service.

Configuration parameters:
  - `config_file` file path to store the time already spent
    and restore it the next session
  - `hour_price` your price per hour
  - `tax` tax value (1.02 = 2%)

**author** Amaury Brisou <py3status AT puzzledge.org>

---

### <a name="rt"></a>rt

Display the number of ongoing tickets from selected RT queues.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 300)*
  - `threshold_critical` set bad color above this threshold
  - `db` database to use
  - `format` see placeholders below
  - `host` database host to connect to
  - `password` login password
  - `user` login user
  - `threshold_warning` set degraded color above this threshold

Format of status string placeholders:
  - `{YOUR_QUEUE_NAME}` number of ongoing RT tickets (open+new+stalled)

Requires:
  - `PyMySQL` https://pypi.python.org/pypi/PyMySQL
    or
  - `MySQL-python` http://pypi.python.org/pypi/MySQL-python

It features thresholds to colorize the output and forces a low timeout to
limit the impact of a server connectivity problem on your i3bar freshness.

**author** ultrabug

---

### <a name="scratchpad_async"></a>scratchpad_async

Display the amount of windows and indicate urgency hints on scratchpad (async).

Configuration parameters:
  - `always_show` whether the indicator should be shown if there are no
    scratchpad windows *(default False)*
  - `color_urgent` color to use if a scratchpad window is urgent (default
    "#900000")
  - `format` string to format the output *(default "{} ⌫")*

Requires:
  - `i3ipc` (https://github.com/acrisci/i3ipc-python)

**author** cornerman

**license** BSD

---

### <a name="scratchpad_counter"></a>scratchpad_counter

Display the amount of windows in your i3 scratchpad.

**author** shadowprince

**license** Eclipse Public License

---

### <a name="screenshot"></a>screenshot

Take a screenshot and optionally upload it to your online server.

Display a 'SHOT' button in your i3bar allowing you to take a screenshot and
directly send (if wanted) the file to your online server.
When the screenshot has been taken, 'SHOT' is replaced by the file_name.

By default, this modules uses the 'gnome-screenshot' program to take the screenshot,
but this can be configured with the `screenshot_command` configuration parameter.

Configuration parameters:
  - `file_length` generated file_name length
  - `push` True/False if yo want to push your screenshot to your server
  - `save_path` Directory where to store your screenshots.
  - `screenshot_command` the command used to generate the screenshot
  - `upload_path` the remote path where to push the screenshot
  - `upload_server` your server address
  - `upload_user` your ssh user

**author** Amaury Brisou <py3status AT puzzledge.org>

---

### <a name="selinux"></a>selinux

Display the current selinux state.

This module displays the current state of selinux on your machine: Enforcing
(good), Permissive (bad), or Disabled (bad).

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds (10s default)
  - `format` see placeholders below, default is 'selinux: {state}'

Format of status string placeholders:
  - `{state}` the current selinux state

Requires:
  - `libselinux-python`
    or
  - `libselinux-python3` (optional for python3 support)

**author** bstinsonmhk

**license** BSD

---

### <a name="spaceapi"></a>spaceapi

Display if your favorite hackerspace is open or not.

Configuration Parameters:
  - `cache_timeout` Set timeout between calls in seconds
  - `closed_color` color if space is closed
  - `closed_text` text if space is closed, strftime parameters
    will be translated
  - `open_color` color if space is open
  - `open_text` text if space is open, strftime parmeters will be translated
  - `url` URL to SpaceAPI json file of your space

**author** timmszigat

**license** WTFPL <http://www.wtfpl.net/txt/copying/>

---

### <a name="spotify"></a>spotify

Display information about the current song playing on Spotify.

Configuration parameters:
  - `cache_timeout` how often to update the bar
  - `color_offline` text color when spotify is not running,
    defaults to color_bad
  - `color_paused` text color when song is stopped or paused,
    defaults to color_degraded
  - `color_playing` text color when song is playing, defaults to color_good
  - `format` see placeholders below
  - `format_down` define output if spotify is not running
  - `format_stopped` define output if spotify is not playing

Format of status string placeholders:
  - `{album}` album name
  - `{artist}` artiste name (first one)
  - `{time}` time duration of the song
  - `{title}` name of the song

i3status.conf example:

```
spotify {
    format = "{title} by {artist} -> {time}"
    format_down = "no Spotify"
}
```

Requires:
    spotify (>=1.0.27.71.g0a26e3b2)

**author** Pierre Guilbert, Jimmy Garpehäll, sondrele, Andrwe

---

### <a name="static_string"></a>static_string

Display static text.

Configuration parameters:
  - `color` color of printed text
  - `format` text that should be printed

**author** frimdo ztracenastopa@centrum.cz

---

### <a name="sysdata"></a>sysdata

Display system RAM and CPU utilization.

Configuration parameters:
  - `format` output format string
  - `high_threshold` percent to consider CPU or RAM usage as 'high load'
  - `med_threshold` percent to consider CPU or RAM usage as 'medium load'

Format of status string placeholders:
  - `{cpu_temp}` cpu temperature
  - `{cpu_usage}` cpu usage percentage
  - `{mem_total}` total memory
  - `{mem_used}` used memory
  - `{mem_used_percent}` used memory percentage

NOTE: If using the `{cpu_temp}` option, the `sensors` command should
be available, provided by the `lm-sensors` or `lm_sensors` package.

**author** Shahin Azad &lt;ishahinism at Gmail&gt;, shrimpza

---

### <a name="taskwarrior"></a>taskwarrior

Display currently active (started) taskwarrior tasks.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds (5s default)

Requires
  - `task`

**author** James Smith http://jazmit.github.io/

**license** BSD

---

### <a name="timer"></a>timer

A simple countdown timer.

This is a very basic countdown timer.  You can change the timer length as well
as pausing, restarting and resetting it.  Currently this is more of a demo of a
composite.

Each part of the timer can be changed independently hours, minutes, seconds using
mouse buttons 4 and 5 (scroll wheel).
Button 1 starts/pauses the countdown.
Button 2 resets timer.

Configuration parameters:
  - `sound` path to a sound file that will be played when the timer expires.
    *(default None)*
  - `time` how long in seconds for the timer
    *(default 60)*

---

### <a name="twitch_streaming"></a>twitch_streaming

Checks if a Twitch streamer is online.

Checks if a streamer is online using the Twitch Kraken API to see
if a channel is currently streaming or not.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds
    *(default 10)*
  - `format` Display format when online
    *(default "{stream_name} is live!")*
  - `format_offline` Display format when offline
    *(default "{stream_name} is offline.")*
  - `format_invalid` Display format when streamer does not exist
    *(default "{stream_name} does not exist!")*
  - `stream_name` name of streamer(twitch.tv/&lt;stream_name&gt;)
    *(default None)*

Format of status string placeholders:
    {stream_name}:  name of the streamer

**author** Alex Caswell horatioesf@virginmedia.com

**license** BSD

---

### <a name="uname"></a>uname

Display uname information.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds (1h default)
  - `format` see placeholders below

Format of status string placeholders:
  - `{system}` system/OS name, e.g. 'Linux', 'Windows', or 'Java'
  - `{node}` computer’s network name (may not be fully qualified!)
  - `{release}` system’s release, e.g. '2.2.0' or 'NT'
  - `{version}` system’s release version, e.g. '#3 on degas'
  - `{machine}` machine type, e.g. 'x86_64'
  - `{processor}` the (real) processor name, e.g. 'amdk6'

**author** ultrabug (inspired by ndalliard)

---

### <a name="vnstat"></a>vnstat

Display vnstat statistics.

Coloring rules.

If value is bigger that dict key, status string will turn to color, specified
in the value.

Example:
    coloring = {
    800: "#dddd00",
    900: "#dd0000",
    }
    (0 - 800: white, 800-900: yellow, >900 - red)

Format of status string placeholders:
  - `{down}` download
  - `{total}` total
  - `{up}` upload

Requires:
  - external program called `vnstat` installed and configured to work.

**author** shadowprince

**license** Eclipse Public License

---

### <a name="volume_status"></a>volume_status

Display current sound volume using amixer.

Expands on the standard i3status volume module by adding color
and percentage threshold settings.
Volume up/down and Toggle mute via mouse clicks can be easily added see
example.

Configuration parameters:
  - `button_down` Button to click to decrease volume. Setting to 0 disables.
    *(default 0)*
  - `button_mute` Button to click to toggle mute. Setting to 0 disables.
    *(default 0)*
  - `button_up` Button to click to increase volume. Setting to 0 disables.
    *(default 0)*
  - `cache_timeout` how often we refresh this module in seconds.
    *(default 10)*
  - `channel` Alsamixer channel to track.
    *(default 'Master')*
  - `device` Alsamixer device to use.
    *(default 'default')*
  - `format` Format of the output.
    *(default '♪: {percentage}%')*
  - `format_muted` Format of the output when the volume is muted.
    *(default '♪: muted')*
  - `threshold_bad` Volume below which color is set to bad.
    *(default 20)*
  - `threshold_degraded` Volume below which color is set to degraded.
    *(default 50)*
  - `volume_delta` Percentage amount that the volume is increased or
    decreased by when volume buttons pressed.
    *(default 5)*

Format status string parameters:
  - `{percentage}` Percentage volume

Example:

```
# Add mouse clicks to change volume

volume_status {
    button_up = 4
    button_down = 5
    button_mute = 2
}
```

Requires:
  - `alsa-utils` (tested with alsa-utils 1.0.29-1)

NOTE:
    If you are changing volume state by external scripts etc and
    want to refresh the module quicker than the i3status interval,
    send a USR1 signal to py3status in the keybinding.
    Example: killall -s USR1 py3status

**author** &lt;Jan T&gt; <jans.tuomi@gmail.com>

**license** BSD

---

### <a name="vpn_status"></a>vpn_status

Drop-in replacement for i3status run_watch VPN module.

Expands on the i3status module by displaying the name of the connected vpn
using pydbus. Asynchronously updates on dbus signals unless check_pid is True.

Configuration parameters:
  - `cache_timeout` How often to refresh in seconds when check_pid is True.
    *(default 10)*
  - `check_pid` If True, act just like the default i3status module.
    *(default False)*
  - `format` Format of the output.
    *(default 'VPN: {name}')*
  - `pidfile` Same as i3status.conf pidfile, checked when check_pid is True.
    *(default '/sys/class/net/vpn0/dev_id')*

Format string parameters:
  - `{name}` The name and/or status of the VPN.

Requires:
  - `pydbus` Which further requires PyGi. Check your distribution's repositories.

**author** Nathan Smith <nathan AT praisetopia.org>

---

### <a name="weather_yahoo"></a>weather_yahoo

Display Yahoo! Weather forecast as icons.

Based on Yahoo! Weather. forecast, thanks guys !
http://developer.yahoo.com/weather/

Find your woeid using:
    http://woeid.rosselliot.co.nz/

Configuration parameters:
  - `cache_timeout` how often to check for new forecasts
  - `forecast_days` how many forecast days you want shown
  - `forecast_include_today` show today's forecast, default false. Note that
    `{today}` in `format` shows the current conditions, while this variable
    shows today's forecast.
  - `forecast_text_separator` separator between forecast entries, default ' '
  - `format` uses 2 placeholders:
  - {today} : text generated by `format_today`
  - {forecasts} : text generated by `format_forecast`, separated by
    `forecast_text_separator`
  - `format_forecast` possible placeholders: {icon}, {low}, {high}, {units},
  - `{text}`
  - `format_today` possible placeholders: {icon}, {temp}, {units}, {text}
    example:
    format = "Now: {icon}{temp}°{units} {text}"
    output:
    Now: ☂-4°C Light Rain/Windy
  - `icon_cloud` cloud icon, default '☁'
  - `icon_default` unknown weather icon, default '?'
  - `icon_rain` rain icon, default '☂'
  - `icon_snow` snow icon, default '☃'
  - `icon_sun` sun icon, default '☀'
  - `request_timeout` check timeout
  - `units` Celsius (C) or Fahrenheit (F)
  - `woeid` Yahoo woeid (extended location)

The WOEID in this example is for Paris, France => 615702

```
weather_yahoo {
    woeid = 615702
    format_today = "Now: {icon}{temp}°{units} {text}"
    forecast_days = 5
}
```

**author** ultrabug, rail

---

### <a name="whatismyip"></a>whatismyip

Display your public/external IP address and toggle to online status on click.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 30s)*
  - `format` the only placeholder available is {ip} *(default '{ip}')*
  - `format_offline` what to display when offline
  - `format_online` what to display when online
  - `hide_when_offline` hide the module output when offline *(default False)*
  - `mode` default mode to display is 'ip' or 'status' (click to toggle)
  - `negative_cache_timeout` how often to check again when offline
  - `timeout` how long before deciding we're offline
  - `url` change IP check url (must output a plain text IP address)

**author** ultrabug

---

### <a name="whoami"></a>whoami

Display the currently logged in user.

Inspired by i3 FAQ:
    https://faq.i3wm.org/question/1618/add-user-name-to-status-bar/

---

### <a name="wifi"></a>wifi

Display WiFi bit rate, quality, signal and SSID using iw.

Configuration parameters:
  - `bitrate_bad` Bad bit rate in Mbit/s *(default: 26)*
  - `bitrate_degraded` Degraded bit rate in Mbit/s *(default: 53)*
  - `blocks` a string, where each character represents quality level
    *(default: "_▁▂▃▄▅▆▇█")*
  - `cache_timeout` Update interval in seconds *(default: 10)*
  - `device` Wireless device name *(default: "wlan0")*
  - `down_color` Output color when disconnected, possible values:
    "good", "degraded", "bad" *(default: "bad")*
  - `format_down` Output when disconnected *(default: "down")*
  - `format_up` See placeholders below
    *(default: "W: {bitrate} {signal_percent} {ssid}")*
  - `round_bitrate` If true, bit rate is rounded to the nearest whole number
    *(default: true)*
  - `signal_bad` Bad signal strength in percent *(default: 29)*
  - `signal_degraded` Degraded signal strength in percent *(default: 49)*
  - `use_sudo` Use sudo to run iw, make sure iw requires no password by
    adding a sudoers entry like
    "&lt;username&gt; ALL=(ALL) NOPASSWD: /usr/bin/iw dev wl* link"
    *(default: false)*

Format of status string placeholders:
  - `{bitrate}` Display bit rate
  - `{device}` Display device name
  - `{icon}` Character representing the quality based on bitrate,
    as defined by the 'blocks'
  - `{ip}` Display IP address
  - `{signal_dbm}` Display signal in dBm
  - `{signal_percent}` Display signal in percent
  - `{ssid}` Display SSID

Requires:
  - `iw`
  - `ip` if {ip} is used

**author** Markus Weimar <mail@markusweimar.de>

**license** BSD

---

### <a name="window_title"></a>window_title

Display the current window title.

Requires:
  - `i3-py` (https://github.com/ziberna/i3-py)
    `pip install i3-py`

If payload from server contains wierd utf-8
(for example one window have something bad in title) - the plugin will
give empty output UNTIL this window is closed.
I can't fix or workaround that in PLUGIN, problem is in i3-py library.

**author** shadowprince

**license** Eclipse Public License

---

### <a name="window_title_async"></a>window_title_async

Display the current window title with async update.

Uses asynchronous update via i3 IPC events.
Provides instant title update only when it required.

Configuration parameters:
  - `always_show` do not hide the title when it can be already
    visible (e.g. in tabbed layout), default: False.
  - `empty_title` string that will be shown instead of the title when
    the title is hidden, default: "" (empty string).
  - `format` format of the title, default: "{title}".
  - `max_width` maximum width of block (in symbols).
    If the title is longer than `max_width`,
    the title will be truncated to `max_width - 1`
    first symbols with ellipsis appended. Default: 120.

Requires:
  - `i3ipc` (https://github.com/acrisci/i3ipc-python)

**author** Anon1234 https://github.com/Anon1234

**license** BSD

---

### <a name="wwan_status"></a>wwan_status

Display current network and ip address for newer Huwei modems.

It is tested for Huawei E3276 (usb-id 12d1:1506) aka Telekom Speed
Stick LTE III but may work on other devices, too.

DEPENDENCIES:
  - `netifaces`
  - `pyserial`

Configuration parameters:
  - `baudrate` There should be no need to configure this, but
    feel free to experiment.
    Default is 115200.
  - `cache_timeout` How often we refresh this module in seconds.
    Default is 5.
  - `consider_3G_degraded` If set to True, only 4G-networks will be
    considered 'good'; 3G connections are shown
    as 'degraded', which is yellow by default. Mostly
    useful if you want to keep track of where there
    is a 4G connection.
    Default is False.
  - `format_down` What to display when the modem is not plugged in
    Default is: 'WWAN: down'
  - `format_error` What to display when modem can't be accessed.
    Default is 'WWAN: {error}'
  - `format_no_service` What to display when the modem does not have a
    network connection. This allows to omit the then
    meaningless network generation. Therefore the
    default is 'WWAN: ({status}) {ip}'
  - `format_up` What to display upon regular connection
    Default is 'WWAN: ({status}/{netgen}) {ip}'
  - `interface` The default interface to obtain the IP address
    from. For wvdial this is most likely ppp0.
    For netctl it can be different.
    Default is: ppp0
  - `modem` The device to send commands to. Default is
  - `modem_timeout` The timespan betwenn querying the modem and
    collecting the response.
    Default is 0.4 (which should be sufficient)

**author** Timo Kohorst timo@kohorst-online.com

PGP: B383 6AE6 6B46 5C45 E594 96AB 89D2 209D DBF3 2BB5

---

### <a name="xrandr"></a>xrandr

Control your screen(s) layout easily.

This modules allows you to handle your screens outputs directly from your bar!
  - Detect and propose every possible screen combinations
  - Switch between combinations using click events and mouse scroll
  - Activate the screen or screen combination on a single click
  - It will detect any newly connected or removed screen automatically

For convenience, this module also proposes some added features:
  - Dynamic parameters for POSITION and WORKSPACES assignment (see below)
  - Automatic fallback to a given screen or screen combination when no more
    screen is available (handy for laptops)
  - Automatically apply this screen combination on start: no need for xorg!
  - Automatically move workspaces to screens when they are available
  - Define your own subset of output combinations to use

Configuration parameters:
  - `cache_timeout` how often to (re)detect the outputs
  - `fallback` when the current output layout is not available anymore,
    fallback to this layout if available. This is very handy if you
    have a laptop and switched to an external screen for presentation
    and want to automatically fallback to your laptop screen when you
    disconnect the external screen.
  - `force_on_start` switch to the given combination mode if available
    when the module starts (saves you from having to configure xorg)
  - `format_clone` string used to display a 'clone' combination
  - `format_extend` string used to display a 'extend' combination
  - `output_combinations` string used to define your own subset of output
    combinations to use, instead of generating every possible combination
    automatically. Provide the values in the format that this module uses,
    splitting the combinations using '|' character.
    The combinations will be rotated in the exact order as you listed them.
    When an output layout is not available anymore, the configurations
    are automatically filtered out.
    Example:
    Assuming the default values for `format_clone` and `format_extend`
    are used, and assuming you have two screens 'eDP1' and 'DP1', the
    following setup will reduce the number of output combinations
    from four (every possible one) down to two:
    output_combinations = "eDP1|eDP1+DP1"

Dynamic configuration parameters:
  - &lt;OUTPUT&gt;_pos: apply the given position to the OUTPUT
    Example: DP1_pos = "-2560x0"
    Example: DP1_pos = "above eDP1"
    Example: DP1_pos = "below eDP1"
    Example: DP1_pos = "left-of LVDS1"
    Example: DP1_pos = "right-of eDP1"
  - &lt;OUTPUT&gt;_workspaces: comma separated list of workspaces to move to
    the given OUTPUT when it is activated
    Example: DP1_workspaces = "1,2,3"

Example config:

```
xrandr {
    force_on_start = "eDP1+DP1"
    DP1_pos = "left-of eDP1"
    VGA_workspaces = "7"
}
```

**author** ultrabug

---

### <a name="xrandr_rotate"></a>xrandr_rotate

Switch between horizontal and vertical screen rotation on a single click.

Configuration parameters:
  - `cache_timeout` how often to refresh this module.
    *(default is 10)*
  - `format` a string that formats the output, can include placeholders.
    *(default is '{icon}')*
  - `hide_if_disconnected` a boolean flag to hide icon when `screen` is
    disconnected.
    it has no effect unless `screen` option is also configured.
    *(default: None)*
  - `horizontal_icon` a character to represent horizontal rotation.
    *(default is 'H')*
  - `horizontal_rotation` a horizontal rotation for xrandr to use.
    available options: 'normal' or 'inverted'.
    *(default is 'normal')*
  - `screen` display output name to rotate, as detected by xrandr.
    if not provided, all enabled screens will be rotated.
    *(default: None)*
  - `vertical_icon` a character to represent vertical rotation.
    *(default is 'V')*
  - `vertical_rotation` a vertical rotation for xrandr to use.
    available options: 'left' or 'right'.
    *(default is 'left')*

Available placeholders for formatting the output:
  - `{icon}` a rotation icon, specified by `horizontal_icon` or `vertical_icon`.
  - `{screen}` a screen name, specified by `screen` option or detected
    automatically if only one screen is connected, otherwise 'ALL'.

**author** Maxim Baz (https://github.com/maximbaz)

**license** BSD

---

### <a name="xsel"></a>xsel

Display the X selection.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds
    *(default is at every py3status configured interval)*
  - `command` the xsel command to run *(default 'xsel')*
  - `max_size` stip the selection to this value *(default 15)*
  - `symmetric` show the beginning and the end of the selection string
    with respect to configured max_size.

Requires:
  - `xsel` command line tool

**author** Sublim3 umbsublime@gamil.com

**license** BSD

---

### <a name="yandexdisk_status"></a>yandexdisk_status

Display Yandex.Disk status.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds
    *(default 10)*
  - `format` prefix text for the Yandex.Disk status
    *(default 'Yandex.Disk: {status}')*

Format of status string placeholders:
  - `{status}` daemon status

Requires:
  - `yandex-disk` command line tool (link: https://disk.yandex.com/)

**author** Vladimir Potapev (github:vpotapev)

**license** BSD
