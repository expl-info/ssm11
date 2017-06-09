#! /usr/bin/env python
#
# ssm_build.py

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

"""Provides the build subcommand.
"""

import json
import os.path
import sys
from sys import stderr
import tarfile
import traceback

from ssm import globls
from ssm.builder import Builder
from ssm.deps import DependencyManager
from ssm.domain import Domain
from ssm.error import Error
from ssm.misc import exits
from ssm.packagefile import PackageFile

def load_builders(workdir, bssmdir, sourcesurl, dompath, repourl, buildnames, platform, initfile, initpkg):
    name2bssmpath = {}
    name2builder = {}
    builders = []

    # determine build dependencies
    dm = DependencyManager()
    for fname in os.listdir(bssmdir):
        if not fname.endswith(".bssm"):
            continue
        bssmpath = os.path.join(bssmdir, fname)
        if globls.verbose:
            print "loadings bssm file (%s)" % (bssmpath,)
        try:
            tarf = tarfile.open(bssmpath)
            s = tarf.extractfile("bcontrol.json").read()
            bcontrol = json.loads(s)
        except:
            raise Exception("cannot load file (%s)" % (bssmpath,))
        name2bssmpath[bcontrol["name"]] = bssmpath
        dm.add(bcontrol.get("name"),
            bcontrol.get("version"),
            bcontrol.get("requires", None),
            bcontrol.get("provides", None),
            bcontrol.get("conflicts", None))
    buildnames2 = dm.generate(buildnames)

    # create Builders for each
    dom = Domain(dompath)
    for buildname in buildnames2:
        bssmpath = name2bssmpath.get(buildname)
        if bssmpath:
            builders.append(Builder(workdir, bssmpath, sourcesurl, dompath, repourl, platform, initfile, initpkg))

    return builders

def print_usage():
    print("""\
usage: ssm build [<options>] -b <bssmdir> -s <sourcesurl> -d <dompath> -p <platform> <pkgname> ...
       ssm build -h|--help

Perform the necessary steps to result in the named packages being
published to a domain. The steps involved may be build (based on a
buildspec file), copy to a repository, install, and publish. All
package dependencies (for build and publish) are satisfied which
means that unspecified package may be added to the build list.

Where:
<bssmdir>       Directory containing bssm files
<dompath>       Domain path
<platform>      SSM platform to build for
<sourcesurl>    URL where source files are located (BH_SOURCES_URL)
<pkgname>       Short form package name (not including version or
                platform)

Options:
--dry           Dry run; do not build
--init-file <path>
                File to load prior to building each package
--init-pkg <name>
                Package to load prior to building each package
--install       Install after successful build
--publish       Publish and install after successful build
-r <url>        Repository URL
--show-all      Show the ordered list of all packages to build
--show-missing  Show the ordered list of missing packages to build
-w <path>       Work directory; default is current directory

--debug         Enable debugging
--force         Force operation
--verbose       Enable verbose output""")

def run(args):
    try:
        bssmdir = None
        dompath = None
        doinstall = False
        dopublish = False
        dry = False
        initfile = None
        initpkg = None
        platform = None
        repourl = None
        showall = False
        showmissing = False
        sourcesurl = None
        workdir = os.getcwd()

        while args:
            arg = args.pop(0)
            if arg == "-b" and args:
                bssmdir = args.pop(0)
            elif arg == "-d" and args:
                dompath = args.pop(0)
            elif arg == "-p" and args:
                platform = args.pop(0)
            elif arg == "-r" and args:
                repourl = args.pop(0)
            elif arg == "-s" and args:
                sourcesurl = args.pop(0)
            elif arg == "--dry":
                dry = True
            elif arg == "--init-file" and args:
                initfile = args.pop(0)
            elif arg == "--init-pkg" and args:
                initpkg = args.pop(0)
            elif arg == "--install":
                doinstall = True
            elif arg == "--publish":
                doinstall = True
                dopublish = True
            elif arg == "--show-all":
                showall = True
                showmissing = False
            elif arg == "--show-missing":
                showall = False
                showmissing = True
            elif arg == "-w" and args:
                workdir = args.pop(0)

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
                buildnames = [arg]+args
                del args[:]
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: bad/missing arguments")

    if not bssmdir \
        or not sourcesurl \
        or not dompath \
        or not platform:
        exits("error: bad/missing arguments")

    try:
        if not os.path.exists(workdir):
            os.makedirs(workdir)

        dom = Domain(dompath)
        if not dom.exists():
            exits("error: cannot find domain")

        if not repourl:
            repourl = dom.get_repository()
            if isinstance(repourl, Error):
                exits(repourl)

        builders = load_builders(workdir, bssmdir, sourcesurl, dompath, repourl, buildnames, platform, initfile, initpkg)

        if showall or showmissing:
            for builder in builders:
                if showmissing:
                    if dom.get_installed(builder.name) \
                        or dom.get_published(builder.name, platform):
                        continue
                print builder.name

        if dry:
            sys.exit(0)

        for builder in builders:
            print "buildname (%s)" % (builder.name,)
            if builder.platform == "dummy":
                # special
                continue

            pkg = dom.get_published(builder.name, platform)
            if pkg:
                print "info: package (%s) already published" % (pkg.name,)
                continue

            pkg = dom.get_installed(builder.name)
            if pkg:
                print "info: package (%s) already installed" % (pkg.name,)
            else:
                pkgfpath = os.path.join(repourl, builder.name+".ssm")
                if not os.path.exists(pkgfpath):
                    print "info: building package (%s)" % (builder.name,)
                    pkgfpath, err = builder.run()
                    if err:
                        exits(err)

                pkgf = PackageFile(pkgfpath)
                if not pkgf.is_valid():
                    exits("error: bad package file")

                if doinstall:
                    print "info: installing package file (%s)" % (pkgf.name,)
                    err = dom.install(pkgf, globls.force)
                    if err:
                        exits(err)

            if dopublish:
                pkg = dom.get_installed(builder.name)
                if pkg and dom.is_published(pkg, [platform]):
                    print "info: package (%s) already published" % (pkg.name,)
                else:
                    print "info: publishing package (%s) to platform (%s)" % (pkg.name, platform)
                    err = dom.publish(pkg, platform, globls.force)
                    if err:
                        exits(err)
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    sys.exit(0)

def buildpkg(workdir, bssmpath, sourcesurl, dompath, repourl, platform, initfile=None, initpkg=None):
    b = Builder(workdir, bssmpath, sourcesurl, dompath, repourl, platform, initfile, initpkg)
    pkgfpath, err = b.run()
    if err:
        # cleanup
        return None, err
    return pkgfpath, None
