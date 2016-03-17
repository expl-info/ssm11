#! /usr/bin/env python
#
# ssm/package.py

import json
import os
import os.path
import re
import subprocess
import traceback

from ssm.error import Error
from ssm.misc import oswalk1, puts

def determine_platform(pkg=None):
    platform = pkg and pkg.platform
    if platform in [None, "all", "multi"]:
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
        path = os.path.join(relapth, filename)
        if cre.match(path):
            members.append(path)
    return members

class Package:

    def __init__(self, path):
        path = os.path.realpath(path)
        self.path = path
        self.name = os.path.basename(path)
        self.short, self.version, self.platform = self.name.split("_", 2)
        self.control_path = os.path.join(self.path, ".ssm.d/control.json")

    def __str__(self):
        return "<Package name (%s, %s, %s)>" % (self.short, self.version, self.platform)

    __repr__ = __str__

    def execute_script(self, name, dompath):
        path = os.path.join(self.path, ".ssm.d/%s" % name)
        if not os.path.isfile(path):
            return

        args = [path, dompath, self.path]
        try:
            if not os.access(path, os.X_OK):
                raise Exception("script (%s) is not executable" % (path,))
            if os.environ.get("SSM_OLD_PREPOST"):
                cmd.insert(0, "/bin/sh")

            p = subprocess.Popen(args)
            p.wait()
            if p.returncode != 0:
                raise Exception("script (%s) failed" % (path,))
        except:
            traceback.print_exc()
            raise

    def exists(self):
        return os.path.exists(self.path)

    def get_control(self):
        return json.load(open(self.control_path))

    def get_domain(self):
        from ssm.domain import Domain
        return Domain(os.path.dirname(self.path))

    def get_members(self, pattern=None):
        return find_paths(self.path, "", re.compile(pattern or ".*"))

    def set_control(self, d):
        puts(self.control_path, json.dumps(d, indent=2, sort_keys=True))
