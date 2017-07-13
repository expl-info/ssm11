#! /usr/bin/env python
#
# ssm_install.py

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
from ssm.repository import RepositoryGroup

def print_usage():
    print("""\
usage: ssm install [<options>] -d <dompath> (-p <pkgname>|-f <pkgfile>)
       ssm install -h|--help

Install package to domain.

Where:
<dompath>       Domain path
<pkgfile>       Package file (ending in .ssm)
<pkgname>       Package name found in repository

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
        meta = dom.get_meta()
        if meta.get("version") == None:
            exits("error: old domain not supported; you may want to upgrade")

        if pkgfpath:
            pkgf = PackageFile(pkgfpath)
        elif pkgname:
            if repourl:
                repo = RepositoryGroup([repourl])
            else:
                repo = dom.get_repository()
                if repo == None:
                    exits("error: no repository")

            pkgf = repo.get_packagefile(pkgname)

        if pkgf == None:
            exits("error: cannot find package")

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