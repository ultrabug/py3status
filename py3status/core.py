from __future__ import print_function

import argparse
import os
import sys

from copy import deepcopy
from json import dumps
from signal import signal
from signal import SIGTERM, SIGUSR1
from subprocess import Popen
from subprocess import call
from threading import Event
from time import sleep, time
from syslog import syslog, LOG_ERR, LOG_INFO, LOG_WARNING

import py3status.docstrings as docstrings
from py3status.events import Events
from py3status.helpers import print_line, print_stderr
from py3status.i3status import I3status
from py3status.module import Module
from py3status.profiling import profile


class Py3statusWrapper():
    """
    This is the py3status wrapper.
    """

    def __init__(self):
        """
        Useful variables we'll need.
        """
        self.last_refresh_ts = time()
        self.lock = Event()
        self.modules = {}
        self.py3_modules = []

    def get_config(self):
        """
        Create the py3status based on command line options we received.
        """
        # get home path
        home_path = os.path.expanduser('~')

        # defaults
        config = {
            'cache_timeout': 60,
            'include_paths': ['{}/.i3/py3status/'.format(home_path)],
            'interval': 1,  # no longer used but is an existing cli option
            'minimum_interval': 0.1  # minimum module update interval
        }

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
            '{}/.config/i3status/config'.format(os.environ.get(
                'XDG_CONFIG_HOME', home_path)), '/etc/i3status.conf',
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
        if options.include_paths:
            config['include_paths'] = options.include_paths
        config['interval'] = int(options.interval)
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
        for include_path in sorted(self.config['include_paths']):
            include_path = os.path.abspath(include_path) + '/'
            if not os.path.isdir(include_path):
                continue
            for f_name in sorted(os.listdir(include_path)):
                if not f_name.endswith('.py'):
                    continue
                module_name = f_name[:-3]
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
                my_m = Module(self.lock, self.config, module,
                              self.i3status_thread, user_modules)
                # only start and handle modules with available methods
                if my_m.methods:
                    my_m.start()
                    self.modules[module] = my_m
                elif self.config['debug']:
                    syslog(LOG_INFO,
                           'ignoring module "{}" (no methods found)'.format(
                               module))
            except Exception:
                err = sys.exc_info()[1]
                msg = 'loading module "{}" failed ({})'.format(module, err)
                self.i3_nagbar(msg, level='warning')

    def setup(self):
        """
        Setup py3status and spawn i3status/events/modules threads.
        """
        # set the Event lock
        self.lock.set()

        # setup configuration
        self.config = self.get_config()

        if self.config.get('cli_command'):
            self.handle_cli_command(self.config)
            sys.exit()

        if self.config['debug']:
            syslog(LOG_INFO,
                   'py3status started with config {}'.format(self.config))

        # setup i3status thread
        self.i3status_thread = I3status(self.lock,
                                        self.config['i3status_config_path'],
                                        self.config['standalone'])
        if self.config['standalone']:
            self.i3status_thread.mock()
        else:
            self.i3status_thread.start()
            while not self.i3status_thread.ready:
                if not self.i3status_thread.is_alive():
                    err = self.i3status_thread.error
                    raise IOError(err)
                sleep(0.1)
        if self.config['debug']:
            syslog(LOG_INFO, 'i3status thread {} with config {}'.format(
                'started' if not self.config['standalone'] else 'mocked',
                self.i3status_thread.config))

        # setup input events thread
        self.events_thread = Events(self.lock, self.config, self.modules,
                                    self.i3status_thread.config)
        self.events_thread.start()
        if self.config['debug']:
            syslog(LOG_INFO, 'events thread started')

        # suppress modules' ouput wrt issue #20
        if not self.config['debug']:
            sys.stdout = open('/dev/null', 'w')
            sys.stderr = open('/dev/null', 'w')

        # get the list of py3status configured modules
        self.py3_modules = self.i3status_thread.config['py3_modules']

        # get a dict of all user provided modules
        user_modules = self.get_user_configured_modules()
        if self.config['debug']:
            syslog(LOG_INFO, 'user_modules={}'.format(user_modules))

        if self.py3_modules:
            # load and spawn i3status.conf configured modules threads
            self.load_modules(self.py3_modules, user_modules)

    def i3_nagbar(self, msg, level='error'):
        """
        Make use of i3-nagbar to display errors and warnings to the user.
        We also make sure to log anything to keep trace of it.
        """
        msg = 'py3status: {}. '.format(msg)
        msg += 'please try to fix this and reload i3wm (Mod+Shift+R)'
        try:
            log_level = LOG_ERR if level == 'error' else LOG_WARNING
            syslog(log_level, msg)
            Popen(['i3-nagbar', '-m', msg, '-t', level],
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
                syslog(LOG_INFO, 'lock cleared, exiting')
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
        if time() > (self.last_refresh_ts + 0.1):
            syslog(LOG_INFO, 'received USR1, forcing refresh')

            # send SIGUSR1 to i3status
            call(['killall', '-s', 'USR1', 'i3status'])

            # clear the cache of all modules
            self.clear_modules_cache()

            # reset the refresh timestamp
            self.last_refresh_ts = time()
        else:
            syslog(LOG_INFO,
                   'received USR1 but rate limit is in effect, calm down')

    def clear_modules_cache(self):
        """
        For every module, reset the 'cached_until' of all its methods.
        """
        for module in self.modules.values():
            module.clear_cache()

    def terminate(self, signum, frame):
        """
        Received request to terminate (SIGTERM), exit nicely.
        """
        raise KeyboardInterrupt()

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
        delta = 0
        last_delta = -1
        previous_json_list = []

        # main loop
        while True:
            # check i3status thread
            if not self.i3status_thread.is_alive():
                err = self.i3status_thread.error
                if not err:
                    err = 'i3status died horribly'
                self.i3_nagbar(err)
                break

            # check events thread
            if not self.events_thread.is_alive():
                # don't spam the user with i3-nagbar warnings
                if not hasattr(self.events_thread, 'i3_nagbar'):
                    self.events_thread.i3_nagbar = True
                    err = 'events thread died, click events are disabled'
                    self.i3_nagbar(err, level='warning')

            # get output from i3status
            prefix = self.i3status_thread.last_prefix
            json_list = deepcopy(self.i3status_thread.json_list)

            # transform time and tztime outputs from i3status
            # every configured interval seconds
            if self.config['interval'] <= 1 or \
                    int(delta) % self.config['interval'] == 0 \
                    and int(last_delta) != int(delta):
                delta = 0
                last_delta = 0
                json_list = self.i3status_thread.tick_time_modules(json_list,
                                                                   force=True)
            else:
                json_list = self.i3status_thread.tick_time_modules(json_list,
                                                                   force=False)

            # construct the global output
            if self.modules and self.py3_modules:
                # new style i3status configured ordering
                json_list = self.i3status_thread.get_modules_output(
                    json_list, self.modules)

            # dump the line to stdout only on change
            if json_list != previous_json_list:
                print_line('{}{}'.format(prefix, dumps(json_list)))

            # remember the last json list output
            previous_json_list = deepcopy(json_list)

            # reset i3status json_list and json_list_ts
            self.i3status_thread.update_json_list()

            # sleep a bit before doing this again to avoid killing the CPU
            delta += 0.1
            sleep(0.1)

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
