#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2007 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

"""Class that manages .ini files for translation

@note: A simple summary of what is permissible follows.

# a comment
; a comment
    
[Section]
a = a string
b : a string

"""
from translate.storage import base
from translate.misc.ini import INIConfig 
from StringIO import StringIO
import re


class iniunit(base.TranslationUnit):
    """A INI file entry"""
    def __init__(self, source=None, encoding="UTF-8"):
        self.location = ""
        if source:
            self.source = source
        super(iniunit, self).__init__(source)

    def addlocation(self, location):
        self.location = location

    def getlocations(self):
        return [self.location]

class inifile(base.TranslationStore):
    """An INI file"""
    UnitClass = iniunit
    def __init__(self, inputfile=None, unitclass=iniunit):
        """construct an INI file, optionally reading in from inputfile."""
        self.UnitClass = unitclass
        base.TranslationStore.__init__(self, unitclass=unitclass)
        self.units = []
        self.filename = ''
        self._inifile = None
        if inputfile is not None:
            self.parse(inputfile)

    def __str__(self):
        _outinifile = self._inifile
        for unit in self.units:
            for location in unit.getlocations():
                match = re.match('\\[(?P<section>.+)\\](?P<entry>.+)', location)
                _outinifile[match.groupdict()['section']][match.groupdict()['entry']] = unit.target
        if _outinifile:
            return str(_outinifile)
        else:
            return ""

    def parse(self, input):
        """parse the given file or file source string"""
        if hasattr(input, 'name'):
            self.filename = input.name
        elif not getattr(self, 'filename', ''):
            self.filename = ''
        if hasattr(input, "read"):
            inisrc = input.read()
            input.close()
            input = inisrc
        if isinstance(input, str):
            input = StringIO(input)
            self._inifile = INIConfig(input, optionxformvalue=None)
        else:
            self._inifile = INIConfig(file(input), optionxformvalue=None)
        for section in self._inifile:
            for entry in self._inifile[section]:
                newunit = self.addsourceunit(self._inifile[section][entry])
                newunit.addlocation("[%s]%s" % (section, entry))
