#! /usr/bin/env python2
#
# ssm_diffd.py

# GPL--start
# This file is part of ssm (Simple Software Manager)
# Copyright (C) 2005-2019 Environment/Environnement Canada
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

"""Provides the diffd subcommand.
"""

import os.path
import sys
from sys import stderr
import traceback

from ssm import constants
from ssm import globls
from ssm.domain import Domain
from ssm.meta import Meta
from ssm.misc import exits
from ssm.package import Package
from ssm.packagefile import PackageFile
from ssm.repository import Repository

DIFFMARKD = {
    -1: "-",
    0: "=",
    1: "+",
}

def diff_value(value, lvalues, rvalues):
    diff = 0
    if value in lvalues:
        diff -= 1
    if value in rvalues:
        diff += 1
    return diff

def print_usage():
    print("""\
usage: ssm diffd [<options>] [<srcdom> ...] <dstdom>
       ssm diffd -h|--help

Compare two domains and show the differences. Default is to compare
installed and published.

Where:
<ldompath>      Path of left domain
<rdompath>      Path of right domain

Options:
--meta          Compare meta information
--installed     Compare installed
--published     Compare published

--debug         Enable debugging
--force         Force operation
--verbose       Enable verbose output""")

def run(args):
    try:
        ldompath = None
        rdompath = None
        compares = []

        while args:
            arg = args.pop(0)
            if arg == "--installed":
                compares.append("installed")
            elif arg == "--meta":
                compares.append("meta")
            elif arg == "--published":
                compares.append("published")

            elif arg in ["-h", "--help"]:
                print_usage()
                sys.exit(0)
            elif arg == "--debug":
                globls.debug = True
            elif arg == "--force":
                globls.force = True
            elif arg == "--verbose":
                globls.verbose = True
            elif len(args) == 1:
                ldompath = arg
                rdompath = args.pop(0)
            else:
                raise Exception()

        if None in [ldompath, rdompath]:
            raise Exception()

        if not compares:
            compares = ["installed", "published"]
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: bad/missing arguments")

    try:
        doms = [Domain(dompath) for dompath in [ldompath, rdompath]]
        for dom in doms:
            if not dom.exists():
                exits("error: cannot find domain (%s)" % dom.path)
            meta = dom.get_meta()
            if meta.get("version") == None:
                exits("error: old domain (%d) not supported" % dom.path)

        linvd = doms[0].get_inventory()
        rinvd = doms[1].get_inventory()

        if "meta" in compares:
            # compare values of each meta item
            lmeta = linvd["meta"]
            rmeta = rinvd["meta"]
            lnames = set(lmeta)
            rnames = set(rmeta)
            names = sorted(lnames.union(rnames))
            for name in names:
                lvalue = lmeta.get(name)
                rvalue = rmeta.get(name)
                if lvalue == rvalue:
                    print "%s M %s '%s'" % (DIFFMARKD[0], name, lvalue)
                else:
                    print "%s M %s '%s'" % (DIFFMARKD[-1], name, lvalue)
                    print "%s M %s '%s'" % (DIFFMARKD[1], name, rvalue)

        if "installed" in compares:
            lnames = set(linvd["installed"])
            rnames = set(rinvd["installed"])
            names = sorted(lnames.union(rnames))
            for name in names:
                print "%s I %s" % (DIFFMARKD[diff_value(name, lnames, rnames)], name)

        if "published" in compares:
            lpubd = linvd.get("published", {})
            rpubd = rinvd.get("published", {})
            lplatforms = set(lpubd)
            rplatforms = set(rpubd)
            platforms = sorted(lplatforms.union(rplatforms))

            for platform in platforms:
                lplatpubd = lpubd.get(platform, {})
                rplatpubd = rpubd.get(platform, {})
                lnames = set(lplatpubd)
                rnames = set(rplatpubd)
                names = sorted(lnames.union(rnames))
                for name in names:
                    print "%s P %s %s" % (DIFFMARKD[diff_value(name, lnames, rnames)], platform, name)

    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    sys.exit(0)
