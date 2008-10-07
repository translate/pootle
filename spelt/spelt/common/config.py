#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of Spelt.
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

"""Contains the Configuration class."""

import locale, os
import logging
try:
    import iniparse as ConfigParser
except ImportError, e:
    import ConfigParser

from gettext import gettext as _

from spelt.common.singleton import SingletonMeta


default_config = '~/.locamotion/spelt.ini'

class Configuration(object):
    """Singleton access to the program's configuration.

    This class is mostly based on VirTaal's Settings class."""

    __metaclass__ = SingletonMeta # Make this a Singleton class

    current_database = None # This is not really a config section, but a form of globally accessible variable.

    sections = ['user', 'general']

    user = {
        'id': '0'
    }
    general = {
        'last_langdb_path': '',
        'uilang': None
    }

    def __init__(self, filename=default_config):
        if not filename or '~' in filename:
            self.filename = os.path.expanduser(default_config)
        else:
            self.filename = filename

        try:
            lang = locale.getlocale()[0]
            self.general["uilang"] = lang
        except:
            logging.info(_("Could not get locale"))

        self.parser = ConfigParser.ConfigParser()

        for section in self.sections:
            if not self.parser.has_section(section):
                self.parser.add_section(section)

        self.read();

    def read(self):
        """Read the configuration file and set the dictionaries up."""
        self.parser.read(self.filename)

        for key, value in self.parser.items("user"):
            self.user[key] = value
        for key, value in self.parser.items("general"):
            self.general[key] = value

        # Cast some values to its correct types.
        self.user['id'] = int(self.user['id'])

    def save(self):
        """Write the configuration file."""
        for key in self.user:
            self.parser.set("user", key, self.user[key])
        for key in self.general:
            self.parser.set("general", key, self.general[key])

        # make sure that the configuration directory exists
        project_dir = os.path.split(self.filename)[0]
        if not os.path.isdir(project_dir):
            os.makedirs(project_dir)
        file = open(self.filename, 'w')
        self.parser.write(file)
        file.close()

    def __str__(self):
        return '%s(%s)' % (self.__class__.__name__, self.filename)
