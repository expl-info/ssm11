#! /usr/bin/env python2
#
# ssm/config.py

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

from ConfigParser import ConfigParser
import os.path
import sys

from ssm import globls

def split_commaspace(v):
    v = v.replace(",", " ")
    return v.split()

def load_configuration():

    SYSCONFPATH = os.path.join(os.path.dirname(sys.argv[0]), "../etc/ssm/ssm.conf")
    USERCONFPATH = os.path.expanduser("~/.ssm/ssm.conf")

    globls.conf = ConfigParser()
    globls.conf.optionxform = str
    globls.conf.read([SYSCONFPATH, USERCONFPATH])

    if globls.conf.has_option("defaults", "disabled_publish_platforms"):
        v = globls.conf.get("defaults", "disabled_publish_platforms")
        v = split_commaspace(v)
        globls.disabled_publish_platforms = [None]+v

    if globls.conf.has_option("defaults", "list_for_all_platforms"):
        v = globls.conf.get("defaults", "list_for_all_platforms")
        v = v.lower()
        globls.list_for_all_platforms = v in ["yes", "true"]
