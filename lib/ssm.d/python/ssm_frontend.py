#! /usr/bin/env python
#
# ssm_frontend.py

import sys

def print_usage():
    sys.stderr.write("""\
usage: ssm <cmd> [<args>]

Simple Software Manager.

List operations:
    ssm diffd|find|listd [<args>]

Package management:
    ssm install|publish|uninstall|unpublish [<args>]
        
Domain management:
    ssm cloned|created|freezed|showd|unfreezed|updated [<args>]

Other:
    ssm version

For help, specify -h or --help to the command.
""")

if __name__ == "__main__":
    args = sys.argv[1:]
    if not args:
        sys.stderr.write("error: bad/missing arguments\n")
        sys.exit(1)

    cmd = args.pop(0)
    if cmd in ["-h", "--help"]:
        print_usage()
        sys.exit(0)

    elif cmd == "diffd":
        print("NIY")
    elif cmd == "find":
        print("NIY")
    elif cmd == "listd":
        import ssm_listd
        ssm_listd.run(args)

    elif cmd == "build":
        import ssm_build
        ssm_build.run(args)
    elif cmd == "install":
        import ssm_install
        ssm_install.run(args)
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
    elif cmd == "version":
        from ssm import constants
        print(constants.SSM_VERSION)
