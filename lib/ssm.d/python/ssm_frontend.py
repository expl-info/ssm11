#! /usr/bin/env python
#
# ssm_frontend.py

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

import sys
from sys import stderr

def print_usage():
    stderr.write("""\
usage: ssm <cmd> [<args>]

Simple Software Manager.

List operations:
    ssm inv|listd [<args>]

Package management:
    ssm install|publish|uninstall|unpublish [<args>]
        
Domain management:
    ssm cloned|created|upgraded [<args>]

Other:
    ssm version

For help, specify -h or --help to the command.
""")

#    ssm diffd|find|listd [<args>]
#    ssm cloned|created|freezed|showd|unfreezed|updated|upgraded [<args>]

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        stderr.write("error: bad/missing arguments\n")
        sys.exit(1)

    cmd = args.pop(0)
    if cmd in ["-h", "--help"]:
        print_usage()
        sys.exit(0)

    elif cmd == "cloned":
        import ssm_cloned
        ssm_cloned.run(args)
    elif cmd == "diffd":
        print("NIY")
    elif cmd == "find":
        import ssm_find
        ssm_find.run(args)
    elif cmd == "listd":
        import ssm_listd
        ssm_listd.run(args)

    elif cmd == "build":
        import ssm_build
        ssm_build.run(args)
    elif cmd == "install":
        import ssm_install
        ssm_install.run(args)
    elif cmd == "inv":
        import ssm_inv
        ssm_inv.run(args)
    elif cmd == "publish":
        import ssm_publish
        ssm_publish.run(args)
    elif cmd == "uninstall":
        import ssm_uninstall
        ssm_uninstall.run(args)
    elif cmd == "unpublish":
        import ssm_unpublish
        ssm_unpublish.run(args)

    elif cmd == "cloned":
        print("NIY")
    elif cmd == "created":
        import ssm_created
        ssm_created.run(args)
    elif cmd == "freezed":
        print("NIY")
    elif cmd == "showd":
        print("NIY")
    elif cmd == "unfreezed":
        print("NIY")
    elif cmd == "updated":
        print("NIY")
    elif cmd == "upgraded":
        import ssm_upgraded
        ssm_upgraded.run(args)
    elif cmd == "version":
        from ssm import constants
        print(constants.SSM_VERSION)
    else:
        stderr.write("error: unknown subcommand\n")
        sys.exit(1)
