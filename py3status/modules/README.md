<a name="top"></a>Modules
========


**[arch_updates](#arch_updates)** — Displays the number of package updates pending for an Arch Linux installation.

**[aws_bill](#aws_bill)** — Display the current AWS bill.

**[backlight](#backlight)** — Display the current screen backlight level.

**[battery_level](#battery_level)** — Display the battery level.

**[bitcoin_price](#bitcoin_price)** — Display bitcoin prices using bitcoincharts.com.

**[bluetooth](#bluetooth)** — Display bluetooth status.

**[check_tcp](#check_tcp)** — Display if a TCP port is available on the given host.

**[clementine](#clementine)** — Display the current "artist - title" playing in Clementine.

**[clock](#clock)** — Display time and date information.

**[coin_balance](#coin_balance)** — Display balances of diverse crypto-currencies

**[deadbeef](#deadbeef)** — Display track currently playing in deadbeef.

**[diskdata](#diskdata)** — Display advanced disk usage information

**[do_not_disturb](#do_not_disturb)** — A simple "Do Not Disturb" module that can turn on and off all system notifications.

**[dpms](#dpms)** — Activate or deactivate DPMS and screen blanking.

**[dropboxd_status](#dropboxd_status)** — Display dropboxd status.

**[exchange_rate](#exchange_rate)** — Display foreign exchange rates.

**[external_script](#external_script)** — Display output of given script.

**[fedora_updates](#fedora_updates)** — The number of package updates pending for a Fedora Linux installation.

**[file_status](#file_status)** — Display if a file or dir exists.

**[frame](#frame)** — Group modules and treat them as a single one.

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

**[mpris](#mpris)** — Display information about the current song and video playing on player with

**[net_iplist](#net_iplist)** — Display the list of network interfaces and their IPs.

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

**[rss_aggregator](#rss_aggregator)** — Display the unread feed items in your favorite RSS aggregator.

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

**[volume_status](#volume_status)** — Display current sound volume.

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
  - `hide_if_zero` Don't show on bar if True
    *(default False)*
  - `include_aur` Set to True to use 'cower' to check for AUR updates
    *(default False)*

Format placeholders:
  - `{aur}` Number of pending aur updates
  - `{pacman}` Number of pending pacman updates

Requires:
  - `cower` Needed to display pending 'aur' updates

**author** Iain Tatch &lt;iain.tatch@gmail.com&gt;

**license** BSD

---

### <a name="aws_bill"></a>aws_bill

Display the current AWS bill.

**WARNING: This module generate some costs on the AWS bill.
Take care about the cache_timeout to limit these fees!**

Configuration parameters:
  - `aws_access_key_id` Your AWS access key *(default '')*
  - `aws_account_id` The root ID of the AWS account
    Can be found here` https://console.aws.amazon.com/billing/home#/account
    *(default '')*
  - `aws_secret_access_key` Your AWS secret key *(default '')*
  - `billing_file` Csv file location *(default '/tmp/.aws_billing.csv')*
  - `cache_timeout` How often we refresh this module in seconds *(default 3600)*
  - `format`  string that formats the output. See placeholders below.
    *(default '{bill_amount}$')*
  - `s3_bucket_name` The bucket where billing files are sent by AWS.
    Follow this article to activate this feature:
    http://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/detailed-billing-reports.html
    *(default '')*

Format placeholders:
  - `{bill_amount}` AWS bill amount

Color options:
  - `color_good` Balance available
  - `color_bad` An error has occured

Requires:
  - `boto`

**author** nawadanp

---

### <a name="backlight"></a>backlight

Display the current screen backlight level.

Configuration parameters:
  - `brightness_delta` Change the brightness by this step.
    *(default 5)*
  - `brightness_initial` Set brightness to this value on start.
    *(default None)*
  - `brightness_minimal` Don't go below this brightness to avoid black screen
    *(default 1)*
  - `button_down` Button to click to decrease brightness. Setting to 0 disables.
    *(default 5)*
  - `button_up` Button to click to increase brightness. Setting to 0 disables.
    *(default 4)*
  - `cache_timeout` How often we refresh this module in seconds *(default 10)*
  - `device` The backlight device
    If not specified the plugin will detect it automatically
    *(default None)*
  - `device_path` path to backlight eg /sys/class/backlight/acpi_video0
    if None then use first device found.
    *(default None)*
  - `format` Display brightness, see placeholders below
    *(default '☼: {level}%')*

Format status string parameters:
  - `{level}` brightness

Requires:
  - `xbacklight` need for changing brightness, not detection

**author** Tjaart van der Walt (github:tjaartvdwalt)

**license** BSD

---

### <a name="battery_level"></a>battery_level

Display the battery level.

Configuration parameters:
  - `battery_id` id of the battery to be displayed
    set to 'all' for combined display of all batteries
    *(default 0)*
  - `blocks` a string, where each character represents battery level
    especially useful when using icon fonts (e.g. FontAwesome)
    *(default "_▁▂▃▄▅▆▇█")*
  - `cache_timeout` a timeout to refresh the battery state
    *(default 30)*
  - `charging_character` a character to represent charging battery
    especially useful when using icon fonts (e.g. FontAwesome)
    *(default "⚡")*
  - `format` string that formats the output. See placeholders below.
    *(default "{icon}")*
  - `format_notify_charging` format of the notification received when you click
    on the module while your computer is plugged in
    *(default 'Charging ({percent}%)')*
  - `format_notify_discharging` format of the notification received when you
    click on the module while your computer is not plugged in
    *(default "{time_remaining}")*
  - `hide_seconds` hide seconds in remaining time
    *(default False)*
  - `hide_when_full` hide any information when battery is fully charged (when
    the battery level is greater than or equal to 'threshold_full')
    *(default False)*
  - `measurement_mode` either 'acpi' or 'sys', or None to autodetect. 'sys'
    should be more robust and does not have any extra requirements, however
    the time measurement may not work in some cases
    *(default None)*
  - `notification` show current battery state as notification on click
    *(default False)*
  - `notify_low_level` display notification when battery is running low (when
    the battery level is less than 'threshold_degraded')
    *(default False)*
  - `sys_battery_path` set the path to your battery(ies), without including its
    number
    *(default "/sys/class/power_supply/")*
  - `threshold_bad` a percentage below which the battery level should be
    considered bad
    *(default 10)*
  - `threshold_degraded` a percentage below which the battery level should be
    considered degraded
    *(default 30)*
  - `threshold_full` a percentage at or above which the battery level should
    should be considered full
    *(default 100)*

Format placeholders:
  - `{ascii_bar}` - a string of ascii characters representing the battery level,
    an alternative visualization to '{icon}' option
  - `{icon}` - a character representing the battery level,
    as defined by the 'blocks' and 'charging_character' parameters
  - `{percent}` - the remaining battery percentage (previously '{}')
  - `{time_remaining}` - the remaining time until the battery is empty

Color options:
  - `color_bad` Battery level is below threshold_bad
  - `color_charging` Battery is charging *(default "#FCE94F")*
  - `color_degraded` Battery level is below threshold_degraded
  - `color_good` Battery level is above thresholds

Requires:
  - the `acpi` the acpi command line utility (only if
    `measurement_mode='acpi'`)

**author** shadowprince, AdamBSteele, maximbaz, 4iar, m45t3r

**license** Eclipse Public License

---

### <a name="bitcoin_price"></a>bitcoin_price

Display bitcoin prices using bitcoincharts.com.

Configuration parameters:
  - `cache_timeout` Should be at least 15 min according to bitcoincharts.
    *(default 900)*
  - `color_index` Index of the market responsible for coloration,
  -1 means no coloration, except when only one market is selected
    *(default -1)*
  - `field` Field that is displayed per market,
    see http://bitcoincharts.com/about/markets-api/ *(default 'close')*
  - `hide_on_error` Display empty response if True, else an error message
    *(default False)*
  - `markets` Comma-separated list of markets. Supported markets can
    be found at http://bitcoincharts.com/markets/list/
    *(default 'btceUSD, btcdeEUR')*
  - `symbols` Try to match currency abbreviations to symbols,
    e.g. USD -&gt; $, EUR -&gt; € and so on *(default True)*

Color options:
  - `color_bad`  Price has dropped or not available
  - `color_good` Price has increased

**author** Andre Doser &lt;doser.andre AT gmail.com&gt;

---

### <a name="bluetooth"></a>bluetooth

Display bluetooth status.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 10)*
  - `device_separator` the separator char between devices (only if more than one
    device) *(default '|')*
  - `format` format when there is a connected device *(default '{name}')*
  - `format_no_conn` format when there is no connected device *(default 'OFF')*
  - `format_no_conn_prefix` prefix when there is no connected device
    *(default 'BT: ')*
  - `format_prefix` prefix when there is a connected device *(default 'BT: ')*

Format placeholders:
  - `{name}` device name
  - `{mac}` device MAC address

Color options:
  - `color_bad` Connection on
  - `color_good` Connection off

Requires:
  - `hcitool`

**author** jmdana &lt;https://github.com/jmdana&gt;

**license** GPLv3 &lt;http://www.gnu.org/licenses/gpl-3.0.txt&gt;

---

### <a name="check_tcp"></a>check_tcp

Display if a TCP port is available on the given host.

Configuration parameters:
  - `cache_timeout` how often to run the check *(default 10)*
  - `format` what to display on the bar *(default '{host}:{port} {state}')*
  - `host` check if tcp port on host is up *(default 'localhost')*
  - `port` the tcp port *(default 22)*

Format placeholders:
  - `{state}` port state ('DOWN' or 'UP')

Color options:
  - `color_down` Unavailable, default color_bad
  - `color_up` Available, default color_good

**author** obb, Moritz Lüdecke

---

### <a name="clementine"></a>clementine

Display the current "artist - title" playing in Clementine.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 5)*
  - `format` Display format for Clementine *(default '♫ {current}')*

Format placeholders:
  - `{current}` currently playing

Requires:
  - `clementine`

**author** Francois LASSERRE &lt;choiz@me.com&gt;

**license** GNU GPL http://www.gnu.org/licenses/gpl.html

---

### <a name="clock"></a>clock

Display time and date information.

This module allows one or more datetimes to be displayed.
All datetimes share the same format_time but can set their own timezones.
Timezones are defined in the `format` using the TZ name in squiggly brackets eg
`{GMT}`, `{Portugal}`, `{Europe/Paris}`, `{America/Argentina/Buenos_Aires}`.

ISO-3166 two letter country codes eg `{de}` can also be used but if more than
one timezone exists for the country eg `{us}` the first one will be selected.

`{Local}` can be used for the local settings of your computer.

Note: Timezones are case sensitive

A full list of timezones can be found at
https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

Configuration parameters:
  - `block_hours` length of time period for all blocks in hours *(default 12)*
  - `blocks` a string, where each character represents time period
    from the start of a time period.
    *(default '🕛🕧🕐🕜🕑🕝🕒🕞🕓🕟🕔🕠🕕🕡🕖🕢🕗🕣🕘🕤🕙🕥🕚🕦')*
  - `button_change_format` button that switches format used setting to None
    disables *(default 1)*
  - `button_change_time_format` button that switches format_time used. Setting
    to None disables *(default 2)*
  - `button_reset` button that switches display to the first timezone. Setting
    to None disables *(default 3)*
  - `cycle` If more than one display then how many seconds between changing the
    display *(default 0)*
  - `format` defines the timezones displayed. This can be a single string or a
    list.  If a list is supplied then the formats can be cycled through
    using `cycle` or by button click.  *(default '{Local}')*
  - `format_time` format to use for the time, strftime directives such as `%H`
    can be used this can be either a string or to allow multiple formats as
    a list.  The one used can be changed by button click.
    *(default ['[{name_unclear} ]%c', '[{name_unclear} ]%x %X',
    '[{name_unclear} ]%a %H:%M', '[{name_unclear} ]{icon}'])*

Format placeholders:
  - `{icon}` a character representing the time from `blocks`
  - `{name}` friendly timezone name eg `Buenos Aires`
  - `{name_unclear}` friendly timezone name eg `Buenos Aires` but is empty if
    only one timezone is provided
  - `{timezone}` full timezone name eg `America/Argentina/Buenos_Aires`
  - `{timezone_unclear}` full timezone name eg `America/Argentina/Buenos_Aires`
    but is empty if only one timezone is provided


Requires:
  - `pytz` python library
  - `tzlocal` python library

i3status.conf example:

```
# cycling through London, Warsaw, Tokyo
clock {
    cycle = 30
    format = ["{Europe/London}", "{Europe/Warsaw}", "{Asia/Tokyo}"]
    format_time = "{name} %H:%M"
}


# Show the time and date in New York
clock {
   format = "Big Apple {America/New_York}"
   format_time = "%Y-%m-%d %H:%M:%S"
}


# wall clocks
clock {
    format = "{Asia/Calcutta} {Africa/Nairobi} {Asia/Bangkok}"
    format_time = "{name} {icon}"
}
```

**author** tobes

**license** BSD

---

### <a name="coin_balance"></a>coin_balance

Display balances of diverse crypto-currencies

This module grabs your current balance of different crypto-currents from a
wallet server. The server must conform to the bitcoin RPC specification.
Currently Bitcoin, Dogecoin, and Litecoin are supported.

Configuration parameters:
  - `cache_timeout` An integer specifying the cache life-time of the output in
    seconds *(default 30)*
  - `coin_password` A string containing the password for the server for
    'coin'. The 'coin' part must be replaced by a supported coin identifier
    (see below for a list of identifiers). If no value is supplied,
    the value of 'password' (see below) will be used.  If 'password' too is
    not set, the value will be retrieved from the standard 'coin' daemon
    configuration file. *(default None)*
  - `coin_username` A string containing the username for the server for
    'coin'. The 'coin' part must be replaced by a supported coin identifier
    (see below for a list of identifiers). If no value is supplied,
    the value of 'username' (see below) will be used.  If 'username' too is
    not set, the value will be retrieved from the standard 'coin' daemon
    configuration file. *(default None)*
  - `credentials` *(default None)*
  - `format` A string describing the output format for the module. The {&lt;coin&gt;}
    placeholder (see below) will be used to determine how to fetch the
    coin balance. Multiple placeholders are allowed, but all balances will
    be fetched from the same host. *(default 'LTC: {litecoin}')*
  - `host` The coin-server hostname. Note that all coins will use the same host
    for their querries. *(default 'localhost')*
  - `password` A string containing the password for all coin-servers. If neither
    this setting, nor a specific coin_password (see above) is specified,
    the password for each coin will be read from the respective standard
    daemon configuration file. *(default None)*
  - `protocol` A string to select the server communication protocol.
    *(default 'http')*
  - `username` A string containing the username for all coin-servers. If neither
    this setting, nor a specific coin_username (see above) is specified,
    the username for each coin will be read from the respective standard
    daemon configuration file. *(default None)*

Format placeholders:
  - `{<coin>}` Your balance for the coin &lt;coin&gt; where &lt;coin&gt; is one of:
  - bitcoin
  - dogecoin
  - litecoin

Requires:
  - `requests` python module from pypi https://pypi.python.org/pypi/requests
    At least version 2.4.2 is required.

Example:

```
# Get your Bitcoin balance using automatic credential detection
coin_balance {
    cache_timeout = 45
    format = "My BTC: {bitcoin}"
    host = "localhost"
    protocol = "http"
}

# Get your Bitcoin, Dogecoin and Litecoin balances using specific credentials
# for Bitcoin and automatic detection for Dogecoin and Litecoin
coin_balance {
    # ...
    format = "{bitcoin} BTC {dogecoin} XDG {litecoin} LTC"
    bitcoin_username = "lcdata"
    bitcoin_password = "omikron-theta"
    # ...
}

# Get your Dogecoin and Litecoin balances using 'global' credentials
coin_balance {
    # ...
    format = "XDG: {dogecoin} LTC: {litecoin}"
    username = "crusher_b"
    password = "WezRulez"
    # ...
}

# Get you Dogecoin, Litecoin, and Bitcoin balances by using 'global'
# credentials for Bitcoin and Dogecoin but specific credentials for
# Litecoin.
coin_balance {
    # ...
    format = "XDG: {dogecoin} LTC: {litecoin} BTC: {bitcoin}"
    username = "zcochrane"
    password = "sunny_islands"
    litecoin_username = 'locutus'
    litecoin_password = 'NCC-1791-D'
    # ...
}
```

**author** Felix Morgner &lt;felix.morgner@gmail.com&gt;

**license** 3-clause-BSD

---

### <a name="deadbeef"></a>deadbeef

Display track currently playing in deadbeef.

Configuration parameters:
  - `cache_timeout` how often we refresh usage in seconds *(default 1)*
  - `delimiter` delimiter character for parsing *(default '¥')*
  - `format` see placeholders below *(default '{artist} - {title}')*

Format placeholders:
  - `{artist}` artist
  - `{title}` title
  - `{elapsed}` elapsed time
  - `{length}` total length
  - `{year}` year
  - `{tracknum}` track number

Color options:
  - `color_bad` An error occurred

Requires:
    deadbeef:

**author** mrt-prodz

---

### <a name="diskdata"></a>diskdata

Display advanced disk usage information

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds.
    *(default 10)*
  - `disk` disk or partition whose stat to check. Set to None to get global stats.
    *(default None)*
  - `format` format of the output.
    *(default "{disk}: {used_percent}% ({total})")*
  - `format_rate` format for the rates value
    *(default "[\?min_length=11 {value:.1f} {unit}]")*
  - `format_space` format for the disk space values
    *(default "[\?min_length=5 {value:.1f}]")*
  - `sector_size` size of the disk's sectors.
    *(default 512)*
  - `si_units` use SI units
    *(default False)*
  - `thresholds` thresholds to use for color changes
    *(default {'free': [(0, 'bad'), (10, 'degraded'), (100, 'good')],
    'total': [(0, "good"), (1024, 'degraded'), (1024 * 1024, 'bad')]})*
  - `unit` unit to use. If the unit contains a multiplier prefix, only this
    exact unit will ever be used
    *(default "B/s")*

Format placeholders:
  - `{disk}` the selected disk
  - `{free}` free space on disk in GB
  - `{used}` used space on disk in GB
  - `{used_percent}` used space on disk in %
  - `{read}` reading rate
  - `{total}` total IO rate
  - `{write}` writing rate

format_rate placeholders:
  - `{unit}` name of the unit
  - `{value}` numeric value of the rate

format_space placeholders:
  - `{value}` numeric value of the free/used space on the device

Color thresholds:
  - `{free}` Change color based on the value of free
  - `{used}` Change color based on the value of used_percent
  - `{read}` Change color based on the value of read
  - `{total}` Change color based on the value of total
  - `{write}` Change color based on the value of write

**author** guiniol

**license** BSD

---

### <a name="do_not_disturb"></a>do_not_disturb

A simple "Do Not Disturb" module that can turn on and off all system notifications.

A left mouse click will toggle the state of this module.

Configuration parameters:
  - `format` Display format for the "Do Not Disturb" module.
    *(default '{state}')*
  - `notification_manager` The process name of your notification manager.
    *(default 'dunst')*
  - `refresh_interval` Refresh interval to use for killing notification manager process.
    *(default 0.25)*
  - `state_off` Message when the "Do Not Disturb" mode is disabled.
    *(default 'OFF')*
  - `state_on` Message when the "Do Not Disturb" mode is enabled.
    *(default 'ON')*

Color options:
  - `color_bad` "Do Not Disturb" mode is enabled.
  - `color_good` "Do Not Disturb" mode is disabled.

---

### <a name="dpms"></a>dpms

Activate or deactivate DPMS and screen blanking.

This module allows activation and deactivation
of DPMS (Display Power Management Signaling)
by clicking on 'DPMS' in the status bar.

Configuration parameters:
  - `format` string to display *(default '{icon}')*
  - `icon_off` string to display when dpms is disabled *(default 'DPMS')*
  - `icon_on` string to display when dpms is enabled *(default 'DPMS')*

Format placeholders:
  - `{icon}` display current dpms icon

Color options:
  - `color_on` when dpms is enabled, defaults to color_good
  - `color_off` when dpms is disabled, defaults to color_bad

**author** Andre Doser &lt;dosera AT tf.uni-freiburg.de&gt;

---

### <a name="dropboxd_status"></a>dropboxd_status

Display dropboxd status.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 10)*
  - `format` prefix text for the dropbox status *(default 'Dropbox: {}')*

Valid status values include:
  - Dropbox isn't running!
  - Starting...
  - Downloading file list...
  - Syncing "filename"
  - Up to date

Color options:
  - `color_bad` Dropbox is unavailable
  - `color_degraded` All other statuses
  - `color_good` Dropbox up-to-date

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
    *(default 15)*
  - `format` see placeholders below *(default '{output}')*
  - `script_path` script you want to show output of (compulsory)
    *(default None)*
  - `strip_output` shall we strip leading and trailing spaces from output
    *(default False)*

Format placeholders:
  - `{output}` output of script given by "script_path"

i3status.conf example:

```
external_script {
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
  - `check_security` Check for security updates
    *(default True)*
  - `format` Display format to use
    *(default 'DNF: {updates}')*

Format placeholders:
  - `{updates}` number of pending dnf updates

Color options:
  - `color_bad` Security notice
  - `color_degraded` Upgrade available
  - `color_good` No upgrades needed

**author** tobes

**license** BSD

---

### <a name="file_status"></a>file_status

Display if a file or dir exists.

Configuration parameters:
  - `cache_timeout` how often to run the check *(default 10)*
  - `format` format of the output. *(default '{icon}')*
  - `icon_available` icon to display when available *(default '●')*
  - `icon_unavailable` icon to display when unavailable *(default '■')*
  - `path` the path to a file or dir to check if it exists *(default None)*

Color options:
  - `color_bad` Error or file/directory does not exist
  - `color_good` File or directory exists

Format placeholders:
  - `{icon}` icon for the current availability

**author** obb, Moritz Lüdecke

---

### <a name="frame"></a>frame

Group modules and treat them as a single one.

This can be useful for example when adding modules to a group and you wish two
modules to be shown at the same time.

By adding the `{button}` placeholder in the format you can enable a toggle
button to hide or show the content.

Configuration parameters:
  - `button_toggle` Button used to toggle if one in format.
    Setting to None disables *(default 1)*
  - `format` Display format to use *(default '{output}')*
  - `format_button_closed` Format for the button when frame open *(default '+')*
  - `format_button_open` Format for the button when frame closed *(default '-')*
  - `format_separator` Specify separator between contents.
    If this is None then the default i3bar separator will be used
    *(default None)*
  - `open` If button then the frame can be set to be open or close
    *(default True)*

Format of status string parameters:
  - `{button}` If used a button will be used that can be clicked to hide/show
    the contents of the frame.
  - `{output}` The output of the modules in the frame

Example config:

```
# A frame showing times in different cities.
# We also have a button to hide/show the content

frame time {
    format = '{output}{button}'
    format_separator = ' '  # have space instead of usual i3bar separator

    tztime la {
        format = "LA %H:%M"
        timezone = "America/Los_Angeles"
    }

    tztime ny {
        format = "NY %H:%M"
        timezone = "America/New_York"
    }

    tztime du {
        format = "DU %H:%M"
        timezone = "Asia/Dubai"
    }
}

# Define a group which shows volume and battery info
# or the current time.
# The frame, volume_status and battery_level modules are named
# to prevent them clashing with any other defined modules of the same type.
group {
    frame {
        volume_status {}
        battery_level {}
    }

    time {}
}
```

**author** tobes

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
    if notifications, else the project page for the repository if there is
    one (otherwise the github home page). Setting to `0` disables.
    *(default 3)*
  - `cache_timeout` How often we refresh this module in seconds
    *(default 60)*
  - `format` Format of output
    *(default '{repo} {issues}/{pull_requests}{notifications}'
    if username and auth_token provided else
    '{repo} {issues}/{pull_requests}')*
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

Format placeholders:
  - `{repo}` the short name of the repository being checked.
    eg py3status
  - `{repo_full}` the full name of the repository being checked.
    eg ultrabug/py3status
  - `{issues}` Number of open issues.
  - `{pull_requests}` Number of open pull requests
  - `{notifications}` Notifications.  If no notifications this will be empty.
  - `{notifications_count}` Number of notifications.  This is also the __Only__
    placeholder available to `format_notifications`.

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

It features thresholds to colorize the output and forces a low timeout to
limit the impact of a server connectivity problem on your i3bar freshness.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 300)*
  - `critical` set bad color above this threshold *(default 20)*
  - `db` database to use *(default '')*
  - `format` format of the module output *(default '{tickets_open} tickets')*
  - `host` database host to connect to *(default '')*
  - `password` login password *(default '')*
  - `timeout` timeout for database connection *(default 5)*
  - `user` login user *(default '')*
  - `warning` set degraded color above this threshold *(default 15)*

Format placeholders:
  - `{tickets_open}` The number of open tickets

Color options:
  - `color_bad` Open ticket above critical threshold
  - `color_degraded` Open ticket above warning threshold

Requires:
    MySQL-python: http://pypi.python.org/pypi/MySQL-python

---

### <a name="gpmdp"></a>gpmdp

Display currently playing song from Google Play Music Desktop Player.

Configuration parameters:
  - `cache_timeout`  how often we refresh this module in seconds *(default 5)*
  - `format`         specify the items and ordering of the data in the status bar.
    These area 1:1 match to gpmdp-remote's options
    *(default '♫ {info}')*

Format placeholders:
  - `{info}`            Print info about now playing song
  - `{title}`           Print current song title
  - `{artist}`          Print current song artist
  - `{album}`           Print current song album
  - `{album_art}`       Print current song album art URL
  - `{time_current}`    Print current song time in milliseconds
  - `{time_total}`      Print total song time in milliseconds
  - `{status}`          Print whether GPMDP is paused or playing
  - `{current}`         Print now playing song in "artist - song" format
  - `{help}`            Print this help message


Requires:
  - `gpmdp` http://www.googleplaymusicdesktopplayer.com/
  - `gpmdp-remote` https://github.com/iandrewt/gpmdp-remote

**author** Aaron Fields https://twitter.com/spirotot

**license** BSD

---

### <a name="graphite"></a>graphite

Display Graphite metrics.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds.
    *(default 120)*
  - `datapoint_selection` when multiple data points are returned,
    use "max" or "min" to determine which one to display.
    *(default "max")*
  - `format` you MUST use placeholders here to display data, see below.
    *(default '')*
  - `graphite_url` URL to your graphite server. *(default '')*
  - `http_timeout` HTTP query timeout to graphite.
    *(default 10)*
  - `proxy` You can configure the proxy with HTTP or HTTPS.
    *(default: None)*
    examples:
    proxy = 'https://myproxy.example.com:1234/'
    proxy = 'http://user:passwd@myproxy.example.com/'
    proxy = 'socks5://user:passwd@host:port'
    (proxy_socks is available after an 'pip install requests[socks]')
    *(default None)*
  - `targets` semicolon separated list of targets to query graphite for.
    *(default '')*
  - `threshold_bad` numerical threshold,
    if set will send a notification and colorize the output.
    *(default None)*
  - `threshold_degraded` numerical threshold,
    if set will send a notification and colorize the output.
    *(default None)*
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

Color options:
  - `color_bad` threshold_bad has been exceeded
  - `color_degraded` threshold_degraded has been exceeded

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
    *(default "{output}" if click_mode is 'all',
    "{output} {button}" if click_mode 'button')*
  - `format_button_closed` Format for the button when group open
    *(default  '+')*
  - `format_button_open` Format for the button when group closed
    *(default '-')*
  - `format_closed` Format for module output when closed.
    *(default "{button}")*
  - `open` Is the group open and displaying its content. Has no effect if
    `{button}` not in format *(default True)*


Format placeholders:
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
  - `cache_timeout` how often we refresh this module in seconds *(default 10)*
  - `format` see placeholders below *(default '{current}')*

Format placeholders:
  - `{current}` hamster current

Requires:
  - `hamster`

**author** Aaron Fields (spirotot [at] gmail.com)

**license** BSD

---

### <a name="icinga2"></a>icinga2

Display Icinga2 service status information.

Configuration parameters:
  - `base_url` the base url to the icinga-web2 services list *(default '')*
  - `ca` *(default True)*
  - `cache_timeout` how often the data should be updated *(default 60)*
  - `disable_acknowledge` enable or disable counting of acknowledged
    service problems *(default False)*
  - `format` define a format string like "CRITICAL: %d"
    *(default '{status_name}: {count}')*
  - `password` password to authenticate against the icinga-web2 interface
    *(default '')*
  - `status` set the status you want to obtain
    (0=OK,1=WARNING,2=CRITICAL,3=UNKNOWN)
    *(default 0)*
  - `url_parameters` *(default '?service_state={service_state}&amp;format=json')*
  - `user` username to authenticate against the icinga-web2 interface
    *(default '')*

**author** Ben Oswald &lt;ben.oswald@root-space.de&gt;

**license** BSD License &lt;https://opensource.org/licenses/BSD-2-Clause&gt;

**source** https://github.com/nazco/i3status-modules

---

### <a name="imap"></a>imap

Display the unread messages count from your IMAP account.

Configuration parameters:
  - `cache_timeout` how often to run this check *(default 60)*
  - `criterion` status of emails to check for *(default 'UNSEEN')*
  - `format` format to display *(default 'Mail: {unseen}')*
  - `hide_if_zero` don't show on bar if True *(default False)*
  - `imap_server` IMAP server to connect to *(default '&lt;IMAP_SERVER&gt;')*
  - `mailbox` name of the mailbox to check *(default 'INBOX')*
  - `new_mail_color` what color to output on new mail *(default '')*
  - `password` login password *(default '&lt;PASSWORD&gt;')*
  - `port` IMAP server port *(default '993')*
  - `security` what authentication method is used: 'ssl' or 'starttls'
    (startssl needs python 3.2 or later) *(default 'ssl')*
  - `user` login user *(default '&lt;USERNAME&gt;')*

Format placeholders:
  - `{unseen}` number of unread emails

**author** obb

---

### <a name="insync"></a>insync

Get current insync status

Thanks to Iain Tatch &lt;iain.tatch@gmail.com&gt; for the script that this is based on.

Configuration parameters:
  - `cache_timeout` How often we refresh this module in seconds
    *(default 10)*
  - `format` Display format to use *(default '{status} {queued}')*

Format placeholders:
  - `{status}` Status of Insync
  - `{queued}` Number of files queued

Color options:
  - `color_bad` Offline
  - `color_degraded` Default
  - `color_good` Synced

Requires:
  - `insync` command line tool

**author** Joshua Pratt &lt;jp10010101010000@gmail.com&gt;

**license** BSD

---

### <a name="kdeconnector"></a>kdeconnector

Display information of your android device over KDEConnector.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 30)*
  - `device` the device name, you need this if you have more than one device
    connected to your PC *(default None)*
  - `device_id` alternatively to the device name you can set your device id here
    *(default None)*
  - `format` see placeholders below
    *(default '{name}{notif_status} {bat_status} {charge}%')*
  - `format_disconnected` text if device is disconnected
    *(default 'device disconnected')*
  - `low_threshold` percentage value when text is twitch to color_bad
    *(default 20)*
  - `status_bat` text when battery is discharged *(default '⬇')*
  - `status_chr` text when device is charged *(default '⬆')*
  - `status_full` text when battery is full *(default '☻')*
  - `status_no_notif` text when you have no notifications *(default '')*
  - `status_notif` text when notifications are available *(default ' ✉')*

Format placeholders:
  - `{bat_status}` battery state
  - `{charge}` the battery charge
  - `{name}` name of the device
  - `{notif_size}` number of notifications
  - `{notif_status}` shows if a notification is available or not

Color options:
  - `color_bad` Device unknown, unavailable
    or battery below low_threshold and not charging
  - `color_degraded` Connected and battery not charging
  - `color_good` Connected and battery charging

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
  - `cache_timeout` check for keyboard layout change every seconds *(default 10)*
  - `colors` a comma separated string of color values for each layout,
    eg: "us=#FCE94F, fr=#729FCF". (deprecated use color options)
    *(default None)*
  - `format` see placeholders below *(default '{layout}')*

Format placeholders:
  - `{layout}` currently active keyboard layout

Color options:
  - `color_<layout>` color for the layout
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
  - `cache_timeout` how often we refresh this module in seconds *(default 2)*
  - `format` template string (see below)
    *(default '%state% [[[%artist%] - %title%]|[%file%]]')*
  - `hide_when_paused` hide the status if state is paused *(default False)*
  - `hide_when_stopped` hide the status if state is stopped *(default True)*
  - `host` mpd host *(default 'localhost')*
  - `max_width` maximum status length *(default 120)*
  - `password` mpd password *(default None)*
  - `port` mpd port *(default '6600')*
  - `state_pause` label to display for "paused" state *(default '[pause]')*
  - `state_play` label to display for "playing" state *(default '[play]')*
  - `state_stop` label to display for "stopped" state *(default '[stop]')*

Color options:
  - `color_pause` Paused, default color_degraded
  - `color_play` Playing, default color_good
  - `color_stop` Stopped, default color_bad

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

### <a name="mpris"></a>mpris

Display information about the current song and video playing on player with
mpris support.

There are two ways to control the media player. Either by clicking with a mouse
button in the text information or by using buttons. For former you have
to define the button parameters in the i3status config.

Configuration parameters:
  - `button_next` mouse button to play the next entry *(default 4)*
  - `button_previous` mouse button to play the previous entry *(default 5)*
  - `button_stop` mouse button to stop the player *(default None)*
  - `button_toggle` mouse button to toggle between play and pause mode *(default 1)*
  - `format` see placeholders below
    *(default '{previous}{toggle}{next} {state} [{artist} - ][{title}]')*
  - `format_none` define output if no player is running
    *(default 'no player running')*
  - `icon_next` text for the next button in the button control panel *(default '»')*
  - `icon_pause` text for the pause button in the button control panel *(default '▮')*
  - `icon_play` text for the play button in the button control panel *(default '▶')*
  - `icon_previous` text for the previous button in the button control panel *(default '«')*
  - `icon_stop` text for the stop button in the button control panel *(default '◾')*
  - `player_priority` priority of the players.
    Keep in mind that the state has a higher priority than
    player_priority. So when player_priority is "[mpd, bomi]" and mpd is
    paused and bomi is playing than bomi wins. *(default [])*
  - `state_pause` text for placeholder {state} when song is paused *(default '▮')*
  - `state_play` text for placeholder {state} when song is playing *(default '▶')*
  - `state_stop` text for placeholder {state} when song is stopped *(default '◾')*

Format of status string placeholders:
  - `{album}` album name
  - `{artist}` artiste name (first one)
  - `{length}` time duration of the song
  - `{player}` show name of the player
  - `{state}` playback status of the player
  - `{time}` played time of the song
  - `{title}` name of the song

Format of button placeholders:
  - `{next}` play the next title
  - `{pause}` pause the player
  - `{play}` play the player
  - `{previous}` play the previous title
  - `{stop}` stop the player
  - `{toggle}` toggle between play and pause

Color options:
  - `color_control_inactive` button is not clickable
  - `color_control_active` button is clickable
  - `color_paused` song is paused, defaults to color_degraded
  - `color_playing` song is playing, defaults to color_good
  - `color_stopped` song is stopped, defaults to color_bad

Requires:
  - `pydbus` python library module

i3status.conf example:

```
mpris {
    format = "{previous}{play}{next} {player}: {state} [[{artist} - {title}]|[{title}]]"
    format_none = "no player"
    player_priority = "[mpd, cantata, vlc, bomi, *]"
}
```

only show information from mpd and vlc, but mpd has a higher priority:

```
mpris {
    player_priority = "[mpd, vlc]"
}
```

show information of all players, but mpd and vlc have the highest priority:

```
mpris {
    player_priority = "[mpd, vlc, *]"
}
```

vlc has the lowest priority:

```
mpris {
    player_priority = "[*, vlc]"
}
```

Tested players:
    bomi
    Cantata
    mpDris2 (mpris extension for mpd)
    vlc

**author** Moritz Lüdecke, tobes

---

### <a name="net_iplist"></a>net_iplist

Display the list of network interfaces and their IPs.

This module supports both IPv4 and IPv6. There is the possibility to blacklist
interfaces and IPs, as well as to show interfaces with no IP address. It will
show an alternate text if no IP are available.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds.
    *(default 30)*
  - `format` format of the output.
    *(default 'Network: {format_iface}')*
  - `format_iface` format string for the list of IPs of each interface.
    *(default '{iface}:[ {ip4}][ {ip6}]')*
  - `format_no_ip` string to show if there are no IPs to display.
    *(default 'no connection')*
  - `iface_blacklist` list of interfaces to ignore. Accepts shell-style wildcards.
    *(default ['lo'])*
  - `iface_sep` string to write between interfaces.
    *(default ' ')*
  - `ip_blacklist` list of IPs to ignore. Accepts shell-style wildcards.
    *(default [])*
  - `ip_sep` string to write between IP addresses.
    *(default ',')*
  - `remove_empty` do not show interfaces with no IP.
    *(default True)*

Format placeholders:
  - `{format_iface}` the format_iface string.

Format placeholders for format_iface:
  - `{iface}` name of the interface.
  - `{ip4}` list of IPv4 of the interface.
  - `{ip6}` list of IPv6 of the interface.

Color options:
  - `color_bad` no IPs to show
  - `color_good` IPs to show

Example:

```
net_iplist {
    iface_blacklist = []
    ip_blacklist = ['127.*', '::1']
}
```

Requires:
  - `ip` utility found in iproute2 package

---

### <a name="net_rate"></a>net_rate

Display the current network transfer rate.

Configuration parameters:
  - `all_interfaces` ignore self.interfaces, but not self.interfaces_blacklist
    *(default True)*
  - `cache_timeout` how often we refresh this module in seconds
    *(default 2)*
  - `devfile` location of dev file under /proc
    *(default '/proc/net/dev')*
  - `format` format of the module output
    *(default '{interface}: {total}')*
  - `format_no_connection` when there is no data transmitted from the start of the plugin
    *(default '')*
  - `format_value` format to use for values
    *(default "[\?min_length=11 {value:.1f} {unit}]")*
  - `hide_if_zero` hide indicator if rate == 0
    *(default False)*
  - `interfaces` comma separated list of interfaces to track
    *(default [])*
  - `interfaces_blacklist` comma separated list of interfaces to ignore
    *(default 'lo')*
  - `si_units` use SI units
    *(default False)*
  - `sum_values` sum values of each interface instead of taking the top one
    *(default False)*
  - `thresholds` thresholds to use for colors
    *(default [(0, 'bad'), (1024, 'degraded'), (1024 * 1024, 'good')])*
  - `unit` unit to use. If the unit contains a multiplier prefix, only this
    exact unit will ever be used
    *(default "B/s")*

Format placeholders:
  - `{down}` download rate
  - `{interface}` name of interface
  - `{total}` total rate
  - `{up}` upload rate

format_value placeholders:
  - `{unit}` current unit
  - `{value}` numeric value

Color thresholds:
  - `{down}` Change color based on the value of down
  - `{total}` Change color based on the value of total
  - `{up}` Change color based on the value of up

**author** shadowprince

**license** Eclipse Public License

---

### <a name="netdata"></a>netdata

Display network speed and bandwidth usage.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 2)*
  - `low_speed` threshold *(default 30)*
  - `low_traffic` threshold *(default 400)*
  - `med_speed` threshold *(default 60)*
  - `med_traffic` threshold *(default 700)*
  - `nic` the network interface to monitor *(default 'eth0')*

Color options:
  - `color_bad` Rate is below low threshold
  - `color_degraded` Rate is below med threshold
  - `color_good` Rate is med threshold or higher

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
  - `cache_timeout` how often we refresh this module in seconds *(default 300)*
  - `domain` domain name to check *(default '')*
  - `format` output format string *(default '{total_count} NS {status}')*
  - `lifetime` resolver lifetime *(default 0.3)*
  - `nameservers` comma separated list of reference DNS nameservers *(default '')*
  - `resolvers` comma separated list of DNS resolvers to use *(default '')*

Format placeholders:
  - `{nok_count}` The number of failed name servers
  - `{ok_count}` The number of working name servers
  - `{status}` The overall status of the name servers (OK or NOK)
  - `{total_count}` The total number of name servers

Color options:
  - `color_bad` One or more lookups have failed
  - `color_good` All lookups have succeeded

Requires:
  - `dnspython` python module

**author** nawadanp

---

### <a name="nvidia_temp"></a>nvidia_temp

Display NVIDIA GPU temperature.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 10)*
  - `format_prefix` a prefix for the output. *(default 'GPU: ')*
  - `format_units` the temperature units. Will appear at the end. *(default '°C')*
  - `temp_separator` the separator char between temperatures (only if more than
    one GPU) *(default '|')*

Color options:
  - `color_bad` Temperature can't be read.
  - `color_good` Everything is OK.

Requires:
  - `nvidia-smi`

**author** jmdana &lt;https://github.com/jmdana&gt;

**license** BSD

---

### <a name="online_status"></a>online_status

Display if a connection to the internet is established.

Configuration parameters:
  - `cache_timeout` how often to run the check *(default 10)*
  - `format` display format for online_status *(default '{icon}')*
  - `icon_off` what to display when offline *(default '■')*
  - `icon_on` what to display when online *(default '●')*
  - `timeout` how long before deciding we're offline *(default 2)*
  - `url` connect to this url to check the connection status
    *(default 'http://www.google.com')*

Format placeholders:
  - `{icon}` display current online status

Color options:
  - `color_bad` Offline
  - `color_good` Online

**author** obb

---

### <a name="pingdom"></a>pingdom

Display the latest response time of the configured Pingdom checks.

We also verify the status of the checks and colorize if needed.
Pingdom API doc : https://www.pingdom.com/features/api/documentation/

Configuration parameters:
  - `app_key` create an APP KEY on pingdom first *(default '')*
  - `cache_timeout` how often to refresh the check from pingdom *(default 600)*
  - `checks` comma separated pindgom check names to display *(default '')*
  - `login` pingdom login *(default '')*
  - `max_latency` maximal latency before coloring the output *(default 500)*
  - `password` pingdom password *(default '')*
  - `request_timeout` pindgom API request timeout *(default 15)*

Color options:
  - `color_bad` Site is down
  - `color_degraded` Latency exceeded max_latency

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
  - `cache_timeout` how often to update in seconds *(default 10)*
  - `debug` enable verbose logging (bool) *(default False)*
  - `format` format of the output *(default "{icon}")*
  - `pause_icon` *(default '❚❚')*
  - `play_icon` *(default '▶')*
  - `stop_icon` *(default '◼')*
  - `supported_players` supported players (str) (comma separated list)
    *(default 'audacious,vlc')*
  - `volume_tick` percentage volume change on mouse wheel (int) (positive number
    or None to disable it) *(default 1)*

Format placeholders:
  - `{icon}` an icon to control music/video players

**author** Federico Ceratto &lt;federico.ceratto@gmail.com&gt;, rixx

**license** BSD

---

### <a name="pomodoro"></a>pomodoro

Display and control a Pomodoro countdown.

Button 1 starts/pauses countdown.
Button 2 switch Pomodoro/Break.
Button 3 resets timer.

Configuration parameters:
  - `display_bar` display time in bars when True, otherwise in seconds
    *(default False)*
  - `format` define custom display format. See placeholders below *(default '{ss}')*
  - `format_separator` separator between minutes:seconds *(default ':')*
  - `max_breaks` maximum number of breaks *(default 4)*
  - `num_progress_bars` number of progress bars *(default 5)*
  - `sound_break_end` break end sound (file path) (requires pyglet
    or pygame) *(default None)*
  - `sound_pomodoro_end` pomodoro end sound (file path) (requires pyglet
    or pygame) *(default None)*
  - `sound_pomodoro_start` pomodoro start sound (file path) (requires pyglet
    od pygame) *(default None)*
  - `timer_break` normal break time (seconds) *(default 300)*
  - `timer_long_break` long break time (seconds) *(default 900)*
  - `timer_pomodoro` pomodoro time (seconds) *(default 1500)*

Format placeholders:
  - `{bar}` display time in bars
  - `{ss}` display time in total seconds (1500)
  - `{mm}` display time in total minutes (25)
  - `{mmss}` display time in (hh-)mm-ss (25:00)

Color options:
  - `color_bad` Pomodoro not running
  - `color_degraded` Pomodoro break
  - `color_good` Pomodoro active

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
  - `cache_timeout` how often to run the check *(default 10)*
  - `format_not_running` what to display when process is not running
    *(default '■')*
  - `format_running` what to display when process running *(default '●')*
  - `full` if True, match against the full command line and not just the
    process name *(default False)*
  - `process` the process name to check if it is running *(default None)*

Color options:
  - `color_bad` Process not running or error
  - `color_good` Process running

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
  - `cycle_time` How often we change this color in seconds
    *(default 1)*
  - `force` If True then the color will always be set.  If false the color will
    only be changed if it has not been set by a module.
    *(default False)*
  - `gradient` The colors we will cycle through, This is a list of hex values
    *(default [ '#FF0000', '#FFFF00', '#00FF00', '#00FFFF',
    '#0000FF', '#FF00FF', '#FF0000', ])*
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
  - `cache_timeout` how often to update in seconds *(default 5)*
  - `config_file` file path to store the time already spent
    and restore it the next session
    *(default '~/.i3/py3status/counter-config.save')*
  - `format` output format string
    *(default 'Time: {days} day {hours}:{mins:02d} Cost: {total}')*
  - `format_money` output format string
    *(default '{price}$')*
  - `hour_price` your price per hour *(default 30)*
  - `tax` tax value (1.02 = 2%) *(default 1.02)*

Format placeholders:
  - `{days}` The number of whole days in running timer
  - `{hours}` The remaining number of whole hours in running timer
  - `{mins}` The remaining number of whole minutes in running timer
  - `{secs}` The remaining number of seconds in running timer
  - `{subtotal}` The subtotal cost (time * rate)
  - `{tax}` The tax cost, based on the subtotal cost
  - `{total}` The total cost (subtotal + tax)
  - `{total_hours}` The total number of whole hours in running timer
  - `{total_mins}` The total number of whole minutes in running timer

Money placeholders:
  - `{price}` numeric value of money

Color options:
  - `color_running` Running, default color_good
  - `color_stopped` Stopped, default color_bad

**author** Amaury Brisou &lt;py3status AT puzzledge.org&gt;

---

### <a name="rss_aggregator"></a>rss_aggregator

Display the unread feed items in your favorite RSS aggregator.

For now, supported aggregators are:
    * OwnCloud/NextCloud with News application
    * Tiny Tiny RSS 1.6 or newer

You can also decide to check only for specific feeds or folders of feeds. To use this
feature, you have to first get the IDs of those feeds or folders. You can get those IDs
by clicking on the desired feed or folder and watching the URL.

For OwnCloud/NextCloud:
```
https://yourcloudinstance.com/index.php/apps/news/#/items/feeds/FEED_ID
https://yourcloudinstance.com/index.php/apps/news/#/items/folders/FOLDER_ID

```
    For Tiny Tiny RSS:

```
https://yourttrssinstance.com/index.php#f=FEED_ID&c=0
https://yourttrssinstance.com/index.php#f=FOLDER_ID&c=1
```

If both feeds list and folders list are left empty, all unread feed items will be counted.
You may use both feeds list and folders list, but given feeds shouldn't be included in
given folders, else unread count number behavior is unpredictable. Same warning when
aggregator allows subfolders: the folders list shouldn't include a folder and one of its
subfolder.

Configuration parameters:
  - `aggregator` feed aggregator used. Supported values are `owncloud` and `ttrss`.
    Other aggregators might be supported in future releases. Contributions are
    welcome. *(default 'owncloud')*
  - `cache_timeout` how often to run this check *(default 60)*
  - `feed_ids` list of IDs of feeds to watch, see note below *(default [])*
  - `folder_ids` list of IDs of folders ro watch *(default [])*
  - `format` format to display *(default 'Feed: {unseen}')*
  - `password` login password *(default None)*
  - `server` aggregator server to connect to *(default 'https://yourcloudinstance.com')*
  - `user` login user *(default None)*

Format placeholders:
  - `{unseen}` sum of numbers of unread feed elements

Color options:
  - `color_new_items` text color when there is new items *(default color_good)*
  - `color_error` text color when there is an error *(default color_bad)*

Requires:
  - `requests` python module from pypi https://pypi.python.org/pypi/requests

**author** raspbeguy

---

### <a name="rt"></a>rt

Display the number of ongoing tickets from selected RT queues.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 300)*
  - `db` database to use *(default '')*
  - `format` see placeholders below *(default 'general: {General}')*
  - `host` database host to connect to *(default '')*
  - `password` login password *(default '')*
  - `threshold_critical` set bad color above this threshold *(default 20)*
  - `threshold_warning` set degraded color above this threshold *(default 10)*
  - `timeout` timeout for database connection *(default 5)*
  - `user` login user *(default '')*

Format placeholders:
  - `{YOUR_QUEUE_NAME}` number of ongoing RT tickets (open+new+stalled)

Color options:
  - `color_bad` Exceeded threshold_critical
  - `color_degraded` Exceeded threshold_warning

Requires:
    PyMySQL: https://pypi.python.org/pypi/PyMySQL
    or
    MySQL-python: http://pypi.python.org/pypi/MySQL-python

It features thresholds to colorize the output and forces a low timeout to
limit the impact of a server connectivity problem on your i3bar freshness.

**author** ultrabug

---

### <a name="scratchpad_async"></a>scratchpad_async

Display the amount of windows and indicate urgency hints on scratchpad (async).

Configuration parameters:
  - `always_show` always display the format *(default False)*
  - `format` display format for scratchpad_async *(default "{counter} ⌫")*

Format placeholders:
  - `{counter}` number of scratchpad windows

Requires:
  - `i3ipc` (https://github.com/acrisci/i3ipc-python)

**author** cornerman

**license** BSD

---

### <a name="scratchpad_counter"></a>scratchpad_counter

Display the amount of windows in your i3 scratchpad.

Configuration parameters:
  - `cache_timeout` How often we refresh this module in seconds *(default 5)*
  - `format` Format of indicator *(default '{counter} ⌫')*
  - `hide_when_none` Hide indicator when there is no windows *(default False)*

Format placeholders:
  - `{counter}` number of scratchpad windows

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
  - `cache_timeout` how often to update in seconds *(default 5)*
  - `file_length` generated file_name length *(default 4)*
  - `push` True/False if you want to push your screenshot to your server
    *(default True)*
  - `save_path` Directory where to store your screenshots. *(default '~/Pictures/')*
  - `screenshot_command` the command used to generate the screenshot
    *(default 'gnome-screenshot -f')*
  - `upload_path` the remote path where to push the screenshot *(default '/files')*
  - `upload_server` your server address *(default 'puzzledge.org')*
  - `upload_user` your ssh user *(default 'erol')*

Color options:
  - `color_good` Displayed color

**author** Amaury Brisou &lt;py3status AT puzzledge.org&gt;

---

### <a name="selinux"></a>selinux

Display the current selinux state.

This module displays the current state of selinux on your machine: Enforcing
(good), Permissive (bad), or Disabled (bad).

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 10)*
  - `format` see placeholders below, *(default 'selinux: {state}')*

Format placeholders:
  - `{state}` the current selinux state

Color options:
  - `color_bad` Enforcing
  - `color_degraded` Permissive
  - `color_good` Disabled

Requires:
  - `libselinux-python`
    or
  - `libselinux-python3` (optional for python3 support)

**author** bstinsonmhk

**license** BSD

---

### <a name="spaceapi"></a>spaceapi

Display if your favorite hackerspace is open or not.

Configuration parameters:
  - `button_url` Button that when clicked opens the URL sent in the space's API.
    Setting to None disables. *(default 3)*
  - `cache_timeout` Set timeout between calls in seconds *(default 60)*
  - `closed_text` text if space is closed, strftime parameters
    will be translated *(default 'closed')*
  - `open_text` text if space is open, strftime parmeters will be translated
    *(default 'open')*
  - `time_text` format used for time display *(default ' since %H:%M')*
  - `url` URL to SpaceAPI json file of your space
    *(default 'http://status.chaospott.de/status.json')*

Color options:
  - `color_closed` Space is open, defaults to color_bad
  - `color_open` Space is closed, defaults to color_good

**author** timmszigat

**license** WTFPL &lt;http://www.wtfpl.net/txt/copying/&gt;

---

### <a name="spotify"></a>spotify

Display information about the current song playing on Spotify.

Configuration parameters:
  - `cache_timeout` how often to update the bar *(default 5)*
  - `format` see placeholders below *(default '{artist} : {title}')*
  - `format_down` define output if spotify is not running
    *(default 'Spotify not running')*
  - `format_stopped` define output if spotify is not playing
    *(default 'Spotify stopped')*

Format placeholders:
  - `{album}` album name
  - `{artist}` artiste name (first one)
  - `{time}` time duration of the song
  - `{title}` name of the song

Color options:
  - `color_offline` Spotify is not running, defaults to color_bad
  - `color_paused` Song is stopped or paused, defaults to color_degraded
  - `color_playing` Song is playing, defaults to color_good

i3status.conf example:

```
spotify {
    format = "{title} by {artist} -> {time}"
    format_down = "no Spotify"
}
```

Requires:
    spotify (&gt;=1.0.27.71.g0a26e3b2)

**author** Pierre Guilbert, Jimmy Garpehäll, sondrele, Andrwe

---

### <a name="static_string"></a>static_string

Display static text.

Configuration parameters:
  - `format` text that should be printed *(default '')*

**author** frimdo ztracenastopa@centrum.cz

---

### <a name="sysdata"></a>sysdata

Display system RAM and CPU utilization.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 10)*
  - `format` output format string
    *(default '[\?color=cpu CPU: {cpu_usage}%], '
    '[\?color=mem Mem: {mem_used}/{mem_total} GB ({mem_used_percent}%)]')*
  - `mem_unit` the unit of memory to use in report, case insensitive.
    ['dynamic', 'KiB', 'MiB', 'GiB'] *(default 'GiB')*
  - `padding` length of space padding to use on the left
    *(default 0)*
  - `precision` precision of values
    *(default 2)*
  - `thresholds` thresholds to use for color changes
    *(default [(0, "good"), (40, "degraded"), (75, "bad")])*
  - `zone` thermal zone to use. If None try to guess CPU temperature
    *(default None)*

Format placeholders:
  - `{cpu_temp}` cpu temperature
  - `{cpu_usage}` cpu usage percentage
  - `{mem_total}` total memory
  - `{mem_unit}` unit for memory
  - `{mem_used}` used memory
  - `{mem_used_percent}` used memory percentage

Color thresholds:
  - `cpu` change color based on the value of cpu_usage
  - `max_cpu_mem` change the color based on the max value of cpu_usage and mem_used_percent
  - `mem` change color based on the value of mem_used_percent
  - `temp` change color based on the value of cpu_temp

NOTE: If using the `{cpu_temp}` option, the `sensors` command should
be available, provided by the `lm-sensors` or `lm_sensors` package.

**author** Shahin Azad &lt;ishahinism at Gmail&gt;, shrimpza, guiniol

---

### <a name="taskwarrior"></a>taskwarrior

Display currently active (started) taskwarrior tasks.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 5)*
  - `format` string to print *(default '{task}')*

Format placeholders:
  - `{task}` to-do list of active tasks

Requires
    task: https://taskwarrior.org/download/

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
  - `format_invalid` Display format when streamer does not exist
    *(default "{stream_name} does not exist!")*
  - `format_offline` Display format when offline
    *(default "{stream_name} is offline.")*
  - `stream_name` name of streamer(twitch.tv/&lt;stream_name&gt;)
    *(default None)*

Format placeholders:
    {stream_name}:  name of the streamer

Color options:
  - `color_bad` Stream offline or error
  - `color_good` Stream is live

**author** Alex Caswell horatioesf@virginmedia.com

**license** BSD

---

### <a name="uname"></a>uname

Display uname information.

Configuration parameters:
  - `format` see placeholders below *(default '{system} {release} {machine}')*

Format placeholders:
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

Configuration parameters:
  - `cache_timeout` *(default 180)*
  - `coloring` *(default {})*
  - `format` *(default '{total}')*
  - `initial_multi` *(default 1024)*
  - `left_align` *(default 0)*
  - `multiplier_top` *(default 1024)*
  - `precision` *(default 1)*
  - `statistics_type` *(default 'd')*
  - `unit_multi` *(default 1024)*

Coloring rules.

If value is bigger that dict key, status string will turn to color, specified
in the value.

Example:
    coloring = {
    800: "#dddd00",
    900: "#dd0000",
    }
    (0 - 800: white, 800-900: yellow, &gt;900 - red)

Format placeholders:
  - `{down}` download
  - `{total}` total
  - `{up}` upload

Requires:
  - external program called `vnstat` installed and configured to work.

**author** shadowprince

**license** Eclipse Public License

---

### <a name="volume_status"></a>volume_status

Display current sound volume.

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
  - `channel` channel to track. Default value is backend dependent.
    *(default None)*
  - `command` Choose between "amixer", "pamixer" or "pactl".
    If None, try to guess based on available commands.
    *(default None)*
  - `device` Device to use. Defaults value is backend dependent
    *(default None)*
  - `format` Format of the output.
    *(default '♪: {percentage}%')*
  - `format_muted` Format of the output when the volume is muted.
    *(default '♪: muted')*
  - `max_volume` Allow the volume to be increased past 100% if available.
    pactl supports this *(default 120)*
  - `thresholds` Threshold for percent volume.
    *(default [(0, 'bad'), (20, 'degraded'), (50, 'good')])*
  - `volume_delta` Percentage amount that the volume is increased or
    decreased by when volume buttons pressed.
    *(default 5)*

Format placeholders:
  - `{percentage}` Percentage volume

Color options:
  - `color_muted` Volume is muted, if not supplied color_bad is used
    if set to `None` then the threshold color will be used.

Example:

```
# Add mouse clicks to change volume
# Set thresholds to rainbow colors

volume_status {
    button_up = 4
    button_down = 5
    button_mute = 2

    thresholds = [
        (0, "#FF0000"),
        (10, "#E2571E"),
        (20, "#FF7F00"),
        (30, "#FFFF00"),
        (40, "#00FF00"),
        (50, "#96BF33"),
        (60, "#0000FF"),
        (70, "#4B0082"),
        (80, "#8B00FF"),
        (90, "#FFFFFF")
    ]
}
```

Requires:
  - `alsa-utils` alsa backend (tested with alsa-utils 1.0.29-1)
  - `pamixer` pulseaudio backend

NOTE:
    If you are changing volume state by external scripts etc and
    want to refresh the module quicker than the i3status interval,
    send a USR1 signal to py3status in the keybinding.
    Example: killall -s USR1 py3status

**author** &lt;Jan T&gt; &lt;jans.tuomi@gmail.com&gt;

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

Format placeholders:
  - `{name}` The name and/or status of the VPN.

Color options:
  - `color_bad` VPN connected
  - `color_good` VPN down

Requires:
  - `pydbus` Which further requires PyGi. Check your distribution's repositories.

**author** Nathan Smith &lt;nathan AT praisetopia.org&gt;

---

### <a name="weather_yahoo"></a>weather_yahoo

Display Yahoo! Weather forecast as icons.

Based on Yahoo! Weather. forecast, thanks guys !
http://developer.yahoo.com/weather/

Find your woeid using:
    http://woeid.rosselliot.co.nz/

Configuration parameters:
  - `cache_timeout` how often to check for new forecasts *(default 7200)*
  - `forecast_days` how many forecast days you want shown *(default 3)*
  - `forecast_include_today` show today's forecast. Note that
    `{today}` in `format` shows the current conditions, while this variable
    shows today's forecast. *(default False)*
  - `forecast_text_separator` separator between forecast entries. *(default ' ')*
  - `format` uses 2 placeholders
    `forecast_text_separator`
    *(default '{today} {forecasts}')*
  - `format_forecast` format of a forecast item *(default '{icon}')*
  - `format_today` format for today `{today}` in format
    example:
    format = "Now: {icon}{temp}°{units} {text}"
    output:
    Now: ☂-4°C Light Rain/Windy
    *(default '{icon}')*
  - `icon_cloud` cloud icon, *(default '☁')*
  - `icon_default` unknown weather icon, *(default '?')*
  - `icon_rain` rain icon, *(default '☂')*
  - `icon_snow` snow icon, *(default '☃')*
  - `icon_sun` sun icon, *(default '☀')*
  - `request_timeout` check timeout *(default 10)*
  - `units` Celsius (C) or Fahrenheit (F) *(default 'c')*
  - `woeid` Yahoo woeid (extended location) *(default None)*

Format placeholders:
  - `{today}` text generated by `format_today`
  - `{forecasts}` text generated by `format_forecast`, separated by

Forcast placeholders:
  - `{icon}` Icon representing weather
  - `{low}` low temperature
  - `{high}` high temperature
  - `{units}` units 'C' or 'F'
  - `{text}` text description of forecats

The WOEID in this example is for Paris, France =&gt; 615702

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
  - `cache_timeout` how often we refresh this module in seconds *(default 30)*
  - `format` available placeholders are {ip} and {country}
    *(default '{ip}')*
  - `format_offline` what to display when offline *(default '■')*
  - `format_online` what to display when online *(default '●')*
  - `hide_when_offline` hide the module output when offline *(default False)*
  - `mode` default mode to display is 'ip' or 'status' (click to toggle)
    *(default 'ip')*
  - `negative_cache_timeout` how often to check again when offline *(default 2)*
  - `timeout` how long before deciding we're offline *(default 5)*
  - `url` change IP check url (must output a plain text IP address)
    *(default 'http://ultrabug.fr/py3status/whatismyip')*
  - `url_geo` IP to check for geo location (must output json)
    *(default 'http://ip-api.com/json')*

Format placeholders:
  - `{country}` display the country
  - `{ip}` display current ip address

Color options:
  - `color_bad` Offline
  - `color_good` Online

**author** ultrabug

---

### <a name="whoami"></a>whoami

Display the currently logged in user.

Configuration parameters:
  - `format` string to print *(default '{username}')*

Format placeholders:
  - `{username}` display current username

Inspired by i3 FAQ:
    https://faq.i3wm.org/question/1618/add-user-name-to-status-bar.1.html

---

### <a name="wifi"></a>wifi

Display WiFi bit rate, quality, signal and SSID using iw.

Configuration parameters:
  - `bitrate_bad` Bad bit rate in Mbit/s *(default 26)*
  - `bitrate_degraded` Degraded bit rate in Mbit/s *(default 53)*
  - `blocks` a string, where each character represents quality level
    *(default "_▁▂▃▄▅▆▇█")*
  - `cache_timeout` Update interval in seconds *(default 10)*
  - `device` Wireless device name *(default "wlan0")*
  - `down_color` Output color when disconnected, possible values:
    "good", "degraded", "bad" *(default "bad")*
  - `format_down` Output when disconnected *(default "W: down")*
  - `format_up` See placeholders below
    *(default "W: {bitrate} {signal_percent} {ssid}")*
  - `round_bitrate` If true, bit rate is rounded to the nearest whole number
    *(default True)*
  - `signal_bad` Bad signal strength in percent *(default 29)*
  - `signal_degraded` Degraded signal strength in percent *(default 49)*
  - `use_sudo` Use sudo to run iw, make sure iw requires no password by
    adding a sudoers entry like
    "&lt;username&gt; ALL=(ALL) NOPASSWD: /usr/bin/iw dev wl* link"
    *(default False)*

Format placeholders:
  - `{bitrate}` Display bit rate
  - `{device}` Display device name
  - `{icon}` Character representing the quality based on bitrate,
    as defined by the 'blocks'
  - `{ip}` Display IP address
  - `{signal_dbm}` Display signal in dBm
  - `{signal_percent}` Display signal in percent
  - `{ssid}` Display SSID

Color options:
  - `color_bad` Signal strength signal_bad or lower
  - `color_degraded` Signal strength signal_degraded or lower
  - `color_good` Signal strength above signal_degraded

Requires:
  - `iw`
  - `ip` if {ip} is used

**author** Markus Weimar &lt;mail@markusweimar.de&gt;

**license** BSD

---

### <a name="window_title"></a>window_title

Display the current window title.

Configuration parameters:
  - `cache_timeout` How often we refresh this module in seconds *(default 0.5)*
  - `format` display format for window_title *(default '{title}')*
  - `max_width` If width of title is greater, shrink it and add '...'
    *(default 120)*

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
    visible (e.g. in tabbed layout). *(default False)*
  - `empty_title` string that will be shown instead of the title when
    the title is hidden. *(default "")*
  - `format` format of the title, *(default "{title}")*
  - `max_width` maximum width of block (in symbols).
    If the title is longer than `max_width`,
    the title will be truncated to `max_width - 1`
    first symbols with ellipsis appended. *(default 120)*

Requires:
  - `i3ipc` (https://github.com/acrisci/i3ipc-python)

**author** Anon1234 https://github.com/Anon1234

**license** BSD

---

### <a name="wwan_status"></a>wwan_status

Display current network and ip address for newer Huwei modems.

It is tested for Huawei E3276 (usb-id 12d1:1506) aka Telekom Speed
Stick LTE III but may work on other devices, too.

Configuration parameters:
  - `baudrate` There should be no need to configure this, but
    feel free to experiment.
    *(default 115200)*
  - `cache_timeout` How often we refresh this module in seconds.
    *(default 5)*
  - `consider_3G_degraded` If set to True, only 4G-networks will be
    considered 'good'; 3G connections are shown
    as 'degraded', which is yellow by default. Mostly
    useful if you want to keep track of where there
    is a 4G connection.
    *(default False)*
  - `format_down` What to display when the modem is not plugged in
    *(default 'WWAN: down')*
  - `format_error` What to display when modem can't be accessed.
    *(default 'WWAN: {error}')*
  - `format_no_service` What to display when the modem does not have a
    network connection. This allows to omit the (then
    meaningless) network generation.
    *(default 'WWAN: {status} {ip}')*
  - `format_up` What to display upon regular connection
    *(default 'WWAN: {status} ({netgen}) {ip}')*
  - `interface` The default interface to obtain the IP address
    from. For wvdial this is most likely ppp0.
    For netctl it can be different.
    *(default 'ppp0')*
  - `modem` The device to send commands to. *(default '/dev/ttyUSB1')*
  - `modem_timeout` The timespan between querying the modem and
    collecting the response.
    *(default 0.4)*

Color options:
  - `color_bad` Error or no connection
  - `color_degraded` Low generation connection eg 2G
  - `color_good` Good connection

Requires:
  - `netifaces`
  - `pyserial`

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
  - `cache_timeout` how often to (re)detect the outputs *(default 10)*
  - `fallback` when the current output layout is not available anymore,
    fallback to this layout if available. This is very handy if you
    have a laptop and switched to an external screen for presentation
    and want to automatically fallback to your laptop screen when you
    disconnect the external screen. *(default True)*
  - `fixed_width` show output as fixed width *(default True)*
  - `force_on_start` switch to the given combination mode if available
    when the module starts (saves you from having to configure xorg)
    *(default None)*
  - `format` display format for xrandr
    *(default '{output}')*
  - `icon_clone` icon used to display a 'clone' combination
    *(default '=')*
  - `icon_extend` icon used to display a 'extend' combination
    *(default '+')*
  - `output_combinations` string used to define your own subset of output
    combinations to use, instead of generating every possible combination
    automatically. Provide the values in the format that this module uses,
    splitting the combinations using '|' character.
    The combinations will be rotated in the exact order as you listed them.
    When an output layout is not available any more, the configurations
    are automatically filtered out.
    Example:
    Assuming the default values for `icon_clone` and `icon_extend`
    are used, and assuming you have two screens 'eDP1' and 'DP1', the
    following setup will reduce the number of output combinations
    from four (every possible one) down to two:
    output_combinations = "eDP1|eDP1+DP1"
    *(default None)*

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
  - &lt;OUTPUT&gt;_rotate: rotate the output as told
    Example: DP1_rotate = "left"

Color options:
  - `color_bad` Displayed layout unavailable
  - `color_degraded` Using a fallback layout
  - `color_good` Displayed layout active

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
    *(default 10)*
  - `format` a string that formats the output, can include placeholders.
    *(default '{icon}')*
  - `hide_if_disconnected` a boolean flag to hide icon when `screen` is
    disconnected.
    It has no effect unless `screen` option is also configured.
    *(default False)*
  - `horizontal_icon` a character to represent horizontal rotation.
    *(default 'H')*
  - `horizontal_rotation` a horizontal rotation for xrandr to use.
    Available options: 'normal' or 'inverted'.
    *(default 'normal')*
  - `screen` display output name to rotate, as detected by xrandr.
    If not provided, all enabled screens will be rotated.
    *(default None)*
  - `vertical_icon` a character to represent vertical rotation.
    *(default 'V')*
  - `vertical_rotation` a vertical rotation for xrandr to use.
    Available options: 'left' or 'right'.
    *(default 'left')*

Format placeholders:
  - `{icon}` a rotation icon, specified by `horizontal_icon` or `vertical_icon`.
  - `{screen}` a screen name, specified by `screen` option or detected
    automatically if only one screen is connected, otherwise 'ALL'.

Color options:
  - `color_degraded` Screen is disconnected
  - `color_good` Displayed rotation is active

**author** Maxim Baz (https://github.com/maximbaz)

**license** BSD

---

### <a name="xsel"></a>xsel

Display the X selection.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds
    *(default 0.5)*
  - `command` the xsel command to run *(default 'xsel')*
  - `max_size` stip the selection to this value *(default 15)*
  - `symmetric` show the beginning and the end of the selection string
    with respect to configured max_size. *(default True)*

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

Format placeholders:
  - `{status}` daemon status

Color options:
  - `color_bad` Not started
  - `color_degraded` Idle
  - `color_good` Busy

Requires:
  - `yandex-disk` command line tool (link: https://disk.yandex.com/)

**author** Vladimir Potapev (github:vpotapev)

**license** BSD
