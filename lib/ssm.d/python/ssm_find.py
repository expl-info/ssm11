#! /usr/bin/env python2
#
# ssm_find.py

"""Provides the find subcommand.
"""

import fnmatch
import os
import re
import sys
from sys import stderr, stdout
import time
import traceback

from pyerrors.errors import Error, is_error

from ssm import globls
from ssm.domain import Domain
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

Patterns support wildcards: * (zero or more) and ? (single)
character match.

Options:
-d <pattern>    Domain path pattern. Default is match all (*).
-p <pattern>    Package name pattern. Default is match all (*).
-P <pattern>    Pattern for domain and package. Default is match all (*).
-pp <pattern>   Platform pattern. Default is list taken from
                SSM_PLATFORMS or SSMUSE_PLATFORMS.
--show-progress Show progress information.
--show-skip     Show skipped paths.
-t <type>[,...] Search for each type. Default is domain,package.

--debug         Enable debugging.
--force         Force operation.
--verbose       Enable verbose output.""")

FINDTYPES_ALL = ["domain", "package"]

def run(args):
    try:
        displayfmt = None
        dompatt = None
        findtypes = FINDTYPES_ALL
        onecolumn = True
        paths = None
        pkgpatt = None
        platforms = determine_platforms()
        platpatt = None
        showprogress = False
        showskip = False
        stats = False

        while args:
            arg = args.pop(0)
            if arg == "-1":
                onecolumn = True
            elif arg == "-d" and args:
                dompatt = args.pop(0)
            elif arg == "--fmt" and args:
                displayfmt = args.pop(0)
            elif arg == "-p" and args:
                pkgpatt = args.pop(0)
            elif arg == "-P" and args:
                dompatt = pkgpatt = args.pop(0)
            elif arg == "-pp" and args:
                platpatt = args.pop(0)
            elif arg == "--show-progress":
                showprogress = True
            elif arg == "--show-skip":
                showskip = True
            elif arg == "--stats":
                stats = True
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

    stats_ndirs = 0
    stats_ndomains = 0
    stats_npkginsts = 0
    stats_npkgpubs = 0
    stats_ndommatches = 0
    stats_npkgdoms = 0
    stats_npkgmatches = 0

    domcre = None
    pkgcre = None

    domcre = dompatt and re.compile(fnmatch.translate(dompatt))
    pkgcre = pkgpatt and re.compile(fnmatch.translate(pkgpatt))
    platcre = platpatt and re.compile(fnmatch.translate(platpatt))

    if globls.debug:
        print "stats", stats
        print "paths", paths
        print "displayfmt", displayfmt
        print "dompatt", dompatt
        print "domcre", domcre
        print "pkgpatt", pkgpatt
        print "pkgcre", pkgcre
        print "platpatt", platpatt
        print "platcre", platcre
        print "findtypes", findtypes
        print "platforms", platforms

    fmt = "%-4s  %-26s  %-30s"
    _, displaywidth = get_terminal_size()
    blanksline = " "*displaywidth

    try:
        t0 = time.time()
        dom = None
        for basedir in paths:
            #print "basedir", basedir
            dw = DirWalker(basedir, dirsonly=True)
            for dirpath in dw.next():
                eraseline = blanksline[:min(len(dirpath), displaywidth)]
                if showprogress:
                    print "%s\r" % dirpath[:len(eraseline)],

                skippath = os.path.join(dirpath, ".skip-ssm")
                if os.path.exists(skippath):
                    if showskip:
                        if showprogress:
                            print "%s\r" % eraseline,
                        stderr.write("skipped path (%s)\n" % dirpath)
                    dw.skip()
                    continue

                if os.path.basename(dirpath).startswith("."):
                    dw.skip()
                    continue
                stats_ndirs += 1
                #print "dirpath", dirpath
                dom = Domain(dirpath)
                if dom.exists():
                    stats_ndomains += 1
                    dw.skip()
                    try:
                        invd = dom.get_inventory()
                    except:
                        print "%s\r" % eraseline,
                        stderr.write("error: problem with domain (%s)\n" % dom.path)
                        continue

                    # filter domain
                    domname = os.path.basename(dom.path)
                    if (domcre and domcre.match(domname)) \
                        or pkgpatt:
                        stats_ndommatches += 1

                        if showprogress:
                            print "%s\r" % eraseline,

                        if "package" not in findtypes:
                            if displayfmt == "csv":
                                print dom.path
                            else:
                                print "----- domain (%s) -----" % (dom.path,)
                            continue

                        installeds = set(invd.get("installed", []))
                        publishedd = invd.get("published", {})
                        publisheds = set([])

                        if not platpatt:
                            xplatforms = platforms
                        else:
                            xplatforms = set([x for x in publishedd.keys() if platcre.match(x)])
                            xplatforms.update([x.split("_")[-1] for x in installeds])

                        for platform in xplatforms:
                            publisheds.update(publishedd.get(platform, []))
                        allnames = installeds.union(publisheds)

                        stats_npkginsts += len(installeds)
                        stats_npkgpubs += len(publisheds)

                        # filter package names
                        if pkgcre:
                            allnames = set([name for name in allnames if pkgcre.match(name)])

                        stats_npkgmatches += len(allnames)

                        recs = []
                        for name in sorted(allnames):
                            for platform in xplatforms:
                                status = []
                                # TODO: fix this UGLY!
                                if name in installeds and name.endswith("_"+platform):
                                    status.append("I")
                                if name in publishedd.get(platform, {}):
                                    if status:
                                        status.append("P")
                                    else:
                                        status.append("p")
                                if status:
                                    recs.append(("".join(status), platform, name))
                            #print "package  %s  %s" % ("".join(status), pname)
                        if recs:
                            stats_npkgdoms += 1

                            if displayfmt == "csv":
                                for rec in recs:
                                    print "%s,%s,%s,%s" % (dom.path, rec[0], rec[1], rec[2])
                            else:
                                lines = []
                                for rec in recs:
                                    lines.append(fmt % (rec[0], rec[1], rec[2]))
                                print "----- domain (%s) -----" % (dom.path,)
                                print "\n".join(columnize(lines, onecolumn and 1 or displaywidth, 2))
                                print

                if showprogress:
                    print "%s\r" % eraseline,

        if stats:
            stats_elapsedtime = time.time()-t0

            fmt = "%-25s: %s"
            print fmt % ("elapsed time", stats_elapsedtime)
            print fmt % ("total dirs", stats_ndirs)
            print fmt % ("total domains", stats_ndomains)
            print fmt % ("total domain matches", stats_ndommatches)
            #print fmt % ("total packages", stats_npackages)
            print fmt % ("total installed packages", stats_npkginsts)
            print fmt % ("total published packages", stats_npkgpubs)
            print fmt % ("total package matches", stats_npkgmatches)
            print fmt % ("total package domains", stats_npkgdoms)
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    sys.exit(0)
