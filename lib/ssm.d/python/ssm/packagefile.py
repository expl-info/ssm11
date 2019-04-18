#! /usr/bin/env python2
#
# ssm/packagefile.py

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
import tarfile
import traceback

from ssm.constants import *
from ssm import globls
from ssm import misc
from ssm.control import Control
from ssm.error import Error
from ssm.package import Package

class PackageFile:

    def __init__(self, path):
        path = os.path.realpath(path)
        self.path = path
        self.filename = os.path.basename(path)
        self.name = self.filename[:-4]

    def exists(self):
        return os.path.exists(self.path)

    def is_valid(self):
        try:
            tarf = None
            tarf = tarfile.open(self.path)
            for member in tarf.getnames():
                if not member.startswith(self.name):
                    return False
        except:
            if globls.debug:
                traceback.print_exc()
            return False
        finally:
            if tarf:
                tarf.close()
        return True

    def unpack(self, dstpath):
        try:
            tarf = None
            tarf = tarfile.open(self.path)
            tarf.extractall(dstpath)
        except:
            if globls.debug:
                traceback.print_exc()
            return Error("could not unpack package file")
        finally:
            if tarf:
                tarf.close()

        try:
            # upgrade legacy control file (if necessary)
            pkg = Package(os.path.join(dstpath, self.name))
            if not pkg.has_control():
                control = pkg.get_control(legacy=True)
                if control.get("name") == None:
                    return Error("missing control file")

                ft = self.name.split("_", 2)
                ct = control.get("name"), control.get("version"), control.get("platform")
                if ct[0] != ft[0]:
                    return Error("bad control file name mismatch (%s, %s)" % (ct[0], ft[0]))
                if ct[1] != ft[1]:
                    return Error("bad control file version mismatch (%s, %s)" % (t[1], ft[1]))
                if ct[2] != ft[2]:
                    return Error("bad control file platform mismatch (%s, %s)" % (ct[2], ft[2]))

                pkg.put_control(control)
        except:
            if globls.debug:
                traceback.print_exc()
            return Error("bad control file")

class PackageFileSkeleton(PackageFile):

    def __init__(self, path, components=None):
        PackageFile.__init__(self, path)
        self.components = components

    def exists(self):
        return True

    def is_valid(self):
        return True

    def unpack(self, dstpath):
        try:
            pkg = Package(os.path.join(dstpath, self.name))

            if "control" in self.components:
                control = pkg.get_control()
                control.set("name", pkg.short)
                control.set("version", pkg.version)
                control.set("platform", pkg.platform)
                control.set("summary", self.name)
                pkg.put_control(control)

            if "pubdirs" in self.components:
                for name in PUBLISHABLE_DIRS:
                    path = os.path.join(pkg.path, name)
                    if not os.path.exists(path):
                        os.makedirs(path)
        except:
            if globls.debug:
                traceback.print_exc()
            return Error("could not unpack skeleton package file")
