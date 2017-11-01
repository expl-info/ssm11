#! /usr/bin/env python
#
# ssm/builder.py

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
import shutil
import subprocess
import tarfile
import tempfile
import time
import traceback

from ssm.error import Error
from ssm import misc

class Builder:

    def __init__(self, workdir, bssmpath, sourcesurl, dompath, repourl, platform, initfile, initpkg):
        self.workdir = workdir
        self.bssmpath = bssmpath
        self.sourcesurl = sourcesurl
        self.dompath = dompath
        self.repourl = repourl
        try:
            self.bcontrol = dict(json.load(tarfile.open(bssmpath).extractfile("bcontrol.json")))
        except:
            self.bcontrol = {}
        self.platform = self.bcontrol.get("platform") or platform
        self.initfile = initfile
        self.initpkg = initpkg
        self.name = "%s_%s_%s" % (self.bcontrol["name"], self.bcontrol["version"], self.platform)
        self.bssmtmp = None

    def __del__(self):
        """Clean up.
        """
        self.__cleanbssm()

    def __cleanbssm(self):
        if self.bssmtmp:
            shutil.rmtree(self.bssmtmp)
            self.bssmtmp = None

    def __unpackbssm(self):
        try:
            self.bssmtmp = tempfile.mkdtemp(dir=self.workdir)
            tarf = tarfile.open(self.bssmpath)
            for name in tarf.getnames():
                path = os.path.normpath(os.path.join(self.bssmtmp, name))
                if not path.startswith(self.bssmtmp):
                    raise Exception("fatal: refuse to unpack bad member path")
            tarf.extractall(self.bssmtmp)
        except:
            self.__cleanbssm()

    def __build_from_source(self):
        try:
            self.__unpackbssm()

            # setup initfile and initpkg
            initdotfd, initdotpath = tempfile.mkstemp(dir=self.workdir)
            os.write(initdotfd, ". ssmuse-sh -d %s\n" % os.path.realpath(self.dompath))
            if self.initfile:
                os.write(initdotfd, ". %s\n" % self.initfile)
            if self.initpkg:
                os.write(initdotfd, ". ssmuse-sh -p %s\n" % self.initpkg)

            # build command to run
            buildfile = os.path.join(self.bssmtmp, self.bcontrol.get("build-script", "build.sh"))

            # prep env for command
            env = os.environ[:]
            env["SSM_BUILD_BCONTROL_FILE"] = os.path.join(self.bssmtmp, "control.json")
            env["SSM_BUILD_BSSM_DIR"] = self.bssmtmp
            env["SSM_BUILD_BUILD_FILE"] = buildfile
            env["SSM_BUILD_INIT_DOT"] = initdotpath
            env["SSM_BUILD_PACKAGE_NAME"] = self.bcontrol.get("name")
            env["SSM_BUILD_PACKAGE_PLATFORM"] = self.platform
            env["SSM_BUILD_PACKAGE_VERSION"] = self.bcontrol.get("version")
            env["SSM_BUILD_SOURCES_DIR"] = self.sourcesurl
            env["SSM_BUILD_WORK_DIR"] = self.workdir

            p = subprocess.Popen([buildfile],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=False,
                env=env)
            out, err = p.communicate()
            if p.returncode != 0:
                print "out (%s) err (%s) returncode (%s)" % (out, err, p.returncode)
                raise Exception()

            # move to repo?
            pkgfpath = "%s/%s.ssm" % (os.getcwd(), self.name)
            return pkgfpath
        except:
            traceback.print_exc()
            pass
        finally:
            # clean up
            if initdotpath:
                os.remove(initdotpath)
            if initdotfd != None:
                os.close(initdotfd)
            self.__cleanbssm()

        return Error("error: failed to build")

    def __get_from_domain(self):
        dom = Domain(self.dompath)
        pass
        
    def __get_from_repo(self):
        path = os.path.join(self.repourl, self.name+".ssm")
        if os.path.exists(path):
            return path
        return Error("cannot find in repository")

    def run(self):
        pkgfpath = err = self.__get_from_repo()
        if not isinstance(err, Error):
            return pkgfpath
        return self.__build_from_source()
