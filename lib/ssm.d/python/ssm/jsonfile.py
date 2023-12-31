#! /usr/bin/env python2
#
# ssm/jsonfile.py

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

class JsonFile:

    def __init__(self):
        self.d = {}

    def clear(self):
        self.d = {}

    def dump(self, path, indent=2, sort_keys=False):
        return json.dump(self.d, open(path, "w"), indent=indent, sort_keys=sort_keys)

    def dumps(self, indent=2, sort_keys=False):
        return json.dumps(self.d, indent=indent, sort_keys=sort_keys)

    def get(self, k, default=None):
        return self.d.get(k, default)

    def getall(self):
        return self.d

    def load(self, path):
        if os.path.exists(path):
            self.d.update(json.load(open(path)))

    def set(self, k, v):
        self.d[k] = v
