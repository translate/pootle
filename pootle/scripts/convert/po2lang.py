#!/usr/bin/env python

# po2lang.py
# Converts .po files to .lang files using standard translation-tookit methods

# Author: Dan Schafer <dschafer@mozilla.com>
# Date: 10 Jun 2008

from translate.storage import po
import lang

class po2lang:
    def __init__(self, duplicatestyle="msgctxt"):
        self.duplicatestyle = duplicatestyle

    def convertstore(self, inputstore):
        """converts a file to .lang format"""
        thetargetfile = lang.LangStore()

        # Run over the po units
        for pounit in inputstore.units:
            # Skip the header
            if pounit.isheader():
                continue
            newunit = thetargetfile.addsourceunit(pounit.source)
            newunit.settarget(pounit.target)
        return thetargetfile

def convertlang(inputfile, outputfile, templates):
    """reads in stdin using fromfileclass, converts using convertorclass, writes to stdout"""
    inputstore = po.pofile(inputfile)
    if inputstore.isempty():
        return 0
    convertor = po2lang()
    outputstore = convertor.convertstore(inputstore)
    outputfile.write(str(outputstore))
    return 1

def main(argv=None):
    from translate.convert import convert
    from translate.misc import stdiotell
    import sys
    sys.stdout = stdiotell.StdIOWrapper(sys.stdout)
    formats = {"po": ("lang", convertlang)}
    parser = convert.ConvertOptionParser(formats, usepots=True, description=__doc__)
    parser.run(argv)

if __name__ == '__main__':
    main()
