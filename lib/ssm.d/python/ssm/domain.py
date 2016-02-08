#! /usr/bin/env python
#
# ssm/domain.py

import json
import os
import os.path
import sys
import tarfile
import traceback

from ssm import constants
from ssm import globls
from ssm.deps import DependencyManager
from ssm import misc
from ssm.error import Error
from ssm.misc import gets, oswalk1, puts
from ssm.package import Package

class Domain:

    def __init__(self, path):
        path = os.path.realpath(path)
        self.path = path
        self.installed_path = os.path.join(self.path, "etc/ssm.d/installed")
        self.published_path = os.path.join(self.path, "etc/ssm.d/published")
        self.meta_path = os.path.join(self.path, "etc/ssm.d/meta.json")

        self.meta = None
        self.legacy = None

    def __get_meta(self, force=False):
        if self.meta == None or force:
            s = gets(self.meta_path)
            if s == None:
                return None
            self.meta = json.loads(s)
        return self.meta

    def __create_depmgr(self, platforms):
        dm = DependencyManager()
        for pkg in self.get_publisheds(platforms):
            control = pkg.get_control()
            dm.add(control.get("name", control.get("package")),
                control.get("version"),
                control.get("requires"),
                control.get("provides"),
                control.get("conflicts"))
        return dm

    def __set_installed(self, pkg):
        if self.is_legacy():
            self.__set_installed_legacy(pkg)
            return

        linkdir = os.path.join(self.installed_path, pkg.platform)
        linkname = os.path.join(linkdir, pkg.name)
        if not os.path.exists(linkdir):
            misc.makedirs(linkdir)
        misc.symlink(pkg.path, linkname, True)

    def __set_installed_legacy(self, pkg):
        linkname = os.path.join(self.installed_path, pkg.name)
        misc.symlink(pkg.path, linkname, True)

    def __set_meta(self, meta):
        return puts(self.meta_path, json.dumps(meta))

    def __set_published(self, pkg, platform=None):
        platform = platform or pkg.platform
        linkdir = os.path.join(self.published_path, platform)
        linkname = os.path.join(linkdir, pkg.name)
        if not os.path.exists(linkdir):
            misc.makedirs(linkdir)
        misc.symlink(pkg.path, linkname, True)

    def __unset_installed(self, pkg):
        if self.is_legacy():
            self.__unset_installed_legacy(pkg)
            return

        linkdir = os.path.join(self.installed_path, pkg.platform)
        linkname = os.path.join(linkdir, pkg.name)      
        misc.remove(linkname)

    def __unset_installed_legacy(self, pkg):
        linkname = os.path.join(self.installed_path, pkg.name)
        misc.remove(linkname)

    def __unset_published(self, pkg, platform=None):
        platform = platform or pkg.platform
        linkdir = os.path.join(self.published_path, platform)
        linkname = os.path.join(linkdir, pkg.name)      
        misc.remove(linkname)

    def __update_meta(self, name, value):
        meta = self.__get_meta(True)
        if meta == None:
            return None
        meta[name] = s
        self.__set_meta(meta)
        self.meta = meta
        return meta

    def exists(self):
        return os.path.exists(self.path)

    def get_dependents(self, pkg, platform):
        """Return list of packages dependent on the given one
        published for the platform.
        """
        ppkgs = self.get_publisheds([platform])
        short2ppkg = dict([(ppkg.short, ppkg) for ppkg in ppkgs])

        pkgs = []
        try:
            # find dependent packages
            dm = self.__create_depmgr([platform])
            pkgshorts = dm.get_requiredby([pkg.short], True)
            for pkgshort in pkgshorts:
                pkgs.append(short2ppkg[pkgshort])
        except:
            pkgs = []
        return pkgs

    def get_installed(self, name):
        try:
            pkg = Package(os.path.join(self.path, name))
            return pkg.exists() and pkg or None
        except:
            return None

    def get_installed_platforms(self):
        root, platforms, _ = oswalk1(self.installed_path)
        return platforms

    def get_installeds(self, platforms=None):
        if self.is_legacy():
            return self.get_installeds_legacy(platforms)

        platforms = platforms or self.get_installed_platforms()
        pkgs = []
        for platform in platforms:
            root, dirnames, _ = oswalk1(os.path.join(self.installed_path, platform))
            for dirname in dirnames:
                pkgs.append(Package(os.path.realpath(os.path.join(root, dirname))))
        return pkgs

    def get_installeds_legacy(self, platforms=None):
        pkgs = []
        root, dirnames, _ = oswalk1(self.installed_path)
        for dirname in dirnames:
            pkgs.append(Package(os.path.realpath(os.path.join(root, dirname))))
        if platforms:
            platforms = dict([(platform, None) for platform in platforms])
            pkgs = [pkg for pkg in pkgs if pkg.platform in platforms]
        return pkgs

    def get_label(self):
        meta = self.__get_meta()
        if meta == None:
            return Error("cannot get label")
        return meta.get("label", "")

    def get_published(self, name, platform=None):
        try:
            pkg = Package(name)
            ppkg = Package(os.path.join(self.published_path, platform or pkg.platform, name))
            return ppkg.exists() and ppkg or None
        except:
            return None

    def get_published_platforms(self):
        root, platforms, _ = oswalk1(self.published_path)
        return platforms

    def get_publisheds(self, platforms=None):
        pkgs = []
        platforms = platforms or self.get_published_platforms()
        for platform in platforms:
            root, dirnames, _ = oswalk1(os.path.join(self.published_path, platform))
            for dirname in dirnames:
                pkgs.append(Package(os.path.realpath(os.path.join(root, dirname))))
        return pkgs

    def get_publisheds_legacy(self, platforms=None):
        root, dirnames, _ = oswalk1(self.published_path)
        pkgs = [Package(os.path.realpath(os.path.join(root, dirname))) for dirname in dirnames]
        if platforms:
            platforms = dict([(platform, None) for platform in platforms])
            pkgs = [pkg for pkg in pkgs if pkg.platform in platforms]
        return pkgs

    def get_repository(self):
        meta = self.__get_meta()
        if meta == None:
            return Error("cannot get repository")
        return meta.get("respository", "")

    def get_version(self):
        meta = self.__get_meta()
        if meta == None:
            return Error("cannot get version")
        return meta.get("version", "")

    def is_installed(self, pkg):
        ipkg = self.get_installed(pkg.name)
        return ipkg and ipkg.path == pkg.path

    def is_legacy(self):
        if self.legacy == None:
            version = self.get_version()
            if not isinstance(version, Error) and version[:2] in ["10", "9.", "8.", "7."]:
                self.legacy = True
            else:
                self.legacy = False
        return self.legacy

    def is_owner(self):
        try:
            return os.stat(self.path).st_uid == os.getuid()
        except:
            pass
        return False

    def is_published(self, pkg, platforms=None):
        if not pkg.exists():
            return False
        platforms = platforms or self.get_published_platforms()
        for platform in platforms:
            ppkg = self.get_published(pkg.name, platform)
            if ppkg and ppkg.path == pkg.path:
                return True
        return False

    def set_label(self, s):
        if self.__update_meta(name, value) == None:
            return Error("cannot set label")
        
    def set_repository(self, url):
        if self.__update_meta("repository", url) == None:
            return Error("cannot set repository")

    def set_version(self, s):
        if self.__update_meta("version", s) == None:
            return Error("cannot set version")

    # high-level operations
    def create(self, meta, force=False):
        if self.exists() and not force:
            return Error("domain already exists")
        for dirname in [".", "etc/ssm.d/broken", "etc/ssm.d/installed", "etc/ssm.d/published",]:
            misc.makedirs(os.path.join(self.path, dirname))
        self.__set_meta(meta)

    def install(self, pkgfile, force=False):
        if not self.is_owner():
            return Error("must own domain")
        if pkgfile.is_valid() < 0:
            return Error("package file is not valid")
        pkg = Package(os.path.join(self.path, pkgfile.name))
        if self.is_installed(pkg) and not force:
            return Error("package already installed")
        try:
            pkgfile.unpack(self.path)
            if not os.path.exists(pkg.control_path):
                pkg.set_control(pkg.get_control())
            pkg.execute_script("post-install", self.path)
            self.__set_installed(pkg)
        except:
            if globls.debug:
                traceback.print_exc()
            return Error("install was unsuccessful")

    def prepublish(self, pkg, platform):
        """Check that a package could be published.
        """
        ppkgs = self.get_publisheds([platform])
        short2ppkg = dict([(ppkg.short, ppkg) for ppkg in ppkgs])

        try:
            # find missing requires
            dm = self.__create_depmgr([platform])
            control = pkg.get_control()
            dm.add(control.get("name", control.get("package")),
                control.get("version"),
                control.get("requires"),
                control.get("provides"),
                control.get("conflicts"))
            pkgshorts = dm.generate([pkg.short])
            while pkgshorts:
                pkgshort = pkgshorts.pop(0)
                if pkgshort not in short2ppkg and pkgshort != pkg.short:
                    return Error("error: missing package (%s)" % (pkgshort,))
        except:
            return Error(sys.exc_value)

    def publish(self, pkg, platform, force=False):
        if not self.is_owner():
            return Error("must own domain")
        if self.is_published(pkg, [platform]):
            if not force:
                return Error("package is already published")
            else:
                err = self.unpublish(pkg, platform)
                if err:
                    return err
        try:
            pubplatpath = os.path.join(self.path, platform)
            for pubdirname in constants.PUBLISHABLE_DIRS:
                for root, dirnames, filenames in os.walk(os.path.join(pkg.path, pubdirname)):
                    relpath = os.path.join(root)[len(pkg.path)+1:]
                    pubbasedir = os.path.join(pubplatpath, relpath)
                    if not os.path.exists(pubbasedir):
                        misc.makedirs(pubbasedir)
                    for dirname in dirnames:
                        # TODO: support ./.../.
                        #misc.makedirs(os.path.join(self.path, relpath, dirname))
                        pubsubdir = os.path.join(pubbasedir, dirname)
                        if not os.path.exists(pubsubdir):
                            misc.makedirs(os.path.join(pubbasedir, dirname))
                    for filename in filenames:
                        linkname = os.path.join(pubplatpath, relpath, filename)
                        misc.symlink(os.path.join(root, filename), linkname, force)
            self.__set_published(pkg, platform)
        except:
            if globls.debug:
                traceback.print_exc()
            return Error("publish was unsuccessful")

    def uninstall(self, pkg):
        if not self.is_installed(pkg):
            return Error("package is not installed")
        if self.is_published(pkg):
            return Error("package is published")
        try:
            pkg.execute_script("pre-uninstall", self.path)
            misc.rmtree(pkg.path)
            self.__unset_installed(pkg)
        except:
            if globls.debug:
                traceback.print_exc()
            return Error("uninstall was unsuccessful")

    def unpublish(self, pkg, platform):
        """Unpublish package.
        """
        if not self.is_published(pkg, [platform]):
            return Error("package is not published")
        try:
            pubplatpath = os.path.join(self.path, platform)
            for pubdirname in constants.PUBLISHABLE_DIRS:
                # TODO: implement os.walk() for older pythons
                pubdirpath = os.path.join(pubplatpath, pubdirname)
                for root, dirnames, filenames in os.walk(pubdirpath, topdown=False):
                    rmcount = 0
                    for filename in filenames:
                        linkname = os.path.join(root, filename)
                        path = os.path.realpath(linkname)
                        if path.startswith(pkg.path):
                            misc.remove(linkname)
                            rmcount += 1
                    if rmcount == len(filenames) and len(dirnames) == 0:
                        # remove empty directory
                        if root != pubdirpath:
                            misc.rmdir(root)
            self.__unset_published(pkg, platform)
        except:
            if globls.debug:
                traceback.print_exc()
            return Error("unpublish was unsuccessful")