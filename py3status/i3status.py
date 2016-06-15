import sys
import os

from copy import deepcopy
from json import loads
from datetime import datetime, timedelta, tzinfo
from subprocess import Popen
from subprocess import PIPE
from signal import SIGTSTP, SIGSTOP, SIG_IGN, signal
from tempfile import NamedTemporaryFile
from threading import Thread
from time import time, sleep

from py3status.profiling import profile
from py3status.events import IOPoller

TIME_FORMAT = '%Y-%m-%d %H:%M:%S'
TZTIME_FORMAT = '%Y-%m-%d %H:%M:%S %Z'
TIME_MODULES = ['time', 'tztime']


class Tz(tzinfo):
    """
    Timezone info for creating dates.
    This is mainly so we can use %Z in strftime
    """

    def __init__(self, name, offset):
        self._offset = offset
        self._name = name

    def utcoffset(self, dt):
        return self._offset

    def tzname(self, dt):
        return str(self._name)

    def dst(self, dt):
        # we have no idea if daylight savings, so just say no kids
        return timedelta(0)


class I3statusModule:
    """
    This a wrapper for i3status items so that they mirror some of the methods
    of the Module class.  It also helps encapsulate the auto time updating for
    `time` and `tztime`.
    """

    def __init__(self, module_name, py3_wrapper):
        self.i3status_pipe = None
        self.module_name = module_name

        # i3status returns different name/instances than it is sent we want to
        # be able to restore the correct ones.
        try:
            name, instance = self.module_name.split()
        except:
            name = self.module_name
            instance = ''
        self.name = name
        self.instance = instance

        self.item = {}

        self.i3status = py3_wrapper.i3status_thread
        self.py3_wrapper = py3_wrapper

        self.is_time_module = name in TIME_MODULES
        if self.is_time_module:
            self.tz = None
            self.set_time_format()

    def __repr__(self):
        return '<I3statusModule {}>'.format(self.module_name)

    def get_latest(self):
        return [self.item]

    def update_from_item(self, item):
        """
        Update from i3status output. returns if item has changed.
        """
        # Restore the name/instance.
        item['name'] = self.name
        item['instance'] = self.instance

        # have we updated?
        is_updated = self.item != item
        self.item = item
        if self.is_time_module:
            # If no timezone or a minute has passed update timezone
            # FIXME we should also check if resuming from suspended
            if not self.tz or int(time()) % 60 != 0:
                self.set_time_zone()
            # update time to be shown
            is_updated = self.update_time_value()
        return is_updated

    def set_time_format(self):
        config = self.i3status.config.get(self.module_name, {})
        time_format = config.get('format', TIME_FORMAT)
        # Handle format_time parameter if exists
        # Not sure if i3status supports this but docs say it does
        if 'format_time' in config:
            time_format = time_format.replace('%time', config['format_time'])
        self.time_format = time_format

    def update_time_value(self):
        date = datetime.now(self.tz)
        # set the full_text with the correctly formatted date
        new_value = date.strftime(self.time_format)
        updated = self.item['full_text'] != new_value
        if updated:
            self.item['full_text'] = new_value
        return updated

    def set_time_zone(self):
        """
        Work out the time zone and create a shim tzinfo.
        """
        # parse i3status date
        i3s_time = self.item['full_text'].encode('UTF-8', 'replace')
        try:
            # python3 compatibility code
            i3s_time = i3s_time.decode()
        except:
            pass

        # get datetime and time zone info
        parts = i3s_time.split()
        i3s_datetime = ' '.join(parts[:2])
        i3s_time_tz = parts[2]

        date = datetime.strptime(i3s_datetime, TIME_FORMAT)
        # calculate the time delta
        utcnow = datetime.utcnow()
        delta = (
            datetime(date.year, date.month, date.day, date.hour, date.minute) -
            datetime(utcnow.year, utcnow.month, utcnow.day, utcnow.hour,
                     utcnow.minute))
        # create our custom timezone
        self.tz = Tz(i3s_time_tz, delta)


class I3status(Thread):
    """
    This class is responsible for spawning i3status and reading its output.
    """

    def __init__(self, py3_wrapper):
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
        self.i3modules = {}
        self.json_list = None
        self.json_list_ts = None
        self.last_output = None
        self.lock = py3_wrapper.lock
        self.new_update = False
        self.py3_wrapper = py3_wrapper
        self.ready = False
        self.standalone = py3_wrapper.config['standalone']
        self.time_modules = []
        self.tmpfile_path = None
        #
        config_path = py3_wrapper.config['i3status_config_path']
        self.config = self.i3status_config_reader(config_path)

    def update_times(self):
        """
        Update time for any i3status time/tztime items.
        """
        updated = []
        for module in self.i3modules.values():
            if module.is_time_module:
                if module.update_time_value():
                    updated.append(module.module_name)
        if updated:
            # trigger the update so new time is shown
            self.py3_wrapper.notify_update(updated)

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
            '.group_extras': [],  # extra i3status modules needed by groups
            '.module_groups': {},  # record groups that modules are in
            'py3_modules': []
        }

        # some ugly parsing
        in_section = False
        section_name = ''
        group_name = None

        for line in open(i3status_config_path, 'r'):
            line = line.strip(' \t\n\r')

            if not line or line.startswith('#'):
                continue

            if line.startswith('order'):
                in_section = True
                section_name = 'order'

            if not in_section and line.startswith('group'):
                group_name = line.split('{')[0].strip()
                config[group_name] = {'items': []}
                continue

            if not in_section and group_name and line == '}':
                group_name = None
                continue

            if group_name and not in_section and '=' in line:
                # check this is not a section definition
                if '{' not in line or line.index('{') > line.index('='):
                    key = line.split('=', 1)[0].strip()
                    key = self.eval_config_parameter(key)
                    value = line.split('=', 1)[1].strip()
                    value = self.eval_config_value(value)
                    if not key.startswith('on_click'):
                        config[group_name][key] = value
                    else:
                        # on_click special parameters
                        try:
                            button = int(key.split()[1])
                            if button not in range(1, 6):
                                raise ValueError('should be 1, 2, 3, 4 or 5')
                        except IndexError as e:
                            raise IndexError(
                                'missing "button id" for "on_click" '
                                'parameter in group {}'.format(group_name))
                        except ValueError as e:
                            raise ValueError('invalid "button id" '
                                             'for "on_click" parameter '
                                             'in group {} ({})'.format(
                                                 group_name, e))
                        on_c = config['on_click']
                        on_c[group_name] = on_c.get(group_name, {})
                        on_c[group_name][button] = value
                    continue

            if not in_section:
                section_name = line.split('{')[0].strip()
                section_name = self.eval_config_parameter(section_name)
                if not section_name:
                    continue
                else:
                    in_section = True
                    if section_name not in config:
                        config[section_name] = {}
                    if group_name:
                        # update the items in the group
                        config[group_name]['items'].append(section_name)
                        section = config['.module_groups'].setdefault(
                            section_name, []
                        )
                        if group_name not in section:
                            section.append(group_name)
                        if not self.valid_config_param(section_name):
                            # py3status module add a reference to the group and
                            # make sure we have it in the list of modules to
                            # run
                            if section_name not in config['py3_modules']:
                                config['py3_modules'].append(section_name)
                        else:
                            # i3status module.  Add to the list of needed
                            # modules and add to the `.group-extras` config to
                            # ensure that it gets run even though not in
                            # `order` config
                            if section_name not in config['i3s_modules']:
                                config['i3s_modules'].append(section_name)
                            if section_name not in config['.group_extras']:
                                config['.group_extras'].append(section_name)

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

        # time and tztime modules need a format for correct processing
        for name in config:
            if name.split()[0] in TIME_MODULES and 'format' not in config[
                    name]:
                if name.split()[0] == 'time':
                    config[name]['format'] = TIME_FORMAT
                else:
                    config[name]['format'] = TZTIME_FORMAT

        def clean_i3status_modules(key):
            # cleanup unconfigured i3status modules that have no default
            for module_name in deepcopy(config[key]):
                if (self.valid_config_param(module_name,
                                            cleanup=True) and
                        not config.get(module_name)):
                    config.pop(module_name)
                    if module_name in config['i3s_modules']:
                        config['i3s_modules'].remove(module_name)
                    config[key].remove(module_name)

        clean_i3status_modules('order')
        clean_i3status_modules('.group_extras')
        return config

    def set_responses(self, json_list):
        """
        Set the given i3status responses on their respective configuration.
        """
        self.update_json_list()
        updates = []
        for index, item in enumerate(self.json_list):
            conf_name = self.config['i3s_modules'][index]
            if conf_name not in self.i3modules:
                self.i3modules[conf_name] = I3statusModule(conf_name,
                                                           self.py3_wrapper)
            if self.i3modules[conf_name].update_from_item(item):
                updates.append(conf_name)
        self.py3_wrapper.notify_update(updates)

    def update_json_list(self):
        """
        Copy the last json list output from i3status so that any module
        can modify it without altering the original output.
        This is done so that any module's alteration of a i3status output json
        will not be overwritten when the next i3status output gets polled.
        """
        self.json_list = deepcopy(self.last_output)

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
        # order += ...
        for module in self.config['i3s_modules']:
            self.write_in_tmpfile('order += "%s"\n' % module, tmpfile)
        self.write_in_tmpfile('\n', tmpfile)
        # config params for general section and each module
        for section_name in ['general'] + self.config['i3s_modules']:
            section = self.config[section_name]
            self.write_in_tmpfile('%s {\n' % section_name, tmpfile)
            for key, value in section.items():
                # Set known fixed format for time and tztime so we can work
                # out the timezone
                if section_name.split()[0] in TIME_MODULES:
                    if key == 'format':
                        value = TZTIME_FORMAT
                    if key == 'format_time':
                        continue
                if isinstance(value, bool):
                    value = '{}'.format(value).lower()
                self.write_in_tmpfile('    %s = "%s"\n' % (key, value),
                                      tmpfile)
            self.write_in_tmpfile('}\n\n', tmpfile)
        tmpfile.flush()

    def suspend_i3status(self):
        # Put i3status to sleep
        if self.i3status_pipe:
            self.i3status_pipe.send_signal(SIGSTOP)

    @profile
    def run(self):
        # if the i3status process dies we want to restart it.
        # We give up restarting if we have died too often
        for x in range(10):
            if not self.lock.is_set():
                break
            self.spawn_i3status()
            # check if we never worked properly and if so quit now
            if not self.ready:
                break
            # limit restart rate
            sleep(5)

    def spawn_i3status(self):
        """
        Spawn i3status using a self generated config file and poll its output.
        """
        try:
            with NamedTemporaryFile(prefix='py3status_') as tmpfile:
                self.write_tmp_i3status_config(tmpfile)
                self.py3_wrapper.log(
                    'i3status spawned using config file {}'.format(
                        tmpfile.name))

                i3status_pipe = Popen(
                    ['i3status', '-c', tmpfile.name],
                    stdout=PIPE,
                    stderr=PIPE,
                    # Ignore the SIGTSTP signal for this subprocess
                    preexec_fn=lambda:  signal(SIGTSTP, SIG_IGN)
                )
                self.poller_inp = IOPoller(i3status_pipe.stdout)
                self.poller_err = IOPoller(i3status_pipe.stderr)
                self.tmpfile_path = tmpfile.name

                # Store the pipe so we can signal it
                self.i3status_pipe = i3status_pipe

                try:
                    # loop on i3status output
                    while self.lock.is_set():
                        line = self.poller_inp.readline()
                        if line:
                            # remove leading comma if present
                            if line[0] == ',':
                                line = line[1:]
                            if line.startswith('[{'):
                                json_list = loads(line)
                                self.last_output = json_list
                                self.set_responses(json_list)
                                self.ready = True
                        else:
                            err = self.poller_err.readline()
                            code = i3status_pipe.poll()
                            if code is not None:
                                msg = 'i3status died'
                                if err:
                                    msg += ' and said: {}'.format(err)
                                else:
                                    msg += ' with code {}'.format(code)
                                raise IOError(msg)
                except IOError:
                    err = sys.exc_info()[1]
                    self.error = err
                    self.py3_wrapper.log(err, 'error')
        except Exception:
            err = sys.exc_info()[1]
            self.error = err
            self.py3_wrapper.log(err, 'error')
        self.i3status_pipe = None

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

        # mock i3status output parsing
        self.last_output = []
        self.update_json_list()
