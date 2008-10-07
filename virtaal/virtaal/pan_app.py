#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007-2008 Zuza Software Foundation
#
# This file is part of Virtaal.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import logging

try:
    import iniparse as ConfigParser
except ImportError, e:
    import ConfigParser
import os
import sys
import locale, gettext
gettext.install("virtaal", unicode=1)

from __version__ import ver


x_generator = 'Virtaal ' + ver
default_config = "~/.locamotion/virtaal.ini"

def name():
    # pwd is only available on UNIX
    try:
        import pwd
        import getpass
    except ImportError, _e:
        return u""
    return pwd.getpwnam(getpass.getuser())[4].split(",")[0]


class Settings:
    """Handles loading/saving settings from/to a configuration file."""

    sections = ["translator", "general", "language", "undo"]

    translator =    {
            "name": name(),
            "email": "",
            "team": "",
    }
    general =       {
            "lastdir": "",
            "windowheight": 620,
            "windowwidth": 400,
            "terminology-dir": "",
    }
    language =      {
            "uilang": None,
            "sourcelang": "en",
            "contentlang": None,
            "sourcefont": "mono 9",
            "targetfont": "mono 9",
            "nplurals": 0,
            "plural": None,
    }
    undo = {
            "depth": 50,
    }

    def __init__(self, filename = None):
        """Load settings, using the given or default filename"""
        if not filename:
            self.filename = os.path.expanduser(default_config)
        else:
            self.filename = filename
            if not os.path.isfile(self.filename):
                raise Exception

        try:
            lang = locale.getdefaultlocale()[0]
            self.language["uilang"] = lang
            self.language["contentlang"] = lang
        except:
            logging.info("Could not get locale")
        self.config = ConfigParser.ConfigParser()
        self.read()

    def read(self):
        """Read the configuration file and set the dictionaries up."""
        self.config.read(self.filename)
        for section in self.sections:
            if not self.config.has_section(section):
                self.config.add_section(section)

        for key, value in self.config.items("translator"):
            self.translator[key] = value
        for key, value in self.config.items("general"):
            self.general[key] = value
        for key, value in self.config.items("language"):
            self.language[key] = value
        for key, value in self.config.items("undo"):
            self.undo[key] = value

    def write(self):
        """Write the configuration file."""
        for key in self.translator:
            self.config.set("translator", key, self.translator[key])
        for key in self.general:
            self.config.set("general", key, self.general[key])
        for key in self.language:
            self.config.set("language", key, self.language[key])
        for key in self.undo:
            self.config.set("undo", key, self.undo[key])

        # make sure that the configuration directory exists
        project_dir = os.path.split(self.filename)[0]
        if not os.path.isdir(project_dir):
            os.makedirs(project_dir)
        file = open(self.filename, 'w')
        self.config.write(file)
        file.close()

settings = Settings()


def get_abs_data_filename(path_parts):
    """Get the absolute path to the given file- or directory name in Virtaal's
        data directory.

        @type  path_parts: list
        @param path_parts: The path parts that can be joined by os.path.join().
        """

    if isinstance(path_parts, str):
        path_parts = [path_parts]

    BASE_DIRS = [
        os.path.dirname(unicode(__file__, sys.getfilesystemencoding())),
        os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
    ]

    DATA_DIRS = [
        ["..", "share"],
        ["share"]
    ]

    for basepath, data_dir in ((x, y) for x in BASE_DIRS for y in DATA_DIRS):
        dir_and_filename = data_dir + path_parts
        datafile = os.path.join(basepath or os.path.dirname(__file__), *dir_and_filename)
        if os.path.exists(datafile):
            return datafile
    raise Exception('Could not find "%s"' % (os.path.join(*path_parts)))
