# Copyright (c) 2013, Ultrabug
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice,
#   this list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# includes
################################################################################
import os
import imp
import sys
import argparse
import threading
from threading import Thread

from json import loads
from json import dumps

from time import time
from time import sleep

from datetime import datetime
from datetime import timedelta

from signal import signal
from signal import SIGUSR1

from subprocess import Popen
from subprocess import PIPE
from subprocess import call

from syslog import syslog
from syslog import LOG_ERR
from syslog import LOG_INFO
from syslog import LOG_WARNING

try:
    # python3
    from queue import Queue
    from queue import Empty
except ImportError:
    # python2
    from Queue import Queue
    from Queue import Empty

# module globals and defaults
################################################################################
CACHE_TIMEOUT = 60
DISABLE_TRANSFORM = False
I3STATUS_CONFIG = '/etc/i3status.conf'
INCLUDE_PATHS = ['.i3/py3status/']
INTERVAL = 1

# functions
################################################################################
def print_line(message):
    """
    Non-buffered printing to stdout
    """
    sys.stdout.write(message + '\n')
    sys.stdout.flush()

def read_line():
    """
    Interrupted respecting reader for stdin
    """
    try:
        line = sys.stdin.readline().strip()
        # i3status sends EOF, or an empty line
        if not line:
            sys.exit(3)
        return line
    except KeyboardInterrupt:
        sys.exit()

def print_output(prefix, output_list, modules_cache):
    """
    Merge current user-classes cache with i3status' output and display on i3bar
    """
    inject = []
    for class_name in sorted( modules_cache.keys() ):
        for module in modules_cache[class_name]:
            index, json = modules_cache[class_name][module]
            for n, j in enumerate(output_list):
                if j['name'] == json['name']:
                    output_list.pop(n)
                    break
            inject.append( (index, json) )

    # inject back user classes in the right order
    for index, json in [ tup for tup in inject ]:
        output_list.insert(index, json)

    output = prefix+dumps(output_list)
    print_line(output)
    return output

def i3status_config_reader(config_file):
    """
    i3status.conf reader so we can adapt our code to the i3status config
    """
    in_time = False
    in_general = False
    config = {
        'colors': False,
        'color_good': '#00FF00',
        'color_bad' : '#FF0000',
        'color_degraded' : '#FFFF00',
        'color_separator': '#333333',
        'interval': 5,
        'output_format': None,
        'time_format': '%Y-%m-%d %H:%M:%S',
        }
    for line in open(config_file, 'r'):
        line = line.strip(' \t\n\r')
        if line.startswith('general'):
            in_general = True
        elif line.startswith('time') or line.startswith('tztime'):
            in_time = True
        elif line.startswith('}'):
            in_general = False
            in_time = False
        if in_general and '=' in line:
            key, value = line.split('=')[0].strip(), line.split('=')[1].strip()
            if key in config:
                if value in ['true', 'false']:
                    value = 'True' if value == 'true' else 'False'
                config[key] = eval(value)
        if in_time and '=' in line:
            key, value = line.split('=')[0].strip(), line.split('=')[1].strip()
            if 'time_' + key in config:
                config['time_' + key] = eval(value)
    return config

class I3status(Thread):
    """
    Run i3status in a thread and send its output to a Queue
    """
    def __init__(self, config_file):
        """
        set our useful properties
        """
        Thread.__init__(self)
        self.config_file = config_file
        self.kill = False
        self.queue = Queue()
        self.init = True
        self.started = False

    def stop(self):
        """
        break the i3status loop
        """
        self.kill = True

    def run(self):
        """
        run i3status and queue its output
        """
        i3status_pipe = Popen(
            ['i3status', '-c', self.config_file],
            stdout=PIPE,
            stderr=PIPE,
            )
        self.queue.put(i3status_pipe.stdout.readline())
        self.queue.put(i3status_pipe.stdout.readline())
        while not self.kill:
            line = i3status_pipe.stdout.readline()
            if len(line) > 0:
                self.queue.put(line)
                try:
                    line = line.decode()
                except Exception:
                    pass
                if len(line) > 1 and line.startswith('['):
                    self.init = False
                elif line.startswith(',['):
                    self.started = True
            else:
                break

def process_line(line, **kwargs):
    """
    Main line processor logic
    """
    j = []
    prefix = ''
    if line.startswith('{') and 'version' in line:
        print_line(line.strip('\n'))
    elif line == '[\n':
        print_line(line.strip('\n'))
    else:
        if line.startswith(','):
            line, prefix = line[1:], ','
        elif kwargs['delta'] > 0:
            prefix = ','

        # integrated transformations
        if not DISABLE_TRANSFORM:
            j = transform(loads(line), **kwargs)
        else:
            j = loads(line)

    return (prefix, j)

def transform(j, **kwargs):
    """
    Integrated transformations:
    - update the 'time' object so that it's updated at INTERVAL seconds
    """
    try:
        for item in j:
            # time modification
            if item['name'] in [ 'time', 'tztime' ]:
                time_format = I3STATUS_CONFIG['time_format']
                date = datetime.strptime( item['full_text'], time_format ) \
                    + timedelta(seconds=kwargs['delta'])
                item['full_text'] = date.strftime(time_format)
                if kwargs['delta'] > 0:
                    item['transformed'] = True
    except Exception:
        err = sys.exc_info()[1]
        syslog(LOG_ERR, "transformation failed (%s)" % (str(err)))
    return j

class UserModules(Thread):
    """
    This thread executes and caches all of the user's own Py3status classes.
    We run it in a separate thread so that any delay introduced by an external
    class doesn't affect the i3bar updating process.
    """
    def __init__(self, cache_timeout, i3status_conf, include_paths, interval):
        """
        set our useful properties
        """
        Thread.__init__(self)
        self.cache = {}
        self.cache_timeout = cache_timeout
        self.classes = {}
        self.i3status_conf = i3status_conf
        self.include_paths = include_paths
        self.interval = interval
        self.i3status_json = {}
        self.kill = False

    @staticmethod
    def load_from_file(filepath):
        """
        return Py3status user-written classes
        """
        inst = None
        expected_class = 'Py3status'
        mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
        if file_ext.lower() == '.py':
            py_mod = imp.load_source(mod_name, filepath)
            if hasattr(py_mod, expected_class):
                inst = py_mod.Py3status()
        return (mod_name, inst)

    def load_files(self):
        """
        read user-written Py3status class files for dynamic inclusion
        """
        for include_path in self.include_paths:
            include_path = os.path.abspath(include_path) + '/'
            if os.path.isdir(include_path):
                for f_name in os.listdir(include_path):
                    try:
                        module, class_inst = self.load_from_file(
                            include_path + f_name
                            )
                        if module and class_inst:
                            self.classes[f_name] = (class_inst, [])
                            self.cache[f_name] = {}
                            for method in dir(class_inst):
                                # exclude private and other decorated methods
                                # such as @property or @staticmethod
                                if method.startswith('_'):
                                    continue
                                else:
                                    m_type = type(getattr(class_inst, method))
                                    if 'method' in str(m_type):
                                        self.classes[f_name][1].append(method)
                    except Exception:
                        err = sys.exc_info()[1]
                        syslog(LOG_ERR, "loading %s failed (%s)" \
                            % (f_name, str(err)))

    def execute_classes(self):
        """
        Run on every user class included and execute every method on the json,
        then cache it for later usage.
        We exclude the 'kill' methods on the classes which are meant to be used
        for convenience only.
        """
        for class_name in sorted( self.classes.keys() ):
            my_class, my_methods = self.classes[class_name]
            for my_method in [ m for m in my_methods if m not in ['kill'] ]:
                try:
                    # handle a cache on user class methods results
                    try:
                        index, result = self.cache[class_name][my_method]
                        if time() > result['cached_until']:
                            raise KeyError('cache timeout')
                    except KeyError:
                        # execute the method
                        try:
                            meth = getattr(my_class, my_method)
                            index, result = meth(
                                self.i3status_json,
                                self.i3status_conf,
                                )
                        except Exception:
                            err = sys.exc_info()[1]
                            syslog(LOG_ERR, "user method %s failed (%s)" \
                                % (my_method, str(err)))
                            index, result = (0, {'name': '', 'full_text': ''})

                        # respect user-defined cache timeout for this module
                        if 'cached_until' not in result:
                            result['cached_until'] = time() + self.cache_timeout

                        # validate the response
                        assert isinstance(result, dict), "should return a dict"
                        assert 'full_text' in result, "missing 'full_text' key"
                        assert 'name' in result, "missing 'name' key"
                    finally:
                        self.cache[class_name][my_method] = (index, result)
                except Exception:
                    err = sys.exc_info()[1]
                    syslog(LOG_ERR, "injection failed (%s)" % str(err))

    def stop(self):
        """
        call any 'kill' method on Py3status modules and break this thread's loop
        """
        for class_name in sorted( self.classes.keys() ):
            my_class, my_methods = self.classes[class_name]
            if 'kill' in my_methods:
                kill_module = getattr(my_class, 'kill')
                kill_module()
        self.kill = True

    def clear(self):
        """
        clear user cache
        """
        for k in self.cache.keys():
            self.cache[k] = {}

    def run(self):
        """
        periodically execute user classes
        """
        self.load_files()
        while not self.kill:
            self.execute_classes()
            sleep(self.interval)

# main stuff
################################################################################
def main():
    """
    Main logic function
    """
    try:
        # global definition
        global CACHE_TIMEOUT, DISABLE_TRANSFORM
        global I3STATUS_CONFIG, INCLUDE_PATHS, INTERVAL

        # command line options
        parser = argparse.ArgumentParser(
            description='The agile, python-powered, i3status wrapper')
        parser = argparse.ArgumentParser(add_help=True)
        parser.add_argument('-c', action="store",
            dest="i3status_conf", type=str,
            default=I3STATUS_CONFIG, help="path to i3status config file")
        parser.add_argument('-d', action="store_true",
            dest="disable_transform", help="disable integrated transformations")
        parser.add_argument('-i', action="append", dest="include_paths",
            help="include user-written modules from those directories \
                (default .i3/py3status)")
        parser.add_argument('-n', action="store",
            dest="interval", type=int,
            default=INTERVAL, help="update interval in seconds (default 1 sec)")
        parser.add_argument('-t', action="store",
            dest="cache_timeout", type=int, default=CACHE_TIMEOUT,
            help="default injection cache timeout in seconds (default 60 sec)")
        options = parser.parse_args()

        # configuration and helper variables
        CACHE_TIMEOUT = options.cache_timeout
        DISABLE_TRANSFORM = True if options.disable_transform else False
        I3STATUS_CONFIG = i3status_config_reader(options.i3status_conf)
        INCLUDE_PATHS = INCLUDE_PATHS \
            if not options.include_paths else options.include_paths
        INTERVAL = options.interval

        # py3status uses only the i3bar protocol
        assert I3STATUS_CONFIG['output_format'] == 'i3bar', \
            'i3status output_format should be set to "i3bar"'
    except Exception:
        err = sys.exc_info()[1]
        syslog(LOG_ERR, "initialization error (%s)" % str(err))
        sys.exit(1)

    try:
        # load user defined modules from a separate thread so that they cannot
        # cause any delay in updating the i3bar
        modules_thread = UserModules(
            CACHE_TIMEOUT,
            I3STATUS_CONFIG,
            INCLUDE_PATHS,
            INTERVAL,
            )
        modules_thread.start()

        # spawn a i3status process on a separate thread
        # we will receive its output on a Queue which we will poll for messages
        i3status_thread = I3status(options.i3status_conf)
        i3status_thread.start()

        # SIGUSR1 forces a refresh of the bar both for py3status and i3status,
        # this mimics the USR1 signal handling of i3status (see man i3status)
        def sig_handler(signum, frame):
            """
            Raise a Warning level exception when a user sends a SIGUSR1 signal
            """
            raise UserWarning("received USR1, forcing refresh")
        signal(SIGUSR1, sig_handler)

        # control variables
        forced = False

        # main loop
        while True:
            try:
                # get a timestamp of now
                tst = time()

                # try to read i3status' output for at most INTERVAL seconds else
                # raise the Empty exception
                line = i3status_thread.queue.get(timeout=INTERVAL)
                try:
                    # python3 compatibility code
                    line = line.decode()
                except UnicodeDecodeError:
                    pass

                # i3status first output lines should be processed asap as only
                # the following lines will be processed by py3status
                if i3status_thread.started:
                    if not forced and I3STATUS_CONFIG['interval'] > INTERVAL:
                        # add a calculated sleep honoring py3status refresh
                        # time of the bar every INTERVAL seconds
                        sleep(INTERVAL - float( '{:.2}'.format( time()-tst ) ))
                    else:
                        # reset the SIGUSR1 flag forcing the refresh of the bar
                        forced = False

                # process the output line straight from i3status
                prefix, output_list = process_line(line, delta=0)
                if output_list:
                    modules_thread.i3status_json = output_list
                    print_output(
                        prefix,
                        output_list,
                        modules_thread.cache
                        )
            except Empty:
                # make sure i3status has started before modifying its output
                if i3status_thread.started or not i3status_thread.init:
                    prefix, output_list = process_line(line, delta=INTERVAL)
                    if output_list:
                        modules_thread.i3status_json = output_list
                        line = print_output(
                            prefix,
                            output_list,
                            modules_thread.cache
                            )
                else:
                    syslog(LOG_INFO, "waiting for i3status")
            except UserWarning:
                # SIGUSR1 was received, we also force i3status to refresh by
                # sending it a SIGUSR1 as well then we refresh the bar asap
                msg = sys.exc_info()[1]
                syslog(LOG_INFO, str(msg))
                call(["killall", "-s", "USR1", "i3status"])
                modules_thread.clear()
                forced = True
            except IOError:
                syslog(LOG_WARNING, "ignored an IOError")
            except KeyboardInterrupt:
                break
            finally:
                if threading.active_count() < 3:
                    # i3status or modules thread died ? oops
                    break

        i3status_thread.stop()
        modules_thread.stop()
    except Exception:
        err = sys.exc_info()[1]
        syslog(LOG_ERR, "fatal error (%s)" % str(err))
        sys.exit(2)

if __name__ == '__main__':
    main()
