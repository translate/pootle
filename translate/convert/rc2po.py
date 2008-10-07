#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2007-2008 Zuza Software Foundation
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

"""convert .rc files to Gettext PO localization files"""

import sys
from translate.storage import po
from translate.storage import rc

class rc2po:
    """convert a .rc file to a .po file for handling the translation..."""
    def __init__(self, charset=None):
        self.charset = charset

    def convertstore(self, thercfile, duplicatestyle="msgctxt"):
        """converts a .rc file to a .po file..."""
        thetargetfile = po.pofile()
        targetheader = thetargetfile.makeheader(charset="UTF-8", encoding="8bit")
        targetheader.addnote("extracted from %s" % thercfile.filename, "developer")
        thetargetfile.addunit(targetheader)
        for rcunit in thercfile.units:
            pounit = self.convertunit(rcunit, "developer")
            if pounit is not None:
                thetargetfile.addunit(pounit)
        thetargetfile.removeduplicates(duplicatestyle)
        return thetargetfile

    def mergestore(self, origrcfile, translatedrcfile, blankmsgstr=False, duplicatestyle="msgctxt"):
        """converts two .rc files to a .po file..."""
        thetargetfile = po.pofile()
        targetheader = thetargetfile.makeheader(charset="UTF-8", encoding="8bit")
        targetheader.addnote("extracted from %s, %s" % (origrcfile.filename, translatedrcfile.filename), "developer")
        thetargetfile.addunit(targetheader)
        translatedrcfile.makeindex()
        for origrc in origrcfile.units:
            origpo = self.convertunit(origrc, "developer")
            # try and find a translation of the same name...
            origrcname = "".join(origrc.getlocations())
            if origrcname in translatedrcfile.locationindex:
                translatedrc = translatedrcfile.locationindex[origrcname]
                translatedpo = self.convertunit(translatedrc, "translator")
            else:
                translatedpo = None
            # if we have a valid po unit, get the translation and add it...
            if origpo is not None:
                if translatedpo is not None and not blankmsgstr:
                    origpo.target = translatedpo.source
                thetargetfile.addunit(origpo)
            elif translatedpo is not None:
                print >> sys.stderr, "error converting original rc definition %s" % origrc.name
        thetargetfile.removeduplicates(duplicatestyle)
        return thetargetfile

    def convertunit(self, rcunit, commenttype):
        """Converts a .rc unit to a .po unit. Returns None if empty
        or not for translation."""
        if rcunit is None:
            return None
        # escape unicode
        pounit = po.pounit(encoding="UTF-8")
        pounit.addlocation("".join(rcunit.getlocations()))
        pounit.source = rcunit.source.decode(self.charset)
        pounit.target = ""
        return pounit

def convertrc(inputfile, outputfile, templatefile, pot=False, duplicatestyle="msgctxt", charset=None):
    """reads in inputfile using rc, converts using rc2po, writes to outputfile"""
    inputstore = rc.rcfile(inputfile)
    convertor = rc2po(charset=charset)
    if templatefile is None:
        outputstore = convertor.convertstore(inputstore, duplicatestyle=duplicatestyle)
    else:
        templatestore = rc.rcfile(templatefile)
        outputstore = convertor.mergestore(templatestore, inputstore, blankmsgstr=pot, duplicatestyle=duplicatestyle)
    if outputstore.isempty():
        return 0
    outputfile.write(str(outputstore))
    return 1

def main(argv=None):
    from translate.convert import convert
    formats = {"rc": ("po", convertrc), ("rc", "rc"): ("po", convertrc), 
               "nls": ("po", convertrc), ("nls", "nls"): ("po", convertrc)}
    parser = convert.ConvertOptionParser(formats, usetemplates=True, usepots=True, description=__doc__)
    defaultcharset="cp1252"
    parser.add_option("", "--charset", dest="charset", default=defaultcharset,
        help="charset to use to decode the RC files (default: %s)" % defaultcharset, metavar="CHARSET")
    parser.add_duplicates_option()
    parser.passthrough.append("pot")
    parser.passthrough.append("charset")
    parser.run(argv)

if __name__ == '__main__':
    main()

