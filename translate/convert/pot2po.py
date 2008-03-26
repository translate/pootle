#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2004-2007 Zuza Software Foundation
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

"""convert Gettext PO templates (.pot) to PO localization files, preserving existing translations

See: http://translate.sourceforge.net/wiki/toolkit/pot2po for examples and 
usage instructions
"""

from translate.storage import po
from translate.storage import factory
from translate.search import match
from translate.misc.multistring import multistring

# We don't want to reinitialise the TM each time, so let's store it here.
tmmatcher = None

def memory(tmfiles, max_candidates=1, min_similarity=75, max_length=1000):
    """Returns the TM store to use. Only initialises on first call."""
    global tmmatcher
    # Only initialise first time
    if tmmatcher is None:
        if isinstance(tmfiles, list):
            tmstore = [factory.getobject(tmfile) for tmfile in tmfiles]
        else:
            tmstore = factory.getobject(tmfiles)
        tmmatcher = match.matcher(tmstore, max_candidates=max_candidates, min_similarity=min_similarity, max_length=max_length)
    return tmmatcher

def convertpot(inputpotfile, outputpofile, templatepofile, tm=None, min_similarity=75, fuzzymatching=True, **kwargs):
    """reads in inputpotfile, adjusts header, writes to outputpofile. if templatepofile exists, merge translations from it into outputpofile"""
    inputpot = po.pofile(inputpotfile)
    inputpot.makeindex()
    thetargetfile = po.pofile()
    # header values
    charset = "UTF-8"
    encoding = "8bit"
    project_id_version = None
    pot_creation_date = None
    po_revision_date = None
    last_translator = None
    language_team = None
    mime_version = None
    plural_forms = None
    kwargs = {}
    if templatepofile is not None:
        templatepo = po.pofile(templatepofile)
        fuzzyfilematcher = None
        if fuzzymatching:
            for unit in templatepo.units:
                if unit.isobsolete():
                    unit.resurrect()
            try:
                fuzzyfilematcher = match.matcher(templatepo, max_candidates=1, min_similarity=min_similarity, max_length=1000, usefuzzy=True)
                fuzzyfilematcher.addpercentage = False
            except ValueError:
                # Probably no usable units
                pass

        templatepo.makeindex()
        templateheadervalues = templatepo.parseheader()
        for key, value in templateheadervalues.iteritems():
            if key == "Project-Id-Version":
                project_id_version = value
            elif key == "Last-Translator":
                last_translator = value
            elif key == "Language-Team":
                language_team = value
            elif key == "PO-Revision-Date":
                po_revision_date = value
            elif key in ("POT-Creation-Date", "MIME-Version"):
                # don't know how to handle these keys, or ignoring them
                pass
            elif key == "Content-Type":
                kwargs[key] = value
            elif key == "Content-Transfer-Encoding":
                encoding = value
            elif key == "Plural-Forms":
                plural_forms = value
            else:
                kwargs[key] = value
    fuzzyglobalmatcher = None
    if fuzzymatching and tm:
        fuzzyglobalmatcher = memory(tm, max_candidates=1, min_similarity=min_similarity, max_length=1000)
        fuzzyglobalmatcher.addpercentage = False
    inputheadervalues = inputpot.parseheader()
    for key, value in inputheadervalues.iteritems():
        if key in ("Project-Id-Version", "Last-Translator", "Language-Team", "PO-Revision-Date", "Content-Type", "Content-Transfer-Encoding", "Plural-Forms"):
            # want to carry these from the template so we ignore them
            pass
        elif key == "POT-Creation-Date":
            pot_creation_date = value
        elif key == "MIME-Version":
            mime_version = value
        else:
            kwargs[key] = value
    targetheader = thetargetfile.makeheader(charset=charset, encoding=encoding, project_id_version=project_id_version,
        pot_creation_date=pot_creation_date, po_revision_date=po_revision_date, last_translator=last_translator,
        language_team=language_team, mime_version=mime_version, plural_forms=plural_forms, **kwargs)
    # Get the header comments and fuzziness state
    if templatepofile is not None and len(templatepo.units) > 0:
        if templatepo.units[0].isheader():
            if templatepo.units[0].getnotes("translator"):
                targetheader.addnote(templatepo.units[0].getnotes("translator"), "translator")
            if inputpot.units[0].getnotes("developer"):
                targetheader.addnote(inputpot.units[0].getnotes("developer"), "developer")
            targetheader.markfuzzy(templatepo.units[0].isfuzzy())
    elif inputpot.units[0].isheader():
        targetheader.addnote(inputpot.units[0].getnotes())
    thetargetfile.addunit(targetheader)
    # Do matching
    for inputpotunit in inputpot.units:
        if not (inputpotunit.isheader() or inputpotunit.isobsolete()):
            if templatepofile:
                possiblematches = []
                for location in inputpotunit.getlocations():
                    templatepounit = templatepo.locationindex.get(location, None)
                    if templatepounit is not None:
                        possiblematches.append(templatepounit)
                if len(inputpotunit.getlocations()) == 0:
                    templatepounit = templatepo.findunit(inputpotunit.source)
                if templatepounit:
                    possiblematches.append(templatepounit)
                for templatepounit in possiblematches:
                    if inputpotunit.source == templatepounit.source and templatepounit.target:
                        inputpotunit.merge(templatepounit, authoritative=True)
                        break
                else:
                    fuzzycandidates = []
                    if fuzzyfilematcher:
                        fuzzycandidates = fuzzyfilematcher.matches(inputpotunit.source)
                        if fuzzycandidates:
                            inputpotunit.merge(fuzzycandidates[0])
                            original = templatepo.findunit(fuzzycandidates[0].source)
                            if original:
                                original.reused = True
                    if fuzzyglobalmatcher and not fuzzycandidates:
                        fuzzycandidates = fuzzyglobalmatcher.matches(inputpotunit.source)
                        if fuzzycandidates:
                            inputpotunit.merge(fuzzycandidates[0])
            else:
                if fuzzyglobalmatcher:
                    fuzzycandidates = fuzzyglobalmatcher.matches(inputpotunit.source)
                    if fuzzycandidates:
                        inputpotunit.merge(fuzzycandidates[0])
            if inputpotunit.hasplural() and len(inputpotunit.target) == 0:
                # Let's ensure that we have the correct number of plural forms:
                nplurals, plural = thetargetfile.getheaderplural()
                if nplurals and nplurals.isdigit() and nplurals != '2':
                    inputpotunit.target = multistring([""]*int(nplurals))
            thetargetfile.addunit(inputpotunit)

    #Let's take care of obsoleted messages
    if templatepofile:
        newlyobsoleted = []
        for unit in templatepo.units:
            if unit.isheader():
                continue
            if unit.target and not (inputpot.findunit(unit.source) or hasattr(unit, "reused")):
                #not in .pot, make it obsolete
                unit.makeobsolete()
                newlyobsoleted.append(unit)
            elif unit.isobsolete():
                thetargetfile.addunit(unit)
        for unit in newlyobsoleted:
            thetargetfile.addunit(unit)
    outputpofile.write(str(thetargetfile))
    return 1

def main(argv=None):
    from translate.convert import convert
    formats = {"pot": ("po", convertpot), ("pot", "po"): ("po", convertpot)}
    parser = convert.ConvertOptionParser(formats, usepots=True, usetemplates=True, 
        allowmissingtemplate=True, description=__doc__)
    parser.add_option("", "--tm", dest="tm", default=None,
        help="The file to use as translation memory when fuzzy matching")
    parser.passthrough.append("tm")
    defaultsimilarity = 75
    parser.add_option("-s", "--similarity", dest="min_similarity", default=defaultsimilarity,
        type="float", help="The minimum similarity for inclusion (default: %d%%)" % defaultsimilarity)
    parser.passthrough.append("min_similarity")
    parser.add_option("--nofuzzymatching", dest="fuzzymatching", action="store_false", 
        default=True, help="Disable fuzzy matching")
    parser.passthrough.append("fuzzymatching")
    parser.run(argv)


if __name__ == '__main__':
    main()
