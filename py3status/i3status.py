import sys
import os

from copy import deepcopy
from json import dumps, loads
from datetime import datetime, timedelta, tzinfo
from subprocess import Popen
from subprocess import PIPE
from syslog import syslog, LOG_INFO
from signal import SIGUSR2, SIGSTOP, SIG_IGN, signal
from tempfile import NamedTemporaryFile
from threading import Thread
from time import time

from py3status.profiling import profile
from py3status.helpers import jsonify, print_line
from py3status.events import IOPoller
import py3status.constants as const


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
        self.i3status = py3_wrapper.i3status_thread
        self.is_time_module = module_name.split()[0] in const.TIME_MODULES
        self.item = {}
        self.py3_wrapper = py3_wrapper
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
        time_format = config.get('format', const.TIME_FORMAT)
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

        date = datetime.strptime(i3s_datetime, const.TIME_FORMAT)
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

    def __init__(self, py3_wrapper, config):
        """
        Our output will be read asynchronously from 'last_output'.
        """
        Thread.__init__(self)
        self.config = config
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
        self.last_prefix = None
        self.lock = py3_wrapper.lock
        self.new_update = False
        self.py3_wrapper = py3_wrapper
        self.ready = False
        self.standalone = py3_wrapper.config['standalone']
        self.time_modules = []
        self.tmpfile_path = None

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
        interval = self.config.get('general', {}).get(
            'interval', const.DEFAULT_I3STATUS_INTERVAL)
        self.write_in_tmpfile(const.I3STATUS_CONF_GENERAL % interval, tmpfile)
        for module in self.config['i3s_modules']:
            self.write_in_tmpfile('order += "%s"\n' % module, tmpfile)
        self.write_in_tmpfile('\n', tmpfile)
        for module in self.config['i3s_modules']:
            section = self.config[module]
            self.write_in_tmpfile('%s {\n' % module, tmpfile)
            for key, value in section.items():
                # Set known fixed format for time and tztime so we can work
                # out the timezone
                if module.split()[0] in const.TIME_MODULES and key == 'format':
                    value = const.TZTIME_FORMAT
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
                    stderr=PIPE,
                    # Ignore the SIGUSR2 signal for this subprocess
                    preexec_fn=lambda:  signal(SIGUSR2, SIG_IGN)
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
                            if line.startswith('[{'):
                                print_line(line)
                                with jsonify(line) as (prefix, json_list):
                                    self.last_output = json_list
                                    self.last_prefix = ','
                                    self.set_responses(json_list)
                                self.ready = True
                            elif not line.startswith(','):
                                if 'version' in line:
                                    header = loads(line)
                                    header.update({'click_events': True})
                                    # set custom stop signal
                                    header['stop_signal'] = SIGUSR2
                                    line = dumps(header)
                                print_line(line)
                            else:
                                with jsonify(line) as (prefix, json_list):
                                    self.last_output = json_list
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

        # mock i3status base output
        init_output = ['{"click_events": true, "version": 1}', '[', '[]']
        for line in init_output:
            print_line(line)

        # mock i3status output parsing
        self.last_output = []
        self.last_prefix = ','
        self.update_json_list()
