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

from json import loads
from json import dumps

from time import time
from time import sleep

from datetime import datetime
from datetime import timedelta

from Queue import Queue
from Queue import Empty

from syslog import syslog
from syslog import LOG_ERR

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

def i3status_config_reader():
	"""
	i3status.conf reader so we can adapt our code to the i3status config
	"""
	in_time = False
	in_general = False
	config = {
		'colors': False,
		'color_good': None,
		'color_bad' : None,
		'color_degraded' : None,
		'color_separator': None,
		'interval': 5,
		'output_format': None,
		'time_format': '%Y-%m-%d %H:%M:%S',
		}
	for line in open(I3STATUS_CONFIG_FILE, 'r'):
		line = line.strip(' \t\n\r')
		if line.startswith('general'):
			in_general = True
		elif line.startswith('time'):
			in_time = True
		elif line.startswith('}'):
			in_general = False
			in_time = False
		if in_general and '=' in line:
			key, value = line.split('=')[0].strip(), line.split('=')[1].strip()
			if config.has_key(key):
				if value in ['true', 'false']:
					value = 'True' if value == 'true' else 'False'
				config[key] = eval(value)
		if in_time and '=' in line:
			key, value = line.split('=')[0].strip(), line.split('=')[1].strip()
			if config.has_key('time_' + key):
				config['time_' + key] = eval(value)
	return config

def i3status(message_queue, stop_thread):
	"""
	Execute i3status in a thread and send its output to a Queue to py3status
	"""
	from subprocess import Popen, PIPE
	i3status_pipe = Popen(['i3status', '-c', I3STATUS_CONFIG_FILE], stdout=PIPE, stderr=PIPE)
	message_queue.put(i3status_pipe.stdout.readline())
	message_queue.put(i3status_pipe.stdout.readline())
	while not stop_thread:
		line = i3status_pipe.stdout.readline()
		if line != '':
			message_queue.put(line)
		else:
			break

def process_line(line, **kwargs):
	"""
	Main line processor logic
	"""
	if line.startswith('{') and 'version' in line:
		print_line(line.strip('\n'))
	elif line == '[\n':
		print_line(line.strip('\n'))
	else:
		prefix = ''
		if line.startswith(','):
			line, prefix = line[1:], ','
		elif kwargs['delta'] > 0:
			prefix = ','

		# integrated transformations
		if not DISABLE_TRANSFORM:
			j = transform(loads(line), **kwargs)
		else:
			j = loads(line)

		# user-based injection and transformation
		j = inject(j)

		print_line(prefix+dumps(j))

def inject(j):
	"""
	Run on every user class included and execute every method on the json,
	then inject the result at the start of the json
	"""
	# inject our own functions' results
	for my_class in USER_CLASSES.keys():
		for my_method in USER_CLASSES[my_class]:
			try:
				# handle a cache on user class methods results
				try:
					index, result = USER_CACHE[my_method]
					if time() > result['cached_until']:
						raise KeyError, 'cache timeout'
				except KeyError:
					# execute the method
					try:
						meth = getattr(my_class, my_method)
						index, result = meth(j, I3STATUS_CONFIG)
					except Exception, err:
						syslog(LOG_ERR, "user method %s failed (%s)" % (my_method, str(err)))
						index, result = (0, {'name': '', 'full_text': ''})

					# respect user-defined cache timeout for this module
					if not result.has_key('cached_until'):
						result['cached_until'] = time() + CACHE_TIMEOUT

					# validate the response
					assert isinstance(result, dict), "user method didn't return a dict"
					assert result.has_key('full_text'), "missing 'full_text' key"
					assert result.has_key('name'), "missing 'name' key"
				finally:
					USER_CACHE[my_method] = (index, result)
					j.insert(index, result)
			except Exception, err:
				syslog(LOG_ERR, "injection failed (%s)" % str(err))
	return j

def transform(j, **kwargs):
	"""
	Integrated transformations:
	- update the 'time' object so that it's updated at INTERVAL seconds
	- update the 'run_watch' objects so that we rely on the color instead of useless 'yes' or 'no' status
	"""
	for item in j:
		# time modification
		if item['name'] == 'time':
			date = datetime.strptime(item['full_text'], I3STATUS_CONFIG['time_format']) + timedelta(seconds=kwargs['delta'])
			item['full_text'] = date.strftime(I3STATUS_CONFIG['time_format'])
	return j

def load_from_file(filepath):
	"""
	Load Py3status user class for later injection
	"""
	inst = None
	expected_class = 'Py3status'
	mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])
	if file_ext.lower() == '.py':
		py_mod = imp.load_source(mod_name, filepath)
		if hasattr(py_mod, expected_class):
			inst = py_mod.Py3status()
	return (mod_name, inst)

# main stuff
################################################################################
def main():
	try:
		# global definition
		global CACHE_TIMEOUT, DISABLE_TRANSFORM, I3STATUS_CONFIG_FILE
		global I3STATUS_CONFIG, INCLUDE_PATH, INTERVAL, USER_CACHE, USER_CLASSES

		# command line options
		PARSER = argparse.ArgumentParser(description='The agile, python-powered, i3status wrapper')
		PARSER = argparse.ArgumentParser(add_help=True)
		PARSER.add_argument('-c', action="store", dest="i3status_conf", type=str, default="/etc/i3status.conf", help="path to i3status config file")
		PARSER.add_argument('-d', action="store_true", dest="disable_transform", help="disable integrated transformations")
		PARSER.add_argument('-i', action="store", dest="include_path", type=str, default='.i3/py3status', help="user-based class include directory")
		PARSER.add_argument('-n', action="store", dest="interval", type=int, default=1, help="polling interval in seconds (default 1 sec)")
		PARSER.add_argument('-t', action="store", dest="cache_timeout", type=int, default=60, help="injection cache timeout in seconds (default 60 sec)")
		OPTS = PARSER.parse_args()

		# globals
		CACHE_TIMEOUT = OPTS.cache_timeout
		DISABLE_TRANSFORM = True if OPTS.disable_transform else False
		I3STATUS_CONFIG_FILE = OPTS.i3status_conf
		I3STATUS_CONFIG = i3status_config_reader()
		INCLUDE_PATH = os.path.abspath( OPTS.include_path ) + '/'
		INTERVAL = OPTS.interval
		DELTA = 0

		# py3status uses only the i3bar protocol
		assert I3STATUS_CONFIG['output_format'] == 'i3bar', 'unsupported output_format'

		# dynamic inclusion
		USER_CACHE = {}
		USER_CLASSES = {}
		if INCLUDE_PATH and os.path.isdir(INCLUDE_PATH):
			for fn in os.listdir(INCLUDE_PATH):
				module, class_inst = load_from_file(INCLUDE_PATH + fn)
				if module and class_inst:
					USER_CLASSES[class_inst] = []
					for method in dir(class_inst):
						if not method.startswith('__'):
							USER_CLASSES[class_inst].append(method)

		# run threaded i3status
		STOP_THREAD = False
		MESSAGE_QUEUE = Queue()
		I3STATUS_THREAD = threading.Thread(target=i3status, name='i3status', args=(MESSAGE_QUEUE, STOP_THREAD, ))
		I3STATUS_THREAD.start()

		# main loop
		while True:
			try:
				TS = time()
				LINE = MESSAGE_QUEUE.get(timeout=INTERVAL)
				if LINE.startswith(',['):
					sleep( INTERVAL - float( '{:.2}'.format( time()-TS ) ) )
				process_line(LINE, delta=0)
				DELTA = 0
			except Empty:
				DELTA += INTERVAL
				process_line(LINE, delta=DELTA)
				if threading.active_count() < 2:
					break
			except KeyboardInterrupt:
				break

		STOP_THREAD = True
		I3STATUS_THREAD.join()
	except Exception, err:
		syslog(LOG_ERR, "py3status error (%s)" % str(err))
		sys.exit(1)

if __name__ == '__main__':
	main()
