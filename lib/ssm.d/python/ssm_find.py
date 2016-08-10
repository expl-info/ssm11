#! /usr/bin/env python
#
# ssm_find.py

"""Provides the find subcommand.
"""

import fnmatch
import os
import re
import sys
from sys import stderr, stdout
import traceback

from ssm import globls
from ssm.domain import Domain
from ssm.error import Error
from ssm.misc import columnize, exits, get_terminal_size
from ssm.package import determine_platforms

class DirWalker:
    """Walks directory trees returning full paths. For each path
    returned by next(), it is possible to tell DirWalker to skip the
    latest directory (i.e., do not descend).
    """

    def __init__(self, path, dirsonly=False):
        self.dirsonly = dirsonly
        self.skipname = False
        self.stack = []
        self.root = None
        self.names = [path]

    def skip(self):
        self.skipname = True

    def next(self):
        while True:
            while True:
                if self.names:
                    name = self.names.pop(0)
                    break
                elif self.stack:
                    self.root, self.names = self.stack.pop()
                else:
                    raise StopIteration()

            path = os.path.join(self.root, name)
            pathisdir = os.path.isdir(path)

            if pathisdir:
                if not self.dirsonly or not os.access(path, os.R_OK|os.X_OK):
                    continue

            yield path

            if self.skipname:
                self.skipname = False
                continue

            if pathisdir:
                try:
                    self.stack.append((path, os.listdir(path)))
                except OSError:
                    continue

def print_usage():
    print("""\
usage: ssm find [<options>] [<path> ...]
       ssm find -h|--help

Find SSM objects. Use <path> as the starting point for the search.
Otherwise, use the paths in SSMUSE_PATH, if available.

Patterns support wildcards: * (zero or more) and ? (single) character
match.

Options:
-d <pattern>    Domain path pattern; default is match all (*).
-p <pattern>    Package name pattern; default is match all (*)
-pp <pattern>   Platform pattern; default is list taken from
                SSM_PLATFORMS or SSMUSE_PLATFORMS
-t <type>[,...] Search for each type. Default is domain,package.

--debug         Enable debugging
--force         Force operation
--verbose       Enable verbose output""")

FINDTYPES_ALL = ["domain", "package"]

def run(args):
    try:
        paths = None
        findtypes = FINDTYPES_ALL
        displayfmt = None
        dompatt = None
        pkgpatt = None
        platpatt = None
        platforms = determine_platforms()

        while args:
            arg = args.pop(0)
            if arg == "-d" and args:
                dompatt = args.pop(0)
            elif arg == "--fmt" and args:
                displayfmt = args.pop(0)
            elif arg == "-p" and args:
                pkgpatt = args.pop(0)
            elif arg == "-pp" and args:
                platpatt = args.pop(0)
            elif arg == "-t" and args:
                findtypes = args.pop(0).split(",")
                for name in findtypes:
                    if name not in FINDTYPES_ALL:
                        raise Exception()

            elif arg in ["-h", "--help"]:
                print_usage()
                sys.exit(0)
            elif arg == "--debug":
                globls.debug = True
            elif arg == "--force":
                globls.force = True
            elif arg == "--verbose":
                globls.verbose = True
            else:
                paths = [arg]+args
                args = []
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: bad/missing arguments")

    if not paths:
        paths = os.environ.get("SSMUSE_PATH", "").split(":")

    domcre = None
    pkgcre = None

    domcre = dompatt and re.compile(".*/%s$" % fnmatch.translate(dompatt))
    pkgcre = pkgpatt and re.compile(fnmatch.translate(pkgpatt))

    if globls.debug:
        print "paths", paths
        print "displayfmt", displayfmt
        print "dompatt", dompatt
        print "domcre", domcre
        print "pkgpatt", pkgpatt
        print "pkgcre", pkgcre
        print "platpatt", platpatt
        print "findtypes", findtypes
        print "platforms", platforms

    fmt = "%-4s  %-30s"
    _, displaywidth = get_terminal_size()

    try:
        dom = None
        for basedir in paths:
            #print "basedir", basedir
            dw = DirWalker(basedir, dirsonly=True)
            for dirpath in dw.next():
                #print "dirpath", dirpath
                dom = Domain(dirpath)
                if dom.exists():
                    dw.skip()
                    if not dompatt \
                        or (domcre and domcre.match(dom.path)):
                        if "package" not in findtypes:
                            if displayfmt == "csv":
                                print dom.path
                            else:
                                print "----- domain (%s) -----" % (dom.path,)
                            continue

                        installeds = dom.get_installeds(platforms)
                        name2installeds = dict([(pkg.name, pkg) for pkg in installeds
                            if not pkgcre or pkgcre.match(pkg.name)])
                        publisheds = dom.get_publisheds(platforms)
                        name2publisheds = dict([(pkg.name, pkg) for pkg in publisheds
                            if not pkgcre or pkgcre.match(pkg.name)])
                        allnames = set(name2installeds.keys()).union(name2publisheds.keys())

                        recs = []
                        for pname in sorted(allnames):
                            status = []
                            if pname in name2installeds:
                                status.append("I")
                            if pname in name2publisheds:
                                if status:
                                    status.append("P")
                                else:
                                    status.append("p")
                            recs.append(("".join(status), pname))
                            #print "package  %s  %s" % ("".join(status), pname)
                        if recs:
                            if displayfmt == "csv":
                                for rec in recs:
                                    print "%s,%s,%s" % (dom.path, rec[0], rec[1])
                            else:
                                lines = []
                                for rec in recs:
                                    lines.append(fmt % (rec[0], rec[1]))
                                print "----- domain (%s) -----" % (dom.path,)
                                print "\n".join(columnize(lines, displaywidth, 2))
                                print
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    sys.exit(0)
