#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2006-2007 Zuza Software Foundation
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

"""Parent class for LISA standards (TMX, TBX, XLIFF)"""

import re

from translate.storage import base
from translate.lang import data
try:
    from lxml import etree
except ImportError, e:
    raise ImportError("lxml is not installed. It might be possible to continue without support for XML formats.")

def getText(node):
    """joins together the text from all the text nodes in the nodelist and their children"""
    # node.xpath is very slow, so we only use it if there are children
    # TODO: consider rewriting by iterating over children
    if node:    # The etree way of testing for children
        return node.xpath("string()") # specific to lxml.etree
    else:
        return data.forceunicode(node.text) or u""
        # if node.text is none, we want to return "" since the tag is there

def _findAllMatches(text, re_obj):
    """generate match objects for all @re_obj matches in @text."""
    start = 0
    max = len(text)
    while start < max:
        m = re_obj.search(text, start)
        if not m: break
        yield m
        start = m.end()

placeholders = ['(%[diouxXeEfFgGcrs])', r'(\\+.?)', '(%[0-9]$lx)', '(%[0-9]\$[a-z])', '(<.+?>)']
re_placeholders = [re.compile(ph) for ph in placeholders]
def _getPhMatches(text):
    'return list of regexp matchobjects for with all place holders in the @text'
    matches = []
    for re_ph in re_placeholders:
        matches.extend(list(_findAllMatches(text, re_ph)))

    # sort them so they come sequentially
    matches.sort(lambda a,b: cmp(a.start(),b.start()))
    return matches

XML_NS = 'http://www.w3.org/XML/1998/namespace'

def setXMLlang(node, lang):
    """Sets the xml:lang attribute on node"""
    node.set("{%s}lang" % XML_NS, lang)

def setXMLspace(node, value):
    """Sets the xml:space attribute on node"""
    node.set("{%s}space" % XML_NS, value)

def namespaced(namespace, name):
    """Returns name in Clark notation within the given namespace.

    For example namespaced("source") in an XLIFF document might return
        {urn:oasis:names:tc:xliff:document:1.1}source
    This is needed throughout lxml.
    """
    if namespace:
        return "{%s}%s" % (namespace, name)
    else:
        return name

class LISAunit(base.TranslationUnit):
    """A single unit in the file. 
Provisional work is done to make several languages possible."""

    #The name of the root element of this unit type:(termEntry, tu, trans-unit)
    rootNode = ""
    #The name of the per language element of this unit type:(termEntry, tu, trans-unit)
    languageNode = ""
    #The name of the innermost element of this unit type:(term, seg)
    textNode = ""

    namespace = None

    def __init__(self, source, empty=False):
        """Constructs a unit containing the given source string"""
        if empty:
            return
        self.xmlelement = etree.Element(self.rootNode)
        #add descrip, note, etc.

        super(LISAunit, self).__init__(source)

    def __eq__(self, other):
        """Compares two units"""
        languageNodes = self.getlanguageNodes()
        otherlanguageNodes = other.getlanguageNodes()
        if len(languageNodes) != len(otherlanguageNodes):
            return False
        for i in range(len(languageNodes)):
            mytext = self.getNodeText(languageNodes[i])
            othertext = other.getNodeText(otherlanguageNodes[i])
            if mytext != othertext:
                #TODO:^ maybe we want to take children and notes into account
                return False
        return True

    def namespaced(self, name):
        """Returns name in Clark notation.

        For example namespaced("source") in an XLIFF document might return
            {urn:oasis:names:tc:xliff:document:1.1}source
        This is needed throughout lxml.
        """
        return namespaced(self.namespace, name)

    def setsource(self, source, sourcelang='en'):
        source = data.forceunicode(source)
        languageNodes = self.getlanguageNodes()
        sourcelanguageNode = self.createlanguageNode(sourcelang, source, "source")
        if len(languageNodes) > 0:
            self.xmlelement[0] = sourcelanguageNode
        else:
            self.xmlelement.append(sourcelanguageNode)

    def getsource(self):
        return self.getNodeText(self.getlanguageNode(lang=None, index=0))
    source = property(getsource, setsource)

    def settarget(self, text, lang='xx', append=False):
        #XXX: we really need the language - can't really be optional
        """Sets the "target" string (second language), or alternatively appends to the list"""
        text = data.forceunicode(text)
        #Firstly deal with reinitialising to None or setting to identical string
        if self.gettarget() == text:
            return
        languageNodes = self.getlanguageNodes()
        assert len(languageNodes) > 0
        if not text is None:
            languageNode = self.createlanguageNode(lang, text, "target")
            if append or len(languageNodes) == 1:
                self.xmlelement.append(languageNode)
            else:
                self.xmlelement.insert(1, languageNode)
        if not append and len(languageNodes) > 1:
            self.xmlelement.remove(languageNodes[1])

    def gettarget(self, lang=None):
        """retrieves the "target" text (second entry), or the entry in the 
        specified language, if it exists"""
        if lang:
            node = self.getlanguageNode(lang=lang)
        else:
            node = self.getlanguageNode(lang=None, index=1)
        return self.getNodeText(node)
    target = property(gettarget, settarget)

    def createlanguageNode(self, lang, text, purpose=None):
        """Returns a xml Element setup with given parameters to represent a 
        single language entry. Has to be overridden."""
        return None

    def createPHnodes(self, parent, text):
        """Create the text node in parent containing all the ph tags"""
        matches = _getPhMatches(text)
        if not matches:
            parent.text = text
            return

        # Now we know there will definitely be some ph tags
        start = matches[0].start()
        pretext = text[:start]
        if pretext:
            parent.text = pretext
        lasttag = parent
        for i, m in enumerate(matches):
            #pretext
            pretext = text[start:m.start()]
            # this will never happen with the first ph tag
            if pretext:
                lasttag.tail = pretext
            #ph node
            phnode = etree.SubElement(parent, "ph")
            phnode.set("id", str(i+1))
            phnode.text = m.group()
            lasttag = phnode
            start = m.end()
        #post text
        if text[start:]:
            lasttag.tail = text[start:]

    def getlanguageNodes(self):
        """Returns a list of all nodes that contain per language information."""
        return self.xmlelement.findall(self.namespaced(self.languageNode))

    def getlanguageNode(self, lang=None, index=None):
        """Retrieves a languageNode either by language or by index"""
        if lang is None and index is None:
            raise KeyError("No criterea for languageNode given")
        languageNodes = self.getlanguageNodes()
        if lang:
            for set in languageNodes:
                if set.get("{%s}lang" % XML_NS) == lang:
                    return set
        else:#have to use index
            if index >= len(languageNodes):
                return None
            else:
                return languageNodes[index]
        return None

    def getNodeText(self, languageNode):
        """Retrieves the term from the given languageNode"""
        if languageNode is None:
            return None
        if self.textNode:
            terms = languageNode.findall('.//%s' % self.namespaced(self.textNode))
            if len(terms) == 0:
                return None
            return getText(terms[0])
        else:
            return getText(languageNode)

    def __str__(self):
        return etree.tostring(self.xmlelement, pretty_print=True, encoding='utf-8')

    def createfromxmlElement(cls, element):
        term = cls(None, empty=True)
        term.xmlelement = element
        return term
    createfromxmlElement = classmethod(createfromxmlElement)

class LISAfile(base.TranslationStore):
    """A class representing a file store for one of the LISA file formats."""
    UnitClass = LISAunit
    #The root node of the XML document:
    rootNode = ""
    #The root node of the content section:
    bodyNode = ""
    #The XML skeleton to use for empty construction:
    XMLskeleton = ""

    namespace = None

    def __init__(self, inputfile=None, sourcelanguage='en', targetlanguage=None, unitclass=None):
        super(LISAfile, self).__init__(unitclass=unitclass)
        self.setsourcelanguage(sourcelanguage)
        self.settargetlanguage(targetlanguage)
        if inputfile is not None:
            self.parse(inputfile)
            assert self.document.getroot().tag == self.namespaced(self.rootNode)
        else:
            # We strip out newlines to ensure that spaces in the skeleton doesn't
            # interfere with the the pretty printing of lxml
            self.parse(self.XMLskeleton.replace("\n", ""))
            self.addheader()

    def addheader(self):
        """Method to be overridden to initialise headers, etc."""
        pass

    def namespaced(self, name):
        """Returns name in Clark notation.

        For example namespaced("source") in an XLIFF document might return
            {urn:oasis:names:tc:xliff:document:1.1}source
        This is needed throughout lxml.
        """
        return namespaced(self.namespace, name)

    def initbody(self):
        """Initialises self.body so it never needs to be retrieved from the XML again."""
        self.namespace = self.document.getroot().nsmap.get(None, None)
        self.body = self.document.find('//%s' % self.namespaced(self.bodyNode))

    def setsourcelanguage(self, sourcelanguage):
        """Sets the source language for this store"""
        self.sourcelanguage = sourcelanguage

    def settargetlanguage(self, targetlanguage):
        """Sets the target language for this store"""
        self.targetlanguage = targetlanguage

    def addsourceunit(self, source):
        #TODO: miskien moet hierdie eerder addsourcestring of iets genoem word?
        """Adds and returns a new unit with the given string as first entry."""
        newunit = self.UnitClass(source)
        self.addunit(newunit)
        return newunit

    def addunit(self, unit):
        unit.namespace = self.namespace
        self.body.append(unit.xmlelement)
        self.units.append(unit)

    def __str__(self):
        """Converts to a string containing the file's XML"""
        return etree.tostring(self.document, pretty_print=True, xml_declaration=True, encoding='utf-8')

    def parse(self, xml):
        """Populates this object from the given xml string"""
        if not hasattr(self, 'filename'):
            self.filename = getattr(xml, 'name', '')
        if hasattr(xml, "read"):
            xml.seek(0)
            posrc = xml.read()
            xml = posrc
        self.document = etree.fromstring(xml).getroottree()
        self.encoding = self.document.docinfo.encoding
        self.initbody()
        assert self.document.getroot().tag == self.namespaced(self.rootNode)
        termEntries = self.body.findall('.//%s' % self.namespaced(self.UnitClass.rootNode))
        if termEntries is None:
            return
        for entry in termEntries:
            term = self.UnitClass.createfromxmlElement(entry)
            term.namespace = self.namespace
            self.units.append(term)

