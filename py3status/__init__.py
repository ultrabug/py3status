from __future__ import print_function

import argparse
import ast
import cProfile
import imp
import locale
import os
import pkgutil
import sys

from collections import OrderedDict
from contextlib import contextmanager
from copy import deepcopy
from datetime import datetime, timedelta
from json import dumps, loads
from py3status import modules as sitepkg_modules
from re import findall
from signal import signal
from signal import SIGTERM, SIGUSR1
from subprocess import Popen
from subprocess import PIPE
from subprocess import call
from tempfile import NamedTemporaryFile
from threading import Thread, Lock
from time import sleep, time
from syslog import syslog, LOG_ERR, LOG_INFO, LOG_WARNING
try:
    from setproctitle import setproctitle
    setproctitle('py3status')
except ImportError:
    pass

from py3status.io import print_line, print_stderr, sanitize_text, InputReader


# Used in development
enable_profiling = False


def profile(thread_run_fn):
    if not enable_profiling:
        return thread_run_fn

    def wrapper_run(self):
        """Wrap the Thread.run() method
        """
        profiler = cProfile.Profile()
        try:
            return profiler.runcall(thread_run_fn, self)
        finally:
            thread_id = getattr(self, 'ident', 'core')
            profiler.dump_stats("py3status-%s.profile" % thread_id)

    return wrapper_run


@contextmanager
def jsonify(string):
    """
    Transform the given string to a JSON in a context manager fashion.
    """
    prefix = ''
    if string.startswith(','):
        prefix, string = ',', string[1:]
    yield (prefix, loads(string))


class I3Status(Thread):
    """
    This class is responsible for spawning i3status and reading its output.
    """

    def __init__(self, exit_lock, i3status_config_path, standalone):
        """
        Our output will be read asynchronously from 'last_output'.
        """
        Thread.__init__(self)
        self.error = None
        self.i3status_module_names = [
            'battery', 'cpu_temperature', 'cpu_usage', 'ddate', 'disk',
            'ethernet', 'ipv6', 'load', 'path_exists', 'run_watch', 'time',
            'tztime', 'volume', 'wireless'
        ]
        self.json_list = None
        self.json_list_ts = None
        self.last_output = None
        self.last_output_ts = None
        self.last_prefix = None
        self.exit_lock = exit_lock
        self.ready = False
        self.standalone = standalone
        self.tmpfile_path = None
        #
        self.config = self.i3status_config_reader(i3status_config_path)

    def valid_config_param(self, param_name, cleanup=False):
        """
        Check if a given section name is a valid parameter for i3status.
        """
        if cleanup:
            valid_config_params = [
                _
                for _ in self.i3status_module_names
                if _ not in ['cpu_usage', 'ddate', 'ipv6', 'load', 'time']
            ]
        else:
            valid_config_params = self.i3status_module_names + [
                'general', 'order'
            ]
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
        if value.lower() in ('true', 'false'):
            return eval(value.title())
        try:
            e_value = eval(value)
            if isinstance(e_value, str):
                if e_value.lower() in ('true', 'false'):
                    value = eval(e_value.title())
                else:
                    value = e_value
            elif isinstance(e_value, int):
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
                    section_line = section_line.split(section_name + ' {')[
                        1].strip()

                key = section_line.split('=', 1)[0].strip()
                key = self.eval_config_parameter(key)

                value = section_line.split('=', 1)[1].strip()
                value = self.eval_config_value(value)

                if section_name == 'order':
                    config[section_name].append(value)
                    line = '}'

                    # create an empty config for this module
                    if value not in config:
                        config[value] = {}

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
                                raise ValueError('should be 1, 2, 3, 4 or 5')
                        except IndexError as e:
                            raise IndexError(
                                'missing "button id" for "on_click" '
                                'parameter in section {}'.format(section_name))
                        except ValueError as e:
                            raise ValueError('invalid "button id" '
                                             'for "on_click" parameter '
                                             'in section {} ({})'.format(
                                                 section_name, e))
                        on_c = config['on_click']
                        on_c[section_name] = on_c.get(section_name, {})
                        on_c[section_name][button] = value

            if line.endswith('}'):
                in_section = False
                section_name = ''

        # py3status only uses the i3bar protocol because it needs JSON output
        if config['general']['output_format'] != 'i3bar':
            raise RuntimeError('i3status output_format should be set' +
                               ' to "i3bar" on {}'.format(
                                   i3status_config_path,
                                   ' or on your own {}/.i3status.conf'.format(
                                       os.path.expanduser(
                                           '~')) if i3status_config_path ==
                                   '/etc/i3status.conf' else ''))

        # cleanup unconfigured i3status modules that have no default
        for module_name in deepcopy(config['order']):
            if (self.valid_config_param(module_name,
                                        cleanup=True) and
                    not config.get(module_name)):
                config.pop(module_name)
                config['i3s_modules'].remove(module_name)
                config['order'].remove(module_name)

        return config

    def set_responses(self, json_list):
        """
        Set the given i3status responses on their respective configuration.
        """
        for index, item in enumerate(self.json_list):
            conf_name = self.config['i3s_modules'][index]
            self.config[conf_name]['response'] = item

    def get_delta_from_format(self, i3s_time, time_format):
        """
        Guess the time delta from %z time formats such as +0400.

        When such a format is found, replace it in the string so we respect
        i3status' output while being able to correctly adjust the time.
        """
        try:
            if '%z' in time_format:
                res = findall('[\-+]{1}[\d]{4}', i3s_time)[0]
                if res:
                    operator = res[0]
                    hours = int(res[1:3])
                    minutes = int(res[-2:])
                    return (time_format.replace('%z', res), timedelta(
                        hours=eval('{}{}'.format(operator, hours)),
                        minutes=eval('{}{}'.format(operator, minutes))))
        except Exception:
            err = sys.exc_info()[1]
            syslog(
                LOG_ERR,
                'i3status get_delta_from_format failed "{}" "{}" ({})'.format(
                    i3s_time, time_format, err))
        return (time_format, None)

    def set_time_modules(self):
        """
        This method is executed only once after the first i3status output.

        We parse all the i3status time and tztime modules and generate
        a datetime for each of them while preserving (or defaulting) their
        configured time format.

        We also calculate a timedelta for each of them representing their
        timezone offset. This is this delta that we'll be using from now on as
        any future time or tztime update from i3status will be overwritten
        thanks to our pre-parsed date here.
        """
        default_time_format = '%Y-%m-%d %H:%M:%S'
        default_tztime_format = '%Y-%m-%d %H:%M:%S %Z'
        utcnow = self.last_output_ts
        #
        for index, item in enumerate(self.json_list):
            if item.get('name') in ['time', 'tztime']:
                conf_name = self.config['i3s_modules'][index]
                time_name = item.get('name')

                # time and tztime have different defaults
                if time_name == 'time':
                    time_format = self.config.get(
                        conf_name, {}).get('format', default_time_format)
                else:
                    time_format = self.config.get(
                        conf_name, {}).get('format', default_tztime_format)

                # handle format_time parameter
                if 'format_time' in self.config.get(conf_name, {}):
                    time_format = time_format.replace(
                        '%time', self.config[conf_name]['format_time'])

                # parse i3status date
                i3s_time = item['full_text'].encode('UTF-8', 'replace')
                try:
                    # python3 compatibility code
                    i3s_time = i3s_time.decode()
                except:
                    pass

                time_format, delta = self.get_delta_from_format(i3s_time,
                                                                time_format)

                try:
                    if '%Z' in time_format:
                        raise ValueError('%Z directive is not supported')

                    # add mendatory items in i3status time format wrt issue #18
                    time_fmt = time_format
                    for fmt in ['%Y', '%m', '%d']:
                        if fmt not in time_format:
                            time_fmt = '{} {}'.format(time_fmt, fmt)
                            i3s_time = '{} {}'.format(
                                i3s_time, datetime.now().strftime(fmt))

                    # get a datetime from the parsed string date
                    date = datetime.strptime(i3s_time, time_fmt)

                    # calculate the delta if needed
                    if not delta:
                        delta = (
                            datetime(date.year, date.month, date.day,
                                     date.hour, date.minute) - datetime(
                                         utcnow.year, utcnow.month, utcnow.day,
                                         utcnow.hour, utcnow.minute))
                except ValueError:
                    date = i3s_time
                except Exception:
                    err = sys.exc_info()[1]
                    syslog(LOG_ERR,
                           'i3status set_time_modules "{}" failed ({})'.format(
                               conf_name, err))
                    date = i3s_time
                finally:
                    self.config[conf_name]['date'] = date
                    self.config[conf_name]['delta'] = delta
                    self.config[conf_name]['time_format'] = time_format

    def tick_time_modules(self, json_list, force):
        """
        Adjust the 'time' and 'tztime' objects from the given json_list so that
        they are updated only at py3status interval seconds.

        This method is used to overwrite any i3status time or tztime output
        with respect to their parsed and timezone offset detected on start.
        """
        utcnow = datetime.utcnow()
        # every whole minute, resync our time from i3status'
        # this ensures we will catch any daylight savings time change
        if utcnow.second == 0:
            self.set_time_modules()
        #
        for index, item in enumerate(json_list):
            if item.get('name') in ['time', 'tztime']:
                conf_name = self.config['i3s_modules'][index]
                time_module = self.config[conf_name]
                if not isinstance(time_module['date'], datetime):
                    # something went wrong in the datetime parsing
                    # output i3status' date string
                    item['full_text'] = time_module['date']
                else:
                    if force:
                        date = utcnow + time_module['delta']
                        time_module['date'] = date
                    else:
                        date = time_module['date']
                    time_format = self.config[conf_name].get('time_format')

                    # set the full_text date on the json_list to be returned
                    item['full_text'] = date.strftime(time_format)
                json_list[index] = item

                # reset the full_text date on the config object for next
                # iteration to be consistent with this one
                time_module['response']['full_text'] = item['full_text']
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
        for module_name in self.config['order']:
            if module_name in py3_modules:
                for method in py3_modules[module_name].methods.values():
                    ordered.append(method['last_output'])
            else:
                if self.config.get(module_name, {}).get('response'):
                    ordered.append(self.config[module_name]['response'])
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
        for section_name, conf in sorted(self.config.items()):
            if section_name in ['i3s_modules', 'py3_modules']:
                continue
            elif section_name == 'order':
                for module_name in conf:
                    if self.valid_config_param(module_name):
                        self.write_in_tmpfile('order += "%s"\n' % module_name,
                                              tmpfile)
                self.write_in_tmpfile('\n', tmpfile)
            elif self.valid_config_param(section_name) and conf:
                self.write_in_tmpfile('%s {\n' % section_name, tmpfile)
                for key, value in conf.items():
                    if isinstance(value, bool):
                        value = '{}'.format(value).lower()
                    self.write_in_tmpfile('    %s = "%s"\n' % (key, value),
                                          tmpfile)
                self.write_in_tmpfile('}\n\n', tmpfile)
        tmpfile.flush()

    @profile
    def run(self):
        """
        Spawn i3status using a self generated config file and poll its output.
        """
        with NamedTemporaryFile(prefix='py3status_') as tmpfile:
            self.write_tmp_i3status_config(tmpfile)
            syslog(LOG_INFO,
                   'i3status spawned using config file {}'.format(
                       tmpfile.name))

            i3status_pipe = Popen(
                ['i3status', '-c', tmpfile.name], stdout=PIPE, stderr=PIPE
            )
            pipe_out = i3status_pipe.stdout
            pipe_err = i3status_pipe.stderr
            self.tmpfile_path = tmpfile.name

            try:
                # loop on i3status output
                for line in pipe_out:
                    if not self.exit_lock.locked():
                        break

                    line = sanitize_text(line)

                    if line:
                        if line.startswith('[{'):
                            print_line(line)
                            with jsonify(line) as (prefix, json_list):
                                self.last_output = json_list
                                self.last_output_ts = datetime.utcnow()
                                self.last_prefix = ','
                                self.update_json_list()
                                self.set_responses(json_list)
                                # on first i3status output, we parse
                                # the time and tztime modules
                                self.set_time_modules()
                            self.ready = True
                        elif not line.startswith(','):
                            if 'version' in line:
                                header = loads(line)
                                header.update({'click_events': True})
                                line = dumps(header)
                            print_line(line)
                        else:
                            with jsonify(line) as (prefix, json_list):
                                self.last_output = json_list
                                self.last_output_ts = datetime.utcnow()
                                self.last_prefix = prefix
                                self.update_json_list()
                                self.set_responses(json_list)
                    else:
                        code = i3status_pipe.poll()
                        if code is not None:
                            msg = 'i3status died'
                            err = sanitize_text(pipe_err.read())
                            # Condense whitespace
                            err = ' '.join(err.split())
                            if err:
                                msg += ' and said: {}'.format(err)
                            else:
                                msg += ' with code {}'.format(code)
                            raise IOError(msg)
            except IOError:
                err = sys.exc_info()[1]
                self.error = err

    def mock(self):
        """
        Mock i3status behavior, used in standalone mode.
        """
        # mock thread is_alive() method
        self.is_alive = lambda: True

        # mock i3status base output
        init_output = ['{"click_events": true, "version": 1}', '[', '[]']
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

    def __init__(self, exit_lock, config, modules, i3s_config):
        """
        We need to poll stdin to receive i3bar messages.
        """
        Thread.__init__(self)
        self.config = config
        self.i3s_config = i3s_config
        self.last_refresh_ts = time()
        self.exit_lock = exit_lock
        self.modules = modules
        self.on_click = i3s_config['on_click']
        self.input_reader = InputReader(sys.stdin)

    def dispatch(self, module, obj, event):
        """
        Dispatch the event or enforce the default clear cache action.
        """
        module_name = '{} {}'.format(module.module_name,
                                     module.module_inst).strip()
        #
        if module.click_events:
            # module accepts click_events, use it
            module.click_event(event)
            if self.config['debug']:
                syslog(LOG_INFO, 'dispatching event {}'.format(event))
        else:
            # default button 2 action is to clear this method's cache
            if self.config['debug']:
                syslog(LOG_INFO, 'dispatching default event {}'.format(event))

        # to make the bar more responsive to users we ask for a refresh
        # of the module or of i3status if the module is an i3status one
        self.refresh(module_name)

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

        We rate limit the i3status refresh to 100ms.
        """
        module = self.modules.get(module_name)
        if module is not None:
            if self.config['debug']:
                syslog(LOG_INFO, 'refresh module {}'.format(module_name))
            for obj in module.methods.values():
                obj['cached_until'] = time()
        else:
            if time() > (self.last_refresh_ts + 0.1):
                if self.config['debug']:
                    syslog(
                        LOG_INFO,
                        'refresh i3status for module {}'.format(module_name))
                call(['killall', '-s', 'USR1', 'i3status'])
                self.last_refresh_ts = time()

    def refresh_all(self, module_name):
        """
        Force a full refresh of py3status and i3status modules by sending
        a SIGUSR1 signal to py3status.

        We rate limit this command to 100ms for obvious abusive behavior.
        """
        if time() > (self.last_refresh_ts + 0.1):
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
        syslog(LOG_INFO, 'i3-msg module="{}" command="{}" stdout={}'.format(
            module_name, command, i3_msg_pipe.stdout.read()))

    def i3status_mod_guess(self, instance, name):
        """
        Some i3status modules output a name and instance that are different
        from their configuration name in i3status.conf.

        For example the 'disk' module will output with name 'disk_info' so
        we try to be clever and figure it out here, case by case.

        Guessed modules:
            - battery
            - cpu_temperature
            - disk_info
            - ethernet
            - run_watch
            - volume
            - wireless
        """
        try:
            # /sys/class/power_supply/BAT0/uevent and _first_
            if name == 'battery':
                for k, v in self.i3s_config.items():
                    if k.startswith('battery') and isinstance(v, dict) and \
                            v.get('response', {}).get('instance') == instance:
                        instance = k.split(' ', 1)[1]
                        break
                else:
                    instance = str([int(s) for s in instance if s.isdigit()][
                        0])

            # /sys/devices/platform/coretemp.0/temp1_input
            elif name == 'cpu_temperature':
                instance = str([int(s) for s in instance if s.isdigit()][0])

            # disk_info /home
            elif name == 'disk_info':
                name = 'disk'

            # ethernet _first_
            elif name == 'ethernet':
                for k, v in self.i3s_config.items():
                    if k.startswith('ethernet') and isinstance(v, dict) and \
                            v.get('response', {}).get('instance') == instance:
                        instance = k.split(' ', 1)[1]

            # run_watch /var/run/openvpn.pid
            elif name == 'run_watch':
                for k, v in self.i3s_config.items():
                    if k.startswith('run_watch') and isinstance(v, dict) and \
                            v.get('pidfile') == instance:
                        instance = k.split(' ', 1)[1]
                        break

            # volume default.Master.0
            elif name == 'volume':
                device, mixer, mixer_idx = instance.split('.')
                for k, v in self.i3s_config.items():
                    if k.startswith('volume') and isinstance(v, dict) and \
                            v.get('device') == device and \
                            v.get('mixer') == mixer and \
                            str(v.get('mixer_idx')) == mixer_idx:
                        instance = k.split(' ', 1)[1]
                        break
                else:
                    instance = 'master'

            # wireless _first_
            elif name == 'wireless':
                for k, v in self.i3s_config.items():
                    if k.startswith('wireless') and isinstance(v, dict) and \
                            v.get('response', {}).get('instance') == instance:
                        instance = k.split(' ', 1)[1]
        except:
            pass
        finally:
            return (instance, name)

    @profile
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
        self.input_reader.start()
        while self.exit_lock.locked():
            event = self.input_reader.get()
            if not event:
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
                                '{} {}'.format(name, instance).strip()))

                    # guess the module config name
                    module_name = '{} {}'.format(name, instance).strip()

                    # execute any configured i3-msg command
                    if self.on_click.get(module_name, {}).get(button):
                        self.on_click_dispatcher(
                            module_name,
                            self.on_click[module_name].get(button))
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
                                    'dispatching event to i3bar_click_events')
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

    def __init__(self, exit_lock, config, module, i3_thread, user_modules):
        """
        We need quite some stuff to occupy ourselves don't we ?
        """
        Thread.__init__(self)
        self.click_events = False
        self.config = config
        self.has_kill = False
        self.i3status_thread = i3_thread
        self.last_output = []
        self.exit_lock = exit_lock
        self.methods = OrderedDict()
        self.module_class = None
        self.module_inst = ''.join(module.split(' ')[1:])
        self.module_name = module.split(' ')[0]
        #
        self.load_methods(module, user_modules)

    @staticmethod
    def load_from_file(filepath):
        """
        Return user-written class object from given path.
        """
        class_inst = None
        expected_class = 'Py3status'
        module_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
        if file_ext.lower() == '.py':
            py_mod = imp.load_source(module_name, filepath)
            if hasattr(py_mod, expected_class):
                class_inst = py_mod.Py3status()
        return class_inst

    @staticmethod
    def load_from_namespace(module_name):
        """
        Load a py3status bundled module.
        """
        class_inst = None
        name = 'py3status.modules.{}'.format(module_name)
        py_mod = __import__(name)
        components = name.split('.')
        for comp in components[1:]:
            py_mod = getattr(py_mod, comp)
        class_inst = py_mod.Py3status()
        return class_inst

    def clear_cache(self):
        """
        Reset the cache for all methods of this module.
        """
        for meth in self.methods:
            self.methods[meth]['cached_until'] = time()
            if self.config['debug']:
                syslog(LOG_INFO, 'clearing cache for method {}'.format(meth))

    def load_methods(self, module, user_modules):
        """
        Read the given user-written py3status class file and store its methods.
        Those methods will be executed, so we will deliberately ignore:
            - private methods starting with _
            - decorated methods such as @property or @staticmethod
            - 'on_click' methods as they'll be called upon a click_event
            - 'kill' methods as they'll be called upon this thread's exit
        """
        # user provided modules take precedence over py3status provided modules
        if self.module_name in user_modules:
            include_path, f_name = user_modules[self.module_name]
            syslog(LOG_INFO,
                   'loading module "{}" from {}{}'.format(module, include_path,
                                                          f_name))
            class_inst = self.load_from_file(include_path + f_name)
        # load from py3status provided modules
        else:
            syslog(LOG_INFO,
                   'loading module "{}" from py3status.modules.{}'.format(
                       module, self.module_name))
            class_inst = self.load_from_namespace(self.module_name)

        if class_inst:
            self.module_class = class_inst

            # apply module configuration from i3status config
            mod_config = self.i3status_thread.config.get(module, {})
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
                                'name': None
                            }
                            self.methods[method] = method_obj

        # done, syslog some debug info
        if self.config['debug']:
            syslog(LOG_INFO,
                   'module "{}" click_events={} has_kill={} methods={}'.format(
                       module, self.click_events, self.has_kill,
                       self.methods.keys()))

    def click_event(self, event):
        """
        Execute the 'on_click' method of this module with the given event.
        """
        try:
            click_method = getattr(self.module_class, 'on_click')
            click_method(self.i3status_thread.json_list,
                         self.i3status_thread.config['general'], event)
        except Exception:
            err = sys.exc_info()[1]
            msg = 'on_click failed with ({}) for event ({})'.format(err, event)
            syslog(LOG_WARNING, msg)

    @profile
    def run(self):
        """
        On a timely fashion, execute every method found for this module.
        We will respect and set a cache timeout for each method if the user
        didn't already do so.
        We will execute the 'kill' method of the module when we terminate.
        """
        while self.exit_lock.locked():
            # execute each method of this module
            for meth, obj in self.methods.items():
                my_method = self.methods[meth]

                # always check the lock
                if not self.exit_lock.locked():
                    break

                # respect the cache set for this method
                if time() < obj['cached_until']:
                    continue

                try:
                    # execute method and get its output
                    method = getattr(self.module_class, meth)
                    response = method(self.i3status_thread.json_list,
                                      self.i3status_thread.config['general'])

                    if isinstance(response, dict):
                        # this is a shiny new module giving a dict response
                        result = response
                    elif isinstance(response, tuple):
                        # this is an old school module reporting its position
                        position, result = response
                        if not isinstance(result, dict):
                            raise TypeError('response should be a dict')
                    else:
                        raise TypeError('response should be a dict')

                    # validate the response
                    if 'full_text' not in result:
                        raise KeyError('missing "full_text" key in response')
                    else:
                        result['instance'] = self.module_inst
                        result['name'] = self.module_name

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

                    # debug info
                    if self.config['debug']:
                        syslog(LOG_INFO,
                               'method {} returned {} '.format(meth, result))
                except Exception:
                    err = sys.exc_info()[1]
                    syslog(LOG_WARNING,
                           'user method {} failed ({})'.format(meth, err))

            # don't be hasty mate, let's take it easy for now
            sleep(self.config['interval'])

        # check and execute the 'kill' method if present
        if self.has_kill:
            kill_method = getattr(self.module_class, 'kill')
            kill_method(self.i3status_thread.json_list,
                        self.i3status_thread.config['general'])


class Py3StatusWrapper(object):
    """
    This is the py3status wrapper.
    """

    def __init__(self):
        """
        Useful variables we'll need.
        """
        self.last_refresh_ts = time()
        self.exit_lock = Lock()
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
            'interval': 1
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

    def get_all_modules(self):
        """
        Search and yield all available py3status modules:
            - in the current python's implementation site-packages
            - provided by the user using the inclusion directories

        User provided modules take precedence over py3status generic modules.
        """
        all_modules = {}
        for importer, module_name, ispkg in \
                pkgutil.iter_modules(sitepkg_modules.__path__):
            if not ispkg:
                mod = importer.find_module(module_name)
                all_modules[module_name] = (mod, None)
        user_modules = self.get_user_modules()
        all_modules.update(user_modules)
        for module_name, module_info in sorted(all_modules.items()):
            yield (module_name, module_info)

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
                my_m = Module(self.exit_lock, self.config, module,
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
        # set the exit lock
        self.exit_lock.acquire()

        # setup configuration
        self.config = self.get_config()

        if self.config.get('cli_command'):
            self.handle_cli_command(self.config['cli_command'])
            sys.exit()

        if self.config['debug']:
            syslog(LOG_INFO,
                   'py3status started with config {}'.format(self.config))

        # setup i3status thread
        self.i3status_thread = I3Status(self.exit_lock,
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
        self.events_thread = Events(self.exit_lock, self.config, self.modules,
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
        Release the exit lock, this will break all threads' loops.
        """
        try:
            self.exit_lock.release()
            if self.config['debug']:
                syslog(LOG_INFO, 'lock cleared, exiting')
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
        raise KeyboardInterrupt

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

            # check that every module thread is alive
            for module in self.modules.values():
                if not module.is_alive():
                    # don't spam the user with i3-nagbar warnings
                    if not hasattr(module, 'i3_nagbar'):
                        module.i3_nagbar = True
                        msg = 'output frozen for dead module(s) {}'.format(
                            ','.join(module.methods.keys()))
                        self.i3_nagbar(msg, level='warning')

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

    @staticmethod
    def print_module_description(details, mod_name, mod_info):
        """Print module description extracted from its docstring.
        """
        if mod_name == '__init__':
            return

        mod, f_name = mod_info
        if f_name:
            path = os.path.join(*mod_info)
            with open(path) as f:
                module = ast.parse(f.read())
        else:
            path = mod.get_filename(mod_name)
            module = ast.parse(mod.get_source(mod_name))
        try:
            docstring = ast.get_docstring(module, clean=True)
            if docstring:
                short_description = docstring.split('\n')[0].rstrip('.')
                print_stderr('  %-22s %s.' % (mod_name, short_description))
                if details:
                    for description in docstring.split('\n')[1:]:
                        print_stderr(' ' * 25 + '%s' % description)
                    print_stderr(' ' * 25 + '---')
            else:
                print_stderr('  %-22s No docstring in %s' % (mod_name, path))
        except Exception:
            print_stderr('  %-22s Unable to parse %s' % (mod_name, path))

    def handle_cli_command(self, cmd):
        """Handle a command from the CLI.
        """
        # aliases
        if cmd[0] in ['mod', 'module', 'modules']:
            cmd[0] = 'modules'

        # allowed cli commands
        if cmd[:2] in (['modules', 'list'], ['modules', 'details']):
            details = cmd[1] == 'details'
            print_stderr('Available modules:')
            for mod_name, mod_info in self.get_all_modules():
                self.print_module_description(details, mod_name, mod_info)
        elif cmd[:2] in (['modules', 'enable'], ['modules', 'disable']):
            # TODO: to be implemented
            pass
        else:
            print_stderr('Error: unknown command')
            sys.exit(1)


def main():
    try:
        locale.setlocale(locale.LC_ALL, '')
        py3 = Py3StatusWrapper()
        py3.setup()
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
    finally:
        py3.stop()
        sys.exit(0)


if __name__ == '__main__':
    main()
