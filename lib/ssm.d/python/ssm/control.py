#! /usr/bin/env python2
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

import os.path
import string
import traceback

from ssm import globls
from ssm.jsonfile import JsonFile2

class Control(JsonFile2):

    def __init__(self):
        JsonFile2.__init__(self)

    def load_legacy(self, path):
        def put(d, k, v):
            if k == "description":
                d["summary"] = v[0]
                # trim leading space
                v = [x[1:] for x in v[1:]]
            d[k] = "\n".join(v)

        try:
            d = {}
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
