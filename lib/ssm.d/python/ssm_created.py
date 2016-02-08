#! /usr/bin/env python
#
# ssm_created.py

"""Provides the created subcommand.
"""

import sys
from sys import stderr
import traceback

from ssm import constants
from ssm import globls
from ssm.domain import Domain
from ssm.misc import exits

def print_usage():
    print("""\
usage: ssm created [<options>] -d <dompath>
       ssm created -h|--help

Create a new domain at dompath.

Where:
-d <dompath>    Path for domain
-L <string>     Short label for domain
-r <url>        Repository URL

Options:
--debug         Enable debugging
--force         Force operation
--verbose       Enable verbose output""")

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
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: bad/missing arguments")

    if not dompath:
        exits("error: bad/missing arguments")

    try:
        meta = {
            "label": label or "",
            "repository": repourl or "",
            "version": constants.SSM_VERSION,
        }
        dom = Domain(dompath)
        err = dom.create(meta, globls.force)
        if err:
            exits(err)
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")
    sys.exit(0)