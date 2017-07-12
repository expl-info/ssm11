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

    def load(self):
        if self.exists():
            self.d = json.load(open(self.path))

    def load_legacy(self):
        def put(d, k, v):
            if k == "description":
                d["summary"] = v[0]
                # trim leading space
                v = [x[1:] for x in v[1:]]
            d[k] = "\n".join(v)

        try:
            d = {}
            path = os.path.join(os.path.dirname(self.path), "control")
            if os.path.exists(path):
                k = None
                v = []
                for line in open(path):
                    if line.startswith(" "):
                        v.append(line)
                    else:
                        line = line.strip()
                        if line == "":
                            continue
                        else:
                            if k != None:
                                put(d, k, v)
                            t = map(string.strip, line.split(":", 1))
                            k = t[0].lower().replace(" ", "-")
                            if k == "package":
                                k = "name"
                            v = [t[1]]
                if k != None:
                    put(d, k, v)
        except:
            if globls.debug:
                traceback.print_exc()
        self.d = d

    def set(self, k, v):
        self.d[k] = v

    def store(self):
        json.dump(self.d, open(self.path, "w"), indent=2, sort_keys=True)
