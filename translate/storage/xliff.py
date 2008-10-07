#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2005-2007 Zuza Software Foundation
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

"""Module for handling XLIFF files for translation.

The official recommendation is to use the extention .xlf for XLIFF files.
"""

from translate.storage import base
from translate.storage import lisa
from lxml import etree

# TODO: handle translation types

class xliffunit(lisa.LISAunit):
    """A single term in the xliff file."""

    rootNode = "trans-unit"
    languageNode = "source"
    textNode = ""
    namespace = 'urn:oasis:names:tc:xliff:document:1.1'

    #TODO: id and all the trans-unit level stuff

    def createlanguageNode(self, lang, text, purpose):
        """Returns an xml Element setup with given parameters."""

        #TODO: for now we do source, but we have to test if it is target, perhaps 
        # with parameter. Alternatively, we can use lang, if supplied, since an xliff 
        #file has to conform to the bilingual nature promised by the header.
        assert purpose
        langset = etree.Element(self.namespaced(purpose))
        #TODO: check language
#        lisa.setXMLlang(langset, lang)

#        self.createPHnodes(langset, text)
        langset.text = text
        return langset
    
    def getlanguageNodes(self):
        """We override this to get source and target nodes."""
        sources = self.xmlelement.findall('.//%s' % self.namespaced(self.languageNode))
        targets = self.xmlelement.findall('.//%s' % self.namespaced('target'))
        sourcesl = len(sources)
        targetsl = len(targets)
        nodes = []
        for pair in zip(sources, targets):
            nodes.extend(list(pair))
        if sourcesl > targetsl:
            nodes.extend(sources[- (sourcesl - targetsl):])
        return nodes

    def addalttrans(self, txt, origin=None, lang=None):
        """Adds an alt-trans tag and alt-trans components to the unit.
        
        @type txt: String
        @param txt: Alternative translation of the source text.
        """

        #TODO: support adding a source tag ad match quality attribute.  At 
        # the source tag is needed to inject fuzzy matches from a TM.
        if isinstance(txt, str):
            txt = txt.decode("utf-8")
        alttrans = etree.SubElement(self.xmlelement, self.namespaced("alt-trans"))
        alttarget = etree.SubElement(alttrans, self.namespaced("target"))
        alttarget.text = txt
        if origin:
            alttrans.set("origin", origin)
        if lang:
            lisa.setXMLlang(alttrans, lang)

    def getalttrans(self, origin=None):
        """Returns <alt-trans> for the given origin as a list of units. No 
        origin means all alternatives."""
        translist = []
        for node in self.xmlelement.findall(".//%s" % self.namespaced("alt-trans")):
            if self.correctorigin(node, origin):
                # We build some mini units that keep the xmlelement. This 
                # makes it easier to delete it if it is passed back to us.
                newunit = base.TranslationUnit(self.source)

                # the source tag is optional
                sourcenode = node.find(".//%s" % self.namespaced("source"))
                if not sourcenode is None:
                    newunit.source = lisa.getText(sourcenode)

                # must have one or more targets
                targetnode = node.find(".//%s" % self.namespaced("target"))
                newunit.target = lisa.getText(targetnode)
                #TODO: support multiple targets better
                #TODO: support notes in alt-trans
                newunit.xmlelement = node

                translist.append(newunit)
        return translist

    def delalttrans(self, alternative):
        """Removes the supplied alternative from the list of alt-trans tags"""
        self.xmlelement.remove(alternative.xmlelement)

    def addnote(self, text, origin=None):
        """Add a note specifically in a "note" tag"""
        if isinstance(text, str):
            text = text.decode("utf-8")
        note = etree.SubElement(self.xmlelement, self.namespaced("note"))
        note.text = text.strip()
        if origin:
            note.set("from", origin)

    def getnotelist(self, origin=None):
        """Private method that returns the text from notes matching 'origin' or all notes."""
        notenodes = self.xmlelement.findall(".//%s" % self.namespaced("note"))
        # TODO: consider using xpath to construct initial_list directly
        # or to simply get the correct text from the outset (just remember to
        # check for duplication.
        initial_list = [lisa.getText(note) for note in notenodes if self.correctorigin(note, origin)]

        # Remove duplicate entries from list:
        dictset = {}
        notelist = [dictset.setdefault(note, note) for note in initial_list if note not in dictset]

        return notelist 

    def getnotes(self, origin=None):
        return '\n'.join(self.getnotelist(origin=origin))

    def removenotes(self):
        """Remove all the translator notes."""
        notes = self.xmlelement.findall(".//%s" % self.namespaced("note"))
        for note in notes:
            if self.correctorigin(note, origin="translator"):
                self.xmlelement.remove(note)

    def adderror(self, errorname, errortext):
        """Adds an error message to this unit."""
        #TODO: consider factoring out: some duplication between XLIFF and TMX
        text = errorname + ': ' + errortext
        self.addnote(text, origin="pofilter")

    def geterrors(self):
        """Get all error messages."""
        #TODO: consider factoring out: some duplication between XLIFF and TMX
        notelist = self.getnotelist(origin="pofilter")
        errordict = {}
        for note in notelist:
            errorname, errortext = note.split(': ')
            errordict[errorname] = errortext
        return errordict

    def isapproved(self):
        """States whether this unit is approved."""
        return self.xmlelement.get("approved") == "yes"

    def markapproved(self, value=True):
        """Mark this unit as approved."""
        if value:
            self.xmlelement.set("approved", "yes")
        elif self.isapproved():
            self.xmlelement.set("approved", "no")

    def isreview(self):
        """States whether this unit needs to be reviewed"""
        targetnode = self.getlanguageNode(lang=None, index=1)
        return not targetnode is None and \
                "needs-review" in targetnode.get("state", "")

    def markreviewneeded(self, needsreview=True, explanation=None):
        """Marks the unit to indicate whether it needs review. Adds an optional explanation as a note."""
        targetnode = self.getlanguageNode(lang=None, index=1)
        if not targetnode is None:
            if needsreview:
                targetnode.set("state", "needs-review-translation")
                if explanation:
                    self.addnote(explanation, origin="translator")
            else:
                del targetnode.attrib["state"]

    def isfuzzy(self):
#        targetnode = self.getlanguageNode(lang=None, index=1)
#        return not targetnode is None and \
#                (targetnode.get("state-qualifier") == "fuzzy-match" or \
#                targetnode.get("state") == "needs-review-translation")
        return not self.isapproved()
                
    def markfuzzy(self, value=True):
        if value:
            self.markapproved(False)
        else:
            self.markapproved(True)
        targetnode = self.getlanguageNode(lang=None, index=1)
        if not targetnode is None:
            if value:
                targetnode.set("state", "needs-review-translation")
            else:
                for attribute in ["state", "state-qualifier"]:
                    if attribute in targetnode.attrib:
                        del targetnode.attrib[attribute]

    def settarget(self, text, lang='xx', append=False):
        """Sets the target string to the given value."""
        super(xliffunit, self).settarget(text, lang, append)
        if text:
            self.marktranslated()

# This code is commented while this will almost always return false.
# This way pocount, etc. works well.
#    def istranslated(self):
#        targetnode = self.getlanguageNode(lang=None, index=1)
#        return not targetnode is None and \
#                (targetnode.get("state") == "translated")

    def istranslatable(self):
        value = self.xmlelement.get("translate")
        if value and value.lower() == 'no':
            return False
        return True

    def marktranslated(self):
        targetnode = self.getlanguageNode(lang=None, index=1)
        if targetnode is None:
            return
        if self.isfuzzy() and "state-qualifier" in targetnode.attrib:
            #TODO: consider
            del targetnode.attrib["state-qualifier"]
        targetnode.set("state", "translated")

    def setid(self, id):
        self.xmlelement.set("id", id)

    def getid(self):
        return self.xmlelement.get("id") or ""

    def addlocation(self, location):
        self.setid(location)

    def getlocations(self):
        return [self.getid()]

    def createcontextgroup(self, name, contexts=None, purpose=None):
        """Add the context group to the trans-unit with contexts a list with
        (type, text) tuples describing each context."""
        assert contexts
        group = etree.Element(self.namespaced("context-group"))
        # context-group tags must appear at the start within <group>
        # tags. Otherwise it must be appended to the end of a group
        # of tags.
        if self.xmlelement.tag == self.namespaced("group"):
            self.xmlelement.insert(0, group)
        else:
            self.xmlelement.append(group)
        group.set("name", name)
        if purpose:
            group.set("purpose", purpose)
        for type, text in contexts:
            if isinstance(text, str):
                text = text.decode("utf-8")
            context = etree.SubElement(group, self.namespaced("context"))
            context.text = text
            context.set("context-type", type)

    def getcontextgroups(self, name):
        """Returns the contexts in the context groups with the specified name"""
        groups = []
        grouptags = self.xmlelement.findall(".//%s" % self.namespaced("context-group"))
        for group in grouptags:
            if group.get("name") == name:
                contexts = group.findall(".//%s" % self.namespaced("context"))
                pairs = []
                for context in contexts:
                    pairs.append((context.get("context-type"), lisa.getText(context)))
                groups.append(pairs) #not extend
        return groups
        
    def getrestype(self):
        """returns the restype attribute in the trans-unit tag"""
        return self.xmlelement.get("restype")

    def merge(self, otherunit, overwrite=False, comments=True):
        #TODO: consider other attributes like "approved"
        super(xliffunit, self).merge(otherunit, overwrite, comments)
        if self.target:
            self.marktranslated()
        if otherunit.isfuzzy():
            self.markfuzzy()

    def correctorigin(self, node, origin):
        """Check against node tag's origin (e.g note or alt-trans)"""
        if origin == None:
            return True
        elif origin in node.get("from", ""):
            return True
        elif origin in node.get("origin", ""):
            return True
        else:
            return False

class xlifffile(lisa.LISAfile):
    """Class representing a XLIFF file store."""
    UnitClass = xliffunit
    Name = "XLIFF file"
    Mimetypes  = ["application/x-xliff", "application/x-xliff+xml"]
    Extensions = ["xlf", "xliff"]
    rootNode = "xliff"
    bodyNode = "body"
    XMLskeleton = '''<?xml version="1.0" ?>
<xliff version='1.1' xmlns='urn:oasis:names:tc:xliff:document:1.1'>
<file original='NoName' source-language='en' datatype='plaintext'>
<body>
</body>
</file>
</xliff>'''
    namespace = 'urn:oasis:names:tc:xliff:document:1.1'

    def __init__(self, *args, **kwargs):
        lisa.LISAfile.__init__(self, *args, **kwargs)
        self._filename = "NoName"
        self._messagenum = 0

        # Allow the inputfile to override defaults for source and target language.
        filenode = self.document.find('.//%s' % self.namespaced('file'))
        sourcelanguage = filenode.get('source-language')
        if sourcelanguage:
            self.setsourcelanguage(sourcelanguage)
        targetlanguage = filenode.get('target-language')
        if targetlanguage:
            self.settargetlanguage(targetlanguage)

    def addheader(self):
        """Initialise the file header."""
        filenode = self.document.find(self.namespaced("file"))
        filenode.set("source-language", self.sourcelanguage)
        if self.targetlanguage:
            filenode.set("target-language", self.targetlanguage)

    def createfilenode(self, filename, sourcelanguage=None, targetlanguage=None, datatype='plaintext'):
        """creates a filenode with the given filename. All parameters are needed
        for XLIFF compliance."""
        self.removedefaultfile()
        if sourcelanguage is None:
            sourcelanguage = self.sourcelanguage
        if targetlanguage is None:
            targetlanguage = self.targetlanguage
        filenode = etree.Element(self.namespaced("file"))
        filenode.set("original", filename)
        filenode.set("source-language", sourcelanguage)
        if targetlanguage:
            filenode.set("target-language", targetlanguage)
        filenode.set("datatype", datatype)
        bodyNode = etree.SubElement(filenode, self.namespaced(self.bodyNode))
        return filenode

    def getfilename(self, filenode):
        """returns the name of the given file"""
        return filenode.get("original")

    def getfilenames(self):
        """returns all filenames in this XLIFF file"""
        filenodes = self.document.findall(self.namespaced("file"))
        filenames = [self.getfilename(filenode) for filenode in filenodes]
        filenames = filter(None, filenames)
        if len(filenames) == 1 and filenames[0] == '':
            filenames = []
        return filenames

    def getfilenode(self, filename):
        """finds the filenode with the given name"""
        filenodes = self.document.findall(self.namespaced("file"))
        for filenode in filenodes:
            if self.getfilename(filenode) == filename:
                return filenode
        return None

    def getdatatype(self, filename=None):
        """Returns the datatype of the stored file. If no filename is given,
        the datatype of the first file is given."""
        if filename:
            node = self.getfilenode(filename)
            if not node is None:
                return node.get("datatype")
        else:
            filenames = self.getfilenames()
            if len(filenames) > 0 and filenames[0] != "NoName":
                return self.getdatatype(filenames[0])
        return ""

    def getdate(self, filename=None):
        """Returns the date attribute for the file. If no filename is given,
        the date of the first file is given. If the date attribute is not
        specified, None is returned."""
        if filename:
            node = self.getfilenode(filename)
            if not node is None:
                return node.get("date")
        else:
            filenames = self.getfilenames()
            if len(filenames) > 0 and filenames[0] != "NoName":
                return self.getdate(filenames[0])
        return None

    def removedefaultfile(self):
        """We want to remove the default file-tag as soon as possible if we 
        know if still present and empty."""
        filenodes = self.document.findall(self.namespaced("file"))
        if len(filenodes) > 1:
            for filenode in filenodes:
                if filenode.get("original") == "NoName" and \
                        not filenode.findall(".//%s" % self.namespaced(self.UnitClass.rootNode)):
                    self.document.getroot().remove(filenode)
                break

    def getheadernode(self, filenode, createifmissing=False):
        """finds the header node for the given filenode"""
        # TODO: Deprecated?
        headernode = list(filenode.find(self.namespaced("header")))
        if not headernode is None:
            return headernode
        if not createifmissing:
            return None
        headernode = etree.SubElement(filenode, self.namespaced("header"))
        return headernode

    def getbodynode(self, filenode, createifmissing=False):
        """finds the body node for the given filenode"""
        bodynode = filenode.find(self.namespaced("body"))
        if not bodynode is None:
            return bodynode
        if not createifmissing:
            return None
        bodynode = etree.SubElement(filenode, self.namespaced("body"))
        return bodynode

    def addsourceunit(self, source, filename="NoName", createifmissing=False):
        """adds the given trans-unit to the last used body node if the filename has changed it uses the slow method instead (will create the nodes required if asked). Returns success"""
        if self._filename != filename:
            if not self.switchfile(filename, createifmissing):
                return None
        unit = super(xlifffile, self).addsourceunit(source)
        self._messagenum += 1
        unit.setid("%d" % self._messagenum)
        lisa.setXMLspace(unit.xmlelement, "preserve")
        return unit

    def switchfile(self, filename, createifmissing=False):
        """adds the given trans-unit (will create the nodes required if asked). Returns success"""
        self._filename = filename
        filenode = self.getfilenode(filename)
        if filenode is None:
            if not createifmissing:
                return False
            filenode = self.createfilenode(filename)
            self.document.getroot().append(filenode)

        self.body = self.getbodynode(filenode, createifmissing=createifmissing)
        if self.body is None:
            return False
        self._messagenum = len(self.body.findall(".//%s" % self.namespaced("trans-unit")))
        #TODO: was 0 based before - consider
    #    messagenum = len(self.units)
        #TODO: we want to number them consecutively inside a body/file tag
        #instead of globally in the whole XLIFF file, but using len(self.units)
        #will be much faster
        return True
    
    def creategroup(self, filename="NoName", createifmissing=False, restype=None):
        """adds a group tag into the specified file"""
        if self._filename != filename:
            if not self.switchfile(filename, createifmissing):
                return None
        group = etree.SubElement(self.body, self.namespaced("group"))
        if restype:
            group.set("restype", restype)
        return group
        
    def __str__(self):
        self.removedefaultfile()
        return super(xlifffile, self).__str__()

    def parsestring(cls, storestring):
        """Parses the string to return the correct file object"""
        xliff = super(xlifffile, cls).parsestring(storestring)
        if xliff.units:
            header = xliff.units[0]
            if ("gettext-domain-header" in (header.getrestype() or "") \
                    or xliff.getdatatype() == "po") \
                    and cls.__name__.lower() != "poxlifffile":
                import poxliff
                xliff = poxliff.PoXliffFile.parsestring(storestring)
        return xliff
    parsestring = classmethod(parsestring)

