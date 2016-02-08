#! /usr/bin/env python
#
# ssm_install.py

"""Provides the install subcommand.
"""

import os.path
import sys
from sys import stderr
import traceback

from ssm import globls
from ssm.domain import Domain
from ssm.error import Error
from ssm.misc import exits
from ssm.packagefile import PackageFile

def print_usage():
    print("""\
usage: ssm install [<options>] -d <dompath> (-p <pkgname>|-f <pkgfile>)
       ssm install -h|--help

Install package to domain.

Where:
-d <dompath>    Domain path
-f <pkgfile>    Package file (ending in .ssm)
-p <pkgname>    Package name found in repository

Options:
-r <url>        Repository URL

--debug         Enable debugging
--force         Force operation
--verbose       Enable verbose output""")

def run(args):
    try:
        dompath = None
        pkgname = None
        pkgfpath = None
        repourl = None

        while args:
            arg = args.pop(0)
            if arg == "-d" and args:
                dompath = args.pop(0)
            elif arg == "-f" and args:
                pkgfpath = args.pop(0)
                pkgname = None
            elif arg == "-p" and args:
                pkgname = args.pop(0)
                pkgfpath = None
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
        dom = Domain(dompath)
        if not dom.exists():
            exits("error: cannot find domain")

        if pkgname:
            if not repourl:
                repourl = dom.get_repository()
                if isinstance(repourl, Error):
                    exits(repourl)
            # TODO: add support for non-file urls
            pkgfpath = os.path.join(repourl, pkgname+".ssm")

        pkgf = PackageFile(pkgfpath)
        err = dom.install(pkgf, globls.force)
        if err:
            exits(err)
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    finally:
        try:
            misc.remove(pkgfpath)
        except:
            pass
    sys.exit(0)