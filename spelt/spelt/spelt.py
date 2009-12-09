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

import gobject
import gtk
import os

from gui    import GUI
from common import _

def get_data_file_abs_name(basepath, filename):
    """Get the absolute path to the given file- or directory name in VirTaal's
        data directory.

        @type  filename: str
        @param filename: The file- or directory name to look for in the data
            directory.
        """
    import sys

    BASE_DIRS = [
        basepath,
        os.path.dirname(unicode(__file__, sys.getfilesystemencoding())),
        os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
    ]

    DATA_DIRS = [
        ["..", "share", "spelt"],
        ["share", "spelt"]
    ]

    for basepath, data_dir in ((x, y) for x in BASE_DIRS for y in DATA_DIRS):
        dir_and_filename = data_dir + [filename]
        datafile = os.path.join(basepath or os.path.dirname(__file__), *dir_and_filename)
        if os.path.exists(datafile):
            return datafile
    raise Exception('Could not find "%s"' % (filename,))


class Spelt(object):
    """Main entry point for Spelt."""
    def __init__(self, dbfilename, basepath):
        """Creates a gui.GUI object."""
        self.gui = GUI(
            dbfilename,
            get_data_file_abs_name(basepath, 'spelt.glade'),
            get_data_file_abs_name(basepath, 'spelt.ico'),
            get_data_file_abs_name(basepath, 'splash_logo.png')
        )

    def find_glade(self, basepath, glade_filename):
        """This method is based on the load_glade_file() function in VirTaal's virtaal/main_window.py."""
        for glade_dir in GLADE_DIRS:
            path = glade_dir + [glade_filename]
            file = os.path.join(basepath or os.path.dirname(__file__), *path)

            if os.path.exists(file):
                return file

        raise Exception(_('Could not find Glade file: ') + glade_filename)

    def run(self):
        """Calls gtk.main()"""
        gobject.idle_add(self.gui.show)
        gtk.main()
