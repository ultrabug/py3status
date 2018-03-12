from __future__ import print_function
from __future__ import division

import os
import sys
import time

from collections import deque
from json import dumps
from platform import python_version
from pprint import pformat
from signal import signal, SIGTERM, SIGUSR1, SIGTSTP, SIGCONT
from subprocess import Popen
from threading import Event, Thread
from syslog import syslog, LOG_ERR, LOG_INFO, LOG_WARNING
from traceback import extract_tb, format_tb, format_stack

import py3status.docstrings as docstrings
from py3status.command import CommandServer
from py3status.constants import COLOR_NAMES
from py3status.events import Events
from py3status.helpers import print_stderr
from py3status.i3status import I3status
from py3status.parse_config import process_config
from py3status.module import Module
from py3status.profiling import profile
from py3status.version import version

LOG_LEVELS = {'error': LOG_ERR, 'warning': LOG_WARNING, 'info': LOG_INFO, }

DBUS_LEVELS = {'error': 'critical', 'warning': 'normal', 'info': 'low', }

CONFIG_SPECIAL_SECTIONS = [
    '.group_extras',
    '.module_groups',
    'general',
    'i3s_modules',
    'on_click',
    'order',
    'py3_modules',
    'py3status',
]


class Runner(Thread):
    """
    A Simple helper to run a module in a Thread so it is non-locking.
    """
    def __init__(self, module, py3_wrapper, module_name):
        Thread.__init__(self)
        self.daemon = True
        self.module = module
        self.module_name = module_name
        self.py3_wrapper = py3_wrapper
        self.start()

    def run(self):
        try:
            self.module.run()
        except:
            self.py3_wrapper.report_exception('Runner')
        # the module is no longer running so notify the timeout logic
        if self.module_name:
            self.py3_wrapper.timeout_finished.append(self.module_name)


class NoneSetting:
    """
    This class represents no setting in the config.
    """
    # this attribute is used to identify that this is a none setting
    none_setting = True

    def __len__(self):
        return 0

    def __repr__(self):
        # this is for output via module_test
        return 'None'


class Task:
    """
    A simple task that can be run by the scheduler.
    """

    def run(self):
        raise NotImplemented()


class CheckI3StatusThread(Task):
    """
    Checks that the i3status thread is alive
    """

    def __init__(self, i3status_thread, py3_wrapper):
        self.i3status_thread = i3status_thread
        self.timeout_queue_add = py3_wrapper.timeout_queue_add
        self.notify_user = py3_wrapper.notify_user

    def run(self):
        # check i3status thread
        if not self.i3status_thread.is_alive():
            err = self.i3status_thread.error
            if not err:
                err = 'I3status died horribly.'
            self.notify_user(err)
        else:
            # check again in 5 seconds
            self.timeout_queue_add(self, int(time.time()) + 5)


class ModuleRunner(Task):
    """
    Starts up a Module
    """

    def __init__(self, module):
        self.module = module

    def run(self):
        self.module.start_module()


class Common:
    """
    This class is used to hold core functionality so that it can be shared more
    easily.  This allow us to run the module tests through the same code as
    when we are running for real.
    """

    def __init__(self, py3_wrapper):
        self.py3_wrapper = py3_wrapper
        self.none_setting = NoneSetting()
        self.config = py3_wrapper.config

    def get_config_attribute(self, name, attribute):
        """
        Look for the attribute in the config.  Start with the named module and
        then walk up through any containing group and then try the general
        section of the config.
        """

        # A user can set a param to None in the config to prevent a param
        # being used.  This is important when modules do something like
        #
        # color = self.py3.COLOR_MUTED or self.py3.COLOR_BAD
        config = self.config['py3_config']
        param = config[name].get(attribute, self.none_setting)
        if hasattr(param, 'none_setting') and name in config['.module_groups']:
            for module in config['.module_groups'][name]:
                if attribute in config.get(module, {}):
                    param = config[module].get(attribute)
                    break
        if hasattr(param, 'none_setting'):
            # check py3status config section
            param = config['py3status'].get(attribute, self.none_setting)
        if hasattr(param, 'none_setting'):
            # check py3status general section
            param = config['general'].get(attribute, self.none_setting)
        if param and (attribute == 'color' or attribute.startswith('color_')):
            if param[0] != '#':
                # named color
                param = COLOR_NAMES.get(param.lower(), self.none_setting)
            elif len(param) == 4:
                # This is a color like #123 convert it to #112233
                param = (
                    '#' + param[1] + param[1] + param[2] +
                    param[2] + param[3] + param[3]
                )
        return param

    def report_exception(self, msg, notify_user=True, level='error',
                         error_frame=None):
        """
        Report details of an exception to the user.
        This should only be called within an except: block Details of the
        exception are reported eg filename, line number and exception type.

        Because stack trace information outside of py3status or it's modules is
        not helpful in actually finding and fixing the error, we try to locate
        the first place that the exception affected our code.

        Alternatively if the error occurs in a module via a Py3 call that
        catches and reports the error then we receive an error_frame and use
        that as the source of the error.

        NOTE: msg should not end in a '.' for consistency.
        """
        # Get list of paths that our stack trace should be found in.
        py3_paths = [os.path.dirname(__file__)]
        user_paths = self.config.get('include_paths', [])
        py3_paths += [os.path.abspath(path) + '/' for path in user_paths]
        traceback = None

        try:
            # We need to make sure to delete tb even if things go wrong.
            exc_type, exc_obj, tb = sys.exc_info()
            stack = extract_tb(tb)
            error_str = '{}: {}\n'.format(exc_type.__name__, exc_obj)
            traceback = [error_str]

            if error_frame:
                # The error occurred in a py3status module so the traceback
                # should be made to appear correct.  We caught the exception
                # but make it look as though we did not.
                traceback += format_stack(error_frame, 1) + format_tb(tb)
                filename = os.path.basename(error_frame.f_code.co_filename)
                line_no = error_frame.f_lineno
            else:
                # This is a none module based error
                traceback += format_tb(tb)
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
        self.py3_wrapper.log(msg, 'warning')
        if traceback:
            # if debug is not in the config  then we are at an early stage of
            # running py3status and logging is not yet available so output the
            # error to STDERR so it can be seen
            if 'debug' not in self.config:
                print_stderr('\n'.join(traceback))
            elif self.config.get('log_file'):
                self.py3_wrapper.log(''.join(['Traceback\n'] + traceback))
        if notify_user:
            self.py3_wrapper.notify_user(msg, level=level)


class Py3statusWrapper:
    """
    This is the py3status wrapper.
    """

    def __init__(self, options):
        """
        Useful variables we'll need.
        """
        self.config = {}
        self.i3bar_running = True
        self.last_refresh_ts = time.time()
        self.lock = Event()
        self.modules = {}
        self.notified_messages = set()
        self.options = options
        self.output_modules = {}
        self.py3_modules = []
        self.running = True
        self.update_queue = deque()
        self.update_request = Event()

        # shared code
        self.common = Common(self)
        self.get_config_attribute = self.common.get_config_attribute
        self.report_exception = self.common.report_exception

        # these are used to schedule module updates
        self.timeout_add_queue = deque()
        self.timeout_due = None
        self.timeout_finished = deque()
        self.timeout_keys = []
        self.timeout_missed = {}
        self.timeout_queue = {}
        self.timeout_queue_lookup = {}
        self.timeout_running = set()
        self.timeout_update_due = deque()

    def timeout_queue_add(self, item, cache_time=0):
        """
        Add a item to be run at a future time.
        This must be a Module, I3statusModule or a Task
        """
        # add the info to the add queue.  We do this so that actually adding
        # the module is done in the core thread.
        self.timeout_add_queue.append((item, cache_time))
        # if the timeout_add_queue is not due to be processed until after this
        # update request is due then trigger an update now.
        if self.timeout_due is None or cache_time < self.timeout_due:
            self.update_request.set()

    def timeout_process_add_queue(self, module, cache_time):
        """
        Add a module to the timeout_queue if it is scheduled in the future or
        if it is due for an update immediately just trigger that.

        the timeout_queue is a dict with the scheduled time as the key and the
        value is a list of module instance names due to be updated at that
        point. An ordered list of keys is kept to allow easy checking of when
        updates are due.  A list is also kept of which modules are in the
        update_queue to save having to search for modules in it unless needed.
        """
        # If already set to update do nothing
        if module in self.timeout_update_due:
            return

        # remove if already in the queue
        key = self.timeout_queue_lookup.get(module)
        if key:
            queue_item = self.timeout_queue[key]
            queue_item.remove(module)
            if not queue_item:
                del self.timeout_queue[key]
                self.timeout_keys.remove(key)

        if cache_time == 0:
            # if cache_time is 0 we can just trigger the module update
            self.timeout_update_due.append(module)
            self.timeout_queue_lookup[module] = None
        else:
            # add the module to the timeout queue
            if cache_time not in self.timeout_keys:
                self.timeout_queue[cache_time] = set([module])
                self.timeout_keys.append(cache_time)
                # sort keys so earliest is first
                self.timeout_keys.sort()

                # when is next timeout due?
                try:
                    self.timeout_due = self.timeout_keys[0]
                except IndexError:
                    self.timeout_due = None
            else:
                self.timeout_queue[cache_time].add(module)
            # note that the module is in the timeout_queue
            self.timeout_queue_lookup[module] = cache_time

    def timeout_queue_process(self):
        """
        Check the timeout_queue and set any due modules to update.
        """
        # process any items that need adding to the queue
        while self.timeout_add_queue:
            self.timeout_process_add_queue(*self.timeout_add_queue.popleft())
        now = time.time()
        due_timeouts = []
        # find any due timeouts
        for timeout in self.timeout_keys:
            if timeout > now:
                break
            due_timeouts.append(timeout)

        if due_timeouts:
            # process them
            for timeout in due_timeouts:
                modules = self.timeout_queue[timeout]
                # remove from the queue
                del self.timeout_queue[timeout]
                self.timeout_keys.remove(timeout)

                for module in modules:
                    # module no longer in queue
                    del self.timeout_queue_lookup[module]
                    # tell module to update
                    self.timeout_update_due.append(module)

            # when is next timeout due?
            try:
                self.timeout_due = self.timeout_keys[0]
            except IndexError:
                self.timeout_due = None

        # process any finished modules.
        # Now that the module has finished running it may have been marked to
        # be triggered again. This is most likely to happen when events are
        # being processed and the events are arriving much faster than the
        # module can handle them.  It is important as a module may handle
        # events but not trigger the module update.  If during the event the
        # module is due to update the update is not actioned but it needs to be
        # once the events have finished or else the module will no longer
        # continue to update.
        while self.timeout_finished:
            module_name = self.timeout_finished.popleft()
            self.timeout_running.discard(module_name)
            if module_name in self.timeout_missed:
                module = self.timeout_missed.pop(module_name)
                self.timeout_update_due.append(module)

        # run any modules that are due
        while self.timeout_update_due:
            module = self.timeout_update_due.popleft()
            module_name = getattr(module, 'module_full_name', None)
            # if the module is running then we do not want to trigger it but
            # instead wait till it has finished running and then trigger
            if module_name and module_name in self.timeout_running:
                self.timeout_missed[module_name] = module
            else:
                self.timeout_running.add(module_name)
                Runner(module, self, module_name)

        # we return how long till we next need to process the timeout_queue
        if self.timeout_due is not None:
            return self.timeout_due - time.time()

    def get_config(self):
        """
        Create the py3status based on command line options we received.
        """
        # get home path
        home_path = os.path.expanduser('~')

        # defaults
        config = {
            'minimum_interval': 0.1,  # minimum module update interval
        }

        # include path to search for user modules
        config['include_paths'] = [
            '{}/.i3/py3status/'.format(home_path),
            '{}/i3status/py3status'.format(os.environ.get(
                'XDG_CONFIG_HOME', '{}/.config'.format(home_path))),
            '{}/i3/py3status'.format(os.environ.get(
                'XDG_CONFIG_HOME', '{}/.config'.format(home_path))),
        ]
        config['version'] = version

        # override configuration and helper variables
        options = self.options
        config['cache_timeout'] = options.cache_timeout
        config['debug'] = options.debug
        config['dbus_notify'] = options.dbus_notify
        config['gevent'] = options.gevent
        if options.include_paths:
            config['include_paths'] = options.include_paths
        # FIXME we allow giving interval as a float and then make it an int!
        config['interval'] = int(options.interval)
        config['log_file'] = options.log_file
        config['standalone'] = options.standalone
        config['i3status_config_path'] = options.i3status_conf
        if options.cli_command:
            config['cli_command'] = options.cli_command
        return config

    def gevent_monkey_patch_report(self):
        """
        Report effective gevent monkey patching on the logs.
        """
        try:
            import gevent.socket
            import socket
            if gevent.socket.socket is socket.socket:
                self.log('gevent monkey patching is active')
            else:
                self.notify_user('gevent monkey patching failed.')
        except ImportError:
            self.notify_user(
                'gevent is not installed, monkey patching failed.')

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
                # only handle modules with available methods
                if my_m.methods:
                    self.modules[module] = my_m
                elif self.config['debug']:
                    self.log(
                        'ignoring module "{}" (no methods found)'.format(
                            module))
            except Exception:
                err = sys.exc_info()[1]
                msg = 'Loading module "{}" failed ({}).'.format(module, err)
                self.report_exception(msg, level='warning')

    def setup(self):
        """
        Setup py3status and spawn i3status/events/modules threads.
        """

        # SIGTSTP will be received from i3bar indicating that all output should
        # stop and we should consider py3status suspended.  It is however
        # important that any processes using i3 ipc should continue to receive
        # those events otherwise it can lead to a stall in i3.
        signal(SIGTSTP, self.i3bar_stop)
        # SIGCONT indicates output should be resumed.
        signal(SIGCONT, self.i3bar_start)

        # update configuration
        self.config.update(self.get_config())

        if self.config.get('cli_command'):
            self.handle_cli_command(self.config)
            sys.exit()

        # logging functionality now available
        # log py3status and python versions
        self.log('=' * 8)
        self.log('Starting py3status version {} python {}'.format(
            self.config['version'], python_version())
        )

        try:
            # if running from git then log the branch and last commit
            # we do this by looking in the .git directory
            git_path = os.path.join(os.path.dirname(__file__), '..', '.git')
            # branch
            with open(os.path.join(git_path, 'HEAD'), 'r') as f:
                out = f.readline()
            branch = '/'.join(out.strip().split('/')[2:])
            self.log('git branch: {}'.format(branch))
            # last commit
            log_path = os.path.join(git_path, 'logs', 'refs', 'heads', branch)
            with open(log_path, 'r') as f:
                out = f.readlines()[-1]
            sha = out.split(' ')[1][:7]
            msg = ':'.join(out.strip().split('\t')[-1].split(':')[1:])
            self.log('git commit: {}{}'.format(sha, msg))
        except:
            pass

        if self.config['debug']:
            self.log(
                'py3status started with config {}'.format(self.config))

        if self.config['gevent']:
            self.gevent_monkey_patch_report()

        # read i3status.conf
        config_path = self.config['i3status_config_path']
        self.config['py3_config'] = process_config(config_path, self)

        # setup i3status thread
        self.i3status_thread = I3status(self)

        # If standalone or no i3status modules then use the mock i3status
        # else start i3status thread.
        i3s_modules = self.config['py3_config']['i3s_modules']
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
                i3s_mode, self.config['py3_config']))

        # add i3status thread monitoring task
        if i3s_mode == 'started':
            task = CheckI3StatusThread(self.i3status_thread, self)
            self.timeout_queue_add(task)

        # setup input events thread
        self.events_thread = Events(self)
        self.events_thread.daemon = True
        self.events_thread.start()
        if self.config['debug']:
            self.log('events thread started')

        # initialise the command server
        self.commands_thread = CommandServer(self)
        self.commands_thread.daemon = True
        self.commands_thread.start()
        if self.config['debug']:
            self.log('commands thread started')

        # suppress modules' ouput wrt issue #20
        if not self.config['debug']:
            sys.stdout = open('/dev/null', 'w')
            sys.stderr = open('/dev/null', 'w')

        # get the list of py3status configured modules
        self.py3_modules = self.config['py3_config']['py3_modules']

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
            msg = u'{}'.format(msg)
        else:
            msg = u'py3status: {}'.format(msg)
        if level != 'info' and module_name == '':
            fix_msg = u'{} Please try to fix this and reload i3wm (Mod+Shift+R)'
            msg = fix_msg.format(msg)
        # Rate limiting. If rate limiting then we need to calculate the time
        # period for which the message should not be repeated.  We just use
        # A simple chunked time model where a message cannot be repeated in a
        # given time period. Messages can be repeated more frequently but must
        # be in different time periods.

        limit_key = ''
        if rate_limit:
            try:
                limit_key = time.time() // rate_limit
            except TypeError:
                pass
        # We use a hash to see if the message is being repeated.  This is crude
        # and imperfect but should work for our needs.
        msg_hash = hash(u'{}#{}#{}'.format(module_name, limit_key, msg))
        if msg_hash in self.notified_messages:
            return
        elif module_name:
            log_msg = 'Module `%s` sent a notification. "%s"' % (module_name, msg)
            self.log(log_msg, level)
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
                py3_config = self.config.get('py3_config', {})
                nagbar_font = py3_config.get('py3status', {}).get('nagbar_font')
                if nagbar_font:
                    cmd = ['i3-nagbar', '-f', nagbar_font, '-m', msg, '-t', level]
                else:
                    cmd = ['i3-nagbar', '-m', msg, '-t', level]
            Popen(cmd,
                  stdout=open('/dev/null', 'w'),
                  stderr=open('/dev/null', 'w'))
        except Exception as err:
            self.log('notify_user error: %s' % err)

    def stop(self):
        """
        Set the Event lock, this will break all threads' loops.
        """
        self.running = False
        # stop the command server
        try:
            self.commands_thread.kill()
        except:
            pass

        try:
            self.lock.set()
            if self.config['debug']:
                self.log('lock set, exiting')
            # run kill() method on all py3status modules
            for module in self.modules.values():
                module.kill()
        except:
            pass

    def refresh_modules(self, module_string=None, exact=True):
        """
        Update modules.
        if module_string is None all modules are refreshed
        if module_string then modules with the exact name or those starting
        with the given string depending on exact parameter will be refreshed.
        If a module is an i3status one then we refresh i3status.
        To prevent abuse, we rate limit this function to 100ms for full
        refreshes.
        """
        if not module_string:
            if time.time() > (self.last_refresh_ts + 0.1):
                self.last_refresh_ts = time.time()
            else:
                # rate limiting
                return
        update_i3status = False
        for name, module in self.output_modules.items():
            if (module_string is None or
                    (exact and name == module_string) or
                    (not exact and name.startswith(module_string))):
                if module['type'] == 'py3status':
                    if self.config['debug']:
                        self.log('refresh py3status module {}'.format(name))
                    module['module'].force_update()
                else:
                    if self.config['debug']:
                        self.log('refresh i3status module {}'.format(name))
                    update_i3status = True
        if update_i3status:
            self.i3status_thread.refresh_i3status()

    def sig_handler(self, signum, frame):
        """
        SIGUSR1 was received, the user asks for an immediate refresh of the bar
        """
        self.log('received USR1')
        self.refresh_modules()

    def terminate(self, signum, frame):
        """
        Received request to terminate (SIGTERM), exit nicely.
        """
        raise KeyboardInterrupt()

    def purge_module(self, module_name):
        """
        A module has been removed e.g. a module that had an error.
        We need to find any containers and remove the module from them.
        """
        containers = self.config['py3_config']['.module_groups']
        containers_to_update = set()
        if module_name in containers:
            containers_to_update.update(set(containers[module_name]))
        for container in containers_to_update:
            try:
                self.modules[container].module_class.items.remove(module_name)
            except ValueError:
                pass

    def notify_update(self, update, urgent=False):
        """
        Name or list of names of modules that have updated.
        """
        if not isinstance(update, list):
            update = [update]
        self.update_queue.extend(update)

        # find containers that use the modules that updated
        containers = self.config['py3_config']['.module_groups']
        containers_to_update = set()
        for item in update:
            if item in containers:
                containers_to_update.update(set(containers[item]))
        # force containers to update
        for container in containers_to_update:
            container_module = self.output_modules.get(container)
            if container_module:
                # If the container registered a urgent_function then call it
                # if this update is urgent.
                if urgent and container_module.get('urgent_function'):
                    container_module['urgent_function'](update)
                # If a container has registered a content_function we use that
                # to see if the container needs to be updated.
                # We only need to update containers if their active content has
                # changed.
                if container_module.get('content_function'):
                    if set(update) & container_module['content_function']():
                        container_module['module'].force_update()
                else:
                    # we don't know so just update.
                    container_module['module'].force_update()

        # we need to update the output
        if self.update_queue:
            self.update_request.set()

    def log(self, msg, level='info'):
        """
        log this information to syslog or user provided logfile.
        """
        if not self.config.get('log_file'):
            # If level was given as a str then convert to actual level
            level = LOG_LEVELS.get(level, level)
            syslog(level, u'{}'.format(msg))
        else:
            # Binary mode so fs encoding setting is not an issue
            with open(self.config['log_file'], 'ab') as f:
                log_time = time.strftime("%Y-%m-%d %H:%M:%S")
                # nice formating of data structures using pretty print
                if isinstance(msg, (dict, list, set, tuple)):
                    msg = pformat(msg)
                    # if multiline then start the data output on a fresh line
                    # to aid readability.
                    if '\n' in msg:
                        msg = u'\n' + msg
                out = u'{} {} {}\n'.format(log_time, level.upper(), msg)
                try:
                    # Encode unicode strings to bytes
                    f.write(out.encode('utf-8'))
                except (AttributeError, UnicodeDecodeError):
                    # Write any byte strings straight to log
                    f.write(out)

    def create_output_modules(self):
        """
        Setup our output modules to allow easy updating of py3modules and
        i3status modules allows the same module to be used multiple times.
        """
        py3_config = self.config['py3_config']
        i3modules = self.i3status_thread.i3modules
        output_modules = self.output_modules
        # position in the bar of the modules
        positions = {}
        for index, name in enumerate(py3_config['order']):
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
                output_modules[name]['color'] = self.mappings_color.get(name)
        # i3status modules
        for name in i3modules:
            if name not in output_modules:
                output_modules[name] = {}
                output_modules[name]['position'] = positions.get(name, [])
                output_modules[name]['module'] = i3modules[name]
                output_modules[name]['type'] = 'i3status'
                output_modules[name]['color'] = self.mappings_color.get(name)

        self.output_modules = output_modules

    def create_mappings(self, config):
        """
        Create any mappings needed for global substitutions eg. colors
        """
        mappings = {}
        for name, cfg in config.items():
            # Ignore special config sections.
            if name in CONFIG_SPECIAL_SECTIONS:
                continue
            color = self.get_config_attribute(name, 'color')
            if hasattr(color, 'none_setting'):
                color = None
            mappings[name] = color
        # Store mappings for later use.
        self.mappings_color = mappings

    def process_module_output(self, module):
        """
        Process the output for a module and return a json string representing it.
        Color processing occurs here.
        """
        outputs = module['module'].get_latest()
        color = module['color']
        if color:
            for output in outputs:
                # Color: substitute the config defined color
                if 'color' not in output:
                    output['color'] = color
        # Create the json string output.
        return ','.join([dumps(x) for x in outputs])

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
        py3_config = self.config['py3_config']

        # prepare the color mappings
        self.create_mappings(py3_config)

        # self.output_modules needs to have been created before modules are
        # started.  This is so that modules can do things like register their
        # content_function.
        self.create_output_modules()

        # start up all our modules
        for module in self.modules.values():
            task = ModuleRunner(module)
            self.timeout_queue_add(task)

        # this will be our output set to the correct length for the number of
        # items in the bar
        output = [None] * len(py3_config['order'])

        write = sys.__stdout__.write
        flush = sys.__stdout__.flush

        # start our output
        header = {
            'version': 1,
            'click_events': True,
            'stop_signal': SIGTSTP
        }
        write(dumps(header))
        write('\n[[]\n')

        update_due = None
        # main loop
        while True:
            # process the timeout_queue and get interval till next update due
            update_due = self.timeout_queue_process()

            # wait until an update is requested
            if self.update_request.wait(timeout=update_due):
                # event was set so clear it
                self.update_request.clear()

            while not self.i3bar_running:
                time.sleep(0.1)

            # check if an update is needed
            if self.update_queue:
                while (len(self.update_queue)):
                    module_name = self.update_queue.popleft()
                    module = self.output_modules[module_name]
                    out = self.process_module_output(module)

                    for index in module['position']:
                        # store the output as json
                        output[index] = out

                # build output string
                out = ','.join([x for x in output if x])
                # dump the line to stdout
                write(',[{}]\n'.format(out))
                flush()

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
                if show_diff:
                    mods = cmd[3:]
                else:
                    mods = cmd[2:]
                docstrings.check_docstrings(show_diff, config, mods)
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
