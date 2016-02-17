#! /usr/bin/env python
#
# ssm_uninstall.py

"""Provides the uninstall subcommand.
"""

import sys
from sys import stderr
import traceback

from ssm import globls
from ssm.domain import Domain
from ssm.error import Error
from ssm.package import Package
from ssm.misc import exits

def print_usage():
    print("""\
usage: ssm uninstall [<options>] (-d <dompath> -p <pkgname>)|-f <pkgpath>
       ssm uninstall -h|--help

Install package to domain.

Where:
-d <dompath>    Domain path
-p <pkgname>    Package name
-f <pkgpath>    Package path

Options:
--debug         Enable debugging
--force         Force operation
--verbose       Enable verbose output""")

def run(args):
    try:
        dompath = None
        pkgname = None
        pkgpath = None

        while args:
            arg = args.pop(0)
            if arg == "-d" and args:
                dompath = args.pop(0)
            elif arg == "-f" and args:
                pkgpath = args.pop(0)
                pkgname = None
            elif arg == "-p" and args:
                pkgname = args.pop(0)
                pkgpath = None
            elif arg == "-r" and args:
                repourl = args.pop(0)

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
        or (not pkgname and not pkgfpath):
        exits("error: bad/missing arguments")

    try:
        if dompath:
            dom = Domain(dompath)
            pkg = dom.get_installed(pkgname)
        else:
            pkg = Package(pkgpath)
            dom = pkg.get_domain()

        if not dom.exists() or pkg == None:
            exits("error: cannot find domain/package")
        if isinstance(dom.get_version(), Error):
            exits("error: old domain not supported; you may want to upgrade")

        err = dom.uninstall(pkg)
        if err:
            exits(err)
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    sys.exit(0)