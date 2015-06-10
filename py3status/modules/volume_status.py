#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Display current sound volume using amixer.
Expands on the standard i3status volume module by adding color and percentage threshold settings.

NOTE: 	If you want to refresh the module quicker than the i3status interval,
	send a USR1 signal to py3status in the keybinding.
	Example: killall -s USR1 py3status

Dependencies:
	alsa-utils (tested with alsa-utils 1.0.29-1)

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
	format = "♪: {percentage}%"
	format_muted = "♪: muted"
	cache_timeout = 0

	threshold_degraded = 50
	threshold_bad = 20

	color_good = "#00FF00"
	color_degraded = "#FFFF00"
	color_bad = "#FF0000"

	channel = "Master"

	# constructor
	def __init__(self):
		self.text = ""

	# compares current volume to the thresholds, returns a color code
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

		# attempt to find a percentage value in square brackets
		p = re.compile(r"(?<=\[)\d{1,3}(?=%\])")
		text = p.search(output).group()

		# check if the parsed value is sane by checking if it's an integer
		try:
			int(text)
			return text

		# if not, show an error message in output
		except ValueError:
			return "Error: Can't parse amixer output."

	# returns True if the channel is muted
	def _get_muted(self, output):
		p = re.compile(r"(?<=\[)\w{2,3}(?=\])")
		text = p.search(output).group()

		# check if the parsed string is either "off" or "on"
		if text in ["on", "off"]:
			return text == "off"

		# if not, return False
		else:
			return False

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
		text = self._format_output(self.format_muted if muted else self.format, perc)

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
