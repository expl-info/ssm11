#! /usr/bin/env python
#
# ssm_inv.py

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

"""Provides the listd subcommand.
"""

import fnmatch
import json
import os
import sys
from sys import stderr, stdout
import traceback

from ssm import globls
from ssm.domain import Domain
from ssm.error import Error
from ssm.misc import columnize, exits, get_terminal_size
from ssm.package import determine_platforms

def print_usage():
    print("""\
usage: ssm invd [<options>] -d <dompath>
       ssm invd -h|--help

Take an inventory of a domain and return a JSON object.



Where:
<dompath>       Path for domain

--debug         Enable debugging
--verbose       Enable verbose output""")

def run(args):
    try:
        dompath = None

        while args:
            arg = args.pop(0)
            if arg == "-d" and args:
                dompath = args.pop(0)

            elif arg in ["-h", "--help"]:
                print_usage()
                sys.exit(0)
            elif arg == "--debug":
                globls.debug = True
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
        meta = dom.get_meta()
        if meta.get("version") == None:
            exits("error: old domain not supported; you may want to upgrade")

        d = dom.get_inventory()
        print json.dumps(d, sort_keys=True, indent=2)
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    sys.exit(0)