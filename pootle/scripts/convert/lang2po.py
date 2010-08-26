#!/usr/bin/env python

# lang2po.py
# Converts .lang files to .po files using standard translation-tookit methods

# Author: Dan Schafer <dschafer@mozilla.com>
# Date: 10 Jun 2008

from translate.storage import po
import lang

class lang2po:
    def __init__(self, duplicatestyle="msgctxt"):
        self.duplicatestyle = duplicatestyle

    def convertstore(self, thelangfile):
        """converts a file to .po format"""
        thetargetfile = po.pofile()

        # Set up the header
        targetheader = thetargetfile.makeheader(charset="UTF-8", encoding="8bit")
        targetheader.addnote("extracted from %s" % thelangfile.filename, "developer")
        thetargetfile.addunit(targetheader)

        # For each lang unit, make the new po unit accordingly
        for langunit in thelangfile.units:
            newunit = thetargetfile.addsourceunit(langunit.source)
            newunit.settarget(langunit.target)
            newunit.addlocations(langunit.getlocations())

        # Remove duplicates, because we can
        thetargetfile.removeduplicates(self.duplicatestyle)
        return thetargetfile

def convertlang(inputfile, outputfile, templates, duplicatestyle="msgctxt", encoding="utf-8"):
    """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
    inputstore = lang.LangStore(inputfile, encoding=encoding)
    convertor = lang2po(duplicatestyle=duplicatestyle)
    outputstore = convertor.convertstore(inputstore)
    if outputstore.isempty():
        return 0
    outputfile.write(str(outputstore))
    return 1

def main(argv=None):
    from translate.convert import convert
    from translate.misc import stdiotell
    import sys
    sys.stdout = stdiotell.StdIOWrapper(sys.stdout)
    formats = {"lang": ("po", convertlang), "*": ("po", convertlang)}
    parser = convert.ConvertOptionParser(formats, usepots=True, description=__doc__)
    parser.add_option("", "--encoding", dest="encoding", default='utf-8', type="string",
    help="The encoding of the input file (default: UTF-8)")
    parser.passthrough.append("encoding")
    parser.add_duplicates_option()
    parser.run(argv)

if __name__ == '__main__':
    main()
