#! /usr/bin/env python2
#
# ssm_makepkg.py

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

"""Provides the makepkg subcommand.
"""

import json
import os
import os.path
import StringIO
import sys
from sys import stderr
import tarfile
import traceback

from ssm import globls
from ssm import misc
from ssm.control import Control
from ssm.misc import exits, gid2groupname, uid2username

def print_usage():
    print("""\
usage: ssm makepkg [<options>] <dir>
       ssm makepkg -h|--help

Make a package from the contents of a directory.

Where:
<dir>           Directory to be packaged

Options:
--auto-control  Generate minimal control.json; overrides existing
                control file information if available
-p <pkgname>    Use an alternate package name; implies
                --auto-control

--debug         Enable debugging
--force         Force operation
--verbose       Enable verbose output""")

def run(args):
    try:
        autocontrol = False
        srcdir = None
        pkgname = None

        while args:
            arg = args.pop(0)
            if arg == "--auto-control":
                autocontrol = True
            elif arg == "-p" and args:
                pkgname = args.pop(0)
                autocontrol = True

            elif arg in ["-h", "--help"]:
                print_usage()
                sys.exit(0)
            elif arg == "--debug":
                globls.debug = True
            elif arg == "--force":
                globls.force = True
            elif arg == "--verbose":
                globls.verbose = True
            elif args:
                raise Exception()
            else:
                srcdir = arg

        if srcdir == None:
            raise Exception()
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: bad/missing arguments")

    try:
        if not os.path.exists(srcdir):
            exits("error: cannot find directory")

        if not pkgname:
            pkgname = os.path.basename(srcdir)

        pkgname_comps= pkgname.split("_")
        if len(pkgname_comps) != 3:
            exits("error: bad package name (%s)" % (pkgname,))

        # check required components
        control_path = os.path.join(srcdir, ".ssm.d/control.json")
        control_path_short = os.path.join(pkgname, ".ssm.d/control.json")
        control = Control()
        control.load(control_path)
        if not os.path.exists(control_path) and not autocontrol:
            exits("error: no control.json file (%s)" % (control_path,))

        if autocontrol:
            control.set("name", pkgname_comps[0])
            control.set("version", pkgname_comps[1])
            control.set("platform", pkgname_comps[2])

        # check expected components
        postinstall_script = os.path.join(srcdir, ".ssm.d/post-install")
        preuninstall_script = os.path.join(srcdir, ".ssm.d/pre-uninstall")
        if not os.path.exists(postinstall_script):
            sys.stderr.write("warning: no post-install script (%s)\n" % (postinstall_script,))
        if not os.path.exists(preuninstall_script):
            sys.stderr.write("warning: no pre-uninstall script (%s)\n" % (preuninstall_script,))

        sh_profile_script = os.path.join(srcdir, "etc/profile.d/%s.sh" % (pkgname,))
        csh_profile_script = os.path.join(srcdir, "etc/profile.d/%s.csh" % (pkgname,))
        if not os.path.exists(sh_profile_script):
            sys.stderr.write("warning: no sh profile script (%s)\n" % (sh_profile_script,))
        if not os.path.exists(csh_profile_script):
            sys.stderr.write("warning: no csh profile script (%s)\n" % (csh_profile_script,))

        try:
            excluded = [control_path_short, control_path_short[:-5]]
            def filefilter(ti):
                return ti.name not in excluded and ti or None

            pkgfpath = "%s.ssm" % (pkgname,)
            tf = tarfile.open(pkgfpath, "w|gz")
            tf.add(srcdir, pkgname, recursive=True, filter=filefilter)

            # special case for control.json
            ti = tarfile.TarInfo()
            ti.name = control_path_short
            ti.mode = 0644
            ti.type = tarfile.REGTYPE
            ti.uid = os.getuid()
            ti.gid = os.getgid()
            ti.uname = uid2username(ti.uid)
            ti.gname = gid2groupname(ti.gid)
            s = control.dumps()
            f = StringIO.StringIO(s)
            ti.size = len(s)
            tf.addfile(ti, f)

            tf.close()
        except:
            if os.path.exists(pkgfpath):
                misc.remove(pkgfpath)
            raise
    except SystemExit:
        raise
    except:
        if globls.debug:
            traceback.print_exc()
        exits("error: operation failed")

    sys.exit(0)