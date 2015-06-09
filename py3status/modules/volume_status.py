"""
Show current volume from amixer.
Reads the current Master volume from amixer.
Configuration parameters:
	- format : format the output, available variables: {percentage}
	- format_mute : format the output when the volume is muted
	- cache_timeout : 0 by default, you usually want continuous monitoring
	- threshold_degraded : 50 by default, percentage to change color to color_degraded
	- threshold_bad : 20 by default, percentage to change color to color_bad
	- color_good : #00FF00 by default, good volume color
	- color_degraded : #FFFF00 by default, degraded volume color
	- color_bad : #FF0000 by default, bad volume color
	- channel : "Master" by default, alsamixer channel to track
@author <Jan T> <jans.tuomi@gmail.com>
@license BSD
"""

from time import time
import re
from subprocess import check_output


class Py3status:
	format = "{percentage}%"
	format_mute = "mute"
	cache_timeout = 0

	threshold_degraded = 50
	threshold_bad = 20

	color_good = "#00FF00"
	color_degraded = "#FFFF00"
	color_bad = "#FF0000"

	channel = "Master"

	def __init__(self):
		self.text = ""

	def _perc_to_color(self, string):
		try:
			value = int(string)
		except ValueError:
			return self.color_bad

		if value < self.threshold_bad:
			return self.color_bad
		elif value < self.threshold_degraded:
			return self.color_degraded
		else:
			return self.color_good

	# return the format string formatted with available variables
	def _format_output(self, format, percentage):
		text = format
		text = text.replace("{percentage}", percentage)
		return text

	# return the current channel volume value as a string
	def _get_percentage(self, output):
		prog = re.compile(r"\[\d{1,3}%\]")
		text = prog.findall(output)[0][1:-2]
		return text

	# returns True if the channel is muted
	def _get_muted(self, output):
		prog = re.compile(r"\[\w{2,3}\]")
		text = prog.findall(output)[0][1:-1]
		return text == "off"

	# this method is ran by py3status
	# returns a response dict
	def current_volume(self, i3s_output_list, i3s_config):

		# call amixer
		output = check_output(["amixer", "sget", self.channel]).decode()
	
		# get the current percentage value
		perc = self._get_percentage(output)

		# get info about channel mute status
		muted = self._get_muted(output)

		# determine the color based on the current volume level
		color = self._perc_to_color(perc)

		# format the output
		text = self._format_output(self.format_mute if muted else self.format, perc)

		# if the text has been changed, update the cached text and
		# set transformed to True
		transformed = text != self.text
		self.text = text

		# create response dict
		response = {
			'cached_until': time() + self.cache_timeout,
			'full_text': text,
			'transformed': transformed,
			'color': color
		}
		return response

	# open alsamixer on click
	def on_click(self, i3s_output_list, i3s_config, event):
		check_output(["i3-sensible-terminal", "-e", "alsamixer"])

# test if run directly
if __name__ == "__main__":
	from time import sleep
	x = Py3status()
	config = {}

	while True:
		print(x.current_volume([], config))
		sleep(1)
