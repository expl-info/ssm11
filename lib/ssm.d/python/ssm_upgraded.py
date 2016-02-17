#! /usr/bin/env python
#
# ssm_upgraded.py

"""Provides the upgraded subcommand.
"""

import os
import sys
from sys import stderr
import traceback

from ssm import constants
from ssm import globls
from ssm import misc
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
-d <dompath>    Path for domain

Options:
--debug         Enable debugging
--force         Force operation
--verbose       Enable verbose output""")

def run(args):
    try:
        components = ["meta", "installed", "published", "old-files", "old-dirs"]
        dompath = None
        legacy = None
        globls.verbose = True

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
        if legacy == True or dom.is_legacy():
            upgrade_legacy(dompath, components)
        else:
            version = dom.get_version()
            if isinstance(version, Error):
                exits(version)
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    sys.exit(0)

def upgrade_legacy(dompath, components):
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
        sources_path = os.path.join(ssmd_path, "sources.list")
        subdomains_path = os.path.join(ssmd_path, "subdomains")
        version_path = os.path.join(ssmd_path, "version")

        version = misc.gets(version_path)

        if "meta" in components:
            # set meta file
            meta = {
                "label": misc.gets(label_path),
                "repository": misc.gets(sources_path),
                "version": constants.SSM_VERSION,
            }
            if globls.verbose:
                "setting domain metadata"
            print dom.path, meta
            err = dom.create(meta, True)
            if err:
                exits(err)

        if "installed" in components:
            print "AAA"
            # update installed dir
            names = [name for name in os.listdir(installed_dir) if not name.startswith(".")]
            pkgpaths = [os.readlink(os.path.join(installed_dir, name)) for name in names]
            misc.rename(installed_dir, installed_dir+"-old")
            os.mkdir(installed_dir)
            for pkgpath in pkgpaths:
                pkg = Package(pkgpath)
                if pkg.exists():
                    if globls.verbose:
                        "upgrading installed setting for package (%s)" % (pkg,)
                    dom._Domain__set_installed(pkg)

        if "published" in components:
            print "BBB"
            if version[:2] in ["9.", "8.", "7."]:
                # update published dir
                names = [name for name in os.listdir(published_dir) if not name.startswith(".")]
                pkgpaths = [os.readlink(os.path.join(published_dir, name)) for name in names]
                misc.rename(published_dir, published_dir+"-old")
                os.mkdir(published_dir)
                for pkgpath in pkgpaths:
                    pkg = Package(pkgpath)
                    if pkg.exists():
                        if globls.verbose:
                            "upgrading published setting for package (%s)" % (pkg,)
                        dom._Domain__set_published(pkg)

        if "old-files" in components:
            if globls.verbose:
                "cleaning up old files"
            # delete old files
            paths = [label_path, login_path, profile_path, sources_path,
                subdomains_path, version_path]
            for path in paths:
                try:
                    misc.remove(path)
                except:
                    pass

        if "old-dirs" in components:
            if globls.verbose:
                "cleaning up old dirs"
            # delete old dirs
            paths = [domainhomes_dir, platforms_dir]
            for path in paths:
                try:
                    misc.rmtree(path)
                except:
                    pass
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        raise
