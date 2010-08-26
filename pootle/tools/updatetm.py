#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2006 Zuza Software Foundation
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

"""Tool to write the .tm files for Pootle to use"""

from translate.storage import factory
from translate.search import match
from translate.convert import convert
import os.path
import exceptions

# We don't want to reinitialise the TM each time, so let's store it here.
tmmatcher = None

def memory(tmfile, max_candidates=4, min_similarity=75, max_length=1000):
    """Returns the TM store to use. Only initialises on first call."""
    global tmmatcher
    # Only initialise first time
    if tmmatcher is None:
        tmstore = factory.getobject(tmfile)
        tmmatcher = match.matcher(tmstore, max_candidates=max_candidates, min_similarity=min_similarity, max_length=max_length)
    return tmmatcher

def buildmatches(inputfile, outputfile, matcher):
    """Builds a .po.tm file for use in Pootle"""
    #Can't use the same name: it might open the existing file!
    outputfile = factory.getobject(outputfile, ignore=".tm")
    #TODO: Do something useful with current content if file exists

    #inputfile.units.sort(match.sourcelen)
    try:
        for unit in inputfile.units:
            #if len(unit.source) > 70:
            #    break
            if not unit.source:
                continue
            candidates = matcher.matches(unit.source)
            for candidate in candidates:
                source = candidate.source
                target = candidate.target
                newunit = outputfile.addsourceunit(source)
                newunit.target = target
                newunit.addnote(candidate.getnotes())
                newunit.addlocations(unit.getlocations())
    except exceptions.KeyboardInterrupt:
        # Let's write what we have so far
        return outputfile
    return outputfile

def writematches(inputfile, outputfile, templatefile, tm=None, max_candidates=4, min_similarity=75, max_length=1000):
    if templatefile:
        raise Warning("Template ignored")
    inputfile = factory.getobject(inputfile)
    if tm is None:
        raise ValueError("Must have TM storage specified with --tm")
    int_max_candidates = int(max_candidates)
    int_min_similarity = int(min_similarity)
    matcher = memory(tm, max_candidates=int_max_candidates, min_similarity=int_min_similarity, max_length=max_length)
    output = buildmatches(inputfile, outputfile, matcher)
    outputfile.writelines(str(output))
    return 1

def main(argv=None):
    formats = {"po": ("po.tm", writematches)}
    parser = convert.ConvertOptionParser(formats, usetemplates=False, description=__doc__)
    parser.add_option("-t", "--tm", dest="tm", default=None,
        help="The file to use as translation memory")
    parser.passthrough.append("tm")
    parser.add_option("-c", "--candidates", dest="max_candidates", default=4,
        help="The maximum number of TM candidates to store per message")
    parser.passthrough.append("max_candidates")
    parser.add_option("-s", "--similarity", dest="min_similarity", default=75,
        help="The minimum similarity for inclusion")
    parser.passthrough.append("min_similarity")
    parser.add_option("", "--length", dest="max_length", default=1000,
        help="The maximum string length to consider")
    parser.passthrough.append("min_similarity")
    parser.run(argv)
