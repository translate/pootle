#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2002-2006 Zuza Software Foundation
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

"""classes that hold units of .dtd files (dtdunit) or entire files (dtdfile)
these are specific .dtd files for localisation used by mozilla"""

from translate.storage import base
from translate.misc import quote

import re
import sys
import warnings

def quotefordtd(source):
    if '"' in source:
        if "'" in source:
            return "'" + source.replace("'", '&apos;') + "'"
        else:
            return quote.singlequotestr(source)
    else:
        return quote.quotestr(source)

def unquotefromdtd(source):
    """unquotes a quoted dtd definition"""
    # extract the string, get rid of quoting
    if len(source) == 0: source = '""'
    quotechar = source[0]
    extracted,quotefinished = quote.extractwithoutquotes(source,quotechar,quotechar,allowreentry=False)
    if quotechar == "'" and "&apos;" in extracted:
        extracted = extracted.replace("&apos;", "'")
    # the quote characters should be the first and last characters in the string
    # of course there could also be quote characters within the string; not handled here
    return extracted

class dtdunit(base.TranslationUnit):
    """this class represents an entity definition from a dtd file (and possibly associated comments)"""
    def __init__(self, source=""):
        """construct the dtdunit, prepare it for parsing"""
        super(dtdunit, self).__init__(source)
        self.comments = []
        self.unparsedlines = []
        self.incomment = 0
        self.inentity = 0
        self.entity = "FakeEntityOnlyForInitialisationAndTesting" 
        self.source = source

    # Note that source and target are equivalent for monolingual units
    def setsource(self, source):
        """Sets the definition to the quoted value of source"""
        self.definition = quotefordtd(source)

    def getsource(self):
        """gets the unquoted source string"""
        return unquotefromdtd(self.definition)
    source = property(getsource, setsource)

    def settarget(self, target):
        """Sets the definition to the quoted value of target"""
        if target is None:
            target = ""
        self.definition = quotefordtd(target)

    def gettarget(self):
        """gets the unquoted target string"""
        return unquotefromdtd(self.definition)
    target = property(gettarget, settarget)

    def isnull(self):
        """returns whether this dtdunit doesn't actually have an entity definition"""
        # for dtds, we currently return a blank string if there is no .entity (==location in other files)
        # TODO: this needs to work better with base class expectations
        return self.entity is None

    def parse(self, dtdsrc):
        """read the first dtd element from the source code into this object, return linesprocessed"""
        self.comments = []
        # make all the lists the same
        self.locfilenotes = self.comments
        self.locgroupstarts = self.comments
        self.locgroupends = self.comments
        self.locnotes = self.comments
        # self.locfilenotes = []
        # self.locgroupstarts = []
        # self.locgroupends = []
        # self.locnotes = []
        # self.comments = []
        self.entity = None
        self.definition = ''
        if not dtdsrc:
            return 0
        lines = dtdsrc.split("\n")
        linesprocessed = 0
        comment = ""
        for line in lines:
            line += "\n"
            linesprocessed += 1
            # print "line(%d,%d): " % (self.incomment,self.inentity),line[:-1]
            if not self.incomment:
                if (line.find('<!--') != -1):
                    self.incomment = 1
                    self.continuecomment = 0
                    # now work out the type of comment, and save it (remember we're not in the comment yet)
                    (comment, dummy) = quote.extract(line,"<!--","-->",None,0)
                    if comment.find('LOCALIZATION NOTE') != -1:
                        l = quote.findend(comment,'LOCALIZATION NOTE')
                        while (comment[l] == ' '): l += 1
                        if comment.find('FILE',l) == l:
                            self.commenttype = "locfile"
                        elif comment.find('BEGIN',l) == l:
                            self.commenttype = "locgroupstart"
                        elif comment.find('END',l) == l:
                            self.commenttype = "locgroupend"
                        else:
                            self.commenttype = "locnote"
                    else:
                        # plain comment
                        self.commenttype = "comment"

            if self.incomment:
                # some kind of comment
                (comment, self.incomment) = quote.extract(line,"<!--","-->",None,self.continuecomment)
                # print "comment(%d,%d): " % (self.incomment,self.continuecomment),comment
                self.continuecomment = self.incomment
                # strip the comment out of what will be parsed
                line = line.replace(comment, "", 1)
                # add a end of line of this is the end of the comment
                if not self.incomment:
                    if line.isspace():
                        comment += line
                        line = ''
                    else:
                        comment += '\n'
                # check if there's actually an entity definition that's commented out
                # TODO: parse these, store as obsolete messages
                # if comment.find('<!ENTITY') != -1:
                #     # remove the entity from the comment
                #     comment, dummy = quote.extractwithoutquotes(comment, ">", "<!ENTITY", None, 1)
                # depending on the type of comment (worked out at the start), put it in the right place
                # make it record the comment and type as a tuple
                commentpair = (self.commenttype,comment)
                if self.commenttype == "locfile":
                    self.locfilenotes.append(commentpair)
                elif self.commenttype == "locgroupstart":
                    self.locgroupstarts.append(commentpair)
                elif self.commenttype == "locgroupend":
                    self.locgroupends.append(commentpair)
                elif self.commenttype == "locnote":
                    self.locnotes.append(commentpair)
                elif self.commenttype == "comment":
                    self.comments.append(commentpair)

            if not self.inentity and not self.incomment:
                entitypos = line.find('<!ENTITY')
                if entitypos != -1:
                    self.inentity = 1
                    beforeentity = line[:entitypos].strip()
                    if beforeentity.startswith("#"):
                        self.hashprefix = beforeentity
                    self.entitypart = "start"
                else:
                    self.unparsedlines.append(line)

            if self.inentity:
                if self.entitypart == "start":
                    # the entity definition
                    e = quote.findend(line,'<!ENTITY')
                    line = line[e:]
                    self.entitypart = "name"
                    self.entitytype = "internal"
                if self.entitypart == "name":
                    e = 0
                    while (e < len(line) and line[e].isspace()): e += 1
                    self.entity = ''
                    if (e < len(line) and line[e] == '%'):
                        self.entitytype = "external"
                        self.entityparameter = ""
                        e += 1
                        while (e < len(line) and line[e].isspace()): e += 1
                    while (e < len(line) and not line[e].isspace()):
                        self.entity += line[e]
                        e += 1
                    while (e < len(line) and line[e].isspace()): e += 1
                    if self.entity:
                        if self.entitytype == "external":
                            self.entitypart = "parameter"
                        else:
                            self.entitypart = "definition"
                        # remember the start position and the quote character
                        if e == len(line):
                            self.entityhelp = None
                            continue
                        elif self.entitypart == "definition":
                            self.entityhelp = (e,line[e])
                            self.instring = 0
                if self.entitypart == "parameter":
                    paramstart = e
                    while (e < len(line) and line[e].isalnum()): e += 1
                    self.entityparameter += line[paramstart:e]
                    while (e < len(line) and line[e].isspace()): e += 1
                    line = line[e:]
                    e = 0
                    if not line:
                        continue
                    if line[0] in ('"', "'"):
                        self.entitypart = "definition"
                        self.entityhelp = (e,line[e])
                        self.instring = 0
                if self.entitypart == "definition":
                    if self.entityhelp is None:
                        e = 0
                        while (e < len(line) and line[e].isspace()): e += 1
                        if e == len(line):
                            continue
                        self.entityhelp = (e,line[e])
                        self.instring = 0
                    # actually the lines below should remember instring, rather than using it as dummy
                    e = self.entityhelp[0]
                    if (self.entityhelp[1] == "'"):
                        (defpart,self.instring) = quote.extract(line[e:],"'","'",startinstring=self.instring,allowreentry=False)
                    elif (self.entityhelp[1] == '"'):
                        (defpart,self.instring) = quote.extract(line[e:],'"','"',startinstring=self.instring,allowreentry=False)
                    else:
                        raise ValueError("Unexpected quote character... %r" % (self.entityhelp[1]))
                    # for any following lines, start at the beginning of the line. remember the quote character
                    self.entityhelp = (0,self.entityhelp[1])
                    self.definition += defpart
                    if not self.instring:
                        self.inentity = 0
                        break

        # uncomment this line to debug processing
        if 0:
            for attr in dir(self):
                r = repr(getattr(self,attr))
                if len(r) > 60: r = r[:57]+"..."
                self.comments.append(("comment","self.%s = %s" % (attr,r) ))
        return linesprocessed

    def __str__(self):
        """convert to a string. double check that unicode is handled somehow here"""
        source = self.getoutput()
        if isinstance(source, unicode):
            return source.encode(getattr(self, "encoding", "UTF-8"))
        return source

    def getoutput(self):
        """convert the dtd entity back to string form"""
        lines = []
        lines.extend([comment for commenttype,comment in self.comments])
        lines.extend(self.unparsedlines)
        if self.isnull():
            result = "".join(lines)
            return result.rstrip() + "\n"
        # for f in self.locfilenotes: yield f
        # for ge in self.locgroupends: yield ge
        # for gs in self.locgroupstarts: yield gs
        # for n in self.locnotes: yield n
        if len(self.entity) > 0:
            if getattr(self, 'entitytype', None) == 'external':
                entityline = '<!ENTITY % '+self.entity+' '+self.entityparameter+' '+self.definition+'>'
            else:
                entityline = '<!ENTITY '+self.entity+' '+self.definition+'>'
            if getattr(self, 'hashprefix', None):
                entityline = self.hashprefix + " " + entityline
            if isinstance(entityline, unicode):
                entityline = entityline.encode('UTF-8')
            lines.append(entityline+'\n')
        return "".join(lines)

class dtdfile(base.TranslationStore):
    """this class represents a .dtd file, made up of dtdunits"""
    UnitClass = dtdunit
    def __init__(self, inputfile=None):
        """construct a dtdfile, optionally reading in from inputfile"""
        base.TranslationStore.__init__(self, unitclass = self.UnitClass)
        self.units = []
        self.filename = getattr(inputfile, 'name', '')
        if inputfile is not None:
            dtdsrc = inputfile.read()
            self.parse(dtdsrc)
            self.makeindex()

    def parse(self, dtdsrc):
        """read the source code of a dtd file in and include them as dtdunits in self.units (any existing units are lost)"""
        self.units = []
        start = 0
        end = 0
        lines = dtdsrc.split("\n")
        while end < len(lines):
            if (start == end): end += 1
            foundentity = 0
            while end < len(lines):
                if end >= len(lines):
                    break
                if lines[end].find('<!ENTITY') > -1:
                    foundentity = 1
                if foundentity and re.match("[\"']\s*>", lines[end]):
                    end += 1
                    break
                end += 1
            # print "processing from %d to %d" % (start,end)

            linesprocessed = 1 # to initialise loop
            while linesprocessed >= 1:
                newdtd = dtdunit()
                try:
                    linesprocessed = newdtd.parse("\n".join(lines[start:end]))
                    if linesprocessed >= 1 and (not newdtd.isnull() or newdtd.unparsedlines):
                        self.units.append(newdtd)
                except Exception, e:
                    warnings.warn("%s\nError occured between lines %d and %d:\n%s" % (e, start+1, end, "\n".join(lines[start:end])))
                start += linesprocessed

    def __str__(self):
        """convert to a string. double check that unicode is handled somehow here"""
        source = self.getoutput()
        if isinstance(source, unicode):
            return source.encode(getattr(self, "encoding", "UTF-8"))
        return source

    def getoutput(self):
        """convert the units back to source"""
        sources = [str(dtd) for dtd in self.units]
        return "".join(sources)

    def makeindex(self):
        """makes self.index dictionary keyed on entities"""
        self.index = {}
        for dtd in self.units:
            if not dtd.isnull():
                self.index[dtd.entity] = dtd

    def rewrap(self):
        for dtd in self.units:
            lines = dtd.definition.split("\n")
            if len(lines) > 1:
                definition = lines[0]
                for line in lines[1:]:
                    if definition[-1:].isspace() or line[:1].isspace():
                        definition += line
                    else:
                        definition += " " + line
                dtd.definition = definition

if __name__ == "__main__":
    import sys
    d = dtdfile(sys.stdin)
    d.rewrap()
    sys.stdout.write(str(d))

