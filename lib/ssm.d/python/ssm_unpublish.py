#! /usr/bin/env python
#
# ssm_unpublish.py

"""Provides the unpublish subcommand.
"""

import os
import sys
from sys import stderr
import traceback

from ssm import globls
from ssm.domain import Domain
from ssm.error import Error
from ssm.misc import exits
from ssm.package import determine_platform, Package

def print_usage():
    print("""\
usage: ssm publish [<options>] -d <dompath> -p <pkgname>
       ssm publish -h|--help

Unpublish package from domain.

Where:
-d <dompath>    Domain path
-p <pkgname>    Package name found in repository

Options:
-pp <platform>  Alternate platform to unpublish from; default is the
                package platform or SSMUSE_PLATFORM

--debug         Enable debugging
--force         Force operation
--verbose       Enable verbose output""")

def run(args):
    try:
        dompath = None
        pkgname = None
        pubplat = None

        while args:
            arg = args.pop(0)
            if arg == "-d" and args:
                dompath = args.pop(0)
            elif arg == "-p" and args:
                pkgname = args.pop(0)
            elif arg == "-pp" and args:
                pubplat = args.pop(0)

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
                raise Exception()
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: bad/missing arguments")

    if not dompath \
        or not pkgname:
        exits("error: bad/missing arguments")

    try:
        dom = Domain(dompath)
        if not dom.exists():
            exits("error: cannot find domain")
        if isinstance(dom.get_version(), Error):
            exits("error: old domain not supported; you may want to upgrade")

        pubplat = pubplat or determine_platform(Package(pkgname))
        if not pubplat:
            exits("error: cannot determine platform")
        pkg = dom.get_published(pkgname, pubplat)
        if not pkg:
            exits("error: package is not published")
        deppkgs = dom.get_dependents(pkg, pubplat)
        if isinstance(deppkgs, Error):
            exits(deppkgs)
        if len(deppkgs) > 1 and not globls.force:
            depnames = [deppkg.name for deppkg in deppkgs]
            print "found dependent packages: %s" % " ".join(depnames)
            reply = raw_input("unpublish all (y/n)? ")
            if reply != "y":
                exits("aborting operation")
        for deppkg in deppkgs:
            err = dom.unpublish(deppkg, pubplat)
            if err:
                exits(err)
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    sys.exit(0)