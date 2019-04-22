#! /usr/bin/env python2
#
# ssm_listd.py

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

"""Provides the listd subcommand.
"""

import fnmatch
import os
import sys
from sys import stderr, stdout
import traceback

from pyerrors.errors import Error, is_error

from ssm import globls
from ssm.domain import Domain
from ssm.misc import columnize, exits, get_terminal_size
from ssm.package import determine_platforms

def print_usage():
    print("""\
usage: ssm listd [<options>] -d <dompath>
       ssm listd -h|--help

List packages in a domain. Default is to show for current platforms
only.

Where:
<dompath>       Path for domain

Options:
-p <pattern>    Package name pattern with * and ? wilcard support;
                default is match all (*)
-pp <pattern>   Platform pattern with * and ? wildcard support;
                default list is taken from SSM_PLATFORMS or
                SSMUSE_PLATFORMS

--debug         Enable debugging
--force         Force operation
--verbose       Enable verbose output""")

#-o <field>[,...]
#                Print selected field information (:-separated):
#                domain - domain name
#                domain_owner - username of domain owner
#                domain_state - domain state (e.g., F for frozen)
#                domains - install and publish domains
#                install_domain - install domains
#                install_domain_owner - username of domain owner
#                install_domain_state - domain state
#                install_timestamp - time of package install
#                name - package name
#                publish_domain - domain name
#                publish_domain_owner - username of domain owner
#                publish_domain_state - domain state
#                publish_timestamp - time of package publish
#                state - package state (e.g., IPp?)
#                title - package title

def run(args):
    try:
        dompath = None
        fields = None
        longoutput = False
        pkgnamepat = None
        platpat = globls.list_for_all_platforms and "*" or None
        platforms = None

        while args:
            arg = args.pop(0)
            if arg == "-d" and args:
                dompath = args.pop(0)
            #elif arg == "-o" and args:
                #fields = args.pop(0).split(",")
            elif arg == "-p" and args:
                pkgnamepat = args.pop(0)
            elif arg == "-pp" and args:
                platpat = args.pop(0)
            elif arg == "--long":
                longoutput = True

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

        if not dompath:
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
            exits("error: cannot find domain (%s)" % (dompath,))
        meta = dom.get_meta()
        if meta.get("version") == None:
            exits("error: old domain not supported; you may want to upgrade")

        if platpat == None:
            if not platforms:
                platforms = determine_platforms()
                if not platforms:
                    exits("error: cannot determine platforms")
        else:
            platforms = set(dom.get_installed_platforms()+dom.get_published_platforms())
            platforms = fnmatch.filter(platforms, platpat)

        skip = False
        _, displaywidth = get_terminal_size()
        for platform in sorted(platforms):
            ipkgs = dom.get_installeds(platform and [platform])
            ppkgs = dom.get_publisheds(platform and [platform])

            name2ipkg = dict([(ipkg.name, ipkg) for ipkg in ipkgs])
            name2ppkg = dict([(ppkg.name, ppkg) for ppkg in ppkgs])
            names = sorted(set(name2ipkg.keys()+name2ppkg.keys()))
            if pkgnamepat:
                names = fnmatch.filter(names, pkgnamepat)

            if not names:
                continue

            if skip:
                print
            else:
                skip = True
            print "----- platform (%s) -----" % (platform,)

            if not fields:
                lines = []
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
                    if longoutput:
                        lines.append("%-4s  %-40s  %s" % (state, name, pkg.path))
                    else:
                        lines.append("%-4s  %-40s" % (state, name))
                if longoutput:
                    stdout.write("\n".join(lines))
                else:
                    stdout.write("\n".join(columnize(lines, displaywidth, 2)))
                stdout.write("\n")
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    sys.exit(0)