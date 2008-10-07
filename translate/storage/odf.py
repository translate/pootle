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

"""This class implements the functionality for handling OpenDocument files.
"""

from translate.misc import xmlwrapper
from translate.storage import base
import zipfile

class ODFUnit(base.TranslationUnit):
    """This class represents an OpenDocument translatable snippet"""

class ODFFile(base.TranslationStore, xmlwrapper.XMLWrapper):
    """This class represents an OpenDocument file"""
    UnitClass = ODFUnit
    def __init__(self, inputfile):
        base.TranslationStore.__init__(self, unitclass=self.UnitClass)
        self.filename = getattr(inputfile, 'name', '')
        try:
            z = zipfile.ZipFile(self.filename, 'r')
            contents = z.read("content.xml")
        except (ValueError, zipfile.BadZipfile):
            contents = open(self.filename, 'r').read()
        root = xmlwrapper.BuildTree(contents)
        xmlwrapper.XMLWrapper.__init__(self, root)
        if self.tag != "document-content": raise ValueError("root %r != 'document-content'" % self.tag)
        self.body = self.getchild("body")
  
    def excludeiterator(self, obj, excludetags):
        nodes = []
        for node in obj._children:
            if xmlwrapper.splitnamespace(node.tag)[1] not in excludetags:
                nodes.append(node)
                nodes.extend(self.excludeiterator(node, excludetags))
        return nodes
  
    def getunits(self):
        nodes = self.excludeiterator(self.body.obj, ["tracked-changes"])
        paragraphs = []
        for node in nodes:
            childns, childtag = xmlwrapper.splitnamespace(node.tag)
            if childtag == "p" or childtag == "h":
                paragraphs.append(xmlwrapper.XMLWrapper(node))
        for child in paragraphs:
            text = child.gettexts().strip()
            self.addsourceunit(text)
        return self.units

