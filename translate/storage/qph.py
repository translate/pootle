#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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
#

"""Module for handling Qt Phrase Book (.qph) files.

Extract from the U{Qt Linguist Manual:
Translators<http://doc.trolltech.com/4.3/linguist-translators.html>}:
.qph Qt Phrase Book Files are human-readable XML files containing standard
phrases and their translations. These files are created and updated by Qt
Linguist and may be used by any number of projects and applications.
"""

from translate.storage import lisa
from lxml import etree

class QphUnit(lisa.LISAunit):
    """A single term in the qph file."""

    rootNode = "phrase"
    languageNode = "source"
    textNode = ""
    namespace = ''

    def createlanguageNode(self, lang, text, purpose):
        """Returns an xml Element setup with given parameters."""
        assert purpose
        langset = etree.Element(self.namespaced(purpose))
        langset.text = text
        return langset

    def _getsourcenode(self):
        return self.xmlelement.find(self.namespaced(self.languageNode))
    
    def _gettargetnode(self):
        return self.xmlelement.find(self.namespaced("target"))
    
    def getlanguageNodes(self):
        """We override this to get source and target nodes."""
        def not_none(node):
            return not node is None
        return filter(not_none, [self._getsourcenode(), self._gettargetnode()])

    def addnote(self, text, origin=None):
        """Add a note specifically in a "definition" tag"""
        assert isinstance(text, unicode)
        current_notes = self.getnotes(origin)
        self.removenotes()
        note = etree.SubElement(self.xmlelement, self.namespaced("definition"))
        note.text = "\n".join(filter(None, [current_notes, text.strip()]))

    def getnotes(self, origin=None):
        #TODO: consider only responding when origin has certain values
        notenode = self.xmlelement.find(self.namespaced("definition"))
        comment = ''
        if not notenode is None:
            comment = notenode.text
        return comment

    def removenotes(self):
        """Remove all the translator notes."""
        note = self.xmlelement.find(self.namespaced("comment"))
        if not note is None:
            self.xmlelement.remove(note)

    def getid(self):
        return self.source

    def merge(self, otherunit, overwrite=False, comments=True):
        super(QphUnit, self).merge(otherunit, overwrite, comments)


class QphFile(lisa.LISAfile):
    """Class representing a QPH file store."""
    UnitClass = QphUnit
    Name = "Qt Phrase Book File"
    Mimetypes  = ["application/x-qph"]
    Extensions = ["qph"]
    rootNode = "QPH"
    # We will switch out .body to fit with the context we are working on
    bodyNode = "context"
    XMLskeleton = '''<!DOCTYPE QPH>
<QPH>
</QPH>
'''
    namespace = ''

    def __init__(self, *args, **kwargs):
        self._contextname = None
        lisa.LISAfile.__init__(self, *args, **kwargs)

    def initbody(self):
        """Initialises self.body."""
        self.namespace = self.document.getroot().nsmap.get(None, None)
        if self._contextname:
            self.body = self.getcontextnode(self._contextname)
        else:
            self.body = self.document.getroot()

    def createcontext(self, contextname, comment=None):
        """Creates a context node with an optional comment"""
        context = etree.SubElement(self.document.getroot(), self.namespaced(self.bodyNode))
        if comment:
            comment_node = context.SubElement(context, "comment")
            comment_node.text = comment
        return context

    def getcontextname(self, contextnode):
        """Returns the name of the given context."""
        return filenode.find(self.namespaced("name")).text

    def getcontextnames(self):
        """Returns all contextnames in this TS file."""
        contextnodes = self.document.findall(self.namespaced("context"))
        contextnames = [self.getcontextname(contextnode) for contextnode in contextnodes]
        contextnames = filter(None, contextnames)
        if len(contextnames) == 1 and contextnames[0] == '':
            contextnames = []
        return contextnames

    def getcontextnode(self, contextname):
        """Finds the contextnode with the given name."""
        contextnodes = self.document.findall(self.namespaced("context"))
        for contextnode in contextnodes:
            if self.getcontextname(contextnode) == contextname:
                return contextnode
        return None

    def addunit(self, unit, new=True, contextname=None, createifmissing=False):
        """adds the given trans-unit to the last used body node if the contextname has changed it uses the slow method instead (will create the nodes required if asked). Returns success"""
        if self._contextname != contextname:
            if not self.switchcontext(contextname, createifmissing):
                return None
        super(QphFile, self).addunit(unit, new)
#        unit._context_node = self.getcontextnode(self._contextname)
#        lisa.setXMLspace(unit.xmlelement, "preserve")
        return unit

    def switchcontext(self, contextname, createifmissing=False):
        """Switch the current context to the one named contextname, optionally 
        creating it if it doesn't exist."""
        self._context_name = contextname
        contextnode = self.getcontextnode(contextname)
        if contextnode is None:
            if not createifmissing:
                return False
            contextnode = self.createcontextnode(contextname)
            self.document.getroot().append(contextnode)

        self.body = contextnode
        if self.body is None:
            return False
        return True
