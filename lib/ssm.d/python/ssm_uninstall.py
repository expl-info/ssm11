#! /usr/bin/env python2
#
# ssm_uninstall.py

# GPL--start
# This file is part of ssm (Simple Software Manager)
# Copyright (C) 2005-2012 Environment/Environnement Canada
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; version 2
# of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
# GPL--end

"""Provides the uninstall subcommand.
"""

import os.path
import sys
from sys import stderr
import traceback

from pyerrors.errors import Error, is_error

from ssm import globls
from ssm.domain import Domain
from ssm.package import split_pkgref, Package
from ssm.misc import exits

def print_usage():
    print("""\
usage: ssm uninstall [<options>] -d <dompath> -p <pkgname>
       ssm uninstall -h|--help

Uninstall package from domain.

Where:
<dompath>       Domain path
<pkgname>       Package name

Options:
--debug         Enable debugging
--force         Force operation
--verbose       Enable verbose output""")

def run(args):
    try:
        dompath = None
        pkgname = None
        pkgref = None

        while args:
            arg = args.pop(0)
            if arg == "-d" and args:
                dompath = args.pop(0)
                pkgref = None
            elif arg == "-p" and args:
                pkgname = args.pop(0)
                pkgref = None
            elif arg == "-r" and args:
                repourl = args.pop(0)
            elif arg == "-x" and args:
                pkgref = args.pop(0)

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

        if pkgref:
            dompath, pkgname, _ = split_pkgref(pkgref)

        if not dompath or not pkgname:
            raise Exception()
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: bad/missing arguments")

    try:
        if dompath:
            dom = Domain(dompath)
            pkg = dom.get_installed(pkgname)

        if not dom.exists() or pkg == None:
            exits("error: cannot find domain/package")
        meta = dom.get_meta()
        if meta.get("version") == None:
            exits("error: old domain not supported; you may want to upgrade")

        err = dom.uninstall(pkg)
        if is_error(err):
            exits(err)
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    sys.exit(0)