#! /usr/bin/env python
#
# ssm_listd.py

"""Provides the listd subcommand.
"""

import fnmatch
import os
import sys
from sys import stderr
import traceback

from ssm import globls
from ssm.domain import Domain
from ssm.misc import exits
from ssm.package import determine_platform

def print_usage():
    print("""\
usage: ssm listd [<options>] -d <dompath>
       ssm listd -h|--help

List packages in a domain. Default is to show for current platform
only.

Where:
-d <dompath>    Path for domain

Options:
-o <field>[,...]
                Print selected field information (:-separated):
                domain - domain name
                domain_owner - username of domain owner
                domain_state - domain state (e.g., F for frozen)
                domains - install and publish domains
                install_domain - install domains
                install_domain_owner - username of domain owner
                install_domain_state - domain state
                install_timestamp - time of package install
                name - package name
                publish_domain - domain name
                publish_domain_owner - username of domain owner
                publish_domain_state - domain state
                publish_timestamp - time of package publish
                state - package state (e.g., IPp?)
                title - package title

-p <pattern>    Package name pattern with * and ? wilcard support;
                default is match all (*)
-pp <pattern>   Platform pattern with * and ? wildcard support;
                default is taken from SSMUSE_PLATFORM

--debug         Enable debugging
--force         Force operation
--verbose       Enable verbose output""")

def run(args):
    try:
        dompath = None
        fields = None
        pkgnamepat = None
        platpat = None
        platforms = None

        while args:
            arg = args.pop(0)
            if arg == "-d" and args:
                dompath = args.pop(0)
            elif arg == "-o" and args:
                fields = args.pop(0).split(",")
            elif arg == "-p" and args:
                pkgnamepat = args.pop(0)
            elif arg == "-pp" and args:
                platpat = args.pop(0)

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
            exits("error: cannot find domain (%s)" % (dompath,))

        if platpat == None:
            platform = determine_platform()
            if not platform:
                exits("error: cannot determine platform")
            platforms = [platform]
        else:
            platforms = fnmatch.filter(dom.get_published_platforms(), platpat)

        for i, platform in enumerate(platforms):
            ipkgs = dom.get_installeds(platform and [platform])
            ppkgs = dom.get_publisheds(platform and [platform])

            name2ipkg = dict([(ipkg.name, ipkg) for ipkg in ipkgs])
            name2ppkg = dict([(ppkg.name, ppkg) for ppkg in ppkgs])
            names = sorted(set(name2ipkg.keys()+name2ppkg.keys()))
            if pkgnamepat:
                names = fnmatch.filter(names, pkgnamepat)

            if not names:
                continue

            if i:
                print
            print "----- platform (%s) -----" % (platform,)

            if not fields:
                for name in names:
                    state = ""
                    if name in name2ipkg:
                        state += "I"
                        pkg = name2ipkg[name]
                    if name in name2ppkg:
                        if "I" in state:
                            state += "P"
                        else:
                            state += "p"
                        pkg = name2ppkg[name]
                    print("%-4s  %-40s  %s" % (state, name, pkg.path))
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    sys.exit(0)