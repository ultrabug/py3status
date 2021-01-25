import sys
import time

from copy import deepcopy
from json import loads
from datetime import datetime, timezone
from subprocess import Popen
from subprocess import PIPE
from signal import SIGTSTP, SIGSTOP, SIGUSR1, SIG_IGN, signal
from tempfile import NamedTemporaryFile
from threading import Thread

from py3status.profiling import profile
from py3status.py3 import Py3
from py3status.events import IOPoller
from py3status.constants import (
    I3S_ALLOWED_COLORS,
    I3S_COLOR_MODULES,
    TIME_FORMAT,
    TIME_MODULES,
    TZTIME_FORMAT,
)


class I3statusModule:
    """
    This a wrapper for i3status items so that they mirror some of the methods
    of the Module class.  It also helps encapsulate the auto time updating for
    `time` and `tztime`.
    """

    def __init__(self, module_name, i3status):
        self.module_name = module_name
        self.module_full_name = module_name

        # i3status modules always allow user defined click events in the config
        self.allow_config_clicks = True

        # i3status returns different name/instances than it is sent we want to
        # be able to restore the correct ones.
        try:
            name, instance = self.module_name.split()
        except:  # noqa e722
            name = self.module_name
            instance = ""
        self.name = name
        self.instance = instance

        # setup our output
        self.item = {"full_text": "", "name": name, "instance": instance}

        self.i3status = i3status
        py3_wrapper = i3status.py3_wrapper

        markup = py3_wrapper.config["py3_config"]["general"].get("markup")
        if markup:
            self.item["markup"] = markup

        # color map for if color good/bad etc are set for the module
        color_map = {}
        py3_config = py3_wrapper.config["py3_config"]
        for key, value in py3_config[module_name].items():
            if key in I3S_ALLOWED_COLORS:
                color_map[py3_config["general"][key]] = value
        self.color_map = color_map

        self.is_time_module = name in TIME_MODULES
        if self.is_time_module:
            self.setup_time_module()

    def setup_time_module(self):
        self.py3 = Py3()
        self.tz = None
        self.set_time_format()
        # we need to check the timezone this is when the check is next due
        self.time_zone_check_due = 0
        self.time_started = False

        time_format = self.time_format

        if "%f" in time_format:
            # microseconds
            time_delta = 0
        elif "%S" in time_format:
            # seconds
            time_delta = 1
        elif "%s" in time_format:
            # seconds since unix epoch start
            time_delta = 1
        elif "%T" in time_format:
            # seconds included in "%H:%M:%S"
            time_delta = 1
        elif "%c" in time_format or "%+" in time_format:
            # Locale's appropriate date and time representation
            time_delta = 1
        elif "%X" in time_format:
            # Locale's appropriate time representation
            time_delta = 1
        else:
            time_delta = 60
        self.time_delta = time_delta

    def __repr__(self):
        return f"<I3statusModule {self.module_name}>"

    def get_latest(self):
        return [self.item.copy()]

    def run(self):
        """
        updates the modules output.
        Currently only time and tztime need to do this
        """
        if self.update_time_value():
            self.i3status.py3_wrapper.notify_update(self.module_name)
        due_time = self.py3.time_in(sync_to=self.time_delta)

        self.i3status.py3_wrapper.timeout_queue_add(self, due_time)

    def update_from_item(self, item):
        """
        Update from i3status output. returns if item has changed.
        """
        if not self.is_time_module:
            # correct the output
            # Restore the name/instance.
            item["name"] = self.name
            item["instance"] = self.instance

            # change color good/bad is set specifically for module
            if "color" in item and item["color"] in self.color_map:
                item["color"] = self.color_map[item["color"]]

            # have we updated?
            is_updated = self.item != item
            self.item = item
        else:
            # If no timezone or a minute has passed update timezone
            t = time.perf_counter()
            if self.time_zone_check_due < t:
                # If we are late for our timezone update then schedule the next
                # update to happen when we next get new data from i3status
                interval = self.i3status.update_interval
                if not self.set_time_zone(item):
                    # we had an issue with an invalid time zone probably due to
                    # suspending.  re check the time zone when we next can.
                    self.time_zone_check_due = 0
                elif self.time_zone_check_due and (
                    t - self.time_zone_check_due > 5 + interval
                ):
                    self.time_zone_check_due = 0
                else:
                    # Check again in 30 mins.  We do this in case the timezone
                    # used has switched to/from summer time
                    self.time_zone_check_due = ((int(t) // 1800) * 1800) + 1800
                if not self.time_started:
                    self.time_started = True
                    self.i3status.py3_wrapper.timeout_queue_add(self)
            is_updated = False
            # update time to be shown
        return is_updated

    def set_time_format(self):
        config = self.i3status.py3_config.get(self.module_name, {})
        time_format = config.get("format", TIME_FORMAT)
        # Handle format_time parameter if exists
        # Not sure if i3status supports this but docs say it does
        if "format_time" in config:
            time_format = time_format.replace("%time", config["format_time"])
        self.time_format = time_format

    def update_time_value(self):
        date = datetime.now(self.tz)
        # set the full_text with the correctly formatted date
        try:
            new_value = date.strftime(self.time_format)
        except:  # noqa e722
            # python 2 unicode
            new_value = date.strftime(self.time_format.encode("utf-8"))
            new_value = new_value.decode("utf-8")
        updated = self.item["full_text"] != new_value
        if updated:
            self.item["full_text"] = new_value
        return updated

    def set_time_zone(self, item):
        """
        Work out the time zone and create a shim tzinfo.

        We return True if all is good or False if there was an issue and we
        need to re check the time zone.  see issue #1375
        """
        # parse i3status date
        i3s_time = item["full_text"].encode("UTF-8", "replace")
        try:
            # python3 compatibility code
            i3s_time = i3s_time.decode()
        except:  # noqa e722
            pass

        # get datetime and time zone info
        parts = i3s_time.split()
        i3s_datetime = " ".join(parts[:2])
        # occasionally we do not get the timezone name
        if len(parts) < 3:
            return True
        else:
            i3s_time_tz = parts[2]

        date = datetime.strptime(i3s_datetime, TIME_FORMAT)
        # calculate the time delta
        utcnow = datetime.utcnow()
        delta = datetime(
            date.year, date.month, date.day, date.hour, date.minute
        ) - datetime(utcnow.year, utcnow.month, utcnow.day, utcnow.hour, utcnow.minute)
        # create our custom timezone
        try:
            self.tz = timezone(delta, i3s_time_tz)
        except ValueError:
            return False
        return True


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
        self.i3modules = {}
        self.i3status_pipe = None
        self.i3status_path = py3_wrapper.config["i3status_path"]
        self.json_list = None
        self.json_list_ts = None
        self.last_output = None
        self.last_refresh_ts = time.perf_counter()
        self.lock = py3_wrapper.lock
        self.new_update = False
        self.py3_config = py3_wrapper.config["py3_config"]
        self.py3_wrapper = py3_wrapper
        self.ready = False
        self.standalone = py3_wrapper.config["standalone"]
        self.time_modules = []
        self.tmpfile_path = None
        self.update_due = 0

        # the update interval is useful to know
        self.update_interval = self.py3_wrapper.get_config_attribute(
            "general", "interval"
        )
        # do any initialization
        self.setup()

    def setup(self):
        """
        Do any setup work needed to run i3status modules
        """
        for conf_name in self.py3_config["i3s_modules"]:
            module = I3statusModule(conf_name, self)
            self.i3modules[conf_name] = module
            if module.is_time_module:
                self.time_modules.append(module)

    def set_responses(self, json_list):
        """
        Set the given i3status responses on their respective configuration.
        """
        self.update_json_list()
        updates = []
        for index, item in enumerate(self.json_list):
            conf_name = self.py3_config["i3s_modules"][index]

            module = self.i3modules[conf_name]
            if module.update_from_item(item):
                updates.append(conf_name)
        if updates:
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
            tmpfile.write(text.encode("utf-8"))

    def write_tmp_i3status_config(self, tmpfile):
        """
        Given a temporary file descriptor, write a valid i3status config file
        based on the parsed one from 'i3status_config_path'.
        """
        # order += ...
        for module in self.py3_config["i3s_modules"]:
            self.write_in_tmpfile(f'order += "{module}"\n', tmpfile)
        self.write_in_tmpfile("\n", tmpfile)
        # config params for general section and each module
        for section_name in ["general"] + self.py3_config["i3s_modules"]:
            section = self.py3_config[section_name]
            self.write_in_tmpfile(f"{section_name} {{\n", tmpfile)
            for key, value in section.items():
                # don't include color values except in the general section
                if key.startswith("color"):
                    if (
                        section_name.split(" ")[0] not in I3S_COLOR_MODULES
                        or key not in I3S_ALLOWED_COLORS
                    ):
                        continue
                # Set known fixed format for time and tztime so we can work
                # out the timezone
                if section_name.split()[0] in TIME_MODULES:
                    if key == "format":
                        value = TZTIME_FORMAT
                    if key == "format_time":
                        continue
                if isinstance(value, bool):
                    value = f"{value}".lower()
                self.write_in_tmpfile(f'    {key} = "{value}"\n', tmpfile)
            self.write_in_tmpfile("}\n\n", tmpfile)
        tmpfile.flush()

    def suspend_i3status(self):
        # Put i3status to sleep
        if self.i3status_pipe:
            self.i3status_pipe.send_signal(SIGSTOP)

    def refresh_i3status(self):
        # refresh i3status.  This is rate limited
        if time.perf_counter() > (self.last_refresh_ts + 0.1):
            if self.py3_wrapper.config["debug"]:
                self.py3_wrapper.log("refreshing i3status")
            if self.i3status_pipe:
                self.i3status_pipe.send_signal(SIGUSR1)
            self.last_refresh_ts = time.perf_counter()

    @profile
    def run(self):
        # if the i3status process dies we want to restart it.
        # We give up restarting if we have died too often
        for _ in range(10):
            if not self.py3_wrapper.running:
                break
            self.spawn_i3status()
            # check if we never worked properly and if so quit now
            if not self.ready:
                break
            # limit restart rate
            self.lock.wait(5)

    def spawn_i3status(self):
        """
        Spawn i3status using a self generated config file and poll its output.
        """
        try:
            with NamedTemporaryFile(prefix="py3status_") as tmpfile:
                self.write_tmp_i3status_config(tmpfile)

                i3status_pipe = Popen(
                    [self.i3status_path, "-c", tmpfile.name],
                    stdout=PIPE,
                    stderr=PIPE,
                    # Ignore the SIGTSTP signal for this subprocess
                    preexec_fn=lambda: signal(SIGTSTP, SIG_IGN),
                )

                self.py3_wrapper.log(
                    f"i3status spawned using config file {tmpfile.name}"
                )

                self.poller_inp = IOPoller(i3status_pipe.stdout)
                self.poller_err = IOPoller(i3status_pipe.stderr)
                self.tmpfile_path = tmpfile.name

                # Store the pipe so we can signal it
                self.i3status_pipe = i3status_pipe

                try:
                    # loop on i3status output
                    while self.py3_wrapper.running:
                        line = self.poller_inp.readline()
                        if line:
                            # remove leading comma if present
                            if line[0] == ",":
                                line = line[1:]
                            if line.startswith("[{"):
                                json_list = loads(line)
                                self.last_output = json_list
                                self.set_responses(json_list)
                                self.ready = True
                        else:
                            err = self.poller_err.readline()
                            code = i3status_pipe.poll()
                            if code is not None:
                                msg = "i3status died"
                                if err:
                                    msg += f" and said: {err}"
                                else:
                                    msg += f" with code {code}"
                                raise OSError(msg)
                except OSError:
                    err = sys.exc_info()[1]
                    self.error = err
                    self.py3_wrapper.log(err, "error")
        except OSError:
            self.error = "Problem starting i3status maybe it is not installed"
        except Exception:
            self.py3_wrapper.report_exception("", notify_user=True)
        self.i3status_pipe = None

    def mock(self):
        """
        Mock i3status behavior, used in standalone mode.
        """
        # mock thread is_alive() method
        self.is_alive = lambda: True
