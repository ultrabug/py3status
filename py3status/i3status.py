import sys
import os

from copy import deepcopy
from re import findall
from json import dumps, loads
from datetime import datetime, timedelta
from subprocess import Popen
from subprocess import PIPE
from syslog import syslog, LOG_ERR, LOG_INFO
from tempfile import NamedTemporaryFile
from threading import Thread
from time import time

from py3status.profiling import profile
from py3status.helpers import jsonify, print_line
from py3status.events import IOPoller
from py3status.parse_config import parse_config, ModuleDefinition


class I3statusModule:
    """
    This a wrapper for i3status items so that they mirror some of the methods
    of the Module class.  It also helps encapsulate the auto time updating for
    `time` and `tztime`.
    """

    def __init__(self, module_name, py3_wrapper):
        self.module_name = module_name
        self.i3status = py3_wrapper.i3status_thread
        self.is_time_module = module_name.split()[0] in ['time', 'tztime']
        self.item = {}
        self.py3_wrapper = py3_wrapper
        self.time_date = None

    def __repr__(self):
        return '<I3statusModule {}>'.format(self.module_name)


    def get_latest(self):
        return [self.item]

    def update_from_item(self, item):
        """
        Update from i3status output. returns if item has changed.
        """
        is_updated = self.item != item
        self.item = item
        if self.is_time_module:
            self.set_time_zone()
            is_updated = False
        return is_updated

    def update_time_value(self):
        if not self.item:
            return
        if not isinstance(self.time_date, datetime):
            # something went wrong in the datetime parsing
            # output i3status' date string
            self.item['full_text'] = self.time_date
        else:
            date = datetime.utcnow() + self.time_delta
            self.time_date = date
            # set the full_text date on the json_list to be
            # returned
            self.item['full_text'] = date.strftime(self.time_format)
        self.py3_wrapper.notify_update(self.module_name)

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

    def set_time_zone(self):
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
        if self.time_date and int(time()) % 60 != 0:
            return
        default_time_format = '%Y-%m-%d %H:%M:%S'
        default_tztime_format = '%Y-%m-%d %H:%M:%S %Z'
        utcnow = self.i3status.last_output_ts
        #
        config = self.i3status.config
        item = self.item
        conf_name = self.module_name
        time_name = item.get('name')
        # time and tztime have different defaults
        if time_name == 'time':
            time_format = config.get(conf_name,
                                     {}).get('format', default_time_format)
        else:
            time_format = config.get(conf_name,
                                     {}).get('format', default_tztime_format)

        # handle format_time parameter
        if 'format_time' in config.get(conf_name, {}):
            time_format = time_format.replace('%time',
                                              config[conf_name]['format_time'])

        # parse i3status date
        i3s_time = item['full_text'].encode('UTF-8', 'replace')
        try:
            # python3 compatibility code
            i3s_time = i3s_time.decode()
        except:
            pass

        time_format, delta = self.get_delta_from_format(i3s_time, time_format)

        try:
            if '%Z' in time_format:
                raise ValueError('%Z directive is not supported')

            # add mendatory items in i3status time format wrt issue #18
            time_fmt = time_format
            for fmt in ['%Y', '%m', '%d']:
                if fmt not in time_format:
                    time_fmt = '{} {}'.format(time_fmt, fmt)
                    i3s_time = '{} {}'.format(i3s_time,
                                              datetime.now().strftime(fmt))

            # get a datetime from the parsed string date
            date = datetime.strptime(i3s_time, time_fmt)

            # calculate the delta if needed
            if not delta:
                delta = (datetime(date.year, date.month, date.day, date.hour,
                                  date.minute) -
                         datetime(utcnow.year, utcnow.month, utcnow.day,
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
            self.time_date = date
            self.time_delta = delta
            self.time_format = time_format


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
        self.last_output_ts = None
        self.last_prefix = None
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
        for module in self.i3modules.values():
            if module.is_time_module:
                module.update_time_value()

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

    def i3status_config_reader(self, i3status_config_path):
        """
        Parse i3status.conf so we can adapt our code to the i3status config.
        """
        general_defaults = {
            'color_bad': '#FF0000',
            'color_degraded': '#FFFF00',
            'color_good': '#00FF00',
            'color_separator': '#333333',
            'colors': False,
            'interval': 5,
            'output_format': 'i3bar',
        }

        config = {}

        user_modules = self.py3_wrapper.get_user_modules()
        with open(i3status_config_path, 'r') as f:
            config_info = parse_config(f, user_modules=user_modules)

        # update general section with defaults
        if 'general' in config_info:
            general_defaults.update(config_info['general'])
        config['general'] = general_defaults

        # get all modules
        modules = {}
        on_click = {}
        i3s_modules = set()
        py3_modules = set()
        module_groups = {}
        group_extras = []

        def process_onclick(key, value, group_name):
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
            clicks = on_click.setdefault(group_name, {})
            clicks[button] = value

        def get_module_type(name):
            if name.split()[0] in self.i3status_module_names:
                return 'i3status'
            return 'py3status'

        def process_module(name, module, parent):
            if name.split()[0] == 'group':
                module['items'] = []

            if parent:
                modules[parent]['items'].append(name)
                mg = module_groups.setdefault(name, [])
                mg.append(parent)
                group_extras.append(name)
                if get_module_type(name) == 'py3status':
                    module['.group'] = parent

            # get on_click events
            for k, v in module.items():
                if k.startswith('on_click'):
                    process_onclick(k, v, name)
            return module

        def get_modules(data, parent=None):
            for k, v in data.items():
                if isinstance(v, ModuleDefinition):
                    module = process_module(k, v, parent)
                    modules[k] = module
                    get_modules(v, parent=k)

        get_modules(config_info)

        config['order'] = []
        config['.group_extras'] = []

        def fix_module(module):
            fixed = {}
            for k, v in module.items():
                if not isinstance(v, ModuleDefinition):
                    fixed[k] = v
            return fixed

        def update_config(name, order):
            module = modules.get(name, {})
            module_type = get_module_type(name)
            if order:
                config['order'].append(name)
            elif module_type == 'i3status':
                config['.group_extras'].append(name)
            if module_type == 'i3status':
                i3s_modules.add(name)
            else:
                py3_modules.add(name)
            config[name] = fix_module(module)

        for name in config_info['order']:
            update_config(name, order=True)

        for name in group_extras:
            update_config(name, order=False)

        config['on_click'] = on_click
        config['i3s_modules'] = sorted(list(i3s_modules))
        config['py3_modules'] = sorted(list(py3_modules))
        config['.module_groups'] = module_groups

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
                self.i3modules[conf_name] = I3statusModule(
                    conf_name, self.py3_wrapper)
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
        self.json_list_ts = deepcopy(self.last_output_ts)

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
            if section_name in ['order', 'py3_modules', '.group_extras',
                                '.module_groups']:
                continue
            elif section_name == 'i3s_modules':
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
        try:
            with NamedTemporaryFile(prefix='py3status_') as tmpfile:
                self.write_tmp_i3status_config(tmpfile)
                syslog(LOG_INFO,
                       'i3status spawned using config file {}'.format(
                           tmpfile.name))

                i3status_pipe = Popen(
                    ['i3status', '-c', tmpfile.name],
                    stdout=PIPE,
                    stderr=PIPE, )
                self.poller_inp = IOPoller(i3status_pipe.stdout)
                self.poller_err = IOPoller(i3status_pipe.stderr)
                self.tmpfile_path = tmpfile.name

                try:
                    # loop on i3status output
                    while self.lock.is_set():
                        line = self.poller_inp.readline()
                        if line:
                            if line.startswith('[{'):
                                print_line(line)
                                with jsonify(line) as (prefix, json_list):
                                    self.last_output = json_list
                                    self.last_output_ts = datetime.utcnow()
                                    self.last_prefix = ','
                                    self.set_responses(json_list)
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
                                    self.set_responses(json_list)
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
        init_output = ['{"click_events": true, "version": 1}', '[', '[]']
        for line in init_output:
            print_line(line)

        # mock i3status output parsing
        self.last_output = []
        self.last_output_ts = datetime.utcnow()
        self.last_prefix = ','
        self.update_json_list()
