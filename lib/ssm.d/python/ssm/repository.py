#! /usr/bin/env python
#
# ssm/repository.py

# GPL--start
# This file is part of ssm (Simple Software Manager)
# Copyright (C) 2005-2017 Environment/Environnement Canada
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

from ssm.packagefile import PackageFile

class Repository:

    def __init__(self, url):
        self.url = url

    def get_packagefile(self, name):
        try:
            path = os.path.join(self.url, "%s.ssm" % name)
            return PackageFile(path)
        except:
            return None

    def get_url(self):
        return self.url
