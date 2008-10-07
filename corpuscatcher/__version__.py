#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of CorpusCatcher.
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

"""Contains the version of CorpusCatcher."""

__version__ = '0.1'

def print_version_info(scriptname):
    """Print version information (based on `ls --version`)."""
    from gettext import gettext as _

    print '%s (CorpusCatcher) %s' % (scriptname, __version__)
    print _('License GPLv2: GNU GPL version 2 <http://www.gnu.org/licenses/old-licenses/gpl-2.0.html>')
    print _('This is free software: you are free to change and redistribute it.')
    print _('There is NO WARRANTY, to the extent permitted by law.') + '\n'
    print _('Written by Walter Leibbrandt.')
    exit(0)
