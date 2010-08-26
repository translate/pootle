#!/usr/bin/env python

# po2amo.py
# Converts .po files to AMO .po files using standard translation-tookit methods

# Usage: ./po2amo po-file amo-output

# Author: Dan Schafer <dschafer@mozilla.com>
# Date: 11 Jun 2008

from translate.storage import po


class po2amo:

    def convertstore(self, thepofile):
        """converts a file to .po format"""
        thetargetfile = po.pofile()

        for unit in thepofile.units:
            newunit = unit.copy()

            # The AMO id is stored in the context
            newunit.msgid = unit.msgctxt

            # If there's a plural in the po file, then there should be in the
            # amo file
            if unit.msgid_plural != []:
                newunit.msgid_plural = unit.msgctxt

            # No context in AMO
            newunit.msgctxt = []

            # No need to alter the msgstr; it is foreign in the original file,
            # and we started with that as a base

            thetargetfile.addunit(newunit)

        return thetargetfile


def convertpo(inputfile, outputfile, templates=None):
    """reads in stdin using fromfileclass, converts using convertorclass,
    writes to stdout"""
    inputstore = po.pofile(inputfile)
    convertor = po2amo()
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
    formats = {"*": ("po", convertpo)}
    parser = convert.ConvertOptionParser(formats, description=__doc__)
    parser.run(argv)


if __name__ == '__main__':
    main()
