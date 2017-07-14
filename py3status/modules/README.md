<a name="top"></a>Modules
========


**[air_quality](#air_quality)** — Display air quality polluting in a given location.

**[arch_updates](#arch_updates)** — Display number of pending updates for Arch Linux.

**[aws_bill](#aws_bill)** — Display bill for Amazon Web Services.

**[backlight](#backlight)** — Adjust screen backlight brightness.

**[battery_level](#battery_level)** — Display battery information.

**[bitcoin_price](#bitcoin_price)** — Display bitcoin using bitcoincharts.com.

**[bluetooth](#bluetooth)** — Display bluetooth status.

**[check_tcp](#check_tcp)** — Display status of a TCP port on a given host.

**[clementine](#clementine)** — Display song currently playing in Clementine.

**[clock](#clock)** — Display date and time.

**[coin_balance](#coin_balance)** — Display balances of diverse crypto-currencies.

**[deadbeef](#deadbeef)** — Display song currently playing in deadbeef.

**[diskdata](#diskdata)** — Display disk information.

**[do_not_disturb](#do_not_disturb)** — Turn on and off dbus notifications.

**[dpms](#dpms)** — Turn on and off DPMS and screen saver blanking.

**[dropboxd_status](#dropboxd_status)** — Display status of Dropbox daemon.

**[exchange_rate](#exchange_rate)** — Display foreign exchange rates.

**[external_script](#external_script)** — Display output of a given script.

**[fedora_updates](#fedora_updates)** — Display number of pending updates for Fedora Linux.

**[file_status](#file_status)** — Display if a file or directory exists.

**[frame](#frame)** — Group modules and treat them as a single one.

**[getjson](#getjson)** — Display a json response from a url.

**[github](#github)** — Display Github notifications and issue/pull requests for a repo.

**[glpi](#glpi)** — Display number of open tickets from GLPI.

**[gpmdp](#gpmdp)** — Display song currently playing in Google Play Music Desktop Player.

**[graphite](#graphite)** — Display Graphite metrics.

**[group](#group)** — Group modules and switch between them.

**[hamster](#hamster)** — Display time tracking activities from Hamster.

**[icinga2](#icinga2)** — Display service status for Icinga2.

**[imap](#imap)** — Display number of unread messages from IMAP account.

**[insync](#insync)** — Display Insync status

**[kdeconnector](#kdeconnector)** — Display information about your smartphone with KDEConnector.

**[keyboard_layout](#keyboard_layout)** — Display keyboard layout.

**[keyboard_locks](#keyboard_locks)** — Monitor CapsLock, NumLock, and ScrLock keys

**[mpd_status](#mpd_status)** — Display song currently playing in mpd.

**[mpris](#mpris)** — Display song/video and control MPRIS compatible players.

**[net_iplist](#net_iplist)** — Display list of network interfaces and IP addresses.

**[net_rate](#net_rate)** — Display network transfer rate.

**[netdata](#netdata)** — Display network speed and bandwidth usage.

**[ns_checker](#ns_checker)** — Display DNS resolution success on a configured domain.

**[nvidia_temp](#nvidia_temp)** — Display NVIDIA GPU temperature.

**[online_status](#online_status)** — Determine if you have an Internet Connection.

**[pingdom](#pingdom)** — Display response times of the configured Pingdom checks.

**[player_control](#player_control)** — Control Audacious or VLC media player.

**[pomodoro](#pomodoro)** — Use Pomodoro technique to get things done easily.

**[process_status](#process_status)** — Display if a process is running.

**[rainbow](#rainbow)** — Add color cycling fun to your i3bar.

**[rate_counter](#rate_counter)** — Display time spent and calculate the price of your service.

**[rss_aggregator](#rss_aggregator)** — Display unread feeds in your favorite RSS aggregator.

**[rt](#rt)** — Display number of ongoing tickets from RT queues.

**[scratchpad_async](#scratchpad_async)** — Display number of windows and urgency hints asynchronously.

**[scratchpad_counter](#scratchpad_counter)** — Display number of windows in scratchpad.

**[screenshot](#screenshot)** — Take screenshots and upload them to a given server.

**[selinux](#selinux)** — Display SELinux state.

**[spaceapi](#spaceapi)** — Display status of a given hackerspace.

**[spotify](#spotify)** — Display song currently playing in Spotify.

**[static_string](#static_string)** — Display static text.

**[sysdata](#sysdata)** — Display system RAM, SWAP and CPU utilization.

**[systemd](#systemd)** — Check systemd unit status.

**[taskwarrior](#taskwarrior)** — Display tasks currently running in taskwarrior.

**[timer](#timer)** — A simple countdown timer.

**[tor_rate](#tor_rate)** — Display the current transfer rates of a tor instance

**[twitch_streaming](#twitch_streaming)** — Display status on a given Twitch streamer.

**[uname](#uname)** — Display system information from uname.

**[uptime](#uptime)** — Display system uptime.

**[vnstat](#vnstat)** — Display vnstat statistics.

**[volume_status](#volume_status)** — Volume control.

**[vpn_status](#vpn_status)** — Drop-in replacement for i3status run_watch VPN module.

**[weather_yahoo](#weather_yahoo)** — Display Yahoo! Weather forecast.

**[whatismyip](#whatismyip)** — Display public IP address and online status.

**[whoami](#whoami)** — Display logged-in username.

**[wifi](#wifi)** — Display WiFi bit rate, quality, signal and SSID using iw.

**[window_title](#window_title)** — Display window title.

**[window_title_async](#window_title_async)** — Display window title asynchronously.

**[wwan_status](#wwan_status)** — Display network and IP address for newer Huwei modems.

**[xrandr](#xrandr)** — Control screen layout.

**[xrandr_rotate](#xrandr_rotate)** — Control screen rotation.

**[xscreensaver](#xscreensaver)** — Control Xscreensaver.

**[xsel](#xsel)** — Display X selection.

**[yandexdisk_status](#yandexdisk_status)** — Display Yandex.Disk status.

---

### <a name="air_quality"></a>air_quality

Display air quality polluting in a given location.

An air quality index (AQI) is a number used by government agencies to communicate
to the public how polluted the air currently is or how polluted it is forecast to
become. As the AQI increases, an increasingly large percentage of the population
is likely to experience increasingly severe adverse health effects. Different
countries have their own air quality indices, corresponding to different national
air quality standards.

Configuration parameters:
  - `auth_token` Required. Personal token. http://aqicn.org *(default 'demo')*
  - `cache_timeout` refresh interval for this module. A message from the site:
    The default quota is max 1000 (one thousand) requests per minute (~16RPS)
    and with burst up to 60 requests. Read more: http://aqicn.org/api/
    *(default 3600)*
  - `format` display format for this module *(default '{location}: {aqi} {category}')*
  - `location` location or uid to query. To search for nearby stations in Kraków,
    use `curl http://api.waqi.info/search/?token=YOUR_TOKEN&keyword=kraków`
    We recommend you to use uid instead of name in location, eg "@8691"
    *(default 'Shanghai')*

Format placeholders:
  - `{aqi}` air quality index
  - `{category}` health risk category
  - `{location}` location or uid

Note: Stations may use {pm25}, {pm10}, {o3}, {so2}, or other parameters.
See http://api.waqi.info/feed/@UID/?token=TOKEN (Replace UID and TOKEN)

Category options:
  - `category_<name>` display name
    eg category_very_unhealthy = 'Level 5: Wear a mask'

Color options:
  - `color_<category>` display color
    eg color_hazardous = '#7E0023'

Example:
```
air_quality {
    auth_token = 'demo'
    location = 'Shanghai'
    format = 'Shanghai: {aqi} {category}'
}
```
    **author** beetleman, lasers

    **license** BSD

---

### <a name="arch_updates"></a>arch_updates

Display number of pending updates for Arch Linux.

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
  - `{total}` Total updates pending

Requires:
  - `cower` Needed to display pending 'aur' updates

**author** Iain Tatch &lt;iain.tatch@gmail.com&gt;

**license** BSD

---

### <a name="aws_bill"></a>aws_bill

Display bill for Amazon Web Services.

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

Adjust screen backlight brightness.

Configuration parameters:
  - `brightness_delta` Change the brightness by this step.
    *(default 8)*
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

Display battery information.

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

Display bitcoin using bitcoincharts.com.

Configuration parameters:
  - `bitcoin_separator` display separator if more than one *(default ', ')*
  - `cache_timeout` refresh interval for this module. A message from
    the site: Don't query more often than once every 15 minutes
    *(default 900)*
  - `color_index` Index of the market responsible for coloration,
    -1 means no coloration, except when only one market is selected
    *(default -1)*
  - `field` Field that is displayed per market,
    see http://bitcoincharts.com/about/markets-api/ *(default 'close')*
  - `format` display format for this module *(default '{format_bitcoin}')*
  - `format_bitcoin` display format for bitcoin *(default '{market}: {price}{symbol}')*
  - `hide_on_error` show error message *(default False)*
  - `markets` list of supported markets. see http://bitcoincharts.com/markets/list/
    *(default 'btceUSD, btcdeEUR')*
  - `symbols` if possible, convert currency abbreviations to symbols
    e.g. USD -&gt; $, EUR -&gt; € and so on *(default True)*

Format placeholders:
  - `{format_bitcoin}` format for bitcoin

format_bitcoin placeholders:
  - `{market}` market names
  - `{price}` current prices
  - `{symbol}` currency symbols

Color options:
  - `color_bad`  Price has dropped or not available
  - `color_good` Price has increased

**author** Andre Doser &lt;doser.andre AT gmail.com&gt;

---

### <a name="bluetooth"></a>bluetooth

Display bluetooth status.

Configuration parameters:
  - `cache_timeout` refresh interval for this module *(default 10)*
  - `device_separator` show separator only if more than one *(default '|')*
  - `format` display format for this module *(default 'BT[: {format_device}]')*
  - `format_device` display format for bluetooth devices *(default '{name}')*

Format placeholders:
  - `{format_device}` format for bluetooth devices

format_device placeholders:
  - `{mac}` bluetooth device address
  - `{name}` bluetooth device name

Color options:
  - `color_bad` No connection
  - `color_good` Active connection

**author** jmdana &lt;https://github.com/jmdana&gt;

**license** GPLv3 &lt;http://www.gnu.org/licenses/gpl-3.0.txt&gt;

---

### <a name="check_tcp"></a>check_tcp

Display status of a TCP port on a given host.

Configuration parameters:
  - `cache_timeout` refresh interval for this module *(default 10)*
  - `format` display format for this module *(default '{host}:{port} {state}')*
  - `host` name of host to check for *(default 'localhost')*
  - `icon_off` show this when unavailable *(default 'DOWN')*
  - `icon_on` show this when available *(default 'UP')*
  - `port` number of port to check for *(default 22)*

Format placeholders:
  - `{state}` port state

Color options:
  - `color_down` Closed, default to color_bad
  - `color_up` Open, default to color_good

**author** obb, Moritz Lüdecke

---

### <a name="clementine"></a>clementine

Display song currently playing in Clementine.

Configuration parameters:
  - `cache_timeout` refresh interval for this module *(default 5)*
  - `format` display format for this module *(default '♫ {current}')*

Format placeholders:
  - `{current}` currently playing

Requires:
  - `clementine` a modern music player and library organizer
  - `qdbus` a communication-interface for qt-based applications
    (may be part of qt5-tools)

**author** Francois LASSERRE &lt;choiz@me.com&gt;

**license** GNU GPL http://www.gnu.org/licenses/gpl.html

---

### <a name="clock"></a>clock

Display date and time.

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
  - `round_to_nearest_block` defines how a block icon is chosen. Examples:
    when set to True,  '13:14' is '🕐', '13:16' is '🕜' and '13:31' is '🕜';
    when set to False, '13:14' is '🕐', '13:16' is '🕐' and '13:31' is '🕜'.
    *(default True)*

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

Display balances of diverse crypto-currencies.

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

Display song currently playing in deadbeef.

Configuration parameters:
  - `cache_timeout` refresh interval for this module *(default 1)*
  - `format` display format for this module *(default '[{artist} - ][{title}]')*

Format placeholders:
  - `{album}` name of the album
  - `{artist}` name of the artist
  - `{length}` length time in [HH:]MM:SS
  - `{playback_time}` elapsed time in [HH:]MM:SS
  - `{title}` title of the track
  - `{tracknumber}` track number in two digits
  - `{year}` year in four digits

    For more placeholders, see title formatting 2.0 in 'deadbeef --help'
    or http://github.com/Alexey-Yakovenko/deadbeef/wiki/Title-formatting-2.0
    Not all of Foobar2000 remapped metadata fields will work with deadbeef and
    a quick reminder about using {placeholders} here instead of %placeholder%.

Color options:
  - `color_paused` Paused, defaults to color_degraded
  - `color_playing` Playing, defaults to color_good
  - `color_stopped` Stopped, defaults to color_bad

Requires:
  - `deadbeef` a GTK+ audio player for GNU/Linux

**author** mrt-prodz, tobes, lasers

---

### <a name="diskdata"></a>diskdata

Display disk information.

Configuration parameters:
  - `cache_timeout` refresh interval for this module. *(default 10)*
  - `disk` show stats for disk or partition, i.e. `sda1`. None for all disks.
    *(default None)*
  - `format` display format for this module.
    *(default "{disk}: {used_percent}% ({total})")*
  - `format_rate` display format for rates value
    *(default "[\?min_length=11 {value:.1f} {unit}]")*
  - `format_space` display format for disk space values
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

Turn on and off dbus notifications.

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

Turn on and off DPMS and screen saver blanking.

This module allows activation and deactivation
of DPMS (Display Power Management Signaling)
by clicking on 'DPMS' in the status bar.

Configuration parameters:
  - `button_off` mouse button to turn off screen *(default None)*
  - `button_toggle` mouse button to toggle DPMS *(default 1)*
  - `cache_timeout` refresh interval for this module *(default 15)*
  - `format` display format for this module *(default '{icon}')*
  - `icon_off` show when DPMS is disabled *(default 'DPMS')*
  - `icon_on` show when DPMS is enabled *(default 'DPMS')*

Format placeholders:
  - `{icon}` DPMS icon

Color options:
  - `color_on` Enabled, defaults to color_good
  - `color_off` Disabled, defaults to color_bad

**author** Andre Doser &lt;dosera AT tf.uni-freiburg.de&gt;

---

### <a name="dropboxd_status"></a>dropboxd_status

Display status of Dropbox daemon.

Configuration parameters:
  - `cache_timeout` refresh interval for this module *(default 10)*
  - `format` display format for this module *(default "Dropbox: {status}")*
  - `status_busy` text for placeholder {status} when Dropbox is busy *(default None)*
  - `status_off` text for placeholder {status} when Dropbox isn't running *(default "isn't running")*
  - `status_on` text for placeholder {status} when Dropbox is up to date *(default "Up to date")*

Value for `status_off` if not set:
  - Dropbox isn't running!
    Value for `status_on` if not set:
  - Up to date
    Values for `status_busy` if not set:
  - Connecting...
  - Starting...
  - Downloading file list...
  - Syncing "filename"

Format placeholders:
  - `{status}` Dropbox status

Color options:
  - `color_bad` Not running
  - `color_degraded` Busy
  - `color_good` Up to date

Requires:
  - `dropbox-cli` command line interface for dropbox

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

**author** tobes

**license** BSD

---

### <a name="external_script"></a>external_script

Display output of a given script.

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

Display number of pending updates for Fedora Linux.

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

Display if a file or directory exists.

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

### <a name="getjson"></a>getjson

Display a json response from a url.

This module gets the given `url` configuration parameter and assumes the response is a
json object. The keys of the json object are used as the format placeholders. The format
placeholders are replaced by the value. Objects that are nested can be accessed by using
the `delimiter` configuration parameter in between.

Examples:
```
# Straightforward key replacement
url = 'http://ip-api.com/json'
format = '{lat}, {lon}'

# Access child objects
url = 'http://api.icndb.com/jokes/random'
format = '{value-joke}'

# Access title from 0th element of articles list
url = 'https://newsapi.org/v1/articles?source=bbc-news&sortBy=top&apiKey={API_KEY}'
format = '{articles-0-title}'

# Access if top-level object is a list
url = 'https://jsonplaceholder.typicode.com/posts/1/comments'
format = '{0-name}'
```

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds
    *(default 30)*
  - `delimiter` the delimiter between parent and child objects
    *(default '-')*
  - `format` placeholders will be replaced by the returned json key names
    *(default None)*
  - `timeout` how long before deciding we're offline
    *(default 5)*
  - `url` specify a url to fetch json from
    *(default None)*

Format placeholders:
    Placeholders will be replaced by the json keys

    Placeholders for objects with sub-objects are flattened using 'delimiter' in between
        (eg. {'parent': {'child': 'value'}} will use placeholder {parent-child}

    Placeholders for list elements have 'delimiter' followed by the index
        (eg. {'parent': ['this', 'that']) will use placeholders {parent-0} for 'this' and
        {parent-1} for 'that'

**author** vicyap

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
    one (otherwise the github home page). Setting to `None` disables.
    *(default 3)*
  - `button_refresh` Button that when clicked refreshes module.
    Setting to `None` disables.
    *(default 2)*
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
  - `{issues}` Number of open issues.
  - `{notifications}` Notifications.  If no notifications this will be empty.
  - `{notifications_count}` Number of notifications.  This is also the __Only__
    placeholder available to `format_notifications`.
  - `{pull_requests}` Number of open pull requests
  - `{repo}` short name of the repository being checked. eg py3status
  - `{repo_full}` full name of the repository being checked. eg ultrabug/py3status

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

Display number of open tickets from GLPI.

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

Display song currently playing in Google Play Music Desktop Player.

Configuration parameters:
  - `cache_timeout`  refresh interval for this module *(default 5)*
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
    The "format" parameter placeholders are dynamically based on the data
    points names returned by the "targets" query to graphite.

    For example if your target is `"carbon.agents.localhost-a.memUsage"`,
    you'd get a JSON result like this:

        ```
        {
            "target": "carbon.agents.localhost-a.memUsage",
            "datapoints": [[19693568.0, 1463663040]]
        }
        ```

    So the placeholder you could use on your "format" config is:
        `format = "{carbon.agents.localhost-a.memUsage}"`

    TIP: use aliases !
        ```
        targets = "alias(carbon.agents.localhost-a.memUsage, 'local_memuse')"
        format = "local carbon mem usage: {local_memuse} bytes"
        ```

Color options:
  - `color_bad` threshold_bad has been exceeded
  - `color_degraded` threshold_degraded has been exceeded

**author** ultrabug

---

### <a name="group"></a>group

Group modules and switch between them.

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

Display time tracking activities from Hamster.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 10)*
  - `format` see placeholders below *(default '{current}')*

Format placeholders:
  - `{current}` current activity

Requires:
  - `hamster`

**author** Aaron Fields (spirotot [at] gmail.com)

**license** BSD

---

### <a name="icinga2"></a>icinga2

Display service status for Icinga2.

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

Display number of unread messages from IMAP account.

Configuration parameters:
  - `allow_urgent` display urgency on unread messages *(default False)*
  - `cache_timeout` refresh interval for this module *(default 60)*
  - `criterion` status of emails to check for *(default 'UNSEEN')*
  - `format` display format for this module *(default 'Mail: {unseen}')*
  - `hide_if_zero` hide this module when no new mail *(default False)*
  - `mailbox` name of the mailbox to check *(default 'INBOX')*
  - `password` login password *(default None)*
  - `port` number to use *(default '993')*
  - `security` login authentication method: 'ssl' or 'starttls'
    (startssl needs python 3.2 or later) *(default 'ssl')*
  - `server` server to connect *(default None)*
  - `user` login user *(default None)*

Format placeholders:
  - `{unseen}` number of unread emails

Color options:
  - `color_new_mail` use color when new mail arrives, default to color_good

**author** obb

---

### <a name="insync"></a>insync

Display Insync status

Thanks to Iain Tatch &lt;iain.tatch@gmail.com&gt; for the script that this is based on.

Configuration parameters:
  - `cache_timeout` refresh interval for this module *(default 10)*
  - `format` display format for this module *(default '{status} {queued}')*
  - `status_offline` show when Insync is offline *(default 'OFFLINE')*
  - `status_paused` show when Insync is paused *(default 'PAUSED')*
  - `status_share` show when Insync is sharing *(default 'SHARE')*
  - `status_syncing` show when Insync is syncing *(default 'SYNCING')*

Format placeholders:
  - `{status}` Insync status
  - `{queued}` Number of files queued

Color options:
  - `color_bad` Offline
  - `color_degraded` Default
  - `color_good` Synced

Requires:
  - `insync` an unofficial Google Drive client with support for various desktops

**author** Joshua Pratt &lt;jp10010101010000@gmail.com&gt;

**license** BSD

---

### <a name="kdeconnector"></a>kdeconnector

Display information about your smartphone with KDEConnector.

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

Display keyboard layout.

Configuration parameters:
  - `cache_timeout` refresh interval for this module *(default 10)*
  - `colors` deprecated. see color options below *(default None)*
  - `format` display format for this module *(default '{layout}')*

Format placeholders:
  - `{layout}` keyboard layout

Color options:
  - `color_<layout>` colorize the layout. eg color_fr = '#729FCF'

Requires:
  - `xkblayout-state`
    or
  - `setxkbmap` and `xset` (works for the first two predefined layouts.)

**author** shadowprince, tuxitop

**license** Eclipse Public License

---

### <a name="keyboard_locks"></a>keyboard_locks

Monitor CapsLock, NumLock, and ScrLock keys

Configuration parameters:
  - `cache_timeout` refresh interval for this module *(default 1)*
  - `format` display format for this module *(default '{caps} {num} {scr}')*
  - `icon_caps_off` show when Capitals Lock is off *(default 'CAPS')*
  - `icon_caps_on` show when Capitals Lock is on *(default 'CAPS')*
  - `icon_num_off` show when Numeric Lock is off *(default 'NUM')*
  - `icon_num_on` show when Numeric Lock is on *(default 'NUM')*
  - `icon_scr_off` show when Scroll Lock is off *(default 'SCR')*
  - `icon_scr_on` show when Scroll Lock is on *(default 'SCR')*

Color options:
  - `color_good` Lock on
  - `color_bad` Lock off

**author** lasers

---

### <a name="mpd_status"></a>mpd_status

Display song currently playing in mpd.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 2)*
  - `format` template string (see below)
    *(default '{state} [[[{artist}] - {title}]|[{file}]]')*
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

Format placeholders:
  - `{state}` state (paused, playing. stopped) can be defined via `state_..`
    configuration parameters
    Refer to the mpc(1) manual page for the list of available placeholders to
    be used in the format.  Placeholders should use braces `{}` rather than
    percent `%%` eg `{artist}`.
    Every placeholder can also be prefixed with
    `next_` to retrieve the data for the song following the one currently
    playing.

Requires:
  - `python-mpd2` (NOT python2-mpd2)
```
# pip install python-mpd2
```

Note: previously formats using %field% where allowed for this module, but
standard placeholders should be used.

Examples of `format`
```
# Show state and (artist -) title, if no title fallback to file:
{state} [[[{artist} - ]{title}]|[{file}]]

# Show state, [duration], title (or file) and next song title (or file):
{state} \[{time}\] [{title}|{file}] → [{next_title}|{next_file}]
```

**author** shadowprince, zopieux

**license** Eclipse Public License

---

### <a name="mpris"></a>mpris

Display song/video and control MPRIS compatible players.

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

**author** Moritz Lüdecke, tobes, valdur55

---

### <a name="net_iplist"></a>net_iplist

Display list of network interfaces and IP addresses.

This module supports both IPv4 and IPv6. There is the possibility to blacklist
interfaces and IPs, as well as to show interfaces with no IP address. It will
show an alternate text if no IP are available.

Configuration parameters:
  - `cache_timeout` refresh interval for this module in seconds.
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

**author** guiniol

---

### <a name="net_rate"></a>net_rate

Display network transfer rate.

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
  - `cache_timeout` refresh interval for this module *(default 2)*
  - `format` display format for this module
    *(default '{nic} [\?color=down LAN(Kb): {down}↓ {up}↑]
    [\?color=total T(Mb): {download}↓ {upload}↑ {total}↕]')*
  - `nic` network interface to use *(default None)*
  - `thresholds` color thresholds to use
    *(default {'down': [(0, 'bad'), (30, 'degraded'), (60, 'good')],
    'total': [(0, 'good'), (400, 'degraded'), (700, 'bad')]})*

Format placeholders:
  - `{nic}`      network interface
  - `{down}`     number of download speed
  - `{up}`       number of upload speed
  - `{download}` number of download usage
  - `{upload}`   number of upload usage
  - `{total}`    number of total usage

Color thresholds:
  - `{down}`     color threshold of download speed
  - `{total}`    color threshold of total usage

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
  - `cache_timeout` refresh interval for this module *(default 10)*
  - `format` display format for this module *(default 'GPU: {format_temp}')*
  - `format_temp` display format for temperatures *(default '{temp}°C')*
  - `temp_separator` temperature separator (if more than one) *(default '|')*

Format placeholders:
  - `{format_temp}` format for temperatures

format_temp placeholders:
  - `{temp}` temperatures

Color options:
  - `color_bad` Unavailable
  - `color_good` Available

Requires:
  - `nvidia-smi` NVIDIA System Management Interface program

**author** jmdana &lt;https://github.com/jmdana&gt;

**license** BSD

---

### <a name="online_status"></a>online_status

Determine if you have an Internet Connection.

Configuration parameters:
  - `cache_timeout` refresh interval for this module *(default 10)*
  - `format` display format for this module *(default '{icon}')*
  - `icon_off` show when connection is offline *(default '■')*
  - `icon_on` show when connection is online *(default '●')*
  - `timeout` time to wait for a response, in seconds *(default 2)*
  - `url` specify URL to connect when checking for a connection
    *(default 'http://www.google.com')*

Format placeholders:
  - `{icon}` connection status

Color options:
  - `color_off` Connection offline, defaults to color_bad
  - `color_on` Connection online, defaults to color_good

**author** obb

---

### <a name="pingdom"></a>pingdom

Display response times of the configured Pingdom checks.

We also verify the status of the checks and colorize if needed.
Pingdom API doc : https://www.pingdom.com/features/api/documentation/

Configuration parameters:
  - `app_key` create an APP KEY on pingdom first *(default '')*
  - `cache_timeout` how often to refresh the check from pingdom *(default 600)*
  - `checks` comma separated pindgom check names to display *(default '')*
  - `format` display format for this module *(default '{pingdom}')*
  - `login` pingdom login *(default '')*
  - `max_latency` maximal latency before coloring the output *(default 500)*
  - `password` pingdom password *(default '')*
  - `request_timeout` pindgom API request timeout *(default 15)*

Format placeholders:
  - `{pingdom}` pingdom response times

Color options:
  - `color_bad` Site is down
  - `color_degraded` Latency exceeded max_latency

Requires:
  - `requests` python module from pypi
    https://pypi.python.org/pypi/requests

---

### <a name="player_control"></a>player_control

Control Audacious or VLC media player.

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

Use Pomodoro technique to get things done easily.

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
    or pygame) *(default None)*
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
  - `cache_timeout` refresh interval for this module *(default 10)*
  - `format` default format for this module *(default '{icon}')*
  - `full` if True, match against full command line *(default False)*
  - `icon_off` show when process not running *(default '■')*
  - `icon_on` show when process running *(default '●')*
  - `process` process name to check for *(default None)*

Format placeholders:
  - `{icon}` process icon
  - `{process}` process name

Color options:
  - `color_bad` Not running
  - `color_good` Running

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
  - `format` display format for this module *(default '{output}')*
  - `gradient` The colors we will cycle through, This is a list of hex values
    *(default [ '#FF0000', '#FFFF00', '#00FF00', '#00FFFF',
    '#0000FF', '#FF00FF', '#FF0000', ])*
  - `multi_color` If True then each module the rainbow contains will be colored
    differently *(default True)*
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

Display time spent and calculate the price of your service.

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

Display unread feeds in your favorite RSS aggregator.

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

Display number of ongoing tickets from RT queues.

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

Display number of windows and urgency hints asynchronously.

Configuration parameters:
  - `always_show` always display the format *(default False)*
  - `format` display format for this module *(default "{counter} ⌫")*

Format placeholders:
  - `{counter}` number of scratchpad windows

Requires:
  - `i3ipc` (https://github.com/acrisci/i3ipc-python)

**author** cornerman

**license** BSD

---

### <a name="scratchpad_counter"></a>scratchpad_counter

Display number of windows in scratchpad.

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

Take screenshots and upload them to a given server.

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

Display SELinux state.

This module displays the state of SELinux on your machine:
    Enforcing (good), Permissive (bad), or Disabled (bad).

Configuration parameters:
  - `cache_timeout` refresh interval for this module *(default 10)*
  - `format` display format for this module *(default 'selinux: {state}')*
  - `state_disabled` show when no SELinux policy is loaded.
    *(default 'disabled')*
  - `state_enforcing` show when SELinux security policy is enforced.
    *(default 'enforcing')*
  - `state_permissive` show when SELinux prints warnings instead of enforcing.
    *(default 'permissive')*

Format placeholders:
  - `{state}` SELinux state

Color options:
  - `color_bad` Enforcing
  - `color_degraded` Permissive
  - `color_good` Disabled

Requires:
  - `libselinux-python` SELinux python bindings for libselinux

**author** bstinsonmhk

**license** BSD

---

### <a name="spaceapi"></a>spaceapi

Display status of a given hackerspace.

Configuration parameters:
  - `button_url` mouse button to open URL sent in space's API *(default 3)*
  - `cache_timeout` refresh interval for this module *(default 60)*
  - `format` display format for this module *(default '{state}[ {lastchanged}]')*
  - `format_lastchanged` display format for time *(default 'since %H:%M')*
  - `state_closed` show when hackerspace is closed *(default 'closed')*
  - `state_open` show when hackerspace is open *(default 'open')*
  - `url` specify JSON URL of a hackerspace to retrieve from
    *(default 'http://status.chaospott.de/status.json')*

Format placeholders:
  - `{state}` Hackerspace state
  - `{lastchanged}` Time

format_lastchanged conversion:
    '%' Strftime characters to be translated

Color options:
  - `color_closed` Space closed, defaults to color_bad
  - `color_open` Space open, defaults to color_good

**author** timmszigat

**license** WTFPL &lt;http://www.wtfpl.net/txt/copying/&gt;

---

### <a name="spotify"></a>spotify

Display song currently playing in Spotify.

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

Display system RAM, SWAP and CPU utilization.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 10)*
  - `format` output format string
    *(default '[\?color=cpu CPU: {cpu_usage}%], '
    '[\?color=mem Mem: {mem_used}/{mem_total} GB ({mem_used_percent}%)]')*
  - `mem_unit` the unit of memory to use in report, case insensitive.
    ['dynamic', 'KiB', 'MiB', 'GiB'] *(default 'GiB')*
  - `swap_unit` the unit of swap to use in report, case insensitive.
    ['dynamic', 'KiB', 'MiB', 'GiB'] *(default 'GiB')*
  - `temp_unit` unit used for measuring the temperature ('C', 'F' or 'K')
    *(default '°C')*
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
  - `{swap_total}` total swap
  - `{swap_unit}` unit for swap
  - `{swap_used}` used swap
  - `{swap_used_percent}` used swap percentage
  - `{temp_unit}` temperature unit

Color thresholds:
  - `cpu` change color based on the value of cpu_usage
  - `max_cpu_mem` change the color based on the max value of cpu_usage and mem_used_percent
  - `mem` change color based on the value of mem_used_percent
  - `swap` change color based on the value of swap_used_percent
  - `temp` change color based on the value of cpu_temp

NOTE: If using the `{cpu_temp}` option, the `sensors` command should
be available, provided by the `lm-sensors` or `lm_sensors` package.

**author** Shahin Azad &lt;ishahinism at Gmail&gt;, shrimpza, guiniol

---

### <a name="systemd"></a>systemd

Check systemd unit status.

Check the status of a systemd unit.

Configuration parameters:
  - `cache_timeout` How often we refresh this module in seconds *(default 5)*
  - `format` Format for module output *(default "{unit}: {status}")*
  - `unit` Name of the unit *(default "dbus.service")*

Format of status string placeholders:
  - `{unit}` name of the unit
  - `{status}` 'active', 'inactive' or 'not-found'

Color options:
  - `color_good` Unit active
  - `color_bad` Unit inactive
  - `color_degraded` Unit not found

Example:

```
# Check status of vpn service
# Start with left click
# Stop with right click
systemd vpn {
    unit = 'vpn.service'
    on_click 1 = "exec sudo systemctl start vpn"
    on_click 3 = "exec sudo systemctl stop vpn"
    format = '{unit} is {status}'
}
```

Requires:
  - `pydbus` python lib for dbus

**author** Adrian Lopez &lt;adrianlzt@gmail.com&gt;

**license** BSD

---

### <a name="taskwarrior"></a>taskwarrior

Display tasks currently running in taskwarrior.

Configuration parameters:
  - `cache_timeout` refresh interval for this module *(default 5)*
  - `format` display format for this module *(default '{task}')*

Format placeholders:
  - `{task}` active tasks

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
  - `format` display format for this module *(default 'Timer {timer}')*
  - `sound` play sound file path when the timer ends *(default None)*
  - `time` number of seconds to start countdown with *(default 60)*

Format placeholders:
  - `{timer}` display hours:minutes:seconds

**author** tobes

---

### <a name="tor_rate"></a>tor_rate

Display the current transfer rates of a tor instance

Configuration parameters:
  - `cache_timeout` An integer specifying the cache life-time of the modules
    output in seconds *(default 2)*
  - `control_address` The address on which the Tor daemon listens for control
    connections *(default "127.0.0.1")*
  - `control_password` The password to use for the Tor control connection
    *(default None)*
  - `control_port` The port on which the Tor daemon listens for control
    connections *(default 9051)*
  - `format` A string describing the output format for the module
    *(default "↑ {up} ↓ {down}")*
  - `format_value` A string describing how to format the transfer rates
    *(default "[\?min_length=12 {rate:.1f} {unit}]")*
  - `rate_unit` The unit to use for the transfer rates
    *(default "B/s")*
  - `si_units` A boolean value selecting whether or not to use SI units
    *(default False)*

Format placeholders:
  - `{down}` The incoming transfer rate
  - `{up}` The outgoing transfer rate

format_value placeholders:
  - `{rate}` The current transfer-rate's value
  - `{unit}` The current transfer-rate's unit

Requires:
  - `stem` python module from pypi https://pypi.python.org/pypi/stem

Example:

```
tor_rate {
    cache_timeout = 10
    format = "IN: {down} | OUT: {up}"
    control_port = 1337
    control_password = "TertiaryAdjunctOfUnimatrix01"
    si_units = True
}

order += "tor_rate"
```

**author** Felix Morgner &lt;felix.morgner@gmail.com&gt;

**license** 3-clause-BSD

---

### <a name="twitch_streaming"></a>twitch_streaming

Display status on a given Twitch streamer.

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

Display system information from uname.

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

### <a name="uptime"></a>uptime

Display system uptime.

Configuration parameters:
  - `format` display format for this module
    *(default 'up {days} days {hours} hours {minutes} minutes')*

Format placeholders:
  - `{decades}` decades
  - `{years}`   years
  - `{weeks}`   weeks
  - `{days}`    days
  - `{hours}`   hours
  - `{minutes}` minutes
  - `{seconds}` seconds

Note: If you don't use one of the placeholders, the value will be carried over
    to the next unit. For example, given an uptime of 1h 30min:
    If you use {minutes} as your only placeholder, then its value will be 90.
    If you use {hours} and {minutes}, then its values will be 1 and 30, respectively.

Examples:
```
# show uptime without zeroes
uptime {
    format = 'up [\?if=weeks {weeks} weeks ][\?if=days {days} days ]
        [\?if=hours {hours} hours ][\?if=minutes {minutes} minutes ]'
}

# show uptime in multiple formats using group module
group uptime {
    format = "up {output}"
    uptime {
        format = '[\?if=weeks {weeks} weeks ][\?if=days {days} days ]
            [\?if=hours {hours} hours ][\?if=minutes {minutes} minutes]'
    }
    uptime {
        format = '[\?if=weeks {weeks}w ][\?if=days {days}d ]
            [\?if=hours {hours}h ][\?if=minutes {minutes}m]'
    }
    uptime {
        format = '[\?if=days {days}, ][\?if=hours {hours}:]
            [\?if=minutes {minutes:02d}]'
    }
}
```

**author** Alexis "Horgix" Chotard &lt;alexis.horgix.chotard@gmail.com&gt;, tobes, lasers

**license** BSD

---

### <a name="vnstat"></a>vnstat

Display vnstat statistics.

Configuration parameters:
  - `cache_timeout` refresh interval for this module *(default 180)*
  - `coloring` see coloring rules below *(default {})*
  - `format` display format for this module *(default '{total}')*
  - `initial_multi` set to 1 to disable first bytes
    *(default 1024)*
  - `left_align` *(default 0)*
  - `multiplier_top` if value is greater, divide it with unit_multi and get
    next unit from units *(default 1024)*
  - `precision` *(default 1)*
  - `statistics_type` d for daily, m for monthly *(default 'd')*
  - `unit_multi` value to divide if rate is greater than multiplier_top
    *(default 1024)*

Coloring rules:
    If value is more than dict key, the string will change color based on the
    specified values in the coloring section.

Example:
    coloring = {
    800: "#dddd00",     # over 800: yellow
    900: "#dd0000",     # over 900: red
    }

Format placeholders:
  - `{down}` download
  - `{total}` total
  - `{up}` upload

Requires:
  - `vnstat` a console-based network traffic monitor

**author** shadowprince

**license** Eclipse Public License

---

### <a name="volume_status"></a>volume_status

Volume control.

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

Display Yahoo! Weather forecast.

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

Display public IP address and online status.

Configuration parameters:
  - `cache_timeout` how often we refresh this module in seconds *(default 30)*
  - `expected` define expected values for format placeholders,
    and use `color_degraded` to show the output of this module
    if any of them does not match the actual value.
    This should be a dict eg {'country': 'France'}
    *(default None)*
  - `format` available placeholders are {ip} and {country},
    as well as any other key in JSON fetched from `url_geo`
    *(default '{ip}')*
  - `hide_when_offline` hide the module output when offline *(default False)*
  - `icon_off` what to display when offline *(default '■')*
  - `icon_on` what to display when online *(default '●')*
  - `mode` default mode to display is 'ip' or 'status' (click to toggle)
    *(default 'ip')*
  - `negative_cache_timeout` how often to check again when offline *(default 2)*
  - `timeout` how long before deciding we're offline *(default 5)*
  - `url_geo` IP to check for geo location (must output json)
    *(default 'https://freegeoip.net/json/')*

Format placeholders:
  - `{icon}` display the icon
  - `{country}` display the country
  - `{ip}` display current ip address
    any other key in JSON fetched from `url_geo`

Color options:
  - `color_bad` Offline
  - `color_degraded` Output is unexpected (IP/country mismatch, etc.)
  - `color_good` Online

**author** ultrabug

---

### <a name="whoami"></a>whoami

Display logged-in username.

Configuration parameters:
  - `format` display format for whoami *(default '{username}')*

Format placeholders:
  - `{username}` display current username

Inspired by i3 FAQ:
    https://faq.i3wm.org/question/1618/add-user-name-to-status-bar.1.html

**author** ultrabug

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
  - `use_sudo` Use sudo to run iw, make sure iw requires some root rights
    without a password by adding a sudoers entry.
    Example: "&lt;username&gt; ALL=(ALL) NOPASSWD: /usr/bin/iw dev wl* link"
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
  - `iw` cli configuration utility for wireless devices
  - `ip` only for {ip}. may be part of iproute2: ip routing utilities

__Note: Some distributions eg Debian require `iw` to be run with privileges.
In this case you will need to use the `use_sudo` configuration parameter.__

**author** Markus Weimar &lt;mail@markusweimar.de&gt;

**license** BSD

---

### <a name="window_title"></a>window_title

Display window title.

Prints the name of focused window at frequent intervals.

Configuration parameters:
  - `cache_timeout` refresh interval for this module *(default 0.5)*
  - `format` display format for this module *(default '{title}')*
  - `max_width` If width of title is greater, shrink it and add '...'
    *(default 120)*

**author** shadowprince

**license** Eclipse Public License

---

### <a name="window_title_async"></a>window_title_async

Display window title asynchronously.

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

Display network and IP address for newer Huwei modems.

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

Control screen layout.

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
  - `hide_if_single_combination` hide if only one combination is available
    *(default False)*
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

Control screen rotation.

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

### <a name="xscreensaver"></a>xscreensaver

Control Xscreensaver.

This script is useful for people who let Xscreensaver manage DPMS settings.
Xscreensaver has its own DPMS variables separate from xset. DPMS can be
safely turned off in xset as long as Xscreensaver is running.
Settings can be managed using "xscreensaver-demo".

Configuration parameters:
  - `button_activate` mouse button to activate Xscreensaver *(default 3)*
  - `button_toggle` mouse button to toggle Xscreensaver *(default 1)*
  - `cache_timeout` refresh interval for this module *(default 15)*
  - `format` display format for this module *(default '{icon}')*
  - `icon_off` show when Xscreensaver is not running *(default 'XSCR')*
  - `icon_on` show when Xscreensaver is running *(default 'XSCR')*

 Format placeholders:
    {icon} Xscreensaver icon

**author** neutronst4r &lt;c7420{at}posteo{dot}net&gt;, lasers

---

### <a name="xsel"></a>xsel

Display X selection.

Configuration parameters:
  - `cache_timeout` refresh interval for this module *(default 0.5)*
  - `command` the clipboard command to run *(default 'xsel -o')*
  - `format` display format for this module *(default '{selection}')*
  - `max_size` strip the selection to this value *(default 15)*
  - `symmetric` show beginning and end of the selection string
    with respect to configured max_size. *(default True)*

Format placeholders:
  - `{selection}` output from clipboard command

Requires:
  - `xsel` a command-line program to retrieve/set the X selection

**author** Sublim3 umbsublime@gamil.com

**license** BSD

---

### <a name="yandexdisk_status"></a>yandexdisk_status

Display Yandex.Disk status.

Configuration parameters:
  - `cache_timeout` refresh interval for this module *(default 10)*
  - `format` display format for this module *(default 'Yandex.Disk: {status}')*
  - `status_busy` show when Yandex.Disk is busy *(default None)*
  - `status_off` show when Yandex.Disk isn't running *(default 'Not started')*
  - `status_on` show when Yandex.Disk is idling *(default 'Idle')*

Format placeholders:
  - `{status}` Yandex.Disk status

Color options:
  - `color_bad` Not started
  - `color_degraded` Idle
  - `color_good` Busy

Requires:
  - `yandex-disk` command line interface for Yandex.Disk

**author** Vladimir Potapev (github:vpotapev)

**license** BSD
