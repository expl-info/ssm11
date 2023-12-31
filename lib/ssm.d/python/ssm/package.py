#! /usr/bin/env python2
#
# ssm/package.py

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
import os
import os.path
import re
import subprocess
import traceback

from ssm import globls
from ssm.control import Control
from ssm.misc import oswalk1, puts

def determine_platform(pkg=None):
    platform = pkg and pkg.platform
    if platform in globls.disabled_publish_platforms:
        platform = os.environ.get("SSM_PLATFORM")
    return platform

def determine_platforms():
    if "SSM_PLATFORMS" in os.environ:
        platforms = os.environ.get("SSM_PLATFORMS")
    elif "SSMUSE_PLATFORMS" in os.environ:
        platforms = os.environ["SSMUSE_PLATFORMS"]
    else:
        platforms = None
    platforms = platforms and platforms.split() or []
    return platforms

def find_paths(basepath, relpath, cre):
    members = []
    _, dirnames, filenames = oswalk1(os.path.join(basepath, relpath))
    for dirname in dirnames:
        path = os.path.join(relpath, dirname)
        if cre.match(path):
            members.extend(find_paths(basepath, path, cre))
    for filename in filenames:
        path = os.path.join(relpath, filename)
        if cre.match(path):
            members.append(path)
    return members

def split_pkgref(pkgref):
    """Split pkgref into dompath, pkgname, platform.
    """
    try:
        pkgref = os.path.abspath(pkgref)
        pkgref = pkgref.rstrip("/")
        l = pkgref.rsplit("/", 1)
        if len(l) == 2:
            dompath, pkgname = l
        else:
            dompath, pkgname = ".", l[0]
        _, platform = pkgname.rsplit("_", 1)
    except:
        return None
    return dompath, pkgname, platform

class Package:

    def __init__(self, path, splitname=True):
        path = os.path.abspath(path)
        self.path = path
        self.realpath = os.path.realpath(path)
        self.name = os.path.basename(path)
        if splitname:
            self.short, self.version, self.platform = self.name.split("_", 2)
        else:
            self.short, self.version, self.platform = self.name, None, None
        self.control_path = self.joinpath(".ssm.d/control.json")
        self.control_path_legacy = self.joinpath(".ssm.d/control")

    def __str__(self):
        return "<Package name (%s, %s, %s)>" % (self.short, self.version, self.platform)

    __repr__ = __str__

    def execute_script(self, name, dompath):
        path = self.joinpath(".ssm.d", name)
        if not os.path.isfile(path):
            return

        args = [path, dompath, self.path]
        try:
            if not os.access(path, os.X_OK):
                raise Exception("script (%s) is not executable" % (path,))

            env = os.environ.copy()
            if env.get("SSM_OLD_PREPOST"):
                cmd.insert(0, "/bin/sh")

            env["SSM_INSTALL_DOMAIN_HOME"] = dompath
            env["SSM_INSTALL_PACKAGE_HOME"] = self.path
            env["SSM_INSTALL_PROFILE_PATH"] = self.joinpath("etc/profile.d", "%s.sh" % self.name)
            env["SSM_INSTALL_LOGIN_PATH"] = self.joinpath("etc/profile.d", "%s.csh" % self.name)

            p = subprocess.Popen(args, env=env)
            p.wait()
            if p.returncode != 0:
                raise Exception("script (%s) failed" % (path,))
        except:
            traceback.print_exc()
            raise

    def exists(self):
        return os.path.exists(self.path)

    def get_control(self, legacy=False):
        control = Control()
        if legacy:
            control.load_legacy(self.control_path_legacy)
        else:
            control.load(self.control_path)
        return control

    def get_domain(self):
        from ssm.domain import Domain
        return Domain(os.path.dirname(self.path))

    def get_members(self, pattern=None):
        return find_paths(self.path, "", re.compile(pattern or ".*"))

    def has_control(self, legacy=False):
        if legacy:
            return os.path.exists(self.control_path_legacy)
        else:
            return os.path.exists(self.control_path)

    def joinpath(self, *comps):
        return os.path.join(self.path, *comps)

    def put_control(self, control):
        path = os.path.dirname(self.control_path)
        if not os.path.exists(path):
            os.makedirs(path)
        control.dump(self.control_path)
