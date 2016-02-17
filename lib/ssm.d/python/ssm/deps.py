#! /usr/bin/env python
#
# deps.py

import operator
import re
import string

testablere = """^(?P<name>[a-zA-Z][a-zA-Z0-9-]*)(\s*(?P<op>\<|\<=|==|\>=|\>|\!=|~)\s*(?P<value>([0-9]+(\.[0-9]+)*([\+\-a-zA-Z0-9]*))))?$"""
testablecre = re.compile(testablere)

sop2op = {
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    ">=": operator.ge,
    ">": operator.gt,
    "!=": operator.ne,
}
op2sop = dict([(v, k) for k, v in sop2op.items()])

def uniq(l):
    m = {}
    ll = []
    for x in l:
        if x not in m:
            m[x] = None
            ll.append(x)
    return ll

def version2tuple(s):
    l = [int(v) if v.isdigit() else v for v in s.split(".")]
    return tuple(l)

class Provider:

    def __init__(self, name, version=None):
        self.name = name
        self.version = version
        self.versiont = version and version2tuple(version)
        #print "Provider (%s, %s, %s)" % (name, version, self.versiont)

    def __str__(self):
        return "<Provider (%s, %s)>" % (self.name, self.version)

    def __repr__(self):
        return self.__str__()

class Testable:

    def __init__(self, testspec):
        self.testspec = testspec
        self.__parse(testspec)

    def __str__(self):
        return "<Testable (%s)>" % (self.testspec,)

    def __repr__(self):
        return self.__str__()

    def __parse(self, testspec):
        try:
            d = testablecre.match(testspec).groupdict()
            if d["op"] == None:
                self.name = d["name"]
                self.op = None
                self.version = None
                self.versiont = None
            elif len(d) == 3:
                self.name = d["name"]
                self.op = sop2op[d["op"]]
                self.version = d["value"]
                self.versiont = version2tuple(d["value"])
            else:
                raise Exception()
        except:
            traceback.print_exc()
            raise Exception("bad test expression")

    def test(self, prov):
        if prov:
            if self.name == prov.name:
                if not self.op:
                    return True
                return self.op(prov.versiont, self.versiont)
        return False

class Requirement(Testable):

    def __init__(self, *args):
        Testable.__init__(self, *args)
        #print "Requirement testspec (%s)" % (self.testspec,)

    def __str__(self):
        return "<Requirement (%s)>" % (self.testspec,)

class Conflict(Testable):

    def __init__(self, *args):
        Testable.__init__(self, *args)
        #print "Conflict testspec (%s)" % (self.testspec,)

    def __str__(self):
        return "<Conflict (%s)>" % (self.testspec,)

    def test(self, prov):
        return not Testable.test(prov)

class DependencyManager:

    def __init__(self):
        self.name2provider = {}
        self.name2requires = {}
        self.name2provides = {}
        self.name2conflicts = {}
        self.name2requiredby = {}

    def add(self, name, version, requires=None, provides=None, conflicts=None):
        if name in self.name2provider:
            prov = self.name2provider[name]
            raise Exception("duplicate (%s) found with provider (%s)" % (name, prov))
        prov = Provider(name, version)
        self.name2provider[name] = prov

        if requires:
            requires = map(string.strip, requires.split(","))
            self.name2requires[name] = [Requirement(testspec) for testspec in requires]
            for require in self.name2requires[name]:
                #print "name (%s) require (%s)" % (name, require)
                l = self.name2requiredby.setdefault(require.name, [])
                l.append(name)

        if provides:
            l = self.name2provides[name] = []
            provides = map(string.strip, provides.split(","))
            for pprov in provides:
                pprov = Provider(pprov)
                l.append(pprov)
                if 1 or pprov.name not in self.name2provider:
                    self.name2provider[pprov.name] = pprov
                    self.name2requires[pprov.name] = [Requirement(prov.name)]
                else:
                    dprov = self.name2provider[pprov.name]
                    raise Exception("duplicate provider (%s) found" % (dprov,))
                    
        if conflicts:
            conflicts = map(string.strip, conflicts.split(","))
            self.name2conflicts[name] = [Conflict(testspec) for testspec in conflicts]

    def verify(self):
        pass

    def get_names(self):
        return self.name2provider.keys()

    def get_requiredby(self, names, indirect=False):
        """Get list of names required by given list. An indirect
        search will return directly and indirectly required names.
        """
        if indirect:
            seen = set()
            names = set(names)
            while names:
                name = names.pop()
                seen.add(name)
                _names = self.name2requiredby.get(name, [])
                for name in _names:
                    if name not in seen:
                        names.add(name)
            names = seen
        else:
            names = set([names for names in self.name2requiredby.get(name)])
        return names

    def _generate(self, name):
        deps = []
        prov = self.name2provider[name]
        if not prov:
            raise Exception("cannot find name (%s)" % (name,))
        confs = self.name2conflicts.get(name) or []
        for conf in confs:
            tprov = self.name2provider.get(conf.name)
            if conf.test(tprov):
                    raise Exception("conflict (%s) found for provide (%s)" % (conf, tprov))
        reqs = self.name2requires.get(name) or []
        for req in reqs:
            tprov = self.name2provider.get(req.name)
            #print "prov (%s) req (%s) tprov (%s)" % (prov, req, tprov)
            if not tprov:
                raise Exception("cannot find/missing name (%s)" % (req.name,))
            if not req.test(tprov):
                raise Exception("require (%s) does not satisfy provide (%s)" % (req, tprov.name))
            deps.append(req.name)
        return deps

    def generate(self, names):
        """Generate dependency list of named packages (or all if not
        specified).
        """
        deps = names
        newdeps = deps[:]
        while newdeps:
            _deps = []
            for newname in newdeps:
                _deps.extend(self._generate(newname))
            deps.extend(_deps)
            newdeps = _deps
        return uniq(reversed(deps))

if __name__ == "__main__":
    import sys

    if 0:
        try:
            dm = DependencyManager()
            dm.add("openmpi", "1.6.5", "netcdf")
            dm.add("netcdf-fortran", "4.4.2", "netcdf >= 4.3")
            dm.add("netcdf", "4.3.1", "hdf5 >= 1.8")
            dm.add("hdf5", "1.8.3")
            dm.add("gcc", "4.9", None, "c-compiler, fortran-compiler")
        except Exception as e:
            print "error: %s" % (e,)
            sys.exit(1)

        try:
            print dm.generate(sys.argv[1])
        except Exception as e:
            print "error: %s" % (e,)
            sys.exit(1)

    if 1:
        import json
        import os

        buildspecsdir = sys.argv[1]
        targetnames = sys.argv[2:]

        dm = DependencyManager()
        for name in os.listdir(buildspecsdir):
            bs = json.load(open("%s/%s" % (buildspecsdir, name)))
            print "loading (%s)" % (name,)
            dm.add(bs.get("name"),
                bs.get("version"),
                bs.get("requires", None),
                bs.get("provides", None),
                bs.get("conflicts", None))
            print "-----"
        print "====="
        print dm.name2provider
        print "====="
        xtargetnames = dm.generate(targetnames)
        print xtargetnames
        providers = map(dm.name2provider.get, xtargetnames)
        print providers
