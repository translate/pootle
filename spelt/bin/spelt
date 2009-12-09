#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of Spelt
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

import os
import sys
import logging
from optparse import OptionParser, make_option
from os       import path

sys.path.append('spelt')
from spelt.spelt  import Spelt
from spelt.common import _

usage = "usage: %prog [options] [language database]"
option_list = [
    make_option("--profile",
                action="store", type="string", dest="profile",
                help=_("Perform profiling, storing the result to the supplied filename.")),
    make_option("--log",
                action="store", type="string", dest="log",
                help=_("Turn on logging, storing the result to the supplied filename."))
]
parser = OptionParser(option_list=option_list, usage=usage)

def module_path():
    """This will get us the program's directory, even if we are frozen using py2exe"""
    if hasattr(sys, "frozen"):
        return os.path.dirname(unicode(sys.executable, sys.getfilesystemencoding()))
    return os.path.dirname(unicode(__file__, sys.getfilesystemencoding( )))

def run_spelt(dbfilename):
    spelt = Spelt(dbfilename, module_path())
    spelt.run()

def main(argv):
    options, args = parser.parse_args(argv[1:])

    if options.log != None:
        try:
            logging.basicConfig(level=logging.DEBUG,
                                format='%(asctime)s %(levelname)s %(message)s',
                                filename=path.abspath(options.log),
                                filemode='w')
        except IOError:
            parser.error(_("Could not open log file '%s'") % options.log)

    if options.profile != None:
        from devsupport.profiling import profilefunc
        try:
            if not args: args = ['']
            profilefunc(open(options.profile, 'wb'), run_spelt, args[0])
        except IOError:
            parser.error(_("Could not open profile file '%s'") % options.profile)
    else:
        if not args: args = ['']
        run_spelt(args[0])

if __name__ == "__main__":
    main(sys.argv)
