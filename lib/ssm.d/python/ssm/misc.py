#! /usr/bin/env python
#
# ssm/misc.py

import os
import os.path
import shutil
import sys
import traceback

from ssm import globls

def exits(msg, status=1):
    sys.stderr.write("%s\n" % str(msg))
    sys.exit(status)

def gets(path):
    try:
        return open(path, "r").read()
    except:
        return None

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
