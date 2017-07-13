#! /usr/bin/env python
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

    def __init__(self, path, autoload=True):
        self.path = os.path.realpath(path)
        self.d = {}
        if autoload:
            self.load()

    def dumps(self, indent=2, sort_keys=False):
        return json.dumps(self.d, indent=indent, sort_keys=sort_keys)

    def exists(self):
        return os.path.exists(self.path)

    def get(self, k, default=None):
        return self.d.get(k, default)

    def load(self):
        if self.exists():
            self.d = json.load(open(self.path))

    def set(self, k, v):
        self.d[k] = v

    def setstore(self, k, v):
        self.set(k, v)
        self.store()

    def store(self):
        json.dump(self.d, open(self.path, "w"), indent=2, sort_keys=True)
