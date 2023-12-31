#! /usr/bin/env python2
#
# ssm/domain.py

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

import os
import os.path
import sys
import tarfile
import traceback

from pyerrors.errors import Error, is_error

from ssm import constants
from ssm import globls
from ssm.deps import DependencyManager
from ssm import misc
from ssm.meta import Meta
from ssm.misc import gets, oswalk1, puts
from ssm.package import Package
from ssm.repository import RepositoryGroup

class Domain:

    def __init__(self, path):
        self.path = os.path.abspath(path)
        self.realpath = os.path.realpath(self.path)
        self.selfpath = self.joinpath("etc/ssm.d/self")
        if os.path.islink(self.selfpath):
            self.path = os.readlink(self.selfpath)
        self.installed_path = self.joinpath("etc/ssm.d/installed")
        self.published_path = self.joinpath("etc/ssm.d/published")
        self.meta_path = self.joinpath("etc/ssm.d/meta.json")

        self.legacy = None

    def __create_depmgr(self, platforms):
        dm = DependencyManager()
        for pkg in self.get_published_packages(platforms):
            control = pkg.get_control()
            dm.add(control.get("name"),
                control.get("version"),
                control.get("requires"),
                control.get("provides"),
                control.get("conflicts"))
        return dm

    def __set_installed(self, pkg):
        #if self.is_legacy():
            #self.__set_installed_legacy(pkg)
            #return

        linkdir = os.path.join(self.installed_path, pkg.platform)
        linkname = os.path.join(linkdir, pkg.name)
        if not os.path.exists(linkdir):
            misc.makedirs(linkdir)
        misc.symlink(pkg.path, linkname, True)

    def __set_installed_legacy(self, pkg):
        linkname = os.path.join(self.installed_path, pkg.name)
        misc.symlink(pkg.path, linkname, True)

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

    def exists(self):
        return os.path.isdir(self.path) \
            and os.path.isdir(self.joinpath("etc/ssm.d"))

    def get_dependents(self, pkg, platform):
        """Return list of packages dependent on the given one
        published for the platform.
        """
        ppkgs = self.get_published_packages([platform])
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

    def get_installed_package(self, name):
        try:
            pkg = Package(self.joinpath(name))
            return pkg.exists() and pkg or None
        except:
            return None

    def get_installed_platforms(self):
        root, platforms, _ = oswalk1(self.installed_path)
        return platforms

    def get_installed_packages(self, platforms=None):
        if self.is_legacy():
            return self.get_installed_packages_legacy(platforms)

        platforms = platforms or self.get_installed_platforms()
        pkgs = []
        for platform in platforms:
            _, dirnames, _ = oswalk1(os.path.join(self.installed_path, platform))
            for dirname in dirnames:
                pkgs.append(Package(os.path.abspath(self.joinpath(dirname))))
        return pkgs

    def get_installed_packages_legacy(self, platforms=None):
        pkgs = []
        _, dirnames, _ = oswalk1(self.installed_path)
        for dirname in dirnames:
            pkgs.append(Package(os.path.abspath(self.joinpath(dirname))))
        if platforms:
            platforms = dict([(platform, None) for platform in platforms])
            pkgs = [pkg for pkg in pkgs if pkg.platform in platforms]
        return pkgs

    def get_inventory(self):
        d = {}
        d["path"] = self.path
        d["meta"] = self.get_meta().getall()
        d["legacy"] = self.is_legacy()
        installed = {}
        if d["legacy"]:
            for name in os.listdir(self.installed_path):
                path = os.path.join(self.installed_path, name)
                installed[name] = os.readlink(path)
        else:
            for plat in os.listdir(self.installed_path):
                root = os.path.join(self.installed_path, plat)
                for name in os.listdir(root):
                    path = os.path.join(root, name)
                    installed[name] = os.readlink(path)
        d["installed"] = installed
        published = {}
        for plat in os.listdir(self.published_path):
            platpublished = {}
            root = os.path.join(self.published_path, plat)
            for name in os.listdir(root):
                path = os.path.join(root, name)
                platpublished[name] = os.readlink(path)
            published[plat] = platpublished
        d["published"] = published
        return d

    def get_meta(self):
        meta = Meta()
        meta.load(self.meta_path)
        return meta

    def get_published_package(self, name, platform=None):
        try:
            pkg = Package(name)
            ppkg = Package(os.path.join(self.published_path, platform or pkg.platform, name))
            return ppkg.exists() and ppkg or None
        except:
            return None

    def get_published_package_short(self, name, platform=None):
        try:
            pkg = Package(name)
            platform = platform or pkg.platform
            root, dirnames, _ = oswalk1(os.path.join(self.published_path, platform))
            for dirname in dirnames:
                ppkg = Package(os.path.join(root, dirname))
                if pkg.short == ppkg.short:
                    if ppkg.exists():
                        return ppkg
                    return None
        except:
            return None

    def get_published_platforms(self):
        _, platforms, _ = oswalk1(self.published_path)
        return platforms

    def get_published_packages(self, platforms=None):
        pkgs = []
        platforms = platforms or self.get_published_platforms()
        for platform in platforms:
            root, dirnames, _ = oswalk1(os.path.join(self.published_path, platform))
            for dirname in dirnames:
                pkgs.append(Package(os.path.abspath(os.path.join(root, dirname))))
        return pkgs

    def get_published_packages_legacy(self, platforms=None):
        root, dirnames, _ = oswalk1(self.published_path)
        pkgs = [Package(os.path.abspath(os.path.join(root, dirname))) for dirname in dirnames]
        if platforms:
            platforms = dict([(platform, None) for platform in platforms])
            pkgs = [pkg for pkg in pkgs if pkg.platform in platforms]
        return pkgs

    def get_repository(self):
        meta = self.get_meta()
        if meta == None:
            return None
        repourl = meta.get("repository")
        if repourl == None:
            return None
        return RepositoryGroup([repourl])

    def get_version_legacy(self):
        return gets(self.joinpath("etc/ssm.d/version"))

    def has_meta(self):
        return os.path.exists(self.meta_path)

    def is_installed(self, pkg):
        ipkg = self.get_installed_package(pkg.name)
        return ipkg and ipkg.path == pkg.path

    def is_legacy(self):
        if self.legacy == None:
            meta = self.get_meta()
            version = meta.get("version")
            if version == None:
                version = self.get_version_legacy()
            if version and version[:2] in ["10", "9.", "8.", "7."]:
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
            ppkg = self.get_published_package(pkg.name, platform)
            if ppkg and ppkg.realpath == pkg.realpath:
                return True
        return False

    def joinpath(self, *comps):
        return os.path.join(self.path, *comps)

    # high-level operations
    def create(self, meta, force=False):
        if self.exists() and not force:
            return Error("domain already exists")
        for dirname in [".", "etc/ssm.d/broken", "etc/ssm.d/installed", "etc/ssm.d/published",]:
            path = self.joinpath(dirname)
            if not os.path.isdir(path):
                misc.makedirs(path)
        os.symlink(self.path, self.selfpath)
        self.put_meta(meta)

    def install(self, pkgfile, force=False, reinstall=False):
        if not self.is_owner():
            return Error("must own domain")
        if pkgfile.is_valid() < 0:
            return Error("package file is not valid")
        pkg = Package(self.joinpath(pkgfile.name))
        if self.is_installed(pkg) and not reinstall and not force:
            return Error("package already installed")
        try:
            err = pkgfile.unpack(self.path)
            if is_error(err):
                # TODO: clean up? set broken?
                return err
            pkg.execute_script("post-install", self.path)
            self.__set_installed(pkg)
        except:
            if globls.debug:
                traceback.print_exc()
            return Error("install was unsuccessful")

    def prepublish(self, pkg, platform):
        """Check that a package could be published.
        """
        ppkgs = self.get_published_packages([platform])
        short2ppkg = dict([(ppkg.short, ppkg) for ppkg in ppkgs])

        try:
            # find missing requires
            dm = self.__create_depmgr([platform])
            control = pkg.get_control()
            dm.add(control.get("name"),
                control.get("version"),
                control.get("requires"),
                control.get("provides"),
                control.get("conflicts"))
            pkgshorts = dm.generate([pkg.short])
            while pkgshorts:
                pkgshort = pkgshorts.pop(0)
                if pkgshort not in short2ppkg and pkgshort != pkg.short:
                    return Error("missing package (%s)" % (pkgshort,))
        except:
            if globls.debug:
                traceback.print_exc()
            return Error("prepublish was unsuccessful (%s)" % (sys.exc_value,))

    def publish(self, pkg, platform, force=False):
        if not self.is_owner():
            return Error("must own domain")
        if self.is_published(pkg, [platform]):
            if not force:
                return Error("package is already published")
            else:
                err = self.unpublish(pkg, platform)
                if is_error(err):
                    return err
        try:
            pubplatpath = self.joinpath(platform)
            for pubdirname in constants.PUBLISHABLE_DIRS:
                for root, dirnames, filenames in os.walk(pkg.joinpath(pubdirname)):
                    relpath = os.path.join(root)[len(pkg.path)+1:]
                    pubbasedir = os.path.join(pubplatpath, relpath)
                    if not os.path.exists(pubbasedir):
                        misc.makedirs(pubbasedir)
                    for dirname in dirnames:
                        # TODO: support ./.../.
                        #misc.makedirs(self.joinpath(relpath, dirname))
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

    def put_meta(self, meta):
        meta.dump(self.meta_path)

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
        if not self.is_published(pkg, [platform]) and not globls.force:
            return Error("package is not published")
        try:
            pubplatpath = self.joinpath(platform)
            for pubdirname in constants.PUBLISHABLE_DIRS:
                # TODO: implement os.walk() for older pythons
                pubdirpath = os.path.join(pubplatpath, pubdirname)
                for root, dirnames, filenames in os.walk(pubdirpath, topdown=False):
                    rmcount = 0
                    for filename in filenames:
                        linkname = os.path.join(root, filename)
                        pkgfilepath = pkg.joinpath(root[len(pubplatpath)+1:], filename)
                        if os.path.realpath(linkname) == os.path.realpath(pkgfilepath):
                            misc.remove(linkname)
                            rmcount += 1
                    if rmcount == len(filenames):
                        # try to remove possibly empty directory
                        if root != pubdirpath:
                            try:
                                misc.rmdir(root)
                            except:
                                pass
            self.__unset_published(pkg, platform)
        except:
            if globls.debug:
                traceback.print_exc()
            return Error("unpublish was unsuccessful")
