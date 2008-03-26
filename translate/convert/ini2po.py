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

"""convert .ini files to Gettext PO localization files"""

import sys
from translate.storage import po
from translate.storage import xliff
from translate.storage import ini

class ini2po:
    """convert a .ini file to a .po file for handling the translation..."""
    def convertstore(self, theinifile, duplicatestyle="msgctxt"):
        """converts a .ini file to a .po file..."""
        thetargetfile = po.pofile()
        targetheader = thetargetfile.makeheader(charset="UTF-8", encoding="8bit")
        targetheader.addnote("extracted from %s" % theinifile.filename, "developer")
        thetargetfile.addunit(targetheader)
        for iniunit in theinifile.units:
            pounit = self.convertunit(iniunit, "developer")
            if pounit is not None:
                thetargetfile.addunit(pounit)
        thetargetfile.removeduplicates(duplicatestyle)
        return thetargetfile

    def mergestore(self, originifile, translatedinifile, blankmsgstr=False, duplicatestyle="msgctxt"):
        """converts two .ini files to a .po file..."""
        thetargetfile = po.pofile()
        targetheader = thetargetfile.makeheader(charset="UTF-8", encoding="8bit")
        targetheader.addnote("extracted from %s, %s" % (originifile.filename, translatedinifile.filename), "developer")
        thetargetfile.addunit(targetheader)
        translatedinifile.makeindex()
        for origini in originifile.units:
            origpo = self.convertunit(origini, "developer")
            # try and find a translation of the same name...
            origininame = "".join(origini.getlocations())
            if origininame in translatedinifile.locationindex:
                translatedini = translatedinifile.locationindex[origininame]
                translatedpo = self.convertunit(translatedini, "translator")
            else:
                translatedpo = None
            # if we have a valid po unit, get the translation and add it...
            if origpo is not None:
                if translatedpo is not None and not blankmsgstr:
                    origpo.target = translatedpo.source
                thetargetfile.addunit(origpo)
            elif translatedpo is not None:
                print >> sys.stderr, "error converting original ini definition %s" % origini.name
        thetargetfile.removeduplicates(duplicatestyle)
        return thetargetfile

    def convertunit(self, iniunit, commenttype):
        """Converts a .ini unit to a .po unit. Returns None if empty
        or not for translation."""
        if iniunit is None:
            return None
        # escape unicode
        pounit = po.pounit(encoding="UTF-8")
        pounit.addlocation("".join(iniunit.getlocations()))
        pounit.source = iniunit.source
        pounit.target = ""
        return pounit

def convertini(inputfile, outputfile, templatefile, pot=False, duplicatestyle="msgctxt"):
    """reads in inputfile using ini, converts using ini2po, writes to outputfile"""
    inputstore = ini.inifile(inputfile)
    convertor = ini2po()
    if templatefile is None:
        outputstore = convertor.convertstore(inputstore, duplicatestyle=duplicatestyle)
    else:
        templatestore = ini.inifile(templatefile)
        outputstore = convertor.mergestore(templatestore, inputstore, blankmsgstr=pot, duplicatestyle=duplicatestyle)
    if outputstore.isempty():
        return 0
    outputfile.write(str(outputstore))
    return 1

def main(argv=None):
    from translate.convert import convert
    formats = {"ini": ("po", convertini), ("ini", "ini"): ("po", convertini)}
    parser = convert.ConvertOptionParser(formats, usetemplates=True, usepots=True, description=__doc__)
    parser.add_duplicates_option()
    parser.passthrough.append("pot")
    parser.run(argv)

if __name__ == '__main__':
    main()

