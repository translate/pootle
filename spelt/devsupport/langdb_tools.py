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

from spelt.models import *


class LanguageDBProcessor(object):
    """
    A class that performs various actions on a language database.

    This class is intended for use in benchmarking and/or profiling of the
    language database code.

    Only the addition of roots and parts-of-speech are supported here, because
    those are the models that are expected to have the greatest impact on
    Spelt's performance. Also, surface forms can easily be added by importing a
    source (L{LanguageDB.import_source}).

    Example use for adding roots to a language database::
        >>> from langdb_tools import *
        >>> dbproc = LanguageDBProcessor(LanguageDB(filename='testdb.xldb'))
        >>> dbproc.add_roots(500, 'root_prefix')
        >>> dbproc.langdb.save()
    """

    def __init__(self, langdb):
        assert langdb is not None and isinstance(langdb, LanguageDB)
        self.langdb = langdb

    def add_parts_of_speech(self, n, prefix=''):
        """Add C{n} parts-of-speech to the language database with the given
            prefix (default is no prefix).

            The POS's shortcut is set to the same as its name
            """
        for i in range(n):
            name = "%s%d" % (prefix, i+1)
            self.langdb.add_part_of_speech(PartOfSpeech(name=name, shortcut=name))

    def add_roots(self, n, prefix=''):
        """Add C{n} roots to the language database with the given prefix
            (default is no prefix).

            Besides the name, the default values from L{Root}'s C{__init__()}
            are used.
            """
        for i in range(n):
            v = "%s%d" % (prefix, i)
            self.langdb.add_root(Root(value=v))
