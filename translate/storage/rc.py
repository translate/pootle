#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2004-2006, 2008 Zuza Software Foundation
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

"""classes that hold units of .rc files (rcunit) or entire files
(rcfile) these files are used in translating Windows Resources

@note: This implementation is based mostly on observing WINE .rc files,
these should mimic other non-WINE .rc files.
"""

from translate.storage import base
import re
import sys

def escape_to_python(string):
    """escape a given .rc string into a valid Python string"""
    pystring = re.sub('"\s*\\\\\n\s*"', "", string)   # xxx"\n"xxx line continuation
    pystring = re.sub("\\\\\\\n", "", pystring)       # backslash newline line continuation
    pystring = re.sub("\\\\n", "\n", pystring)        # Convert escaped newline to a real newline
    pystring = re.sub("\\\\t", "\t", pystring)        # Convert escape tab to a real tab
    pystring = re.sub("\\\\\\\\", "\\\\", pystring)   # Convert escape backslash to a real escaped backslash
    return pystring

def escape_to_rc(string):
    """escape a given Python string into a valid .rc string"""
    rcstring = re.sub("\\\\", "\\\\\\\\", string)
    rcstring = re.sub("\t", "\\\\t", rcstring)
    rcstring = re.sub("\n", "\\\\n", rcstring)
    return rcstring

class rcunit(base.TranslationUnit):
    """a unit of an rc file"""
    def __init__(self, source=""):
        """construct a blank rcunit"""
        super(rcunit, self).__init__(source)
        self.name = ""
        self._value = ""
        self.comments = []
        self.source = source
        self.match = None

    def setsource(self, source):
        """Sets the source AND the target to be equal"""
        self._value = source or ""

    def getsource(self):
        return self._value

    source = property(getsource, setsource)

    def settarget(self, target):
        """Note: this also sets the .source attribute!"""
        self.source = target

    def gettarget(self):
        return self.source
    target = property(gettarget, settarget)

    def __str__(self):
        """convert to a string. double check that unicode is handled somehow here"""
        source = self.getoutput()
        if isinstance(source, unicode):
            return source.encode(getattr(self, "encoding", "UTF-8"))
        return source

    def getoutput(self):
        """convert the element back into formatted lines for a .rc file"""
        if self.isblank():
            return "".join(self.comments + ["\n"])
        else:
            return "".join(self.comments + ["%s=%s\n" % (self.name, self.value)])

    def getlocations(self):
        return [self.name]

    def addnote(self, note, origin=None):
        self.comments.append(note)

    def getnotes(self, origin=None):
        return '\n'.join(self.comments)

    def removenotes(self):
        self.comments = []

    def isblank(self):
        """returns whether this is a blank element, containing only comments..."""
        return not (self.name or self.value)

class rcfile(base.TranslationStore):
    """this class represents a .rc file, made up of rcunits"""
    UnitClass = rcunit
    def __init__(self, inputfile=None):
        """construct an rcfile, optionally reading in from inputfile"""
        super(rcfile, self).__init__(unitclass = self.UnitClass)
        self.filename = getattr(inputfile, 'name', '')
        if inputfile is not None:
            rcsrc = inputfile.read()
            inputfile.close()
            self.parse(rcsrc)

    def parse(self, rcsrc):
        """read the source of a .rc file in and include them as units"""
        BLOCKS_RE = re.compile("""
                         (?:
                         LANGUAGE\s+[^\n]*|                              # Language details
                         /\*.*?\*/[^\n]*|                                      # Comments
                         (?:[0-9A-Z_]+\s+(?:MENU|DIALOG|DIALOGEX)|STRINGTABLE)\s  # Translatable section
                         .*?
                         (?:
                         BEGIN(?:\s*?POPUP.*?BEGIN.*?END\s*?)+?END|BEGIN.*?END|  # FIXME Need a much better approach to nesting menus
                         {(?:\s*?POPUP.*?{.*?}\s*?)+?}|{.*?})+[\n]|
                         \s*[\n]         # Whitespace
                         )
                         """, re.DOTALL + re.VERBOSE)
        STRINGTABLE_RE = re.compile("""
                         (?P<name>[0-9A-Za-z_]+?),?\s*
                         L?"(?P<value>.*?)"\s*[\n]
                         """, re.DOTALL + re.VERBOSE)
        DIALOG_RE = re.compile("""
                         (?P<type>AUTOCHECKBOX|AUTORADIOBUTTON|CAPTION|Caption|CHECKBOX|CTEXT|CONTROL|DEFPUSHBUTTON|
                         GROUPBOX|LTEXT|PUSHBUTTON|RADIOBUTTON|RTEXT)  # Translatable types
                         \s+
                         L?                                    # Unkown prefix see ./dlls/shlwapi/shlwapi_En.rc
                         "(?P<value>.*?)"                                      # String value
                         (?:\s*,\s*|[\n])                          # FIXME ./dlls/mshtml/En.rc ID_DWL_DIALOG.LTEXT.ID_DWL_STATUS
                         (?P<name>.*?|)\s*(?:/[*].*?[*]/|),
                         """, re.DOTALL + re.VERBOSE)
        MENU_RE = re.compile("""
                         (?P<type>POPUP|MENUITEM)
                         \s+
                         "(?P<value>.*?)"                                      # String value
                         (?:\s*,?\s*)?
                         (?P<name>[^\s]+).*?[\n]
                         """, re.DOTALL + re.VERBOSE)
        languagesection = False

        self.blocks = BLOCKS_RE.findall(rcsrc)

        for blocknum, block in enumerate(self.blocks):
            #print block.split("\n")[0]
            if block.startswith("STRINGTABLE"):
                #print "stringtable:\n %s------\n" % block
                for match in STRINGTABLE_RE.finditer(block): 
                    if not match.groupdict()['value']:
                        continue
                    newunit = rcunit(escape_to_python(match.groupdict()['value']))
                    newunit.name = "STRINGTABLE." + match.groupdict()['name']
                    newunit.match = match 
                    self.addunit(newunit)
            if block.startswith("LANGUAGE"):
                #print "language"
                if not languagesection:
                    languagesection = True
                else:
                    print >> sys.stderr, "Can only process one language section"
                    self.blocks = self.blocks[:blocknum]
                    break
            if block.startswith("/*"):  # Comments
                #print "comment"
                pass
            if re.match("[0-9A-Z_]+\s+DIALOG", block) is not None:
                dialog = re.match("(?P<dialogname>[0-9A-Z_]+)\s+(?P<dialogtype>DIALOGEX|DIALOG)", block).groupdict()
                dialogname = dialog["dialogname"]
                dialogtype = dialog["dialogtype"]
                #print "dialog: %s" % dialogname
                for match in DIALOG_RE.finditer(block):
                    if not match.groupdict()['value']:
                        continue
                    type = match.groupdict()['type']
                    value = match.groupdict()['value']
                    name = match.groupdict()['name']
                    newunit = rcunit(escape_to_python(value))
                    if type == "CAPTION" or type == "Caption":
                        newunit.name = "%s.%s.%s" % (dialogtype, dialogname, type)
                    elif name == "-1":
                        newunit.name = "%s.%s.%s.%s" % (dialogtype, dialogname, type, value.replace(" ", "_"))
                    else:
                        newunit.name = "%s.%s.%s.%s" % (dialogtype, dialogname, type, name)
                    newunit.match = match 
                    self.addunit(newunit)
            if re.match("[0-9A-Z_]+\s+MENU", block) is not None:
                menuname = re.match("(?P<menuname>[0-9A-Z_]+)\s+MENU", block).groupdict()["menuname"]
                #print "menu: %s" % menuname
                for match in DIALOG_RE.finditer(block):
                    if not match.groupdict()['value']:
                        continue
                    type = match.groupdict()['type']
                    value = match.groupdict()['value']
                    name = match.groupdict()['name']
                    newunit = rcunit(escape_to_python(value))
                    if type == "POPUP":
                        newunit.name = "MENU.%s.%s" % (menuname, type)
                    elif name == "-1":
                        newunit.name = "MENU.%s.%s.%s" % (menuname, type, value.replace(" ", "_"))
                    else:
                        newunit.name = "MENU.%s.%s.%s" % (menuname, type, name)
                    newunit.match = match 
                    self.addunit(newunit)
         
    def __str__(self):
        """convert the units back to lines"""
        return "".join(self.blocks)

