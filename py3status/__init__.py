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
from signal import SIGTERM, SIGUSR1
from subprocess import Popen
from subprocess import PIPE
from subprocess import call
from tempfile import NamedTemporaryFile
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
    def __init__(self, lock, i3status_config_path, standalone):
        """
        Our output will be read asynchronously from 'last_output'.
        """
        Thread.__init__(self)
        self.error = None
        self.i3status_module_names = [
            'battery',
            'cpu_temperature',
            'cpu_usage',
            'ddate',
            'disk',
            'ethernet',
            'ipv6',
            'load',
            'path_exists',
            'run_watch',
            'time',
            'tztime',
            'volume',
            'wireless'
        ]
        self.json_list = None
        self.json_list_ts = None
        self.last_output = None
        self.last_output_ts = None
        self.last_prefix = None
        self.lock = lock
        self.standalone = standalone
        self.time_format = '%Y-%m-%d %H:%M:%S'
        self.tmpfile_path = None
        #
        self.config = self.i3status_config_reader(i3status_config_path)

    def valid_config_param(self, param_name):
        """
        Check if a given section name is a valid parameter for i3status.
        """
        valid_config_params = self.i3status_module_names + ['general', 'order']
        return param_name.split(' ')[0] in valid_config_params

    @staticmethod
    def eval_config_parameter(param):
        """
        Try to evaluate the given parameter as a string or integer and return
        it properly. This is used to parse i3status configuration parameters
        such as 'disk "/home" {}' or worse like '"cpu_temperature" 0 {}'.
        """
        params = param.split(' ')
        result_list = list()

        for p in params:
            try:
                e_value = eval(p)
                if isinstance(e_value, str) or isinstance(e_value, int):
                    p = str(e_value)
                else:
                    raise ValueError()
            except (NameError, SyntaxError, ValueError):
                pass
            finally:
                result_list.append(p)

        return ' '.join(result_list)

    @staticmethod
    def eval_config_value(value):
        """
        Try to evaluate the given parameter as a string or integer and return
        it properly. This is used to parse i3status configuration parameters
        such as 'disk "/home" {}' or worse like '"cpu_temperature" 0 {}'.
        """
        try:
            e_value = eval(value)
            if isinstance(e_value, str) or isinstance(e_value, int):
                value = e_value
            else:
                raise ValueError()
        except (NameError, ValueError):
            pass
        finally:
            return value

    def i3status_config_reader(self, i3status_config_path):
        """
        Parse i3status.conf so we can adapt our code to the i3status config.
        """
        config = {
            'general': {
                'color_bad': '#FF0000',
                'color_degraded': '#FFFF00',
                'color_good': '#00FF00',
                'color_separator': '#333333',
                'colors': False,
                'interval': 5,
                'output_format': 'i3bar'
            },
            'i3s_modules': [],
            'on_click': {},
            'order': [],
            'py3_modules': []
        }

        # some ugly parsing
        in_section = False
        section_name = ''

        for line in open(i3status_config_path, 'r'):
            line = line.strip(' \t\n\r')

            if not line or line.startswith('#'):
                continue

            if line.startswith('order'):
                in_section = True
                section_name = 'order'

            if not in_section:
                section_name = line.split('{')[0].strip()
                section_name = self.eval_config_parameter(section_name)
                if not section_name:
                    continue
                else:
                    in_section = True
                    if section_name not in config:
                        config[section_name] = {}

            if '{' in line:
                in_section = True

            if section_name and '=' in line:
                section_line = line

                # one liner cases
                if line.endswith('}'):
                    section_line = section_line.split('}', -1)[0].strip()
                if line.startswith(section_name + ' {'):
                    section_line = section_line.split(
                        section_name + ' {'
                    )[1].strip()

                key = section_line.split('=')[0].strip()
                key = self.eval_config_parameter(key)

                value = section_line.split('=')[1].strip()
                value = self.eval_config_value(value)

                if section_name == 'order':
                    config[section_name].append(value)
                    line = '}'

                    # detect internal modules to be loaded dynamically
                    if not self.valid_config_param(value):
                        config['py3_modules'].append(value)
                    else:
                        config['i3s_modules'].append(value)
                else:
                    if not key.startswith('on_click'):
                        config[section_name][key] = value
                    else:
                        # on_click special parameters
                        try:
                            button = int(key.split()[1])
                            if button not in range(1, 6):
                                raise ValueError(
                                    'should be 1, 2, 3, 4 or 5'
                                )
                        except IndexError as e:
                            raise IndexError(
                                'missing "button id" for "on_click" '
                                'parameter in section {}'.format(section_name)
                            )
                        except ValueError as e:
                            raise ValueError(
                                'invalid "button id" '
                                'for "on_click" parameter '
                                'in section {} ({})'.format(section_name, e)
                            )
                        on_c = config['on_click']
                        on_c[section_name] = on_c.get(section_name, {})
                        on_c[section_name][button] = value

                    # override time format
                    if section_name.split(' ')[0] in ['time', 'tztime'] and key == 'format':
                        self.time_format = value

            if line.endswith('}'):
                in_section = False
                section_name = ''

        # py3status only uses the i3bar protocol because it needs JSON output
        if config['general']['output_format'] != 'i3bar':
            raise RuntimeError(
                'i3status output_format should be set' +
                ' to "i3bar" on {}'.format(
                    i3status_config_path,
                    ' or on your own {}/.i3status.conf'.format(
                        os.path.expanduser('~')
                    )
                    if i3status_config_path == '/etc/i3status.conf'
                    else ''
                )
            )

        return config

    def adjust_time(self, delta):
        """
        Adjust the 'time' object so that it's updated at interval seconds
        """
        json_list = deepcopy(self.json_list)
        try:
            time_format = self.time_format
            for item in json_list:
                if 'name' in item and item['name'] in ['time', 'tztime']:
                    i3status_time = item['full_text'].encode('UTF-8', 'replace')
                    try:
                        # python3 compatibility code
                        i3status_time = i3status_time.decode()
                    except:
                        pass
                    # add mendatory items in i3status time format wrt issue #18
                    for fmt in ['%Y', '%m', '%d']:
                        if not fmt in time_format:
                            time_format = '{} {}'.format(time_format, fmt)
                            i3status_time = '{} {}'.format(
                                i3status_time, datetime.now().strftime(fmt)
                            )
                    date = datetime.strptime(i3status_time, time_format)
                    date += delta
                    item['full_text'] = date.strftime(self.time_format)
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

    def get_modules_output(self, json_list, py3_modules):
        """
        Return the final json list to be displayed on the i3bar by taking
        into account every py3status configured module and i3status'.
        Simply put, this method honors the initial 'order' configured by
        the user in his i3status.conf.
        """
        ordered = []
        for module in self.config['order']:
            if module in py3_modules:
                for method in py3_modules[module].methods.values():
                    ordered.append(method['last_output'])
            else:
                for m, j in zip(self.config['i3s_modules'], json_list):
                    if m == module:
                        ordered.append(j)
        return ordered

    @staticmethod
    def write_in_tmpfile(text, tmpfile):
        """
        Write the given text in the given tmpfile in python2 and python3.
        """
        try:
            tmpfile.write(text)
        except TypeError:
            tmpfile.write(str.encode(text))

    def write_tmp_i3status_config(self, tmpfile):
        """
        Given a temporary file descriptor, write a valid i3status config file
        based on the parsed one from 'i3status_config_path'.
        """
        for section_name, conf in self.config.items():
            if section_name in ['i3s_modules', 'py3_modules']:
                continue
            elif section_name == 'order':
                for module_name in conf:
                    if self.valid_config_param(module_name):
                        self.write_in_tmpfile(
                            'order += "%s"\n' % module_name,
                            tmpfile
                        )
                self.write_in_tmpfile('\n', tmpfile)
            elif self.valid_config_param(section_name):
                self.write_in_tmpfile('%s {\n' % section_name, tmpfile)
                for key, value in conf.items():
                    self.write_in_tmpfile(
                        '    %s = "%s"\n' % (key, value),
                        tmpfile
                    )
                self.write_in_tmpfile('}\n\n', tmpfile)
        tmpfile.flush()

    def run(self):
        """
        Spawn i3status using a self generated config file and poll its output.
        """
        try:
            with NamedTemporaryFile(prefix='py3status_') as tmpfile:
                self.write_tmp_i3status_config(tmpfile)
                syslog(
                    LOG_INFO,
                    'i3status spawned using config file {}'.format(
                        tmpfile.name
                    )
                )

                i3status_pipe = Popen(
                    ['i3status', '-c', tmpfile.name],
                    stdout=PIPE,
                    stderr=PIPE,
                )
                self.poller_inp = IOPoller(i3status_pipe.stdout)
                self.poller_err = IOPoller(i3status_pipe.stderr)
                self.tmpfile_path = tmpfile.name

                try:
                    # at first, poll very quickly
                    # to avoid delay in first i3bar display
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
                                msg = 'i3status died'
                                if err:
                                    msg += ' and said: {}'.format(err)
                                else:
                                    msg += ' with code {}'.format(code)
                                raise IOError(msg)
                            else:
                                # poll is CPU intensive, breath a bit
                                sleep(timeout)
                except IOError:
                    err = sys.exc_info()[1]
                    self.error = err
        except OSError:
            # we cleanup the tmpfile ourselves so when the delete will occur
            # it will usually raise an OSError: No such file or directory
            pass

    def cleanup_tmpfile(self):
        """
        Cleanup i3status tmp configuration file.
        """
        if os.path.isfile(self.tmpfile_path):
            os.remove(self.tmpfile_path)

    def mock(self):
        """
        Mock i3status behavior, used in standalone mode.
        """
        # mock thread is_alive() method
        self.is_alive = lambda: True

        # mock i3status base output
        init_output = [
            '{"click_events": true, "version": 1}',
            '[',
            '[]'
        ]
        for line in init_output:
            print_line(line)

        # mock i3status output parsing
        self.last_output = []
        self.last_output_ts = datetime.utcnow()
        self.last_prefix = ','
        self.update_json_list()


class Events(Thread):
    """
    This class is responsible for dispatching event JSONs sent by the i3bar.
    """
    def __init__(self, lock, config, modules, i3s_config):
        """
        We need to poll stdin to receive i3bar messages.
        """
        Thread.__init__(self)
        self.config = config
        self.i3s_config = i3s_config
        self.last_refresh_ts = time()
        self.lock = lock
        self.modules = modules
        self.on_click = i3s_config['on_click']
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
        for module in self.modules.values():
            if not module.click_events:
                continue
            if module.module_name == 'i3bar_click_events.py':
                return module
        else:
            return False

    def refresh(self, module_name):
        """
        Force a cache expiration for all the methods of the given module.

        We rate limit the i3status refresh to 1/s for obvious abusive behavior.
        """
        module = self.modules.get(module_name)
        if module is not None:
            if self.config['debug']:
                syslog(LOG_INFO, 'refresh module {}'.format(module_name))
            for obj in module.methods.values():
                obj['cached_until'] = time()
        else:
            if time() > (self.last_refresh_ts + 1):
                if self.config['debug']:
                    syslog(
                        LOG_INFO,
                        'refresh i3status for module {}'.format(module_name)
                    )
                call(['killall', '-s', 'USR1', 'i3status'])
                self.last_refresh_ts = time()

    def refresh_all(self, module_name):
        """
        Force a full refresh of py3status and i3status modules by sending
        a SIGUSR1 signal to py3status.

        We rate limit this command to 1/s for obvious abusive behavior.
        """
        if time() > (self.last_refresh_ts + 1):
            call(['killall', '-s', 'USR1', 'py3status'])
            self.last_refresh_ts = time()

    def on_click_dispatcher(self, module_name, command):
        """
        Dispatch on_click config parameters to either:
            - Our own methods for special py3status commands (listed below)
            - The i3-msg program which is part of i3wm
        """
        py3_commands = ['refresh', 'refresh_all']
        if command is None:
            return
        elif command in py3_commands:
            # this is a py3status command handled by this class
            method = getattr(self, command)
            method(module_name)
        else:
            # this is a i3 message
            self.i3_msg(module_name, command)

            # to make the bar more responsive to users we ask for a refresh
            # of the module or of i3status if the module is an i3status one
            self.refresh(module_name)

    @staticmethod
    def i3_msg(module_name, command):
        """
        Execute the given i3 message and log its output.
        """
        i3_msg_pipe = Popen(['i3-msg', command], stdout=PIPE)
        syslog(
            LOG_INFO,
            'i3-msg module="{}" command="{}" stdout={}'.format(
                module_name,
                command,
                i3_msg_pipe.stdout.read()
            )
        )

    def i3status_mod_guess(self, instance, name):
        """
        Some i3status modules output a name and instance that are different
        from the configuration parameters in i3status.conf.

        For example the 'disk' module will output with name 'disk_info' so
        we try to be clever and figure it out here, case by case.
        """
        try:
            # disk_info /home
            if name == 'disk_info':
                name = 'disk'

            # /sys/class/power_supply/BAT0/uevent
            elif name == 'battery':
                instance = str([int(s) for s in instance if s.isdigit()][0])

            # /sys/devices/platform/coretemp.0/temp1_input
            elif name == 'cpu_temperature':
                instance = str([int(s) for s in instance if s.isdigit()][0])

            # run_watch /var/run/openvpn.pid
            elif name == 'run_watch':
                for k, v in self.i3s_config.items():
                    if (
                        k.startswith('run_watch')
                        and isinstance(v, dict)
                        and v.get('pidfile') == instance
                    ):
                        instance = k.split(' ', 1)[1]
                        break

            # volume default.Master.0
            elif name == 'volume':
                device, mixer, mixer_idx = instance.split('.')
                for k, v in self.i3s_config.items():
                    if (
                        k.startswith('volume')
                        and isinstance(v, dict)
                        and v.get('device') == device
                        and v.get('mixer') == mixer
                        and str(v.get('mixer_idx')) == mixer_idx
                    ):
                        instance = k.split(' ', 1)[1]
                        break
                else:
                    instance = 'master'
        except:
            pass
        finally:
            return (instance, name)

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

                    # usage variables
                    button = event.get('button', 0)
                    default_event = False
                    dispatched = False
                    instance = event.get('instance', '')
                    name = event.get('name', '')

                    # i3status module name guess
                    instance, name = self.i3status_mod_guess(instance, name)
                    if self.config['debug']:
                        syslog(
                            LOG_INFO,
                            'trying to dispatch event to module "{}"'.format(
                                '{} {}'.format(name, instance).strip()
                            )
                        )

                    # guess the module config name
                    module_name = '{} {}'.format(name, instance).strip()

                    # execute any configured i3-msg command
                    if self.on_click.get(module_name, {}).get(button):
                        self.on_click_dispatcher(
                            module_name,
                            self.on_click[module_name].get(button)
                        )
                        dispatched = True
                    # otherwise setup default action on button 2 press
                    elif button == 2:
                        default_event = True

                    for module in self.modules.values():
                        # skip modules not supporting click_events
                        # unless we have a default_event set
                        if not module.click_events and not default_event:
                            continue

                        # check for the method name/instance
                        for obj in module.methods.values():
                            if name == obj['name']:
                                if instance:
                                    if instance == obj['instance']:
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
        self.module_name = f_name.rstrip('.py')
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

    @staticmethod
    def load_from_namespace(module_name):
        """
        Load a py3status bundled module.
        """
        inst = None
        name = 'py3status.modules.{}'.format(module_name.split(' ')[0])
        py_mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            py_mod = getattr(py_mod, comp)
        inst = py_mod.Py3status()
        return (module_name, inst)

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
        if include_path is not None:
            module, class_inst = self.load_from_file(include_path + f_name)
        else:
            module, class_inst = self.load_from_namespace(f_name)

        if module and class_inst:
            self.module_class = class_inst

            # apply module configuration from i3status config
            mod_config = self.i3status_thread.config.get(self.module_name, {})
            for config, value in mod_config.items():
                setattr(self.module_class, config, value)

            # get the available methods for execution
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
                self.i3status_thread.config['general'],
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
                    response = method(
                        self.i3status_thread.json_list,
                        self.i3status_thread.config['general']
                    )

                    if isinstance(response, dict):
                        # this is a shiny new module giving a dict response
                        position, result = None, response
                        result['name'] = self.module_name.split(' ')[0]
                        result['instance'] = ''.join(
                            self.module_name.split(' ')[1:]
                        )
                    else:
                        # this is an old school module reporting its position
                        position, result = response
                        if not isinstance(position, int):
                            raise TypeError('position is not an int')
                        if not isinstance(result, dict):
                            raise TypeError('response should be a dict')
                        if 'name' not in result:
                            raise KeyError('missing "name" key in response')

                    # validate the response
                    if not 'full_text' in result:
                        raise KeyError('missing "full_text" key in response')

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
                            'method {} returned {} '.format(meth, result) +
                            'for position {}'.format(position)
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
                    self.i3status_thread.config['general']
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
        self.modules = {}
        self.lock = Event()
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
            'interval': 1
        }

        # package version
        try:
            import pkg_resources
            version = pkg_resources.get_distribution('py3status').version
        except:
            version = 'unknown'
        config['version'] = version

        # command line options
        parser = argparse.ArgumentParser(
            description='The agile, python-powered, i3status wrapper')
        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument('-c', '--config', action="store",
                            dest="i3status_conf",
                            type=str,
                            help="path to i3status config file")
        parser.add_argument('-d', '--debug', action="store_true",
                            help="be verbose in syslog")
        parser.add_argument('-i', '--include', action="append",
                            dest="include_paths",
                            help="""include user-written modules from those
                            directories (default ~/.i3/py3status)""")
        parser.add_argument('-n', '--interval', action="store",
                            dest="interval",
                            type=float,
                            default=config['interval'],
                            help="update interval in seconds (default 1 sec)")
        parser.add_argument('-s', '--standalone', action="store_true",
                            help="standalone mode, do not use i3status")
        parser.add_argument('-t', '--timeout', action="store",
                            dest="cache_timeout",
                            type=int,
                            default=config['cache_timeout'],
                            help="""default injection cache timeout in seconds
                            (default 60 sec)""")
        parser.add_argument('-v', '--version', action="store_true",
                            help="""show py3status version and exit""")
        options = parser.parse_args()

        # only asked for version
        if options.version:
            from platform import python_version
            print(
                'py3status version {} (python {})'.format(
                    config['version'],
                    python_version()
                )
            )
            sys.exit(0)

        # override configuration and helper variables
        config['cache_timeout'] = options.cache_timeout
        config['debug'] = options.debug
        if options.include_paths:
            config['include_paths'] = options.include_paths
        config['interval'] = options.interval
        config['standalone'] = options.standalone

        # i3status config file path setup or default detection
        if options.i3status_conf:
            config['i3status_config_path'] = options.i3status_conf
        else:
            # find i3status default config file
            # respect i3status' file detection order wrt issue #43
            i3status_config_files = [
                '{}/.i3status.conf'.format(home_path),
                '{}/.config/i3status/config'.format(
                    os.environ.get('XDG_CONFIG_HOME', home_path)
                ),
                '/etc/i3status.conf',
                '{}/i3status/config'.format(
                    os.environ.get('XDG_CONFIG_DIRS', '/etc/xdg')
                )
            ]
            i3status_config_files = filter(
                os.path.isfile,
                i3status_config_files
            )

            # if none of the default files exists, we will default
            # to ~/.i3/i3status.conf
            config['i3status_config_path'] = (
                i3status_config_files[0] if i3status_config_files
                else '{}/.i3/i3status.conf'.format(home_path)
            )

        # all done
        return config

    def list_modules(self):
        """
        Search import directories and files through given include paths with
        respect to i3status.conf configured py3status modules.

        User provided modules take precedence over py3status generic modules
        but if none has been configured then we'll load every file present
        as this is the legacy behavior.

        This method is a generator and loves to yield.
        """
        for include_path in sorted(self.config['include_paths']):
            include_path = os.path.abspath(include_path) + '/'
            if not os.path.isdir(include_path):
                continue

            for f_name in sorted(os.listdir(include_path)):
                if f_name.endswith('.py'):
                    if self.py3_modules:
                        mod_name = f_name.rstrip('.py')
                        if mod_name in self.py3_modules:
                            yield (include_path, f_name)
                    else:
                        yield (include_path, f_name)

    def setup(self):
        """
        Setup py3status and spawn i3status/events/modules threads.
        """
        # set the Event lock
        self.lock.set()

        # setup configuration
        self.config = self.get_config()
        if self.config['debug']:
            syslog(
                LOG_INFO,
                'py3status started with config {}'.format(self.config)
            )

        # setup i3status thread
        self.i3status_thread = I3status(
            self.lock,
            self.config['i3status_config_path'],
            self.config['standalone']
        )
        if self.config['standalone']:
            self.i3status_thread.mock()
        else:
            self.i3status_thread.start()
            while not self.i3status_thread.last_output:
                if not self.i3status_thread.is_alive():
                    err = self.i3status_thread.error
                    raise IOError(err)
                sleep(0.1)
        if self.config['debug']:
            syslog(
                LOG_INFO,
                'i3status thread {} with config {}'.format(
                    'started' if not self.config['standalone'] else 'mocked',
                    self.i3status_thread.config
                )
            )

        # setup input events thread
        self.events_thread = Events(
            self.lock,
            self.config,
            self.modules,
            self.i3status_thread.config
        )
        self.events_thread.start()
        if self.config['debug']:
            syslog(LOG_INFO, 'events thread started')

        # suppress modules' ouput wrt issue #20
        if not self.config['debug']:
            sys.stdout = open('/dev/null', 'w')
            sys.stderr = open('/dev/null', 'w')

        # get the list of py3status configured modules
        self.py3_modules = self.i3status_thread.config['py3_modules']

        # load and spawn external modules threads
        # based on inclusion folder
        for include_path, f_name in self.list_modules():
            module_name = f_name.rstrip('.py')
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
                    self.modules[module_name] = my_m
                elif self.config['debug']:
                    syslog(
                        LOG_INFO,
                        'ignoring {} (no methods found)'.format(f_name)
                    )
            except Exception:
                err = sys.exc_info()[1]
                msg = 'loading {} failed ({})'.format(f_name, err)
                self.i3_nagbar(msg, level='warning')

        # load and spawn i3status.conf configured modules threads
        for module_name in self.py3_modules:
            # ignore if the user already provided this module
            if module_name in self.modules:
                continue
            try:
                my_m = Module(
                    self.lock,
                    self.config,
                    None,
                    module_name,
                    self.i3status_thread
                )
                # only start and handle modules with available methods
                if my_m.methods:
                    my_m.start()
                    self.modules[module_name] = my_m
                elif self.config['debug']:
                    syslog(
                        LOG_INFO,
                        'ignoring {} (no methods found)'.format(module_name)
                    )
            except Exception:
                err = sys.exc_info()[1]
                msg = 'loading {} failed ({})'.format(module_name, err)
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
            Popen(
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
            self.i3status_thread.cleanup_tmpfile()
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
        for module in self.modules.values():
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
            '' for value in range(
                sum([len(x.methods) for x in self.modules.values()])
                + len(json_list)
            )
        ]

        # debug the ordering matrix
        if self.config['debug']:
            syslog(
                LOG_INFO,
                'ordering matrix {}'.format(list(range(len(m_list))))
            )

        # run through modules/methods output and insert them in reverse order
        debug_msg = ''
        for m in reversed(list(self.modules.values())):
            for meth in m.methods:
                position = m.methods[meth]['position']
                last_output = m.methods[meth]['last_output']
                try:
                    assert position in range(len(m_list))
                    if m_list[position] == '':
                        m_list[position] = last_output
                    else:
                        if '' in m_list:
                            m_list.remove('')
                        m_list.insert(position, last_output)
                except (AssertionError, IndexError):
                    # out of range indexes get placed at the end of the output
                    m_list.append(last_output)
                finally:
                    # debug user module's index
                    if self.config['debug']:
                        debug_msg += '{}={} '.format(
                            meth,
                            m_list.index(last_output)
                        )

        # debug the user modules ordering
        if self.config['debug']:
            syslog(
                LOG_INFO,
                'ordering user modules positions {}'.format(debug_msg.strip())
            )

        # append i3status json list to the modules' list in empty slots
        debug_msg = ''
        for i3s_json in json_list:
            for i in range(len(m_list)):
                if m_list[i] == '':
                    m_list[i] = i3s_json
                    break
            else:
                # this should not happen !
                m_list.append(i3s_json)

            # debug i3status module's index
            if self.config['debug']:
                debug_msg += '{}={} '.format(
                    i3s_json['name'],
                    m_list.index(i3s_json)
                )

        # debug i3status modules ordering
        if self.config['debug']:
            syslog(
                LOG_INFO,
                'ordering i3status modules positions {}'.format(
                    debug_msg.strip()
                )
            )

        # cleanup and return output list, we also remove empty outputs
        m_list = list(filter(lambda a: a != '' and a['full_text'], m_list))

        # log the final ordering in debug mode
        if self.config['debug']:
            syslog(
                LOG_INFO,
                'ordering result {}'.format([m['name'] for m in m_list])
            )

        # return the ordered result
        return m_list

    def terminate(self, signum, frame):
        """
        Received request to terminate (SIGTERM), exit nicely.
        """
        raise KeyboardInterrupt()

    def run(self):
        """
        Main py3status loop, continuously read from i3status and modules
        and output it to i3bar for displaying.
        """
        # SIGUSR1 forces a refresh of the bar both for py3status and i3status,
        # this mimics the USR1 signal handling of i3status (see man i3status)
        signal(SIGUSR1, self.sig_handler)
        signal(SIGTERM, self.terminate)

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
                for module in self.modules.values():
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
                    if self.py3_modules:
                        # new style i3status configured ordering
                        json_list = self.i3status_thread.get_modules_output(
                            json_list,
                            self.modules
                        )
                    else:
                        # old style ordering
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
