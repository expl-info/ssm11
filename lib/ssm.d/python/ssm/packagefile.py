#! /usr/bin/env python
#
# ssm/packagefile.py

import json
import os.path
import string
import tarfile
import traceback

from ssm import globls
from ssm import misc
from ssm.error import Error

def upgrade_legacy_control(path):
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
                            d[k] = "\n".join(v)
                        t = map(string.strip, line.split(":", 1))
                        k = t[0].lower().replace(" ", "-")
                        if k == "package":
                            k = "name"
                        v = [t[1]]
            if k != None:
                d[k] = "\n".join(v)
    except:
        if globls.debug:
            traceback.print_exc()
    return d

class PackageFile:

    def __init__(self, path):
        path = os.path.realpath(path)
        self.path = path
        self.filename = os.path.basename(path)
        self.name = self.filename[:-4]

    def is_valid(self):
        try:
            tarf = None
            tarf = tarfile.open(self.path)
            for member in tarf.getnames():
                if not member.startswith(self.name):
                    return False
        except:
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
            # upgrade legacy control file
            control_path = os.path.join(dstpath, self.name, ".ssm.d/control.json")
            legacy_control_path = os.path.join(dstpath, self.name, ".ssm.d/control")

            if not os.path.exists(control_path):
                if not os.path.exists(legacy_control_path):
                    return Error("missing control file")
                d = upgrade_legacy_control(legacy_control_path)
                if not misc.puts(control_path, json.dumps(d, indent=2, sort_keys=True)):
                    return Error("cannot write new control file")
            else:
                d = json.load(open(control_path))

            ft = self.name.split("_", 2)
            ct = d.get("name"), d.get("version"), d.get("platform")
            if ct[0] != ft[0]:
                return Error("bad control file name mismatch (%s, %s)" % (ct[0], ft[0]))
            if ct[1] != ft[1]:
                return Error("bad control file version mismatch (%s, %s)" % (t[1], ft[1]))
            if ct[2] != ft[2]:
                return Error("bad control file platform mismatch (%s, %s)" % (ct[2], ft[2]))
        except:
            if globls.debug:
                traceback.print_exc()
            return Error("bad control file")
