#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2006-2008 Zuza Software Foundation
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

"""Base classes for storage interfaces.

@organization: Zuza Software Foundation
@copyright: 2006-2007 Zuza Software Foundation
@license: U{GPL <http://www.fsf.org/licensing/licenses/gpl.html>}
"""

try:
    import cPickle as pickle
except:
    import pickle
from exceptions import NotImplementedError

def force_override(method, baseclass):
    """Forces derived classes to override method."""

    if type(method.im_self) == type(baseclass):
        # then this is a classmethod and im_self is the actual class
        actualclass = method.im_self
    else:
        actualclass = method.im_class
    if actualclass != baseclass:
        raise NotImplementedError("%s does not reimplement %s as required by %s" % (actualclass.__name__, method.__name__, baseclass.__name__))

class TranslationUnit(object):
    """Base class for translation units.
    
    Our concept of a I{translation unit} is influenced heavily by XLIFF:
    U{http://www.oasis-open.org/committees/xliff/documents/xliff-specification.htm}

    As such most of the method- and variable names borrows from XLIFF terminology.

    A translation unit consists of the following:
      - A I{source} string. This is the original translatable text.
      - A I{target} string. This is the translation of the I{source}.
      - Zero or more I{notes} on the unit. Notes would typically be some
        comments from a translator on the unit, or some comments originating from
        the source code.
      - Zero or more I{locations}. Locations indicate where in the original
        source code this unit came from.
      - Zero or more I{errors}. Some tools (eg. L{pofilter <filters.pofilter>}) can run checks on
        translations and produce error messages.

    @group Source: *source*
    @group Target: *target*
    @group Notes: *note*
    @group Locations: *location*
    @group Errors: *error*
    """

    def __init__(self, source):
        """Constructs a TranslationUnit containing the given source string."""

        self.source = source
        self.target = None
        self.notes = ""
        super(TranslationUnit, self).__init__()

    def __eq__(self, other):
        """Compares two TranslationUnits.
        
        @type other: L{TranslationUnit}
        @param other: Another L{TranslationUnit}
        @rtype: Boolean
        @return: Returns True if the supplied TranslationUnit equals this unit.
        
        """

        return self.source == other.source and self.target == other.target

    def settarget(self, target):
        """Sets the target string to the given value."""

        self.target = target

    def gettargetlen(self):
        """Returns the length of the target string.
        
        @note: Plural forms might be combined.
        @rtype: Integer
        
        """

        length = len(self.target or "")
        strings = getattr(self.target, "strings", [])
        if strings:
            length += sum([len(pluralform) for pluralform in strings[1:]])
        return length

    def getid(self):
        """A unique identifier for this unit.

        @rtype: string
        @return: an identifier for this unit that is unique in the store

        Derived classes should override this in a way that guarantees a unique
        identifier for each unit in the store.
        """
        return self.source

    def getlocations(self):
        """A list of source code locations.
        
        @note: Shouldn't be implemented if the format doesn't support it.
        @rtype: List
        
        """

        return []
    
    def addlocation(self, location):
        """Add one location to the list of locations.
        
        @note: Shouldn't be implemented if the format doesn't support it.
        
        """
        pass

    def addlocations(self, location):
        """Add a location or a list of locations.
        
        @note: Most classes shouldn't need to implement this,
               but should rather implement L{addlocation()}.
        @warning: This method might be removed in future.
        
        """

        if isinstance(location, list):
            for item in location:
                self.addlocation(item)
        else:
            self.addlocation(location)

    def getcontext(self):
        """Get the message context."""
        return ""
    
    def getnotes(self, origin=None):
        """Returns all notes about this unit.
        
        It will probably be freeform text or something reasonable that can be
        synthesised by the format.
        It should not include location comments (see L{getlocations()}).
        
        """
        return getattr(self, "notes", "")

    def addnote(self, text, origin=None):
        """Adds a note (comment). 

        @type text: string
        @param text: Usually just a sentence or two.
        @type origin: string
        @param origin: Specifies who/where the comment comes from.
                       Origin can be one of the following text strings:
                         - 'translator'
                         - 'developer', 'programmer', 'source code' (synonyms)

        """
        if getattr(self, "notes", None):
            self.notes += '\n'+text
        else:
            self.notes = text

    def removenotes(self):
        """Remove all the translator's notes."""

        self.notes = u''

    def adderror(self, errorname, errortext):
        """Adds an error message to this unit.
        
          @type errorname: string
          @param errorname: A single word to id the error.
          @type errortext: string
          @param errortext: The text describing the error.
        
        """

        pass

    def geterrors(self):
        """Get all error messages.
        
        @rtype: Dictionary
        
        """

        return {}

    def markreviewneeded(self, needsreview=True, explanation=None):
        """Marks the unit to indicate whether it needs review.
        
        @keyword needsreview: Defaults to True.
        @keyword explanation: Adds an optional explanation as a note.
        
        """

        pass

    def istranslated(self):
        """Indicates whether this unit is translated.
        
        This should be used rather than deducing it from .target,
        to ensure that other classes can implement more functionality
        (as XLIFF does).
        
        """

        return bool(self.target) and not self.isfuzzy()

    def istranslatable(self):
        """Indicates whether this unit can be translated.

        This should be used to distinguish real units for translation from
        header, obsolete, binary or other blank units.
        """
        return True

    def isfuzzy(self):
        """Indicates whether this unit is fuzzy."""

        return False

    def markfuzzy(self, value=True):
        """Marks the unit as fuzzy or not."""
        pass

    def isheader(self):
        """Indicates whether this unit is a header."""

        return False

    def isreview(self):
        """Indicates whether this unit needs review."""
        return False


    def isblank(self):
        """Used to see if this unit has no source or target string.
        
        @note: This is probably used more to find translatable units,
        and we might want to move in that direction rather and get rid of this.
        
        """

        return not (self.source or self.target)

    def hasplural(self):
        """Tells whether or not this specific unit has plural strings."""

        #TODO: Reconsider
        return False

    def merge(self, otherunit, overwrite=False, comments=True):
        """Do basic format agnostic merging."""

        if self.target == "" or overwrite:
            self.target = otherunit.target

    def unit_iter(self):
        """Iterator that only returns this unit."""
        yield self

    def getunits(self):
        """This unit in a list."""
        return [self]

    def buildfromunit(cls, unit):
        """Build a native unit from a foreign unit, preserving as much  
        information as possible."""

        if type(unit) == cls and hasattr(unit, "copy") and callable(unit.copy):
            return unit.copy()
        newunit = cls(unit.source)
        newunit.target = unit.target
        newunit.markfuzzy(unit.isfuzzy())
        locations = unit.getlocations()
        if locations: 
            newunit.addlocations(locations)
        notes = unit.getnotes()
        if notes: 
            newunit.addnote(notes)
        return newunit
    buildfromunit = classmethod(buildfromunit)

class TranslationStore(object):
    """Base class for stores for multiple translation units of type UnitClass."""

    UnitClass = TranslationUnit

    def __init__(self, unitclass=None):
        """Constructs a blank TranslationStore."""

        self.units = []
        self.filepath = None
        self.translator = ""
        self.date = ""
        if unitclass:
            self.UnitClass = unitclass
        super(TranslationStore, self).__init__()

    def unit_iter(self):
        """Iterator over all the units in this store."""
        for unit in self.units:
            yield unit

    def getunits(self):
        """Return a list of all units in this store."""
        return [unit for unit in self.unit_iter()]

    def addunit(self, unit):
        """Appends the given unit to the object's list of units.
        
        This method should always be used rather than trying to modify the
        list manually.

        @type unit: L{TranslationUnit}
        @param unit: The unit that will be added.
        
        """

        self.units.append(unit)

    def addsourceunit(self, source):
        """Adds and returns a new unit with the given source string.
        
        @rtype: L{TranslationUnit}

        """

        unit = self.UnitClass(source)
        self.addunit(unit)
        return unit

    def findunit(self, source):
        """Finds the unit with the given source string.
        
        @rtype: L{TranslationUnit} or None

        """

        if len(getattr(self, "sourceindex", [])):
            if source in self.sourceindex:
                return self.sourceindex[source]
        else:
            for unit in self.units:
                if unit.source == source:
                    return unit
        return None

    def translate(self, source):
        """Returns the translated string for a given source string.
        
        @rtype: String or None

        """

        unit = self.findunit(source)
        if unit and unit.target:
            return unit.target
        else:
            return None

    def makeindex(self):
        """Indexes the items in this store. At least .sourceindex should be usefull."""

        self.locationindex = {}
        self.sourceindex = {}
        for unit in self.units:
            # Do we need to test if unit.source exists?
            self.sourceindex[unit.source] = unit
            if unit.hasplural():
                for nounform in unit.source.strings[1:]:
                    self.sourceindex[nounform] = unit
            for location in unit.getlocations():
                if location in self.locationindex:
                    # if sources aren't unique, don't use them
                    self.locationindex[location] = None
                else:
                    self.locationindex[location] = unit

    def __str__(self):
        """Converts to a string representation that can be parsed back using L{parsestring()}."""

        # We can't pickle fileobj if it is there, so let's hide it for a while.
        fileobj = getattr(self, "fileobj", None)
        self.fileobj = None
        dump = pickle.dumps(self)
        self.fileobj = fileobj
        return dump

    def isempty(self):
        """Returns True if the object doesn't contain any translation units."""

        if len(self.units) == 0:
            return True
        for unit in self.units:
            if not (unit.isblank() or unit.isheader()):
                return False
        return True

    def _assignname(self):
        """Tries to work out what the name of the filesystem file is and 
        assigns it to .filename."""
        fileobj = getattr(self, "fileobj", None)
        if fileobj:
            filename = getattr(fileobj, "name", getattr(fileobj, "filename", None))
            if filename:
                self.filename = filename

    def parsestring(cls, storestring):
        """Converts the string representation back to an object."""
        newstore = cls()
        if storestring:
            newstore.parse(storestring)
        return newstore
    parsestring = classmethod(parsestring)

    def parse(self, data):
        """parser to process the given source string"""
        self.units = pickle.loads(data).units

    def savefile(self, storefile):
        """Writes the string representation to the given file (or filename)."""
        if isinstance(storefile, basestring):
            storefile = open(storefile, "w")
        self.fileobj = storefile
        self._assignname()
        storestring = str(self)
        storefile.write(storestring)
        storefile.close()

    def save(self):
        """Save to the file that data was originally read from, if available."""
        fileobj = getattr(self, "fileobj", None)
        if not fileobj:
            filename = getattr(self, "filename", None)
            if filename:
                fileobj = file(filename, "w")
        else:
            fileobj.close()
            filename = getattr(fileobj, "name", getattr(fileobj, "filename", None))
            if not filename:
                raise ValueError("No file or filename to save to")
            fileobj = fileobj.__class__(filename, "w")
        self.savefile(fileobj)

    def parsefile(cls, storefile):
        """Reads the given file (or opens the given filename) and parses back to an object."""

        if isinstance(storefile, basestring):
            storefile = open(storefile, "r")
        mode = getattr(storefile, "mode", "r")
        #For some reason GzipFile returns 1, so we have to test for that here
        if mode == 1 or "r" in mode:
            storestring = storefile.read()
            storefile.close()
        else:
            storestring = ""
        newstore = cls.parsestring(storestring)
        newstore.fileobj = storefile
        newstore._assignname()
        return newstore
    parsefile = classmethod(parsefile)

