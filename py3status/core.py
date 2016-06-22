from __future__ import print_function
from __future__ import division

import argparse
import os
import sys
import time

from collections import deque
from json import dumps
from signal import signal, SIGTERM, SIGUSR1, SIGTSTP, SIGCONT
from subprocess import Popen, call
from threading import Event
from syslog import syslog, LOG_ERR, LOG_INFO, LOG_WARNING
from traceback import extract_tb, format_tb

import py3status.docstrings as docstrings
from py3status.events import Events
from py3status.helpers import print_line, print_stderr
from py3status.i3status import I3status
from py3status.module import Module
from py3status.profiling import profile

LOG_LEVELS = {'error': LOG_ERR, 'warning': LOG_WARNING, 'info': LOG_INFO, }

DBUS_LEVELS = {'error': 'critical', 'warning': 'normal', 'info': 'low', }


class Py3statusWrapper():
    """
    This is the py3status wrapper.
    """

    def __init__(self):
        """
        Useful variables we'll need.
        """
        self.config = {}
        self.i3bar_running = True
        self.last_refresh_ts = time.time()
        self.lock = Event()
        self.modules = {}
        self.notified_messages = set()
        self.output_modules = {}
        self.py3_modules = []
        self.queue = deque()

    def get_config(self):
        """
        Create the py3status based on command line options we received.
        """
        # get home path
        home_path = os.path.expanduser('~')

        # defaults
        config = {
            'cache_timeout': 60,
            'interval': 1,
            'minimum_interval': 0.1,  # minimum module update interval
            'dbus_notify': False,
        }

        # include path to search for user modules
        config['include_paths'] = [
            '{}/.i3/py3status/'.format(home_path),
            '{}/i3status/py3status'.format(os.environ.get(
                'XDG_CONFIG_HOME', '{}/.config'.format(home_path))),
            '{}/i3/py3status'.format(os.environ.get(
                'XDG_CONFIG_HOME', '{}/.config'.format(home_path))),
        ]

        # package version
        try:
            import pkg_resources
            version = pkg_resources.get_distribution('py3status').version
        except:
            version = 'unknown'
        config['version'] = version

        # i3status config file default detection
        # respect i3status' file detection order wrt issue #43
        i3status_config_file_candidates = [
            '{}/.i3status.conf'.format(home_path),
            '{}/i3status/config'.format(os.environ.get(
                'XDG_CONFIG_HOME', '{}/.config'.format(home_path))),
            '/etc/i3status.conf',
            '{}/i3status/config'.format(os.environ.get('XDG_CONFIG_DIRS',
                                                       '/etc/xdg'))
        ]
        for fn in i3status_config_file_candidates:
            if os.path.isfile(fn):
                i3status_config_file_default = fn
                break
        else:
            # if none of the default files exists, we will default
            # to ~/.i3/i3status.conf
            i3status_config_file_default = '{}/.i3/i3status.conf'.format(
                home_path)

        # command line options
        parser = argparse.ArgumentParser(
            description='The agile, python-powered, i3status wrapper')
        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument('-b',
                            '--dbus-notify',
                            action="store_true",
                            default=False,
                            dest="dbus_notify",
                            help="""use notify-send to send user notifications
                                    rather than i3-nagbar,
                                    requires a notification daemon eg dunst""")
        parser.add_argument('-c',
                            '--config',
                            action="store",
                            dest="i3status_conf",
                            type=str,
                            default=i3status_config_file_default,
                            help="path to i3status config file")
        parser.add_argument('-d',
                            '--debug',
                            action="store_true",
                            help="be verbose in syslog")
        parser.add_argument('-i',
                            '--include',
                            action="append",
                            dest="include_paths",
                            help="""include user-written modules from those
                            directories (default ~/.i3/py3status)""")
        parser.add_argument('-l',
                            '--log-file',
                            action="store",
                            dest="log_file",
                            type=str,
                            default=None,
                            help="path to py3status log file")
        parser.add_argument('-n',
                            '--interval',
                            action="store",
                            dest="interval",
                            type=float,
                            default=config['interval'],
                            help="update interval in seconds (default 1 sec)")
        parser.add_argument('-s',
                            '--standalone',
                            action="store_true",
                            help="standalone mode, do not use i3status")
        parser.add_argument('-t',
                            '--timeout',
                            action="store",
                            dest="cache_timeout",
                            type=int,
                            default=config['cache_timeout'],
                            help="""default injection cache timeout in seconds
                            (default 60 sec)""")
        parser.add_argument('-v',
                            '--version',
                            action="store_true",
                            help="""show py3status version and exit""")
        parser.add_argument('cli_command', nargs='*', help=argparse.SUPPRESS)

        options = parser.parse_args()

        if options.cli_command:
            config['cli_command'] = options.cli_command

        # only asked for version
        if options.version:
            from platform import python_version
            print('py3status version {} (python {})'.format(config['version'],
                                                            python_version()))
            sys.exit(0)

        # override configuration and helper variables
        config['cache_timeout'] = options.cache_timeout
        config['debug'] = options.debug
        config['dbus_notify'] = options.dbus_notify
        if options.include_paths:
            config['include_paths'] = options.include_paths
        config['interval'] = int(options.interval)
        config['log_file'] = options.log_file
        config['standalone'] = options.standalone
        config['i3status_config_path'] = options.i3status_conf

        # all done
        return config

    def get_user_modules(self):
        """
        Search configured include directories for user provided modules.

        user_modules: {
            'weather_yahoo': ('~/i3/py3status/', 'weather_yahoo.py')
        }
        """
        user_modules = {}
        for include_path in self.config['include_paths']:
            include_path = os.path.abspath(include_path) + '/'
            if not os.path.isdir(include_path):
                continue
            for f_name in sorted(os.listdir(include_path)):
                if not f_name.endswith('.py'):
                    continue
                module_name = f_name[:-3]
                # do not overwrite modules if already found
                if module_name in user_modules:
                    pass
                user_modules[module_name] = (include_path, f_name)
        return user_modules

    def get_user_configured_modules(self):
        """
        Get a dict of all available and configured py3status modules
        in the user's i3status.conf.
        """
        user_modules = {}
        if not self.py3_modules:
            return user_modules
        for module_name, module_info in self.get_user_modules().items():
            for module in self.py3_modules:
                if module_name == module.split(' ')[0]:
                    include_path, f_name = module_info
                    user_modules[module_name] = (include_path, f_name)
        return user_modules

    def load_modules(self, modules_list, user_modules):
        """
        Load the given modules from the list (contains instance name) with
        respect to the user provided modules dict.

        modules_list: ['weather_yahoo paris', 'net_rate']
        user_modules: {
            'weather_yahoo': ('/etc/py3status.d/', 'weather_yahoo.py')
        }
        """
        for module in modules_list:
            # ignore already provided modules (prevents double inclusion)
            if module in self.modules:
                continue
            try:
                my_m = Module(module, user_modules, self)
                # only start and handle modules with available methods
                if my_m.methods:
                    my_m.start()
                    self.modules[module] = my_m
                elif self.config['debug']:
                    self.log(
                        'ignoring module "{}" (no methods found)'.format(
                            module))
            except Exception:
                err = sys.exc_info()[1]
                msg = 'Loading module "{}" failed ({}).'.format(module, err)
                self.notify_user(msg, level='warning')

    def setup(self):
        """
        Setup py3status and spawn i3status/events/modules threads.
        """
        # set the Event lock
        self.lock.set()

        # SIGTSTP will be received from i3bar indicating that all output should
        # stop and we should consider py3status suspended.  It is however
        # important that any processes using i3 ipc should continue to receive
        # those events otherwise it can lead to a stall in i3.
        signal(SIGTSTP, self.i3bar_stop)
        # SIGCONT indicates output should be resumed.
        signal(SIGCONT, self.i3bar_start)

        # setup configuration
        self.config = self.get_config()

        if self.config.get('cli_command'):
            self.handle_cli_command(self.config)
            sys.exit()

        if self.config['debug']:
            self.log(
                'py3status started with config {}'.format(self.config))

        # setup i3status thread
        self.i3status_thread = I3status(self)

        # If standalone or no i3status modules then use the mock i3status
        # else start i3status thread.
        i3s_modules = self.i3status_thread.config['i3s_modules']
        if self.config['standalone'] or not i3s_modules:
            self.i3status_thread.mock()
            i3s_mode = 'mocked'
        else:
            i3s_mode = 'started'
            self.i3status_thread.start()
            while not self.i3status_thread.ready:
                if not self.i3status_thread.is_alive():
                    # i3status is having a bad day, so tell the user what went
                    # wrong and do the best we can with just py3status modules.
                    err = self.i3status_thread.error
                    self.notify_user(err)
                    self.i3status_thread.mock()
                    i3s_mode = 'mocked'
                    break
                time.sleep(0.1)
        if self.config['debug']:
            self.log('i3status thread {} with config {}'.format(
                i3s_mode, self.i3status_thread.config))

        # setup input events thread
        self.events_thread = Events(self)
        self.events_thread.start()
        if self.config['debug']:
            self.log('events thread started')

        # suppress modules' ouput wrt issue #20
        if not self.config['debug']:
            sys.stdout = open('/dev/null', 'w')
            sys.stderr = open('/dev/null', 'w')

        # get the list of py3status configured modules
        self.py3_modules = self.i3status_thread.config['py3_modules']

        # get a dict of all user provided modules
        user_modules = self.get_user_configured_modules()
        if self.config['debug']:
            self.log('user_modules={}'.format(user_modules))

        if self.py3_modules:
            # load and spawn i3status.conf configured modules threads
            self.load_modules(self.py3_modules, user_modules)

    def notify_user(self, msg, level='error', rate_limit=None, module_name=''):
        """
        Display notification to user via i3-nagbar or send-notify
        We also make sure to log anything to keep trace of it.

        NOTE: Message should end with a '.' for consistency.
        """
        dbus = self.config.get('dbus_notify')
        if dbus:
            # force msg to be a string
            msg = '{}'.format(msg)
        else:
            msg = 'py3status: {}'.format(msg)
        if level != 'info' and module_name == '':
            fix_msg = '{} Please try to fix this and reload i3wm (Mod+Shift+R)'
            msg = fix_msg.format(msg)
        # Rate limiting. If rate limiting then we need to calculate the time
        # period for which the message should not be repeated.  We just use
        # A simple chunked time model where a message cannot be repeated in a
        # given time period. Messages can be repeated more frequently but must
        # be in different time periods.

        limit_key = ''
        if rate_limit:
            try:
                limit_key = time.time()//rate_limit
            except TypeError:
                pass
        # We use a hash to see if the message is being repeated.  This is crude
        # and imperfect but should work for our needs.
        msg_hash = hash('{}#{}#{}'.format(module_name, limit_key, msg))
        if msg_hash in self.notified_messages:
            return
        else:
            self.log(msg, level)
            self.notified_messages.add(msg_hash)

        try:
            if dbus:
                # fix any html entities
                msg = msg.replace('&', '&amp;')
                msg = msg.replace('<', '&lt;')
                msg = msg.replace('>', '&gt;')
                cmd = ['notify-send', '-u', DBUS_LEVELS.get(level, 'normal'),
                       '-t', '10000', 'py3status', msg]
            else:
                cmd = ['i3-nagbar', '-m', msg, '-t', level]
            Popen(cmd,
                  stdout=open('/dev/null', 'w'),
                  stderr=open('/dev/null', 'w'))
        except:
            pass

    def stop(self):
        """
        Clear the Event lock, this will break all threads' loops.
        """
        try:
            self.lock.clear()
            if self.config['debug']:
                self.log('lock cleared, exiting')
            # run kill() method on all py3status modules
            for module in self.modules.values():
                module.kill()
            self.i3status_thread.cleanup_tmpfile()
        except:
            pass

    def sig_handler(self, signum, frame):
        """
        SIGUSR1 was received, the user asks for an immediate refresh of the bar
        so we force i3status to refresh by sending it a SIGUSR1
        and we clear all py3status modules' cache.

        To prevent abuse, we rate limit this function to 100ms.
        """
        if time.time() > (self.last_refresh_ts + 0.1):
            self.log('received USR1, forcing refresh')

            # send SIGUSR1 to i3status
            call(['killall', '-s', 'USR1', 'i3status'])

            # clear the cache of all modules
            self.clear_modules_cache()

            # reset the refresh timestamp
            self.last_refresh_ts = time.time()
        else:
            self.log('received USR1 but rate limit is in effect, calm down')

    def clear_modules_cache(self):
        """
        For every module, reset the 'cached_until' of all its methods.
        """
        for module in self.modules.values():
            module.force_update()

    def terminate(self, signum, frame):
        """
        Received request to terminate (SIGTERM), exit nicely.
        """
        raise KeyboardInterrupt()

    def notify_update(self, update):
        """
        Name or list of names of modules that have updated.
        """
        if not isinstance(update, list):
            update = [update]
        self.queue.extend(update)

        # find groups that use the modules updated
        module_groups = self.i3status_thread.config['.module_groups']
        groups_to_update = set()
        for item in update:
            if item in module_groups:
                groups_to_update.update(set(module_groups[item]))
        # force groups to update
        for group in groups_to_update:
            group_module = self.output_modules.get(group)
            if group_module:
                group_module['module'].force_update()

    def log(self, msg, level='info'):
        """
        log this information to syslog or user provided logfile.
        """
        if not self.config['log_file']:
            # If level was given as a str then convert to actual level
            level = LOG_LEVELS.get(level, level)
            syslog(level, msg)
        else:
            with open(self.config['log_file'], 'a') as f:
                log_time = time.strftime("%Y-%m-%d %H:%M:%S")
                f.write('{} {} {}\n'.format(log_time, level.upper(), msg))

    def report_exception(self, msg, notify_user=True):
        """
        Report details of an exception to the user.
        This should only be called within an except: block Details of the
        exception are reported eg filename, line number and exception type.

        Because stack trace information outside of py3status or it's modules is
        not helpful in actually finding and fixing the error, we try to locate
        the first place that the exception affected our code.

        NOTE: msg should not end in a '.' for consistency.
        """
        # Get list of paths that our stack trace should be found in.
        py3_paths = [os.path.dirname(__file__)]
        user_paths = self.config['include_paths']
        py3_paths += [os.path.abspath(path) + '/' for path in user_paths]
        traceback = None

        try:
            # We need to make sure to delete tb even if things go wrong.
            exc_type, exc_obj, tb = sys.exc_info()
            stack = extract_tb(tb)
            error_str = '{}: {}\n'.format(exc_type.__name__, exc_obj)
            traceback = [error_str] + format_tb(tb)
            # Find first relevant trace in the stack.
            # it should be in py3status or one of it's modules.
            found = False
            for item in reversed(stack):
                filename = item[0]
                for path in py3_paths:
                    if filename.startswith(path):
                        # Found a good trace
                        filename = os.path.basename(item[0])
                        line_no = item[1]
                        found = True
                        break
                if found:
                    break
            # all done!  create our message.
            msg = '{} ({}) {} line {}.'.format(
                msg, exc_type.__name__, filename, line_no)
        except:
            # something went wrong report what we can.
            msg = '{}.'.format(msg)
        finally:
            # delete tb!
            del tb
        # log the exception and notify user
        self.log(msg, 'warning')
        if traceback and self.config['log_file']:
            self.log(''.join(['Traceback\n'] + traceback))
        if notify_user:
            self.notify_user(msg, level='error')

    def create_output_modules(self):
        """
        Setup our output modules to allow easy updating of py3modules and
        i3status modules allows the same module to be used multiple times.
        """
        config = self.i3status_thread.config
        i3modules = self.i3status_thread.i3modules
        output_modules = self.output_modules
        # position in the bar of the modules
        positions = {}
        for index, name in enumerate(config['order']):
            if name not in positions:
                positions[name] = []
            positions[name].append(index)

        # py3status modules
        for name in self.modules:
            if name not in output_modules:
                output_modules[name] = {}
                output_modules[name]['position'] = positions.get(name, [])
                output_modules[name]['module'] = self.modules[name]
                output_modules[name]['type'] = 'py3status'
        # i3status modules
        for name in i3modules:
            if name not in output_modules:
                output_modules[name] = {}
                output_modules[name]['position'] = positions.get(name, [])
                output_modules[name]['module'] = i3modules[name]
                output_modules[name]['type'] = 'i3status'

        self.output_modules = output_modules

    def i3bar_stop(self, signum, frame):
        self.i3bar_running = False
        # i3status should be stopped
        self.i3status_thread.suspend_i3status()
        self.sleep_modules()

    def i3bar_start(self, signum, frame):
        self.i3bar_running = True
        self.wake_modules()

    def sleep_modules(self):
        # Put all py3modules to sleep so they stop updating
        for module in self.output_modules.values():
            if module['type'] == 'py3status':
                module['module'].sleep()

    def wake_modules(self):
        # Wake up all py3modules.
        for module in self.output_modules.values():
            if module['type'] == 'py3status':
                module['module'].wake()

    @profile
    def run(self):
        """
        Main py3status loop, continuously read from i3status and modules
        and output it to i3bar for displaying.
        """
        # SIGUSR1 forces a refresh of the bar both for py3status and i3status,
        # this mimics the USR1 signal handling of i3status (see man i3status)
        signal(SIGUSR1, self.sig_handler)
        signal(SIGTERM, self.terminate)

        # initialize usage variables
        i3status_thread = self.i3status_thread
        config = i3status_thread.config
        self.create_output_modules()

        # update queue populate with all py3modules
        self.queue.extend(self.modules)

        # this will be our output set to the correct length for the number of
        # items in the bar
        output = [None] * len(config['order'])

        interval = self.config['interval']
        last_sec = 0

        # start our output
        header = {
            'version': 1,
            'click_events': True,
            'stop_signal': SIGTSTP
        }
        print_line(dumps(header))
        print_line('[[]')

        # main loop
        while True:
            while not self.i3bar_running:
                time.sleep(0.1)

            sec = int(time.time())

            # only check everything is good each second
            if sec > last_sec:
                last_sec = sec

                # check i3status thread
                if not i3status_thread.is_alive():
                    err = i3status_thread.error
                    if not err:
                        err = 'I3status died horribly.'
                    self.notify_user(err)

                # check events thread
                if not self.events_thread.is_alive():
                    # don't spam the user with i3-nagbar warnings
                    if not hasattr(self.events_thread, 'nagged'):
                        self.events_thread.nagged = True
                        err = 'Events thread died, click events are disabled.'
                        self.notify_user(err, level='warning')

                # update i3status time/tztime items
                if interval == 0 or sec % interval == 0:
                    i3status_thread.update_times()

            # check if an update is needed
            if self.queue:
                while (len(self.queue)):
                    module_name = self.queue.popleft()
                    module = self.output_modules[module_name]
                    for index in module['position']:
                        # store the output as json
                        # modules can have more than one output
                        out = module['module'].get_latest()
                        output[index] = ', '.join([dumps(x) for x in out])

                # build output string
                out = ','.join([x for x in output if x])
                # dump the line to stdout
                print_line(',[{}]'.format(out))

            # sleep a bit before doing this again to avoid killing the CPU
            time.sleep(0.1)

    def handle_cli_command(self, config):
        """Handle a command from the CLI.
        """
        cmd = config['cli_command']
        # aliases
        if cmd[0] in ['mod', 'module', 'modules']:
            cmd[0] = 'modules'

        # allowed cli commands
        if cmd[:2] in (['modules', 'list'], ['modules', 'details']):
            docstrings.show_modules(config, cmd[1:])
        # docstring formatting and checking
        elif cmd[:2] in (['docstring', 'check'], ['docstring', 'update']):
            if cmd[1] == 'check':
                show_diff = len(cmd) > 2 and cmd[2] == 'diff'
                docstrings.check_docstrings(show_diff, config)
            if cmd[1] == 'update':
                if len(cmd) < 3:
                    print_stderr('Error: you must specify what to update')
                    sys.exit(1)

                if cmd[2] == 'modules':
                    docstrings.update_docstrings()
                else:
                    docstrings.update_readme_for_modules(cmd[2:])
        elif cmd[:2] in (['modules', 'enable'], ['modules', 'disable']):
            # TODO: to be implemented
            pass
        else:
            print_stderr('Error: unknown command')
            sys.exit(1)
