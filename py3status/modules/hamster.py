# -*- coding: utf-8 -*-

# For more information read:
# i3wm homepage: http://i3wm.org
# py3status homepage: https://github.com/ultrabug/py3status

# Copyright (C) <2015> <Aaron Fields (spirotot [at] gmail.com)>

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import subprocess
from time import time

class Py3status:
    def hamster(self, json, i3status_config):
        cur_task = subprocess.check_output(['hamster', 'current']).strip()
        if cur_task != "No activity":
            cur_task = cur_task.split()
            time_elapsed = cur_task [-1]
            cur_task = cur_task[2:-1]
            cur_task = "%s (%s)" % (" ".join(cur_task), time_elapsed)
        response = {'full_text': '', 'name': 'hamster'}
        response['full_text'] = cur_task
        response['cached_until'] = time()
        return (0, response)
