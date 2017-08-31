#! /usr/bin/env python
#
# ssm_publish.py

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

"""Provides the publish subcommand.
"""

import os
import os.path
import sys
from sys import stderr
import traceback

from ssm import globls
from ssm.domain import Domain
from ssm.error import Error
from ssm.misc import exits
from ssm.package import determine_platform, split_pkgref

def print_usage():
    print("""\
usage: ssm publish [<options>] -d <dompath> -p <pkgname>
       ssm publish -h|--help

Publish package to domain.

Where:
<dompath>       Domain path
<pkgname>       Package name found in repository

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
        pkgref = None
        pubplat = None
        pubdompath = None

        while args:
            arg = args.pop(0)
            if arg == "-d" and args:
                dompath = args.pop(0)
                pkgref = None
            elif arg == "-p" and args:
                pkgname = args.pop(0)
                pkgref = None
            elif arg == "-pp" and args:
                pubplat = args.pop(0)
            elif arg == "-P" and args:
                pubdompath = args.pop(0)
            elif arg == "-x" and args:
                pkgref = args.pop(0)
                dompath = None
                pkgname = None

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

    if not pubdompath:
        pubdompath = dompath

    try:
        dom = Domain(dompath)
        pubdom = Domain(pubdompath)
        if not dom.exists():
            exits("error: cannot find domain")
        meta = dom.get_meta()
        if meta.get("version") == None:
            exits("error: old domain not supported; you may want to upgrade")

        if not pubdom.exists():
            exits("error: cannot find publish domain")
        pubmeta = pubdom.get_meta()
        if pubmeta.get("version") == None:
            exits("error: old domain not supported; you may want to upgrade")

        pkg = dom.get_installed(pkgname)
        if not pkg:
            exits("error: package not installed")

        pubplat = pubplat or determine_platform(pkg)
        if not pubplat:
            exits("error: cannot determine platform")
        pubpkg = pubdom.get_published_short(pkg.name, pubplat)
        if pubpkg:
            deppkgs = pubdom.get_dependents(pubpkg, pubplat)
            if isinstance(deppkgs, Error):
                exits(deppkgs)
            if len(deppkgs) > 1 and not globs.force:
                depnames = [deppkg.name for deppkg in deppkgs]
                print "found dependent packages: %s" % " ".join(depnames)
                reply = raw_input("unpublish all (y/n)? ")
                if reply != "y":
                    exits("aborting operation")
            for deppkg in deppkgs:
                err = pubdom.unpublish(deppkg, pubplat)
                if err:
                    exits(err)

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