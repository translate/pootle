#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2004-2006 Zuza Software Foundation
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

"""Insert debug messages into XLIFF and Gettex PO localization files

See: http://translate.sourceforge.net/wiki/toolkit/podebug for examples and
usage instructions
"""

from translate.storage import factory
import os
import re
import md5

class podebug:
    def __init__(self, format=None, rewritestyle=None, hash=None, ignoreoption=None):
        if format is None:
            self.format = ""
        else:
            self.format = format
        self.rewritefunc = getattr(self, "rewrite_%s" % rewritestyle, None)
        self.ignorefunc = getattr(self, "ignore_%s" % ignoreoption, None)
        self.hash = hash

    def rewritelist(cls):
        return [rewrite.replace("rewrite_", "") for rewrite in dir(cls) if rewrite.startswith("rewrite_")]
    rewritelist = classmethod(rewritelist)

    def rewrite_xxx(self, string):
        return "xxx%sxxx" % string

    def rewrite_en(self, string):
        return string

    def rewrite_blank(self, string):
        return ""

    def rewrite_chef(self, string):
        """Rewrite using Mock Swedish as made famous by Monty Python"""
        # From Dive into Python which itself got it elsewhere http://www.renderx.com/demos/examples/diveintopython.pdf
        subs = (
               (r'a([nu])', r'u\1'),
               (r'A([nu])', r'U\1'),
               (r'a\B', r'e'),
               (r'A\B', r'E'),
               (r'en\b', r'ee'),
               (r'\Bew', r'oo'),
               (r'\Be\b', r'e-a'),
               (r'\be', r'i'),
               (r'\bE', r'I'),
               (r'\Bf', r'ff'),
               (r'\Bir', r'ur'),
               (r'(\w*?)i(\w*?)$', r'\1ee\2'),
               (r'\bow', r'oo'),
               (r'\bo', r'oo'),
               (r'\bO', r'Oo'),
               (r'the', r'zee'),
               (r'The', r'Zee'),
               (r'th\b', r't'),
               (r'\Btion', r'shun'),
               (r'\Bu', r'oo'),
               (r'\BU', r'Oo'),
               (r'v', r'f'),
               (r'V', r'F'),
               (r'w', r'w'),
               (r'W', r'W'),
               (r'([a-z])[.]', r'\1. Bork Bork Bork!'))
        for a, b in subs:
            string = re.sub(a, b, string)
        return string

    REWRITE_UNICODE_MAP = u"ȦƁƇḒḖƑƓĦĪĴĶĿḾȠǾƤɊŘŞŦŬṼẆẊẎẐ" + u"[\\]^_`" + u"ȧƀƈḓḗƒɠħīĵķŀḿƞǿƥɋřşŧŭṽẇẋẏẑ"
    def rewrite_unicode(self, string):
        """Convert to Unicode characters that look like the source string"""
        def transpose(char):
            loc = ord(char)-65
            if loc < 0 or loc > 56:
                return char
            return self.REWRITE_UNICODE_MAP[loc]
        return "".join(map(transpose, string))

    def ignorelist(cls):
        return [rewrite.replace("ignore_", "") for rewrite in dir(cls) if rewrite.startswith("ignore_")]
    ignorelist = classmethod(ignorelist)

    def ignore_openoffice(self, locations):
        for location in locations:
            if location.startswith("Common.xcu#..Common.View.Localisation"):
                return True
            elif location.startswith("profile.lng#STR_DIR_MENU_NEW_"):
                return True
            elif location.startswith("profile.lng#STR_DIR_MENU_WIZARD_"):
                return True
        return False

    def ignore_mozilla(self, locations):
        if len(locations) == 1 and locations[0].lower().endswith(".accesskey"):
            return True
        for location in locations:
            if location.endswith(".height") or location.endswith(".width") or \
                    location.endswith(".macWidth") or location.endswith(".unixWidth"):
                return True
            if location == "brandShortName" or location == "brandFullName" or location == "vendorShortName":
                return True
            if location.lower().endswith(".commandkey") or location.endswith(".key"):
                return True
        return False

    def convertunit(self, unit, prefix):
        if self.ignorefunc:
            if self.ignorefunc(unit.getlocations()):
                return unit
        if self.hash:
            if unit.getlocations():
                hashable = unit.getlocations()[0]
            else:
                hashable = unit.source
            prefix = md5.new(hashable).hexdigest()[:self.hash] + " "
        if self.rewritefunc:
            unit.target = self.rewritefunc(unit.source)
        elif not unit.istranslated():
            unit.target = unit.source
        if unit.hasplural():
            strings = unit.target.strings
            for i, string in enumerate(strings):
                strings[i] = prefix + string
            unit.target = strings
        else:
            unit.target = prefix + unit.target
        return unit

    def convertstore(self, store):
        filename = self.shrinkfilename(store.filename)
        prefix = self.format
        for formatstr in re.findall("%[0-9c]*[sfFbBd]", self.format):
            if formatstr.endswith("s"):
                formatted = self.shrinkfilename(store.filename)
            elif formatstr.endswith("f"):
                formatted = store.filename
                formatted = os.path.splitext(formatted)[0]
            elif formatstr.endswith("F"):
                formatted = store.filename
            elif formatstr.endswith("b"):
                formatted = os.path.basename(store.filename)
                formatted = os.path.splitext(formatted)[0]
            elif formatstr.endswith("B"):
                formatted = os.path.basename(store.filename)
            elif formatstr.endswith("d"):
                formatted = os.path.dirname(store.filename)
            else:
                continue
            formatoptions = formatstr[1:-1]
            if formatoptions:
                if "c" in formatoptions and formatted:
                    formatted = formatted[0] + filter(lambda x: x.lower() not in "aeiou", formatted[1:])
                length = filter(str.isdigit, formatoptions)
                if length:
                    formatted = formatted[:int(length)]
            prefix = prefix.replace(formatstr, formatted)
        for unit in store.units:
            if unit.isheader() or unit.isblank():
                continue
            unit = self.convertunit(unit, prefix)
        return store

    def shrinkfilename(self, filename):
        if filename.startswith("." + os.sep):
            filename = filename.replace("." + os.sep, "", 1)
        dirname = os.path.dirname(filename)
        dirparts = dirname.split(os.sep)
        if not dirparts:
            dirshrunk = ""
        else:
            dirshrunk = dirparts[0][:4] + "-"
            if len(dirparts) > 1:
                dirshrunk += "".join([dirpart[0] for dirpart in dirparts[1:]]) + "-"
        baseshrunk = os.path.basename(filename)[:4]
        if "." in baseshrunk:
            baseshrunk = baseshrunk[:baseshrunk.find(".")]
        return dirshrunk + baseshrunk

def convertpo(inputfile, outputfile, templatefile, format=None, rewritestyle=None, hash=None, ignoreoption=None):
    """reads in inputfile using po, changes to have debug strings, writes to outputfile"""
    # note that templatefile is not used, but it is required by the converter...
    inputstore = factory.getobject(inputfile)
    if inputstore.isempty():
        return 0
    convertor = podebug(format=format, rewritestyle=rewritestyle, hash=hash, ignoreoption=ignoreoption)
    outputstore = convertor.convertstore(inputstore)
    outputfile.write(str(outputstore))
    return 1

def main():
    from translate.convert import convert
    formats = {"po":("po", convertpo), "xlf":("xlf", convertpo)}
    parser = convert.ConvertOptionParser(formats, usepots=True, description=__doc__)
    # TODO: add documentation on format strings...
    parser.add_option("-f", "--format", dest="format", default="[%s] ", help="specify format string")
    parser.add_option("", "--rewrite", dest="rewritestyle", 
        type="choice", choices=podebug.rewritelist(), metavar="STYLE", help="the translation rewrite style: %s" % ", ".join(podebug.rewritelist()))
    parser.add_option("", "--ignore", dest="ignoreoption", 
        type="choice", choices=podebug.ignorelist(), metavar="APPLICATION", help="apply tagging ignore rules for the given application: %s" % ", ".join(podebug.ignorelist()))
    parser.add_option("", "--hash", dest="hash", metavar="LENGTH", type="int", help="add an md5 hash to translations")
    parser.passthrough.append("format")
    parser.passthrough.append("rewritestyle")
    parser.passthrough.append("ignoreoption")
    parser.passthrough.append("hash")
    parser.run()


if __name__ == '__main__':
    main()
