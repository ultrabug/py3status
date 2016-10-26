import sys

from copy import deepcopy
from json import loads
from datetime import datetime, timedelta, tzinfo
from subprocess import Popen
from subprocess import PIPE
from signal import SIGTSTP, SIGSTOP, SIGUSR1, SIG_IGN, signal
from tempfile import NamedTemporaryFile
from threading import Thread, Event
from time import time, sleep

from py3status.profiling import profile
from py3status.events import IOPoller
from py3status.constants import (
    I3S_ALLOWED_COLORS, I3S_COLOR_MODULES, I3S_SINGLE_NAMES, I3S_MODULE_NAMES,
    TIME_FORMAT, TIME_MODULES, TZTIME_FORMAT,
)


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
        self.module_name = module_name

        # i3status returns different name/instances than it is sent we want to
        # be able to restore the correct ones.
        try:
            name, instance = self.module_name.split()
        except:
            name = self.module_name
            instance = ''

        i3status_config = py3_wrapper.i3status_config

        self.name = name
        self.instance = instance

        self.item = {}

        self.i3status = py3_wrapper.i3status_runner
        self.i3status_config = i3status_config
        self.py3_wrapper = py3_wrapper

        # color map for if color good/bad etc are set for the module
        color_map = {}
        for key, value in i3status_config[module_name].items():
            if key in I3S_ALLOWED_COLORS:
                color_map[i3status_config['general'][key]] = value
        self.color_map = color_map

        self.is_time_module = name in TIME_MODULES
        if self.is_time_module:
            self.tz = None
            self.set_time_format()

    def __repr__(self):
        return '<I3statusModule {}>'.format(self.module_name)

    def get_latest(self):
        return [self.item.copy()]

    def update_from_item(self, item):
        """
        Update from i3status output. returns if item has changed.
        """
        # Restore the name/instance.
        item['name'] = self.name
        item['instance'] = self.instance

        # change color good/bad is set specifically for module
        if 'color' in item and item['color'] in self.color_map:
            item['color'] = self.color_map[item['color']]

        # have we updated?
        is_updated = self.item != item
        self.item = item
        if self.is_time_module:
            # If no timezone or a minute has passed update timezone
            # FIXME we should also check if resuming from suspended
            if not self.tz or int(time()) % 60 == 0:
                self.set_time_zone()
            # update time to be shown
            is_updated = self.update_time_value() or is_updated
        return is_updated

    def set_time_format(self):
        config = self.i3status_config.get(self.module_name, {})
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
        # occassionally we do not get the timezone name
        if len(parts) < 3:
            return
        else:
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


class I3statusRunner:
    """
    In charge of i3status.
    Creates I3status threads as needed and acts as an intermediary with the
    rest of py3status.  Passes on most functions directly to the I3sataus
    thread.
    """

    def __init__(self, py3_wrapper):
        self.lock_i3status = None
        self.i3status_thread = None
        self.i3status_starting = False
        self.py3_wrapper = py3_wrapper

    def refresh_i3status(self):
        self.i3status_thread.refresh_i3status()

    def suspend_i3status(self):
        self.i3status_thread.suspend_i3status()

    def is_alive(self):
        # when the tread is starting is_alive() may not be True but this does
        # not mean that i3status has died.
        return self.i3status_starting or self.i3status_thread.is_alive()

    def update_times(self):
        self.i3status_thread.update_times()

    @property
    def error(self):
        return self.i3status_thread.error

    @property
    def i3modules(self):
        return self.i3status_thread.i3modules

    @property
    def json_list(self):
        return self.i3status_thread.json_list

    def set_config(self, config):
        # in case we the i3status thread has not started by the time the main
        # loop in core.py has started we need make sure we know that the
        # i3status thread is starting up. So we have i3status_starting to let
        # us not report that the is not yet alive.
        self.i3status_starting = True
        lock = Event()
        lock.set()
        self.lock_i3status = lock
        self.config = config
        self.i3status_thread = I3status(self.py3_wrapper, config, lock)
        thread = Thread(target=self.start_i3status, args=())
        thread.daemon = True
        thread.start()

    def start_i3status(self):
        # If standalone or no i3status modules then use the mock i3status
        # else start i3status thread.
        i3s_modules = self.config['i3s_modules']
        if self.py3_wrapper.config['standalone'] or not i3s_modules:
            self.i3status_thread.mock()
            i3s_mode = 'mocked'
        else:
            i3s_mode = 'started'
            self.i3status_thread.daemon = True
            self.i3status_thread.start()
            while not self.i3status_thread.ready:
                if not self.i3status_thread.is_alive():
                    # i3status is having a bad day, so tell the user what went
                    # wrong and do the best we can with just py3status modules.
                    err = self.i3status_thread.error
                    self.py3_wrapper.notify_user(err)
                    self.i3status_thread.mock()
                    i3s_mode = 'mocked'
                    break
                sleep(0.1)
        if self.py3_wrapper.config['debug']:
            self.log('i3status thread {} with config {}'.format(
                i3s_mode, self.i3status_thread.config))
        # The i3status thread is running (or not) we no longer need to hide
        # this from the main loop.
        self.i3status_starting = False

    def kill(self):
        """
        Stop any i3status process
        """
        if self.lock_i3status:
            self.lock_i3status.clear()
        if self.i3status_thread and self.i3status_thread.i3status_pipe:
            self.i3status_thread.i3status_pipe.kill()


class I3status(Thread):
    """
    This class is responsible for spawning i3status and reading its output.
    """

    def __init__(self, py3_wrapper, config, lock):
        """
        Our output will be read asynchronously from 'last_output'.
        """
        Thread.__init__(self)
        self.config = config
        self.error = None
        self.i3modules = {}
        self.json_list = None
        self.json_list_ts = None
        self.last_output = None
        self.last_refresh_ts = time()
        self.lock = lock
        self.new_update = False
        self.py3_wrapper = py3_wrapper
        self.ready = False
        self.standalone = py3_wrapper.config['standalone']
        self.i3status_pipe = None
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
                for _ in I3S_MODULE_NAMES
                if _ not in I3S_SINGLE_NAMES
            ]
        else:
            valid_config_params = I3S_MODULE_NAMES + [
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
                i3status_module = I3statusModule(conf_name, self.py3_wrapper)
                self.i3modules[conf_name] = i3status_module

                self.py3_wrapper.add_i3status_output_module(
                    conf_name, i3status_module
                )
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
        except UnicodeEncodeError:
            tmpfile.write(text.encode('utf-8'))

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
                # don't include color values except in the general section
                if key.startswith('color'):
                    if (section_name.split(' ')[0] not in I3S_COLOR_MODULES or
                            key not in I3S_ALLOWED_COLORS):
                        continue
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

    def refresh_i3status(self):
        # refresh i3status.  This is rate limited
        if time() > (self.last_refresh_ts + 0.1):
            if self.py3_wrapper.config['debug']:
                self.py3_wrapper.log('refreshing i3status')
            if self.i3status_pipe:
                self.i3status_pipe.send_signal(SIGUSR1)
            self.last_refresh_ts = time()

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
                    preexec_fn=lambda: signal(SIGTSTP, SIG_IGN)
                )
                self.poller_inp = IOPoller(i3status_pipe.stdout)
                self.poller_err = IOPoller(i3status_pipe.stderr)
                self.tmpfile_path = tmpfile.name

                # Store the pipe so we can signal it
                self.i3status_pipe = i3status_pipe

                try:
                    # loop on i3status output
                    while True:
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
                            # if lock is not set we kill i3status thread
                            # intentionally
                            if not self.lock.is_set():
                                message = 'i3status processess shut down'
                                self.py3_wrapper.log(message)
                                break
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
            self.py3_wrapper.report_exception('', notify_user=True)
        self.i3status_pipe = None

    def mock(self):
        """
        Mock i3status behavior, used in standalone mode.
        """
        # mock thread is_alive() method
        self.is_alive = lambda: True

        # mock i3status output parsing
        self.last_output = []
        self.update_json_list()
