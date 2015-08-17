```
Available modules:
  aws_bill               Display the current AWS bill.
                         
                         ##### WARNING #####
                         This module generate some costs on the AWS bill.
                         Take care about the cache_timeout to limit these fees !
                         ##### WARNING #####
                         
                         Configuration parameters:
                             - aws_access_key_id: Your AWS access key
                             - aws_account_id: the root ID of the AWS account.
                               Can be found here: https://console.aws.amazon.com/billing/home#/account
                             - aws_secret_access_key: Your AWS secret key
                             - billing_file: csv file location
                             - cache_timeout: how often we refresh this module in seconds
                             - s3_bucket_name: the bucket where billing files are sent by AWS.
                               Follow this article to activate this feature:
                               http://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/detailed-billing-reports.html
                         
                         Format of status string placeholders:
                             {bill_amount} - AWS bill amount
                         
                         Requires:
                             - boto
                         
                         @author nawadanp
                         ---
  battery_level          Display the battery level.
                         
                         Configuration parameters:
                             - color_* : None means - get it from i3status config
                             - format : text with "text" mode. percentage with % replaces {}
                             - hide_when_full : hide any information when battery is fully charged
                             - mode : for primitive-one-char bar, or "text" for text percentage ouput
                         
                         Requires:
                             - the 'acpi' command line
                         
                         @author shadowprince, AdamBSteele
                         @license Eclipse Public License
                         ---
  bitcoin_price          Display bitcoin prices using bitcoincharts.com.
                         
                         Configuration parameters:
                             - cache_timeout: Should be at least 15 min according to bitcoincharts.
                             - color_index  : Index of the market responsible for coloration,
                                              meaning that the output is going to be green if the
                                              price went up and red if it went down.
                                              default: -1 means no coloration,
                                              except when only one market is selected
                             - field        : Field that is displayed per market,
                                              see http://bitcoincharts.com/about/markets-api/
                             - hide_on_error: Display empty response if True, else an error message
                             - markets      : Comma-separated list of markets. Supported markets can
                                              be found at http://bitcoincharts.com/markets/list/
                             - symbols      : Try to match currency abbreviations to symbols,
                                              e.g. USD -> $, EUR -> € and so on
                         
                         @author Andre Doser <doser.andre AT gmail.com>
                         ---
  bluetooth              Display bluetooth status.
                         
                         Confiuration parameters:
                             - format : format when there is a connected device
                             - format_no_conn : format when there is no connected device
                             - format_no_conn_prefix : prefix when there is no connected device
                             - format_prefix : prefix when there is a connected device
                         
                         Format of status string placeholders
                             {name} : device name
                             {mac} : device MAC address
                         
                         Requires:
                             - hcitool
                         
                         @author jmdana <https://github.com/jmdana>
                         @license GPLv3 <http://www.gnu.org/licenses/gpl-3.0.txt>
                         ---
  clementine             Display the current "artist - title" playing in Clementine.
                         
                         @author Francois LASSERRE <choiz@me.com>
                         @license GNU GPL http://www.gnu.org/licenses/gpl.html
                         ---
  dpms                   Activate or deactivate DPMS and screen blanking.
                         
                         This module allows activation and deactivation
                         of DPMS (Display Power Management Signaling)
                         by clicking on 'DPMS' in the status bar.
                         
                         Configuration parameters:
                             - format_off: string to display when DPMS is disabled
                             - format_on: string to display when DPMS is enabled
                         
                         @author Andre Doser <dosera AT tf.uni-freiburg.de>
                         ---
  dropboxd_status        Display dropboxd status.
                         
                         Configuration parameters:
                             - cache_timeout : how often we refresh this module in seconds (10s default)
                             - format: prefix text for the dropbox status
                         
                         Valid status values include:
                             - Dropbox isn't running!
                             - Starting...
                             - Downloading file list...
                             - Syncing "filename"
                             - Up to date
                         
                         Requires:
                             - the 'dropbox-cli' command
                         
                         @author Tjaart van der Walt (github:tjaartvdwalt)
                         @license BSD
                         ---
  external_script        Display output of given script.
                         
                         Display output of any executable script set by 'script_path'.
                         Pay attention. The output must be one liner, or will break your i3status !
                         The script should not have any parameters, but it could work.
                         
                         Configuration parameters:
                             - cache_timeout : how often we refresh this module in seconds
                             - color         : color of printed text
                             - format        : see placeholders below
                             - script_path   : script you want to show output of (compulsory)
                         
                         Format of status string placeholders:
                             {output} - output of script given by "script_path"
                         
                         i3status.conf example:
                         
                         external_script {
                             color = "#00FF00"
                             format = "my name is {output}"
                             script_path = "/usr/bin/whoami"
                         
                         @author frimdo ztracenastopa@centrum.cz
                         ---
  glpi                   Display the total number of open tickets from GLPI.
                         
                         Configuration parameters:
                             - critical : set bad color above this threshold
                             - db : database to use
                             - host : database host to connect to
                             - password : login password
                             - user : login user
                             - warning : set degraded color above this threshold
                         
                         It features thresholds to colorize the output and forces a low timeout to
                         limit the impact of a server connectivity problem on your i3bar freshness.
                         ---
  imap                   Display the unread messages count from your IMAP account.
                         
                         Configuration parameters:
                             - cache_timeout : how often to run this check
                             - criterion : status of emails to check for
                             - format : format to display
                             - hide_if_zero : don't show on bar if 0
                             - imap_server : IMAP server to connect to
                             - mailbox : name of the mailbox to check
                             - new_mail_color : what color to output on new mail
                             - password : login password
                             - port : IMAP server port
                             - user : login user
                         
                         Format of status string placeholders:
                             {unseen} - number of unread emails
                         
                         @author obb
                         ---
  keyboard_layout        Display the current keyboard layout.
                         
                         Configuration parameters:
                             - cache_timeout: check for keyboard layout change every seconds
                         
                         Requires:
                             - xkblayout-state
                             or
                             - setxkbmap
                         
                         @author shadowprince
                         @license Eclipse Public License
                         ---
  mpd_status             Display information from mpd.
                         
                         Configuration parameters:
                             cache_timeout = how often we refresh this module in seconds (2s default)
                             color = enable coloring output (default False)
                             color_pause = custom pause color (default i3status color degraded)
                             color_play = custom play color (default i3status color good)
                             color_stop = custom stop color (default i3status color bad)
                             format = template string (see below)
                             hide_when_paused: hide the status if state is paused
                             hide_when_stopped: hide the status if state is stopped
                             host: mpd host
                             max_width: maximum status length
                             password: mpd password
                             port: mpd port
                             state_pause: label to display for "paused" state
                             state_play: label to display for "playing" state
                             state_stop: label to display for "stopped" state
                         
                         Requires:
                             - python-mpd2 (NOT python2-mpd2)
                             # pip install python-mpd2
                         
                         Refer to the mpc(1) manual page for the list of available placeholders to be
                         used in `format`.
                         You can also use the %state% placeholder, that will be replaced with the state
                         label (play, pause or stop).
                         Every placeholder can also be prefixed with `next_` to retrieve the data for
                         the song following the one currently playing.
                         
                         You can also use {} instead of %% for placeholders (backward compatibility).
                         
                         Examples of `format`:
                             Show state and (artist -) title, if no title fallback to file:
                             %state% [[[%artist% - ]%title%]|[%file%]]
                         
                             Alternative legacy syntax:
                             {state} [[[{artist} - ]{title}]|[{file}]]
                         
                             Show state, [duration], title (or file) and next song title (or file):
                             %state% \[%time%\] [%title%|%file%] → [%next_title%|%next_file%]
                         
                         @author shadowprince
                         @author zopieux
                         @license Eclipse Public License
                         ---
  net_rate               Display the current network transfer rate.
                         
                         Confiuration parameters:
                             - all_interfaces : ignore self.interfaces, but not self.interfaces_blacklist
                             - devfile : location of dev file under /proc
                             - format_no_connection : when there is no data transmitted from the start of the plugin
                             - hide_if_zero : hide indicator if rate == 0
                             - interfaces : comma separated list of interfaces to track
                             - interfaces_blacklist : comma separated list of interfaces to ignore
                             - precision : amount of numbers after dot
                         
                         Format of status string placeholders:
                             {down} - download rate
                             {interface} - name of interface
                             {total} - total rate
                             {up} - upload rate
                         
                         @author shadowprince
                         @license Eclipse Public License
                         ---
  netdata                Display network speed and bandwidth usage.
                         
                         Configuration parameters:
                             - cache_timeout : how often we refresh this module in seconds (2s default)
                             - low_* / med_* : coloration thresholds
                             - nic : the network interface to monitor (defaults to eth0)
                         
                         @author Shahin Azad <ishahinism at Gmail>
                         ---
  ns_checker             Display DNS resolution success on a configured domain.
                         
                         This module launch a simple query on each nameservers for the specified domain.
                         Nameservers are dynamically retrieved. The FQDN is the only one mandatory parameter.
                         It's also possible to add additional nameservers by appending them in nameservers list.
                         
                         The default resolver can be overwritten with my_resolver.nameservers parameter.
                         
                         Configuration parameters:
                             - domain : domain name to check
                             - lifetime : resolver lifetime
                             - nameservers : comma separated list of reference DNS nameservers
                             - resolvers : comma separated list of DNS resolvers to use
                         
                         @author nawadanp
                         ---
  nvidia_temp            Display NVIDIA GPU temperature.
                         
                         Configuration parameters:
                             - cache_timeout: how often we refresh this module in seconds
                             - color_bad: the color used if the temperature can't be read.
                             - color_good: the color used if everything is OK.
                             - format_prefix: a prefix for the output.
                             - format_units: the temperature units. Will appear at the end.
                             - separator: the separator char between temperatures (only if more than one GPU)
                         
                         Requires:
                             - nvidia-smi
                         
                         @author jmdana <https://github.com/jmdana>
                         @license BSD
                         ---
  online_status          Display if a connection to the internet is established.
                         
                         Configuration parameters:
                             - cache_timeout : how often to run the check
                             - format_offline : what to display when offline
                             - format_online : what to display when online
                             - timeout : how long before deciding we're offline
                             - url : connect to this url to check the connection status
                         
                         @author obb
                         ---
  pingdom                Display the latest response time of the configured Pingdom checks.
                         
                         We also verify the status of the checks and colorize if needed.
                         Pingdom API doc : https://www.pingdom.com/features/api/documentation/
                         
                         Configuration parameters:
                                 - app_key : create an APP KEY on pingdom first
                                 - cache_timeout : how often to refresh the check from pingdom
                                 - checks : comma separated pindgom check names to display
                                 - login : pingdom login
                                 - max_latency : maximal latency before coloring the output
                                 - password : pingdom password
                                 - request_timeout : pindgom API request timeout
                         
                         Requires:
                             - requests python module from pypi
                               https://pypi.python.org/pypi/requests
                         ---
  player_control         Control music/video players.
                         
                         Provides an icon to control simple functions of audio/video players:
                          - start (left click)
                          - stop  (left click)
                          - pause (middle click)
                         
                         Configuration parameters:
                             - debug: enable verbose logging (bool) (default: False)
                             - supported_players: supported players (str) (comma separated list)
                             - volume_tick: percentage volume change on mouse wheel (int) (positive number or None to disable it)
                         
                         @author Federico Ceratto <federico.ceratto@gmail.com>, rixx
                         @license BSD
                         ---
  pomodoro               Display and control a Pomodoro countdown.
                         
                         Configuration parameters:
                             - display_bar: display time in bars when True, otherwise in seconds
                             - max_breaks: maximum number of breaks
                             - num_progress_bars: number of progress bars
                             - sound_break_end: break end sound (file path)
                             - sound_pomodoro_end: pomodoro end sound (file path)
                             - sound_pomodoro_start: pomodoro start sound (file path)
                             - timer_break: normal break time (seconds) (requires pygame)
                             - timer_long_break: long break time (seconds) (requires pygame)
                             - timer_pomodoro: pomodoro time (seconds) (requires pygame)
                         
                         @author Fandekasp (Adrien Lemaire), rixx, FedericoCeratto
                         ---
  rate_counter           Display days/hours/minutes spent and calculate the price of your service.
                         
                         Configuration parameters:
                             - config_file: file path to store the time already spent
                                            and restore it the next session
                             - hour_price : your price per hour
                             - tax  : tax value (1.02 = 2%)
                         
                         @author Amaury Brisou <py3status AT puzzledge.org>
                         ---
  scratchpad_counter     Display the amount of windows in your i3 scratchpad.
                         
                         @author shadowprince
                         @license Eclipse Public License
                         ---
  screenshot             Take a screenshot and optionally upload it to your online server.
                         
                         Display a 'SHOT' button in your i3bar allowing you to take a screenshot and
                         directly send (if wanted) the file to your online server.
                         When the screenshot has been taken, 'SHOT' is replaced by the file_name.
                         
                         This modules uses the 'gnome-screenshot' program to take the screenshot.
                         
                         Configuration parameters:
                             - file_length: generated file_name length
                             - push: True/False if yo want to push your screenshot to your server
                             - save_path: Directory where to store your screenshots.
                             - upload_path: the remote path where to push the screenshot
                             - upload_server: your server address
                             - upload_user: your ssh user
                         
                         @author Amaury Brisou <py3status AT puzzledge.org>
                         ---
  spaceapi               Display if your favorite hackerspace is open or not.
                         
                         Configuration Parameters:
                             - cache_timeout: Set timeout between calls in seconds
                             - closed_color: color if space is closed
                             - closed_text: text if space is closed, strftime parameters will be translated
                             - open_color: color if space is open
                             - open_text: text if space is open, strftime parmeters will be translated
                             - url: URL to SpaceAPI json file of your space
                         
                         @author timmszigat
                         @license WTFPL <http://www.wtfpl.net/txt/copying/>
                         ---
  spotify                Display information about the current song playing on Spotify.
                         
                         Configuration parameters:
                             - cache_timeout : how often to update the bar
                             - format : see placeholders below
                         
                         Format of status string placeholders:
                             {album} - album name
                             {artist} - artiste name (first one)
                             {time} - time duration of the song
                             {title} - name of the song
                         
                         i3status.conf example:
                         
                         spotify {
                             format = "{title} by {artist} -> {time}"
                         }
                         
                         @author Pierre Guilbert <pierre@1000mercis.com>
                         ---
  static_string          Display static text.
                         
                         Configuration parameters:
                             - color         : color of printed text
                             - format        : text that should be printed
                             - separator     : whether the separator is shown or not (true or false)
                         
                         @author frimdo ztracenastopa@centrum.cz
                         ---
  sysdata                Display system RAM and CPU utilization.
                         
                         Configuration parameters:
                             - format: output format string
                             - high_threshold: percent to consider CPU or RAM usage as 'high load'
                             - med_threshold: percent to consider CPU or RAM usage as 'medium load'
                         
                         Format of status string placeholders:
                             {cpu_temp}         - cpu temperature
                             {cpu_usage}        - cpu usage percentage
                             {mem_total}        - total memory
                             {mem_used}         - used memory
                             {mem_used_percent} - used memory percentage
                         
                         NOTE: If using the {cpu_temp} option, the 'sensors' command should 
                         be available, provided by the 'lm-sensors' or 'lm_sensors' package.
                         
                         @author Shahin Azad <ishahinism at Gmail>, shrimpza
                         ---
  taskwarrior            Display currently active (started) taskwarrior tasks.
                         
                         Configuration parameters:
                             - cache_timeout : how often we refresh this module in seconds (5s default)
                         
                         Requires
                             - task
                         
                         @author James Smith http://jazmit.github.io/
                         @license BSD
                         ---
  vnstat                 Display vnstat statistics.
                         
                         Coloring rules.
                         
                         If value is bigger that dict key, status string will turn to color, specified in the value.
                         Example:
                         coloring = {
                             800: "#dddd00",
                             900: "#dd0000",
                         }
                         (0 - 800: white, 800-900: yellow, >900 - red)
                         
                         Format of status string placeholders:
                             {down} - download
                             {total} - total
                             {up} - upload
                         
                         Requires:
                             - external program called "vnstat" installed and configured to work.
                         
                         @author shadowprince
                         @license Eclipse Public License
                         ---
  volume_status          Display current sound volume using amixer.
                         
                         Expands on the standard i3status volume module by adding color
                         and percentage threshold settings.
                         
                         Configuration parameters:
                             - cache_timeout : how often we refresh this module in seconds (10s default)
                             - channel : "Master" by default, alsamixer channel to track
                             - device : "default" by default, alsamixer device to use
                             - format : format the output, available variables: {percentage}
                             - format_muted : format the output when the volume is muted
                             - threshold_bad : 20 by default
                             - threshold_degraded : 50 by default
                         
                         Requires:
                             alsa-utils (tested with alsa-utils 1.0.29-1)
                         
                         NOTE:
                             If you want to refresh the module quicker than the i3status interval,
                             send a USR1 signal to py3status in the keybinding.
                             Example: killall -s USR1 py3status
                         
                         @author <Jan T> <jans.tuomi@gmail.com>
                         @license BSD
                         ---
  weather_yahoo          Display Yahoo! Weather forecast as icons.
                         
                         Based on Yahoo! Weather. forecast, thanks guys !
                             http://developer.yahoo.com/weather/
                         
                         Find your city code using:
                             http://answers.yahoo.com/question/index?qid=20091216132708AAf7o0g
                         
                         Configuration parameters:
                             - cache_timeout : how often to check for new forecasts
                             - city_code : city code to use
                             - forecast_days : how many forecast days you want shown
                             - request_timeout : check timeout
                         
                         The city_code in this example is for Paris, France => FRXX0076
                         ---
  whatismyip             Display your public/external IP address and toggle to online status on click.
                         
                         Configuration parameters:
                             - cache_timeout : how often we refresh this module in seconds (default 30s)
                             - format: the only placeholder available is {ip} (default '{ip}')
                             - format_offline : what to display when offline
                             - format_online : what to display when online
                             - hide_when_offline: hide the module output when offline (default False)
                             - mode: default mode to display is 'ip' or 'status' (click to toggle)
                             - negative_cache_timeout: how often to check again when offline
                             - timeout : how long before deciding we're offline
                         
                         @author ultrabug
                         ---
  whoami                 Display the currently logged in user.
                         
                         Inspired by i3 FAQ:
                             https://faq.i3wm.org/question/1618/add-user-name-to-status-bar/
                         ---
  window_title           Display the current window title.
                         
                         Requires:
                             - i3-py (https://github.com/ziberna/i3-py)
                             # pip install i3-py
                         
                         If payload from server contains wierd utf-8
                         (for example one window have something bad in title) - the plugin will
                         give empty output UNTIL this window is closed.
                         I can't fix or workaround that in PLUGIN, problem is in i3-py library.
                         
                         @author shadowprince
                         @license Eclipse Public License
                         ---
  xrandr                 Control your screen(s) layout easily.
                         
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
                         
                         Configuration parameters:
                             - cache_timeout: how often to (re)detect the outputs
                             - fallback: when the current output layout is not available anymore,
                                 fallback to this layout if available. This is very handy if you
                                 have a laptop and switched to an external screen for presentation
                                 and want to automatically fallback to your laptop screen when you
                                 disconnect the external screen.
                             - force_on_start: switch to the given combination mode if available
                                 when the module starts (saves you from having to configure xorg)
                             - format_clone: string used to display a 'clone' combination
                             - format_extend: string used to display a 'extend' combination
                         
                         Dynamic configuration parameters:
                             - <OUTPUT>_pos: apply the given position to the OUTPUT
                                 Example: DP1_pos = "-2560x0"
                                 Example: DP1_pos = "left-of LVDS1"
                                 Example: DP1_pos = "right-of eDP1"
                         
                             - <OUTPUT>_workspaces: comma separated list of workspaces to move to
                                 the given OUTPUT when it is activated
                                 Example: DP1_workspaces = "1,2,3"
                         
                         Example config:
                             xrandr {
                                 force_on_start = "eDP1+DP1"
                                 DP1_pos = "left-of eDP1"
                                 VGA_workspaces = "7"
                             }
                         
                         @author ultrabug
                         ---
```
