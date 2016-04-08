#! /usr/bin/env python
#
# ssm/control.py

# GPL--start
# This file is part of ssm (Simple Software Manager)
# Copyright (C) 2005-2012 Environment/Environnement Canada
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# GPL--end

import json
import os.path
import string

class Control:

    def __init__(self, path):
        path = os.path.realpath(path)
        self.path = path
        if os.path.exists(path):
            self.json = json.load(open(path))
        else:
            self.json = self.legacy2json()

    def legacy2json(self):
        try:
            j = {}
            path = os.path.join(os.path.dirname(self.path), "control")
            if os.path.exists(path):
                k = None
                v = []
                for line in open(path):
                    if line.startswith(" "):
                        v.append(line)
                    else:
                        if k != None:
                            j[k] = "\n".join(v)
                        t = map(string.strip, line.split(":", 1))
                        k = t[0].lower()
                        v = [t[1]]
                if k != None:
                    j[k] = "\n".join(v)
        except:
            pass
        return j

