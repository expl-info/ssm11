#! /usr/bin/env python
#
# ssm/misc.py

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

import grp
import os
import os.path
import pwd
import shutil
import sys
import traceback

from ssm import globls

def columnize(lines, displaywidth=80, gapwidth=2):
    _lines = []
    gap = " "*gapwidth
    maxwidth = max(map(len, lines))
    ncols = 1+max(0, (displaywidth-maxwidth)/(gapwidth+maxwidth))
    fmt = "%%-%ss" % (maxwidth+gapwidth,)
    col = 0
    _line = []
    for line in lines:
        _line.append(fmt % line)
        col += 1
        if col == ncols:
            _lines.append("".join(_line))
            _line = []
            col = 0
    else:
        if col:
            _lines.append("".join(_line))
    return _lines

def exits(msg, status=1):
    sys.stderr.write("%s\n" % str(msg))
    sys.exit(status)

def gets(path):
    try:
        return open(path, "r").read()
    except:
        return None

def get_terminal_size(_nrows=24, _ncols=80):
    """Get terminal (rows, cols) size.

    If a tty does not exist or some failure occurs, use defaults or
    what is passed in.
    """
    try:
        import fcntl
        import termios
        import struct

        nrows, ncols, pixrows, pixcols = struct.unpack("HHHH", fcntl.ioctl(0, termios.TIOCGWINSZ, struct.pack("HHHH", 0, 0, 0, 0)))
    except:
        nrows, ncols = _nrows, _ncols
    return nrows, ncols

def gid2groupname(gid):
    try:
        gr = grp.getgrgid(gid)
        return gr.gr_name
    except:
        pass

def isrealdir(path):
    return os.path.isdir(path) and not os.path.islink(path)

def makedirs(path, mode=0755):
    try:
        if globls.verbose:
            sys.stderr.write("info: makedirs(%s,%o)\n" % (path, mode))
        os.makedirs(path, mode)
    except:
        if globls.debug:
            sys.stderr.write("%s\n" % traceback.format_exc())
        raise

def mkdir(path, mode=0755):
    try:
        if globls.verbose:
            sys.stderr.write("info: mkdir(%s,%o)\n" % (path, mode))
        os.mkdir(path, mode)
    except:
        if globls.debug:
             sys.stderr.write("%s\n" % traceback.format_exc())
        raise

def oswalk1(path):
    for root, dirnames, filenames in os.walk(path):
        return root, dirnames, filenames
    return path, [], []

def puts(path, s):
    try:
        open(path, "w").write(s)
        return s
    except:
        return None

def remove(path):
    try:
        if globls.verbose:
            sys.stderr.write("info: remove(%s)\n" % (path,))
        os.remove(path)
    except:
        if globls.debug:
             sys.stderr.write("%s\n" % traceback.format_exc())
        raise

def removedirs(path):
    try:
        if globls.verbose:
            sys.stderr.write("info: removedirs(%s)\n" % (path,))
        os.removedirs(path)
    except:
        if globls.debug:
             sys.stderr.write("%s\n" % traceback.format_exc())
        raise

def rename(oldpath, newpath):
    try:
        if globls.verbose:
            sys.stderr.write("info: rename(%s, %s)\n" % (oldpath, newpath))
        os.rename(oldpath, newpath)
    except:
        if globls.debug:
             sys.stderr.write("%s\n" % traceback.format_exc())
        raise

def rmdir(path):
    try:
        if globls.verbose:
            sys.stderr.write("info: rmdir(%s)\n" % (path,))
        os.rmdir(path)
    except:
        if globls.debug:
             sys.stderr.write("%s\n" % traceback.format_exc())
        raise

def rmtree(path):
    try:
        if globls.verbose:
            sys.stderr.write("info: rmtree(%s)\n" % (path,))
        shutil.rmtree(path)
    except:
        if globls.debug:
            sys.stderr.write("%s\n" % traceback.format_exc())
        raise

def symlink(src, linkname, force=False):
    try:
        if force and os.path.exists(linkname):
            remove(linkname)
        if globls.verbose:
            sys.stderr.write("info: symlink(%s, %s)\n" % (src, linkname))
        os.symlink(src, linkname)
    except:
        if globls.debug:
             sys.stderr.write("%s\n" % traceback.format_exc())
        raise

def uid2username(uid):
    try:
        pw = pwd.getpwuid(uid)
        return pw.pw_name
    except:
        pass
