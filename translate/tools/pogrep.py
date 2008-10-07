#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2002-2008 Zuza Software Foundation
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

"""Grep XLIFF, Gettext PO and TMX localization files

Matches are output to snippet files of the same type which can then be reviewed 
and later merged using pomerge

See: http://translate.sourceforge.net/wiki/toolkit/pogrep for examples and
usage instructions
"""

from translate.storage import factory
from translate.misc import optrecurse
from translate.misc.multistring import multistring
from translate.lang import data
import re
import locale

class GrepFilter:
    def __init__(self, searchstring, searchparts, ignorecase=False, useregexp=False, invertmatch=False, accelchar=None, encoding='utf-8', includeheader=False):
        """builds a checkfilter using the given checker"""
        if isinstance(searchstring, unicode):
            self.searchstring = searchstring
        else:
            self.searchstring = searchstring.decode(encoding)
        self.searchstring = data.normalize(self.searchstring)
        if searchparts:
            # For now we still support the old terminology, except for the old 'source'
            # which has a new meaning now.
            self.search_source = ('source' in searchparts) or ('msgid' in searchparts)
            self.search_target = ('target' in searchparts) or ('msgstr' in searchparts)
            self.search_notes =  ('notes' in searchparts) or ('comment' in searchparts)
            self.search_locations = 'locations' in searchparts
        else:
            self.search_source = True
            self.search_target = True
            self.search_notes = False
            self.search_locations = False
        self.ignorecase = ignorecase
        if self.ignorecase:
            self.searchstring = self.searchstring.lower()
        self.useregexp = useregexp
        if self.useregexp:
            self.searchpattern = re.compile(self.searchstring)
        self.invertmatch = invertmatch
        self.accelchar = accelchar
        self.includeheader = includeheader

    def matches(self, teststr):
        if teststr is None:
            return False
        teststr = data.normalize(teststr)
        if self.ignorecase:
            teststr = teststr.lower()
        if self.accelchar:
            teststr = re.sub(self.accelchar + self.accelchar, "#", teststr)
            teststr = re.sub(self.accelchar, "", teststr)
        if self.useregexp:
            found = self.searchpattern.search(teststr)
        else:
            found = teststr.find(self.searchstring) != -1
        if self.invertmatch:
            found = not found
        return found

    def filterunit(self, unit):
        """runs filters on an element"""
        if unit.isheader(): return []

        if self.search_source:
            if isinstance(unit.source, multistring):
                strings = unit.source.strings
            else:
                strings = [unit.source]
            for string in strings:
                if self.matches(string):
                    return True

        if self.search_target:
            if isinstance(unit.target, multistring):
                strings = unit.target.strings
            else:
                strings = [unit.target]
            for string in strings:
                if self.matches(string):
                    return True

        if self.search_notes:
            return self.matches(unit.getnotes())
        if self.search_locations:
            return self.matches(u" ".join(unit.getlocations()))
        return False

    def filterfile(self, thefile):
        """runs filters on a translation file object"""
        thenewfile = type(thefile)()
        thenewfile.setsourcelanguage(thefile.sourcelanguage)
        thenewfile.settargetlanguage(thefile.targetlanguage)
        for unit in thefile.units:
            if self.filterunit(unit):
                thenewfile.addunit(unit)
        if self.includeheader and thenewfile.units > 0:
            if thefile.units[0].isheader():
                thenewfile.units.insert(0, thefile.units[0])
            else:
                thenewfile.units.insert(0, thenewfile.makeheader())
        return thenewfile

class GrepOptionParser(optrecurse.RecursiveOptionParser):
    """a specialized Option Parser for the grep tool..."""
    def parse_args(self, args=None, values=None):
        """parses the command line options, handling implicit input/output args"""
        (options, args) = optrecurse.optparse.OptionParser.parse_args(self, args, values)
        # some intelligence as to what reasonable people might give on the command line
        if args:
            options.searchstring = args[0]
            args = args[1:]
        else:
            self.error("At least one argument must be given for the search string")
        if args and not options.input:
            if not options.output:
                options.input = args[:-1]
                args = args[-1:]
            else:
                options.input = args
                args = []
        if args and not options.output:
            options.output = args[-1]
            args = args[:-1]
        if args:
            self.error("You have used an invalid combination of --input, --output and freestanding args")
        if isinstance(options.input, list) and len(options.input) == 1:
            options.input = options.input[0]
        return (options, args)

    def set_usage(self, usage=None):
        """sets the usage string - if usage not given, uses getusagestring for each option"""
        if usage is None:
            self.usage = "%prog searchstring " + " ".join([self.getusagestring(option) for option in self.option_list])
        else:
            super(GrepOptionParser, self).set_usage(usage)

    def run(self):
        """parses the arguments, and runs recursiveprocess with the resulting options"""
        (options, args) = self.parse_args()
        options.inputformats = self.inputformats
        options.outputoptions = self.outputoptions
        options.checkfilter = GrepFilter(options.searchstring, options.searchparts, options.ignorecase, options.useregexp, options.invertmatch, options.accelchar, locale.getpreferredencoding(), options.includeheader)
        self.usepsyco(options)
        self.recursiveprocess(options)

def rungrep(inputfile, outputfile, templatefile, checkfilter):
    """reads in inputfile, filters using checkfilter, writes to outputfile"""
    fromfile = factory.getobject(inputfile)
    tofile = checkfilter.filterfile(fromfile)
    if tofile.isempty():
        return False
    outputfile.write(str(tofile))
    return True

def cmdlineparser():
    formats = {"po":("po", rungrep), "pot":("pot", rungrep), 
            "xliff":("xliff", rungrep), "xlf":("xlf", rungrep), "xlff":("xlff", rungrep), 
            "tmx":("tmx", rungrep),
            None:("po", rungrep)}
    parser = GrepOptionParser(formats)
    parser.add_option("", "--search", dest="searchparts",
        action="append", type="choice", choices=["source", "target", "notes", "locations", "msgid", "msgstr", "comment" ],
        metavar="SEARCHPARTS", help="searches the given parts (source, target, notes and locations)")
    parser.add_option("-I", "--ignore-case", dest="ignorecase",
        action="store_true", default=False, help="ignore case distinctions")
    parser.add_option("-e", "--regexp", dest="useregexp",
        action="store_true", default=False, help="use regular expression matching")
    parser.add_option("-v", "--invert-match", dest="invertmatch",
        action="store_true", default=False, help="select non-matching lines")
    parser.add_option("", "--accelerator", dest="accelchar",
        action="store", type="choice", choices=["&", "_", "~"],
        metavar="ACCELERATOR", help="ignores the given accelerator when matching")
    parser.add_option("", "--header", dest="includeheader",
        action="store_true", default=False,
        help="include a PO header in the output")
    parser.set_usage()
    parser.passthrough.append('checkfilter')
    parser.description = __doc__
    return parser

def main():
    parser = cmdlineparser()
    parser.run()

if __name__ == '__main__':
    main()
