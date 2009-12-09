#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of the Translate Toolkit.
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

from tools.mozilla import moz_l10n_builder


MOZDIR = os.path.join( os.path.expanduser('~'), 'mozbuild' )

def build_langs(langs, verbose):
    olddir = os.getcwd()
    os.chdir(MOZDIR)

    moz_l10n_builder.main(
        langs=langs,
        mozcheckout=True,
        recover=True,
        potpack=True,
        potincl=['README.mozilla-pot'],
        popack=True,
        update_trans=True,
        diff=False,
        langpack=True,
        verbose=verbose
    )

    os.chdir(olddir)

def check_potpacks():
    """Copy new and check available POT-packs."""
    pass

def update_rss():
    """Update the RSS feed with the available POT-packs."""
    pass

USAGE='%prog [<options>]'
def create_option_parser():
    """Creates and returns cmd-line option parser."""

    from optparse import OptionParser

    parser = OptionParser(usage=USAGE)
    parser.add_option(
        '-q', '--quiet',
        dest='verbose',
        action='store_false',
        default=True,
        help='Print as little as possible output.'
    )

    return parser

def main(langs, verbose):
    if not langs:
        langs = ['ALL']

    if not os.path.isdir(MOZDIR):
        os.makedirs(MOZDIR)

    build_langs(langs, verbose)
    check_potpacks()
    update_rss()

def main_cmd_line():
    """Processes command-line arguments and send them to main()."""
    options, args = create_option_parser().parse_args()

    main(args, options.verbose) # args == langs to build

if __name__ == '__main__':
    main_cmd_line()
