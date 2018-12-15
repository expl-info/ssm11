#! /usr/bin/env python2
#
# ssm_upgraded.py

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

"""Provides the upgraded subcommand.
"""

import json
import os
import sys
from sys import stderr
import traceback

from ssm import constants
from ssm import globls
from ssm import misc
from ssm.control import Control
from ssm.domain import Domain
from ssm.error import Error
from ssm.misc import exits
from ssm.package import Package

def print_usage():
    print("""\
usage: ssm upgraded [<options>] -d <dompath>
       ssm upgraded -h|--help

Upgrade domain to current version.

Where:
<dompath>       Path for domain

Options:
-c <name>[,...] Component names that need upgrading; the default is
                all: meta,control,installed,published,old-files,old-dirs
--legacy        Upgrade applies to a legacy domain (v10 and before)

--debug         Enable debugging
--force         Force operation
--verbose       Enable verbose output""")

def run(args):
    try:
        components = ["meta", "control", "installed", "published", "old-files", "old-dirs", "self"]
        dompath = None
        legacy = None
        globls.verbose = False

        while args:
            arg = args.pop(0)
            if arg == "-c" and args:
                components = args.pop(0).split(",")
            elif arg == "-d" and args:
                dompath = args.pop(0)
            elif arg == "--legacy":
                legacy = True

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

    if not dompath:
        exits("error: bad/missing arguments")

    try:
        dom = Domain(dompath)
        if not dom.exists():
            exits("error: cannot find domain")

        if legacy == True or dom.is_legacy():
            upgrade_legacy(dompath, components)
        else:
            meta = dom.get_meta()
            if meta.get("version") == None:
                exits(dom.get_version_legacy())

            meta.setstore("version", constants.SSM_VERSION)
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    sys.exit(0)

def upgrade_legacy(dompath, components):
    def get_package_names(path):
        names = []
        for name in os.listdir(path):
            t = name.split("_")
            if len(t) == 3:
                names.append(name)
        return names

    try:
        dom = Domain(dompath)

        # prep paths
        ssmd_path = os.path.join(dompath, "etc/ssm.d")
        domainhomes_dir = os.path.join(ssmd_path, "domainHomes")
        installed_dir = os.path.join(ssmd_path, "installed")
        label_path = os.path.join(ssmd_path, "label")
        login_path = os.path.join(ssmd_path, "login")
        profile_path = os.path.join(ssmd_path, "profile")
        platforms_dir = os.path.join(ssmd_path, "platforms")
        published_dir = os.path.join(ssmd_path, "published")
        self_path = os.path.join(ssmd_path, "self")
        sources_path = os.path.join(ssmd_path, "sources.list")
        subdomains_path = os.path.join(ssmd_path, "subdomains")
        version_path = os.path.join(ssmd_path, "version")

        version = misc.gets(version_path)

        # fix self first!
        if "self" in components:
            print "upgrading self path"
            if os.path.exists(self_path):
                os.unlink(self_path)
            os.symlink(dom.path, self_path)

        if "meta" in components:
            # set meta file
            metadata = {
                "label": misc.gets(label_path),
                "repository": misc.gets(sources_path),
                "version": constants.SSM_VERSION,
            }
            print "upgrading domain metadata"
            err = dom.create(metadata, True)
            if err:
                exits(err)

        if "control" in components:
            names = get_package_names(installed_dir)
            for name in names:
                pkgpath = os.path.join(installed_dir, name)
                control_path = os.path.join(pkgpath, ".ssm.d/control.json")
                control = Control(control_path)
                if not control.exists():
                    control.load_legacy()
                    if control.get("name") == None:
                        print "warning: generating control file from name (%s)" % (name,)
                        try:
                            t = name.split("_", 2)
                            control.set("name", t[0])
                            control.set("version", t[1])
                            control.set("platform", t[2])
                        except:
                            exits("warning: could not generate create control file from name (%s)" % (name,))

                print "upgrading package control file (%s)" % (control_path,)
                try:
                    control.store()
                except:
                    exits("cannot write new control file")

        if "installed" in components:
            # update installed dir
            names = get_package_names(installed_dir)
            pkgpaths = [os.readlink(os.path.join(installed_dir, name)) for name in names]
            misc.rename(installed_dir, installed_dir+"-old")
            os.mkdir(installed_dir)
            for pkgpath in pkgpaths:
                pkg = Package(pkgpath)
                if pkg.exists():
                    print "upgrading installed setting for package (%s)" % (pkg,)
                    dom._Domain__set_installed(pkg)

        if "published" in components:
            if version[:2] in ["9.", "8.", "7."]:
                # update published dir
                names = get_package_names(published_dir)
                pkgpaths = [os.readlink(os.path.join(published_dir, name)) for name in names]
                misc.rename(published_dir, published_dir+"-old")
                os.mkdir(published_dir)
                for pkgpath in pkgpaths:
                    pkg = Package(pkgpath)
                    if pkg.exists():
                        print "upgrading published setting for package (%s)" % (pkg,)
                        dom._Domain__set_published(pkg)

        if "old-files" in components:
            # delete old files
            paths = [label_path, login_path, profile_path, sources_path,
                subdomains_path, version_path]
            for path in paths:
                try:
                    print "removing old file (%s)" % (path,)
                    misc.remove(path)
                except:
                    pass

        if "old-dirs" in components:
            # delete old dirs
            paths = [domainhomes_dir, platforms_dir]
            for path in paths:
                try:
                    print "removing old directory (%s)" % (path,)
                    misc.rmtree(path)
                except:
                    pass
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        raise
