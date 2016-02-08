#! /usr/bin/env python
#
# ssm_publish.py

"""Provides the publish subcommand.
"""

import os
import sys
from sys import stderr
import traceback

from ssm import globls
from ssm.domain import Domain
from ssm.error import Error
from ssm.misc import exits
from ssm.package import determine_platform

def print_usage():
    print("""\
usage: ssm publish [<options>] -d <dompath> -p <pkgname>
       ssm publish -h|--help

Publish package to domain.

Where:
-d <dompath>    Domain path
-p <pkgname>    Package name found in repository

Options:
-pp <platform>  Alternate platform to publish to; default is the
                package platform or SSMUSE_PLATFORM
-P <dompath>    Alternate domain to publish to

--debug         Enable debugging
--force         Force operation
--verbose       Enable verbose output""")

def run(args):
    try:
        dompath = None
        pkgname = None
        pubplat = None
        pubdompath = None

        while args:
            arg = args.pop(0)
            if arg == "-d" and args:
                dompath = args.pop(0)
            elif arg == "-p" and args:
                pkgname = args.pop(0)
            elif arg == "-pp" and args:
                pubplat = args.pop(0)
            elif arg == "-P" and args:
                pubdompath = args.pop(0)

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

    if not pubdompath:
        pubdompath = dompath

    try:
        dom = Domain(dompath)
        pubdom = Domain(pubdompath)
        if not dom.exists():
            exits("error: cannot find domain")
        if not pubdom.exists():
            exits("error: cannot find publish domain")

        pkg = dom.get_installed(pkgname)
        if not pkg:
            exits("error: package not installed")
        pubplat = pubplat or determine_platform(pkg)
        if not pubplat:
            exits("error: cannot determine platform")
        if pubdom.get_published(pkg.name, pubplat) and not globls.force:
            # TODO: ask for permission
            exits("error: package already published")

        err = pubdom.prepublish(pkg, pubplat)
        if isinstance(err, Error):
            exits(err)
        err = pubdom.publish(pkg, pubplat, globls.force)
        if err:
            exits(err)
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    sys.exit(0)