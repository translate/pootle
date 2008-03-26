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
#

"""convert OpenDocument (ODF) files to Gettext PO localization files"""

from translate.storage import po
from translate.storage import odf

class odf2po:
    def convertstore(self, inputfile):
        """converts a file to .po format"""
        thetargetfile = po.pofile()
        filename = getattr(inputfile, "name", "unkown")
        targetheader = thetargetfile.makeheader(charset="UTF-8", encoding="8bit")
        targetheader.addnote("extracted from %s\n" % filename, "developer")
        thetargetfile.addunit(targetheader)
        odfdoc = odf.ODFFile(inputfile)
        blocknum = 0
        for unit in odfdoc.getunits():
            if not unit: continue
            blocknum += 1
            newunit = thetargetfile.addsourceunit(unit.source)
            newunit.addlocations("%s:%d" % (filename, blocknum))
        return thetargetfile

def convertodf(inputfile, outputfile, templates):
    """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
    convertor = odf2po()
    outputstore = convertor.convertstore(inputfile)
    if outputstore.isempty():
        return 0
    outputfile.write(str(outputstore))
    return 1

def main(argv=None):
    from translate.convert import convert
    formats = {"sxw":("po",convertodf), "odt":("po",convertodf), "ods":("po",convertodf), "odp":("po",convertodf)}
    parser = convert.ConvertOptionParser(formats, description=__doc__)
    parser.run(argv)


if __name__ == '__main__':
    main()
