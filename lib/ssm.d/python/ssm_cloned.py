#! /usr/bin/env python2
#
# ssm_cloned.py

# GPL--start
# This file is part of ssm (Simple Software Manager)
# Copyright (C) 2005-2017 Environment/Environnement Canada
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

"""Provides the created subcommand.
"""

import os.path
import sys
from sys import stderr
import traceback

from pyerrors.errors import Error, is_error

from ssm import constants
from ssm import globls
from ssm.domain import Domain
from ssm.meta import Meta
from ssm.misc import exits
from ssm.package import Package
from ssm.packagefile import PackageFile
from ssm.repository import Repository

def print_usage():
    print("""\
usage: ssm cloned [<options>] [<srcdom> ...] <dstdom>
       ssm cloned -h|--help

Clone one or more existing domains. If <dstdom> does not exist, it
will be created using the meta information from <srcdom> domain.

Packages are installed from the repository. Packages that are
installed to <dstdom> are published from <dstdom> except if
--published-src is specified, at which point they are published from
the same domain used in <srcdom>.

By default, only --published-src is set. 

Where:
<dstdom>        Path of destination domain
<srcdom>        Path of source domain

Options:
--installed     Clone installed packages
--published     Clone published packages
--published-src Clone published packages from <srcdom> rather than
                from <dstdom>. Defaults to on
-L <string>     Short label for domain
-pp <platform>[,..]
                Limit the publishing to specific platforms
-r <url>        Alternate repository URL overriding the one from
                <srcdom>
--debug         Enable debugging
--force         Force operation
--verbose       Enable verbose output""")

def run(args):
    try:
        dstdompath = None
        installed = False
        installedoverwrite = False
        label = None
        platforms = None
        published = False
        publishedsrc = True
        repourl = None
        srcdompaths = None

        while args:
            arg = args.pop(0)
            if arg == "--installed":
                installed = True
            elif arg == "--installed-overwrite":
                installedoverwrite = True
            elif arg == "--published":
                published = True
                publishedsrc = False
            elif arg == "--published-src":
                publishedsrc = True
                published = False
            elif arg == "-L" and args:
                label = args.pop(0)
            elif arg == "-pp" and args:
                platforms = args.pop(0).split(",")
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
            elif len(args):
                srcdompaths = [arg]+args[:-1]
                dstdompath = args[-1]
                del args[:]
            else:
                raise Exception()

        if not srcdompaths or not dstdompath:
            raise Exception()

        if not installed and not published and not publishedsrc:
            raise Exception()
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: bad/missing arguments")

    try:
        for srcdompath in srcdompaths:
            srcdom = Domain(srcdompath)
            dstdom = Domain(dstdompath)

            if not srcdom.exists():
                exits("error: no domain at srcdompath (%s)" % srcdompath)

            srcinv = srcdom.get_inventory()
            repourl = repourl or srcinv["meta"].get("repository")
            label = label or srcinv["meta"].get("label", "")
            repo = Repository(repourl)

            if not dstdom.exists():
                meta = Meta()
                meta.set("label", label or "")
                meta.set("repository", repourl)
                meta.set("version", constants.SSM_VERSION)

                print "creating dstdom (%s) ... " % (dstdom.path,),
                err = dstdom.create(meta, globls.force)
                if is_error(err):
                    print "fail"
                    exits(err)
                print "ok"

            print "----------------------------------------"
            print "source domain (%s)" % (srcdompath,)

            if installed:
                if not repo:
                    exits("error: no repository for installing packages")

                pkgfiles = []
                for pkgname in srcinv["installed"]:
                    pkgpath = dstdom.joinpath(pkgname)
                    if dstdom.is_installed(Package(pkgpath)) and not installedoverwrite:
                        # skip already installed package
                        continue

                    pkgf = repo.get_packagefile(pkgname)
                    if not pkgf.exists():
                        exits("error: cannot find package (%s) in repository" % (pkgname,))
                    pkgfiles.append(pkgf)

                for pkgf in pkgfiles:
                    print "installing package (%s) ... " % (pkgf.name,),
                    err = dstdom.install(pkgf, globls.force)
                    if is_error(err):
                        print "fail"
                        exits(err)
                    print "ok"

            if published or publishedsrc:
                splatforms = platforms or srcinv["published"].keys()
                print "platforms (%s)" % ",".join(splatforms)
                for plat in splatforms:
                    platpublished = srcinv["published"].get(plat, [])
                    for pkgname in platpublished:
                        if published:
                            pkgpath = dstdom.joinpath(pkgname)
                        else:
                            pkgpath = platpublished[pkgname]
                        pkg = Package(pkgpath)

                        dpkg = dstdom.get_published_short(pkg.name, plat)
                        if dpkg:
                            print "unpublishing package (%s) ... " % (dpkg.name,),
                            err = dstdom.unpublish(dpkg, plat)
                            if is_error(err):
                                print "fail"
                                exits(err)
                            print "ok"

                        print "publishing package (%s) (%s) ... " % (pkg.name, published and "installed" or "source"),
                        err = dstdom.publish(pkg, plat, globls.force)
                        if is_error(err):
                            print "fail"
                            exits(err)
                        print "ok"
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    sys.exit(0)
