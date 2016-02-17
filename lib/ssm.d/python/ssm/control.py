#! /usr/bin/env python
#
# ssm/control.py

import json
import os.path
import string

class Control:

    def __init__(self, path):
        path = os.path.realpath(path)
        self.path = path
        if os.path.exists(path):
            self.json = json.load(open(path))
        else:
            self.json = self.legacy2json()

    def legacy2json(self):
        try:
            j = {}
            path = os.path.join(os.path.dirname(self.path), "control")
            if os.path.exists(path):
                k = None
                v = []
                for line in open(path):
                    if line.startswith(" "):
                        v.append(line)
                    else:
                        if k != None:
                            j[k] = "\n".join(v)
                        t = map(string.strip, line.split(":", 1))
                        k = t[0].lower()
                        v = [t[1]]
                if k != None:
                    j[k] = "\n".join(v)
        except:
            pass
        return j

