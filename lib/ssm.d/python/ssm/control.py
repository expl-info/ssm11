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

    def __init__(self, path, autoload=True):
        path = os.path.realpath(path)
        self.path = path
        self.d = {}
        if autoload:
            self.load()

    def exists(self):
        return os.path.exists(self.path)

    def get(self, k, default=None):
        return self.d.get(k, default)

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

    def load(self):
        if self.exists():
            self.d = json.load(open(self.path))
        elif os.path.exists(self.path[:-4]):
            self.d = self.legacy2json()

    def set(self, k, v):
        self.d[k] = v

    def store(self):
        json.dump(self.d, open(self.path, "w"), indent=2, sort_keys=True)
