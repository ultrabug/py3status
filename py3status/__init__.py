import argparse
import imp
import locale
import os
import select
import sys

from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime
from json import dumps, loads
from signal import signal
from signal import SIGUSR1
from subprocess import Popen
from subprocess import PIPE
from subprocess import call
from threading import Event, Thread
from time import sleep, time
from syslog import syslog, LOG_ERR, LOG_INFO, LOG_WARNING


@contextmanager
def jsonify(string):
    """
    Transform the given string to a JSON in a context manager fashion.
    """
    prefix = ''
    if string.startswith(','):
        prefix, string = ',', string[1:]
    yield (prefix, loads(string))


def print_line(line):
    """
    Print given line to stdout (i3bar).
    """
    sys.__stdout__.write('{}\n'.format(line))
    sys.__stdout__.flush()


class IOPoller:
    """
    This class implements a predictive and timing-out I/O reader
    using select and the poll() mechanism for greater compatibility.
    """
    def __init__(self, io, eventmask=select.POLLIN):
        """
        Our default is to read (POLLIN) the specified 'io' file descriptor.
        """
        self.io = io
        self.poller = select.poll()
        self.poller.register(io, eventmask)

    def readline(self, timeout=0.5):
        """
        Try to read our I/O for 'timeout' seconds, return None otherwise.
        This makes calling and reading I/O non blocking !
        """
        poll_result = self.poller.poll(timeout)
        if poll_result:
            line = self.io.readline().strip()
            if self.io == sys.stdin and line == '[':
                # skip first event line wrt issue #19
                line = self.io.readline().strip()
            try:
                # python3 compatibility code
                line = line.decode()
            except (AttributeError, UnicodeDecodeError):
                pass
            return line
        else:
            return None


class I3status(Thread):
    """
    This class is responsible for spawning i3status and reading its output.
    """
    def __init__(self, lock, i3status_config_path):
        """
        Our output will be read asynchronously from 'last_output'.
        """
        Thread.__init__(self)
        self.i3status_config_path = i3status_config_path
        self.config = self.i3status_config_reader()
        self.error = None
        self.last_output = None
        self.last_output_ts = None
        self.last_prefix = None
        self.lock = lock
        self.json_list = None
        self.json_list_ts = None

    def i3status_config_reader(self):
        """
        Parse i3status.conf so we can adapt our code to the i3status config.
        """
        in_time = False
        in_general = False
        config = {
            'colors': False,
            'color_good': '#00FF00',
            'color_bad': '#FF0000',
            'color_degraded': '#FFFF00',
            'color_separator': '#333333',
            'interval': 5,
            'output_format': None,
            'time_format': '%Y-%m-%d %H:%M:%S',
        }

        # some ugly parsing
        for line in open(self.i3status_config_path, 'r'):
            line = line.strip(' \t\n\r')
            if line.startswith('general'):
                in_general = True
            elif line.startswith('time') or line.startswith('tztime'):
                in_time = True
            elif line.startswith('}'):
                in_general = False
                in_time = False
            if in_general and '=' in line:
                key = line.split('=')[0].strip()
                value = line.split('=')[1].strip()
                if key in config:
                    if value in ['true', 'false']:
                        value = 'True' if value == 'true' else 'False'
                    try:
                        config[key] = eval(value)
                    except NameError:
                        config[key] = value
            if in_time and '=' in line:
                key = line.split('=')[0].strip()
                value = line.split('=')[1].strip()
                if 'time_' + key in config:
                    config['time_' + key] = eval(value)

        # py3status uses only the i3bar protocol
        assert config['output_format'] == 'i3bar', \
            'i3status output_format should be set to "i3bar" on {}'.format(
                self.i3status_config_path
            )

        return config

    def adjust_time(self, delta):
        """
        Adjust the 'time' object so that it's updated at interval seconds
        """
        json_list = deepcopy(self.json_list)
        try:
            time_format = self.config['time_format']
            for item in json_list:
                if item['name'] in ['time', 'tztime']:
                    i3status_time = item['full_text']
                    # add mendatory items in i3status time format wrt issue #18
                    for fmt in ['%Y', '%m', '%d']:
                        if not fmt in time_format:
                            time_format = '{} {}'.format(time_format, fmt)
                            i3status_time = '{} {}'.format(
                                i3status_time, datetime.now().strftime(fmt)
                            )
                    date = datetime.strptime(i3status_time, time_format)
                    date += delta
                    item['full_text'] = date.strftime(
                        self.config['time_format']
                    )
                    item['transformed'] = True
        except Exception:
            err = sys.exc_info()[1]
            syslog(LOG_ERR, "i3status adjust_time failed ({})".format(err))
        return json_list

    def update_json_list(self):
        """
        Copy the last json list output from i3status so that any module
        can modify it without altering the original output.
        This is done so that any module's alteration of a i3status output json
        will not be overwritten when the next i3status output gets polled.
        """
        self.json_list = deepcopy(self.last_output)
        self.json_list_ts = deepcopy(self.last_output_ts)

    def run(self):
        """
        Spawn i3status and poll its output.
        """
        i3status_pipe = Popen(
            ['i3status', '-c', self.i3status_config_path],
            stdout=PIPE,
            stderr=PIPE,
        )
        self.poller_inp = IOPoller(i3status_pipe.stdout)
        self.poller_err = IOPoller(i3status_pipe.stderr)

        try:
            # at first, poll very quickly to avoid delay in first i3bar display
            timeout = 0.001

            # loop on i3status output
            while self.lock.is_set():
                line = self.poller_inp.readline(timeout)
                if line:
                    if line.startswith('[{'):
                        with jsonify(line) as (prefix, json_list):
                            self.last_output = json_list
                            self.last_output_ts = datetime.utcnow()
                            self.last_prefix = ','
                            self.update_json_list()
                        print_line(line)
                    elif not line.startswith(','):
                        if 'version' in line:
                            header = loads(line)
                            header.update({'click_events': True})
                            line = dumps(header)
                        print_line(line)
                    else:
                        timeout = 0.5
                        with jsonify(line) as (prefix, json_list):
                            self.last_output = json_list
                            self.last_output_ts = datetime.utcnow()
                            self.last_prefix = prefix
                else:
                    err = self.poller_err.readline(timeout)
                    code = i3status_pipe.poll()
                    if code is not None:
                        if err:
                            msg = 'i3status died and said: {}'.format(err)
                        else:
                            msg = 'i3status died with code {}'.format(code)
                        raise IOError(msg)
                    else:
                        # poll is CPU intensive, breath a bit
                        sleep(timeout)
        except IOError:
            err = sys.exc_info()[1]
            self.error = err


class Events(Thread):
    """
    This class is responsible for dispatching event JSONs sent by the i3bar.
    """
    def __init__(self, lock, config, modules):
        """
        We need to poll stdin to receive i3bar messages.
        """
        Thread.__init__(self)
        self.config = config
        self.lock = lock
        self.modules = modules
        self.poller_inp = IOPoller(sys.stdin)

    def dispatch(self, module, obj, event):
        """
        Dispatch the event or enforce the default clear cache action.
        """
        if module.click_events:
            # module accepts click_events, use it
            module.click_event(event)
            if self.config['debug']:
                syslog(LOG_INFO, 'dispatching event {}'.format(event))
        else:
            # default button 2 action is to clear this method's cache
            obj['cached_until'] = time()
            if self.config['debug']:
                syslog(LOG_INFO, 'dispatching default event {}'.format(event))

    def i3bar_click_events_module(self):
        """
        Detect the presence of the special i3bar_click_events.py module.

        When py3status detects a module named 'i3bar_click_events.py',
        it will dispatch i3status click events to this module so you can catch
        them and trigger any function call based on the event.
        """
        for module in self.modules:
            if not module.click_events:
                continue
            if module.module_name == 'i3bar_click_events.py':
                return module
        else:
            return False

    def run(self):
        """
        Wait for an i3bar JSON event, then find the right module to dispatch
        the message to based on the 'name' and 'instance' of the event.

        In case the module does NOT support click_events, the default
        implementation is to clear the module's cache
        when the MIDDLE button (2) is pressed on it.

        Example event:
        {'y': 13, 'x': 1737, 'button': 1, 'name': 'empty', 'instance': 'first'}
        """
        while self.lock.is_set():
            event = self.poller_inp.readline()
            if not event:
                sleep(0.20)
                continue
            try:
                with jsonify(event) as (prefix, event):
                    if self.config['debug']:
                        syslog(LOG_INFO, 'received event {}'.format(event))

                    # setup default action on button 2 press
                    default_event = False
                    dispatched = False
                    if 'button' in event and event['button'] == 2:
                        default_event = True

                    for module in self.modules:
                        # skip modules not supporting click_events
                        # unless we have a default_event set
                        if not module.click_events and not default_event:
                            continue

                        # check for the method name/instance
                        for obj in module.methods.values():
                            if event['name'] == obj['name']:
                                if 'instance' in event:
                                    if event['instance'] == obj['instance']:
                                        self.dispatch(module, obj, event)
                                        dispatched = True
                                        break
                                else:
                                    self.dispatch(module, obj, event)
                                    dispatched = True
                                    break

                    # fall back to i3bar_click_events.py module if present
                    if not dispatched:
                        module = self.i3bar_click_events_module()
                        if module:
                            if self.config['debug']:
                                syslog(
                                    LOG_INFO,
                                    'dispatching event to i3bar_click_events'
                                )
                            self.dispatch(module, obj, event)
            except Exception:
                err = sys.exc_info()[1]
                syslog(LOG_WARNING, 'event failed ({})'.format(err))


class Module(Thread):
    """
    This class represents a user module (imported file).
    It is reponsible for executing it every given interval and
    caching its output based on user will.
    """
    def __init__(self, lock, config, include_path, f_name, i3_thread):
        """
        We need quite some stuff to occupy ourselves don't we ?
        """
        Thread.__init__(self)
        self.click_events = False
        self.config = config
        self.has_kill = False
        self.i3status_thread = i3_thread
        self.last_output = []
        self.lock = lock
        self.methods = {}
        self.module_class = None
        self.module_name = f_name
        #
        self.load_methods(include_path, f_name)

    @staticmethod
    def load_from_file(filepath):
        """
        Return user-written class object from given path.
        """
        inst = None
        expected_class = 'Py3status'
        mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
        if file_ext.lower() == '.py':
            py_mod = imp.load_source(mod_name, filepath)
            if hasattr(py_mod, expected_class):
                inst = py_mod.Py3status()
        return (mod_name, inst)

    def clear_cache(self):
        """
        Reset the cache for all methods of this module.
        """
        for meth in self.methods:
            self.methods[meth]['cached_until'] = time()
            if self.config['debug']:
                syslog(LOG_INFO, 'clearing cache for method {}'.format(meth))

    def load_methods(self, include_path, f_name):
        """
        Read the given user-written py3status class file and store its methods.
        Those methods will be executed, so we will deliberately ignore:
            - private methods starting with _
            - decorated methods such as @property or @staticmethod
            - 'on_click' methods as they'll be called upon a click_event
            - 'kill' methods as they'll be called upon this thread's exit
        """
        module, class_inst = self.load_from_file(include_path + f_name)
        if module and class_inst:
            self.module_class = class_inst
            for method in sorted(dir(class_inst)):
                if method.startswith('_'):
                    continue
                else:
                    m_type = type(getattr(class_inst, method))
                    if 'method' in str(m_type):
                        if method == 'on_click':
                            self.click_events = True
                        elif method == 'kill':
                            self.has_kill = True
                        else:
                            # the method_obj stores infos about each method
                            # of this module.
                            method_obj = {
                                'cached_until': time(),
                                'instance': None,
                                'last_output': {
                                    'name': method,
                                    'full_text': ''
                                },
                                'method': method,
                                'name': None,
                                'position': 0
                            }
                            self.methods[method] = method_obj

        # done, syslog some debug info
        if self.config['debug']:
            syslog(
                LOG_INFO,
                'module {} click_events={} has_kill={} methods={}'.format(
                    self.module_name,
                    self.click_events,
                    self.has_kill,
                    self.methods.keys()
                )
            )

    def click_event(self, event):
        """
        Execute the 'on_click' method of this module with the given event.
        """
        try:
            click_method = getattr(self.module_class, 'on_click')
            click_method(
                self.i3status_thread.json_list,
                self.i3status_thread.config,
                event
            )
        except Exception:
            err = sys.exc_info()[1]
            msg = 'on_click failed with ({}) for event ({})'.format(err, event)
            syslog(LOG_WARNING, msg)

    def run(self):
        """
        On a timely fashion, execute every method found for this module.
        We will respect and set a cache timeout for each method if the user
        didn't already do so.
        We will execute the 'kill' method of the module when we terminate.
        """
        while self.lock.is_set():
            # execute each method of this module
            for meth, obj in self.methods.items():
                my_method = self.methods[meth]

                # always check the lock
                if not self.lock.is_set():
                    break

                # respect the cache set for this method
                if time() < obj['cached_until']:
                    continue

                try:
                    # execute method and get its output
                    method = getattr(self.module_class, meth)
                    position, result = method(
                        self.i3status_thread.json_list,
                        self.i3status_thread.config
                    )

                    # validate the result
                    assert isinstance(result, dict), "should return a dict"
                    assert 'full_text' in result, "missing 'full_text' key"
                    assert 'name' in result, "missing 'name' key"

                    # validate the position
                    assert isinstance(position, int), "position is not an int"

                    # initialize method object
                    if my_method['name'] is None:
                        my_method['name'] = result['name']
                        if 'instance' in result:
                            my_method['instance'] = result['instance']
                        else:
                            my_method['instance'] = result['name']

                    # update method object cache
                    if 'cached_until' in result:
                        cached_until = result['cached_until']
                    else:
                        cached_until = time() + self.config['cache_timeout']
                    my_method['cached_until'] = cached_until

                    # update method object output
                    my_method['last_output'] = result

                    # update method object position
                    my_method['position'] = position

                    # debug info
                    if self.config['debug']:
                        syslog(
                            LOG_INFO,
                            'method {} returned {}'.format(meth, result)
                        )
                except Exception:
                    err = sys.exc_info()[1]
                    syslog(
                        LOG_WARNING,
                        'user method {} failed ({})'.format(meth, err)
                    )

            # don't be hasty mate, let's take it easy for now
            sleep(self.config['interval'])

        # check and execute the 'kill' method if present
        if self.has_kill:
            try:
                kill_method = getattr(self.module_class, 'kill')
                kill_method(
                    self.i3status_thread.json_list,
                    self.i3status_thread.config
                )
            except Exception:
                # this would be stupid to die on exit
                pass


class Py3statusWrapper():
    """
    This is the py3status wrapper.
    """
    def __init__(self):
        """
        Useful variables we'll need.
        """
        self.modules = []
        self.lock = Event()

    def get_config(self):
        """
        Create the py3status based on command line options we received.
        """
        # defaults
        config = {
            'cache_timeout': 60,
            'i3status_config_path': '/etc/i3status.conf',
            'include_paths': ['.i3/py3status/'],
            'interval': 1
        }

        # command line options
        parser = argparse.ArgumentParser(
            description='The agile, python-powered, i3status wrapper')
        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument('-c', action="store",
                            dest="i3status_conf",
                            type=str,
                            default=config['i3status_config_path'],
                            help="path to i3status config file")
        parser.add_argument('--debug', action="store_true",
                            help="be verbose in syslog")
        parser.add_argument('-i', action="append",
                            dest="include_paths",
                            help="""include user-written modules from those
                            directories (default .i3/py3status)""")
        parser.add_argument('-n', action="store",
                            dest="interval",
                            type=float,
                            default=config['interval'],
                            help="update interval in seconds (default 1 sec)")
        parser.add_argument('-t', action="store",
                            dest="cache_timeout",
                            type=int,
                            default=config['cache_timeout'],
                            help="""default injection cache timeout in seconds
                            (default 60 sec)""")
        options = parser.parse_args()

        # override configuration and helper variables
        config['cache_timeout'] = options.cache_timeout
        config['debug'] = options.debug
        config['i3status_config_path'] = options.i3status_conf
        if options.include_paths:
            config['include_paths'] = options.include_paths
        config['interval'] = options.interval

        # all done
        return config

    def list_modules(self):
        """
        Search import directories and files through given include paths.
        This method is a generator and loves to yield.
        """
        for include_path in sorted(self.config['include_paths']):
            include_path = os.path.abspath(include_path) + '/'
            if os.path.isdir(include_path):
                for f_name in sorted(os.listdir(include_path)):
                    if f_name.endswith('.py'):
                        yield (include_path, f_name)

    def setup(self):
        """
        Setup py3status and spawn i3status/events/modules threads.
        """
        # set the Event lock
        self.lock.set()

        # setup configuration
        self.config = self.get_config()

        # setup i3status thread
        self.i3status_thread = I3status(
            self.lock,
            self.config['i3status_config_path']
        )
        self.i3status_thread.start()
        if self.config['debug']:
            syslog(
                LOG_INFO,
                'i3status thread started with config {}'.format(
                    self.i3status_thread.config
                )
            )
        while not self.i3status_thread.last_output:
            if not self.i3status_thread.is_alive():
                err = self.i3status_thread.error
                raise IOError(err)
            sleep(0.1)

        # setup input events thread
        self.events_thread = Events(self.lock, self.config, self.modules)
        self.events_thread.start()
        if self.config['debug']:
            syslog(LOG_INFO, 'events thread started')

        # suppress modules' ouput wrt issue #20
        sys.stdout = open('/dev/null', 'w')
        sys.stderr = open('/dev/null', 'w')

        # load and spawn modules threads
        for include_path, f_name in self.list_modules():
            try:
                my_m = Module(
                    self.lock,
                    self.config,
                    include_path,
                    f_name,
                    self.i3status_thread
                )
                # only start and handle modules with available methods
                if my_m.methods:
                    my_m.start()
                    self.modules.append(my_m)
                elif self.config['debug']:
                    syslog(
                        LOG_INFO,
                        'ignoring {} (no methods found)'.format(f_name)
                    )
            except Exception:
                err = sys.exc_info()[1]
                msg = 'loading {} failed ({})'.format(f_name, err)
                self.i3_nagbar(msg, level='warning')

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
            call(
                ['i3-nagbar', '-m', msg, '-t', level],
                stdout=open('/dev/null', 'w'),
                stderr=open('/dev/null', 'w')
            )
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
        except:
            pass

    def sig_handler(self, signum, frame):
        """
        Raise a Warning level exception when a user sends a SIGUSR1 signal.
        """
        raise UserWarning("received USR1, forcing refresh")

    def clear_modules_cache(self):
        """
        For every module, reset the 'cached_until' of all its methods.
        """
        for module in self.modules:
            module.clear_cache()

    def get_modules_output(self, json_list):
        """
        Iterate over user modules and their output. Return the list ordered
        as the user asked.
        If two modules specify the same output index/position, the sorting will
        be alphabetical.
        """
        # prepopulate the list so that every usable index exists, thx @Lujeni
        m_list = [
            '' for value in range(sum([len(x.methods) for x in self.modules]))
        ]
        # append i3status json list to the modules' list
        m_list += json_list
        # run through modules/methods output and insert them in reverse order
        for m in reversed(self.modules):
            for meth in m.methods:
                position = m.methods[meth]['position']
                last_output = m.methods[meth]['last_output']
                try:
                    if m_list[position] == '':
                        m_list[position] = last_output
                    else:
                        if '' in m_list:
                            m_list.remove('')
                        m_list.insert(position, last_output)
                except IndexError:
                    # out of range indexes get placed at the end of the output
                    m_list.append(last_output)
        # cleanup and return output list
        m_list = list(filter(lambda a: a != '', m_list))
        return m_list

    def run(self):
        """
        Main py3status loop, continuously read from i3status and modules
        and output it to i3bar for displaying.
        """
        # SIGUSR1 forces a refresh of the bar both for py3status and i3status,
        # this mimics the USR1 signal handling of i3status (see man i3status)
        signal(SIGUSR1, self.sig_handler)

        # main loop
        while True:
            try:
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
                json_list = self.i3status_thread.json_list

                # transform output from i3status
                delta = datetime.utcnow() - self.i3status_thread.json_list_ts
                if delta.seconds > 0:
                    json_list = self.i3status_thread.adjust_time(delta)

                # check that every module thread is alive
                for module in self.modules:
                    if not module.is_alive():
                        # don't spam the user with i3-nagbar warnings
                        if not hasattr(module, 'i3_nagbar'):
                            module.i3_nagbar = True
                            msg = 'output frozen for dead module(s) {}'.format(
                                ','.join(module.methods.keys())
                            )
                            self.i3_nagbar(msg, level='warning')

                # construct the global output, modules first
                if self.modules:
                    json_list = self.get_modules_output(json_list)

                # dump the line to stdout
                print_line('{}{}'.format(prefix, dumps(json_list)))

                # update i3status output
                self.i3status_thread.update_json_list()

                # sleep a bit before doing this again
                sleep(self.config['interval'])
            except UserWarning:
                # SIGUSR1 was received, we also force i3status to refresh by
                # sending it a SIGUSR1 as well then we refresh the bar asap
                err = sys.exc_info()[1]
                syslog(LOG_INFO, str(err))
                try:
                    call(["killall", "-s", "USR1", "i3status"])
                    self.clear_modules_cache()
                except Exception:
                    err = sys.exc_info()[1]
                    self.i3_nagbar('SIGUSR1 ({})'.format(err), level='warning')


def main():
    try:
        locale.setlocale(locale.LC_ALL, '')
        py3 = Py3statusWrapper()
        py3.setup()
    except KeyboardInterrupt:
        err = sys.exc_info()[1]
        py3.i3_nagbar('setup interrupted (KeyboardInterrupt)')
        sys.exit(0)
    except Exception:
        err = sys.exc_info()[1]
        py3.i3_nagbar('setup error ({})'.format(err))
        py3.stop()
        sys.exit(2)

    try:
        py3.run()
    except Exception:
        err = sys.exc_info()[1]
        py3.i3_nagbar('runtime error ({})'.format(err))
        sys.exit(3)
    except KeyboardInterrupt:
        pass
    finally:
        py3.stop()
        sys.exit(0)


if __name__ == '__main__':
    main()
