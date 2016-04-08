#! /usr/bin/env python
#
# ssm/builder.py

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
            initdotfd, initdotpath = None, None

            self.__unpackbssm()

            initdotfd, initdotpath = tempfile.mkstemp(dir=self.workdir)
            os.write(initdotfd, ". ssmuse-sh -d %s\n" % os.path.realpath(self.dompath))
            if self.initfile:
                os.write(initdotfd, ". %s\n" % self.initfile)
            if self.initpkg:
                os.write(initdotfd, ". ssmuse-sh -p %s\n" % self.initpkg)

            args = self.bcontrol.get("args") or []
            env = self.bcontrol.get("env") or {}
            if self.sourcesurl:
                env["BH_SOURCES_URL"] = self.sourcesurl
            scriptpath = os.path.join(self.bssmtmp, self.bcontrol["bh-script"])
            print self.initfile, self.initpkg
            print scriptpath, args, env
            args = [scriptpath]+args
            for k, v in env.items():
                args.extend(["-v", "%s=%s" % (k, v)])
            args.extend(["-v", "BH_INIT_DOT=%s" % initdotpath])
            #args.extend(["--local"])
            args.extend(["--host", "localhost"])
            args.extend(["-p", self.platform])
            args.extend(["-w", "%s/tmp" % os.getcwd()])
            print "args (%s)" % (args,)
            if 1:
                env = os.environ[:]

                #env["SSM_BUILD_BSSM_FILE"] = self.bssmpath
                env["SSM_BUILD_BSSM_DIR"] = self.bssmtmp
                env["SSM_BUILD_BCONTROL_FILE"] = os.path.join(self.bssmtmp, "control.json")
                env["SSM_BUILD_BUILD_FILE"] = scriptpath
                env["SSM_BUILD_INIT_DOT"] = initdotpath
                env["SSM_BUILD_PACKAGE_NAME"] = self.bcontrol.get("name")
                env["SSM_BUILD_PACKAGE_VERSION"] = self.bcontrol.get("version")
                env["SSM_BUILD_PACKAGE_PLATFORM"] = self.platform
                #env["SSM_BUILD_REPOSITORIES"] = self.repourl
                #env["SSM_BUILD_SOURCES"] = self.sourcesurl
                env["SSM_BUILD_WORKDIR"] = self.workdir

                p = subprocess.Popen(args,
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
            return pkgfpath, None
        except:
            traceback.print_exc()
            pass
        finally:
            if initdotpath:
                os.remove(initdotpath)
            if initdotfd != None:
                os.close(initdotfd)
            self.__cleanbssm()

        return None, Error("error: failed to build")

    def __get_from_domain(self):
        dom = Domain(self.dompath)
        pass
        
    def __get_from_repo(self):
        path = os.path.join(self.repourl, self.name+".ssm")
        if os.path.exists(path):
            return path, None
        else:
            return None, Error("cannot find in repository")

    def run(self):
        pkgfpath, err = self.__get_from_repo()
        if not err:
            return pkgfpath, None
        pkgfpath, err = self.__build_from_source()
        return pkgfpath, err
