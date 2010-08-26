#!/usr/bin/env python

# amo2po.py
# Converts AMO .po files to .po files using standard translation-tookit methods

# Usage: ./amo2po english-file [-t foreign-file] [output-file]

# Author: Dan Schafer <dschafer@mozilla.com>
# Date: 11 Jun 2008

import sys

from translate.storage import po


class amo2po:

    def convertstore(self, engfile, forfile):
        """converts a file to .po format"""
        thetargetfile = po.pofile()

        # A dictionary mapping msgids to their foreign units
        key2for = {}
        # Populate the dictionary
        for unit in forfile.units:
            key2for[str(unit.msgid)] = unit
            if unit.isheader():
                forunit = unit

        for engunit in engfile.units:
            # This removes the depricated strings:
            if engunit.msgid == []:
                continue

            newunit = engunit.copy()

            if engunit.isheader():
                try:
                    thetargetfile.addunit(forunit)
                except: # If there's no foreign header, use english header
                    thetargetfile.addunit(newunit)
                continue

            # If there is a foreign unit corresponding, merge in its comments
            # and use its msgstr as the new msgstr
            try:
                forunit = key2for[str(engunit.msgid)]
                newunit.msgstr = forunit.msgstr
                newunit.merge(forunit)
            except:
                # If there's no foreign unit, then we simply use a blank string
                newunit.msgstr = []

            # We want to put the english translation as the id and the key as
            # the context
            newunit.msgctxt = engunit.msgid
            if type(engunit.msgstr) == dict:
                newunit.msgid = engunit.msgstr[0]
                newunit.msgid_plural = engunit.msgstr[1]
            else:
                newunit.msgid = engunit.msgstr

            thetargetfile.addunit(newunit)

        return thetargetfile


def convertpo(inputfile, outputfile, templatefile):
    """reads in stdin using fromfileclass, converts using convertorclass,
    writes to stdout"""
    engstore = po.pofile(inputfile)
    forstore = po.pofile(templatefile)
    convertor = amo2po()
    outputstore = convertor.convertstore(engstore, forstore)
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
    parser = convert.ConvertOptionParser(formats, usetemplates=True,
                                         description=__doc__)
    parser.run(argv)


if __name__ == '__main__':
    main()
