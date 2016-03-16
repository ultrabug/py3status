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

from py3status.profiling import profile
from py3status.helpers import jsonify, print_line
from py3status.events import IOPoller


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
            'battery', 'cpu_temperature', 'cpu_usage', 'ddate', 'disk',
            'ethernet', 'ipv6', 'load', 'path_exists', 'run_watch', 'time',
            'tztime', 'volume', 'wireless'
        ]
        self.json_list = None
        self.json_list_ts = None
        self.last_output = None
        self.last_output_ts = None
        self.last_prefix = None
        self.lock = lock
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

    def get_modules_output(self, json_list, py3_modules, output):
        """
        Return the final json list to be displayed on the i3bar by taking
        into account every py3status configured module and i3status'.
        Simply put, this method honors the initial 'order' configured by
        the user in his i3status.conf.
        """
        if len(self.config['order']) != len(output):
            output = [None] * len(self.config['order'])
        for index, module_name in enumerate(self.config['order']):
       #     print_line(index)
            if module_name in py3_modules:
                # kill any updated
                if py3_modules[module_name].check_updated(reset=True) or not output[index]:
                   # if module_name == 'weather_yahoo':
                    #    print_line('## weather')
                    for method in py3_modules[module_name].methods.values():
                       # output.append(method['last_output'])
                        output[index] = method['last_output']
               # else:
                #    print_line(module_name)
            else:
                if self.config.get(module_name, {}).get('response'):
                    output[index] = self.config[module_name]['response']
       # print_line(output)
        return output

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
