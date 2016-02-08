#! /usr/bin/env python
#
# ssm/packagefile.py

import os.path
import tarfile
import traceback

from ssm.error import Error

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
            tarf.close()
        except:
            return -1
        finally:
            if tarf:
                tarf.close()
        return 0
