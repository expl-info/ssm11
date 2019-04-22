#! /usr/bin/env python2
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

from ssm.constants import SKELETON_COMPS
from ssm import globls
from ssm import misc
from ssm.domain import Domain
from ssm.error import Error
from ssm.misc import exits
from ssm.package import Package
from ssm.packagefile import PackageFile, PackageFileSkeleton
from ssm.repository import RepositoryGroup

def print_usage():
    print("""\
usage: ssm install [<options>] -d <dompath> -f <pkgfile>
       ssm install [<options>] -d <dompath> -p <pkgname>
       ssm install [<options>] -d <dompath> -p <pkgname> -s <srcdir>
       ssm install -h|--help

Install package to domain. Package contents may come from a package
file, a package in a repository, a source directory, or a skeleton
package only.

Where:
<dompath>       Domain path
<pkgfile>       Package file (ending in .ssm)
<pkgname>       Package name found in repository
<srcdir>        Source directory from which to install

Options:
--names <name>[,...]
                CSV list of top-lvel object names to import.
                Default is all in the <srcdir>. For use with -s
                only.
-r <url>        Repository URL
--reinstall     Allow install over existing installation
--skeleton      Install package skeleton (control.json, etc). No
                package or package file is required. For use with
                -p only.

--debug         Enable debugging
--force         Force operation
--verbose       Enable verbose output""")

def run(args):
    try:
        dompath = None
        names = None
        pkgname = None
        pkgfpath = None
        reinstall = False
        repourl = None
        skeleton = False
        skeleton_comps = None

        while args:
            arg = args.pop(0)
            if arg == "-d" and args:
                dompath = args.pop(0)
            elif arg == "-f" and args:
                pkgfpath = args.pop(0)
                pkgname = None
            elif arg == "--names" and args:
                names = args.pop(0).split(",")
            elif arg == "-p" and args:
                pkgname = args.pop(0)
                pkgfpath = None
            elif arg == "-r" and args:
                repourl = args.pop(0)
            elif arg == "--reinstall":
                reinstall = True
            elif arg == "-s" and args:
                srcdir = args.pop(0)
                skeleton = None
            elif arg == "--skeleton":
                skeleton = True
                srcdir = None

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

        if not dompath \
            or (not pkgname and not pkgfpath):
            raise Exception()
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
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
        elif skeleton:
            # dummy filename
            pkgfpath = "%s.ssm" % (pkgname,)
            if skeleton_comps == None:
                skeleton_comps = SKELETON_COMPS
            pkgf = PackageFileSkeleton(pkgfpath, skeleton_comps)
        elif srcdir:
            pkg = Package(dom.joinpath(pkgname))
            if os.path.exists(pkg.path) and (not reinstall or not globls.force):
                exits("error: package is installed")

            skeleton_comps = ["control"]
            pkgf = PackageFileSkeleton("%s.ssm" % pkg.path, skeleton_comps)

            if names == None:
                names = os.listdir(srcdir)

            if not os.path.exists(pkg.path):
                misc.makedirs(pkg.path)

            for name in names:
                if "/" in name:
                    stderr.write("warning: name (%s) cannot be installed\n" % name)
                srcpath = os.path.join(srcdir, name)
                dstpath = pkg.joinpath(name)
                if not os.path.exists(srcpath):
                    # skip?
                    pass
                misc.symlink(srcpath, dstpath, force=True)

            # force install even with something at pkg.path
            globls.force = True
        else:
            if repourl:
                repo = RepositoryGroup([repourl])
            else:
                repo = dom.get_repository()
                if repo == None:
                    exits("error: no repository")

            pkgf = repo.get_packagefile(pkgname)

        if pkgf == None:
            exits("error: cannot find package")

        err = dom.install(pkgf, globls.force, reinstall=reinstall)
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
            if os.pkgfpath:
                misc.remove(pkgfpath)
        except:
            pass
    sys.exit(0)
