# -*- coding: utf-8 -*-

# sysdata

# Sysdata is a module uses great Py3status (i3status wrapper) to
# display system information (RAM usage) in i3bar (Linux systems).
# For more information read:
# i3wm homepage: http://i3wm.org
# py3status homepage: https://github.com/ultrabug/py3status

# Copyright (C) <2013> <Shahin Azad [ishahinism at Gmail]>

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


class GetData:
    """Get system status

    """
    def execCMD(self, cmd, arg):
        """Take a system command and its argument, then return the result.

        Arguments:
        - `cmd`: system command.
        - `arg`: argument.
        """
        result = subprocess.check_output([cmd, arg])
        return result

    def memory(self):
        """Execute 'free -m' command, grab the memory capacity and used size
        then return; Memory size 'total_mem', Used_mem, and percentage
        of used memory.

        """
        # Run 'free -m' command and make a list from output.
        mem_data = self.execCMD('free', '-m').split()
        total_mem = int(mem_data[7]) / 1024.
        used_mem = int(mem_data[15]) / 1024.
        # Caculate percentage
        used_mem_percent = int(used_mem / (total_mem / 100))

        # Results are in kilobyte.
        return total_mem, used_mem, used_mem_percent


class Py3status:
    """
    System status in i3bar
    """
    def ramInfo(self, json, i3status_config):
        """calculate the memory (RAM) status and return it.

        """
        data = GetData()
        response = {'full_text': '', 'name': 'ram_info'}
        total_mem, used_mem, used_mem_percent = data.memory()

        if used_mem_percent <= 40:
            response['color'] = i3status_config['color_good']
        elif used_mem_percent <= 75:
            response['color'] = i3status_config['color_degraded']
        else:
            response['color'] = i3status_config['color_bad']

        response['full_text'] = "RAM: %.2f/%.2f GB (%d%%)" % \
                                (used_mem, total_mem, used_mem_percent)
        response['cached_until'] = time()

        return (0, response)
