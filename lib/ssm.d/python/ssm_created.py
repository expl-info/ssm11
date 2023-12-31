#! /usr/bin/env python2
#
# ssm_created.py

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

"""Provides the created subcommand.
"""

import os.path
import sys
import traceback

from pyerrors.errors import Error, is_error

from ssm import constants
from ssm import globls
from ssm.domain import Domain
from ssm.meta import Meta
from ssm.misc import exits

def print_usage():
    print("""\
usage: ssm created [<options>] -d <dompath>
       ssm created -h|--help

Create a new domain at dompath.

Where:
<dompath>       Domain path.

Options:
-L <string>     Short label for domain.
-r <url>        Repository URL.

--debug         Enable debugging.
--force         Force operation.
--verbose       Enable verbose output.""")

def run(args):
    try:
        dompath = None
        repourl = None
        label = None

        while args:
            arg = args.pop(0)
            if arg == "-d" and args:
                dompath = args.pop(0)
            elif arg == "-L" and args:
                label = args.pop(0)
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
        meta = Meta()
        meta.set("label", label or "")
        meta.set("repository", repourl or "")
        meta.set("version", constants.SSM_VERSION)

        dom = Domain(dompath)
        if dom.path != dom.realpath:
            if globls.force:
                sys.stderr.write("warning: domain path does not match domain realpath\n")
            else:
                exits("error: domain path does not match domain realpath")

        err = dom.create(meta, globls.force)
        if is_error(err):
            exits(err)
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    sys.exit(0)