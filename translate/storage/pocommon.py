#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2002-2007 Zuza Software Foundation
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

from translate.storage import base
from translate.storage import poheader

class pounit(base.TranslationUnit):

    def adderror(self, errorname, errortext):
        """Adds an error message to this unit."""
        text = u'(pofilter) %s: %s' % (errorname, errortext)
        # Don't add the same error twice:
        if text not in self.getnotes(origin='translator'):
            self.addnote(text, origin="translator")

    def geterrors(self):
        """Get all error messages."""
        notes = self.getnotes(origin="translator").split('\n')
        errordict = {}
        for note in notes:
            if '(pofilter) ' in note:
                error = note.replace('(pofilter) ', '')
                errorname, errortext = error.split(': ')
                errordict[errorname] = errortext
        return errordict

    def markreviewneeded(self, needsreview=True, explanation=None):
        """Marks the unit to indicate whether it needs review. Adds an optional explanation as a note."""
        if needsreview:
            reviewnote = "(review)"
            if explanation:
                reviewnote += " " + explanation
            self.addnote(reviewnote, origin="translator")
        else:
            # Strip (review) notes.
            notestring = self.getnotes(origin="translator")
            notes = notestring.split('\n')
            newnotes = []
            for note in notes:
                if not '(review)' in note:
                    newnotes.append(note)
            newnotes = '\n'.join(newnotes)
            self.removenotes()
            self.addnote(newnotes, origin="translator")

class pofile(base.TranslationStore, poheader.poheader):
    Name = "Gettext PO file"
    Mimetypes  = ["text/x-gettext-catalog", "text/x-gettext-translation", "text/x-po", "text/x-pot"]
    Extensions = ["po", "pot"]

    def makeheader(self, **kwargs):
        """create a header for the given filename. arguments are specially handled, kwargs added as key: value
        pot_creation_date can be None (current date) or a value (datetime or string)
        po_revision_date can be None (form), False (=pot_creation_date), True (=now), or a value (datetime or string)"""

        headerpo = self.UnitClass(encoding=self._encoding)
        headerpo.markfuzzy()
        headerpo.source = ""
        headeritems = self.makeheaderdict(**kwargs)
        headervalue = ""
        for (key, value) in headeritems.items():
            headervalue += "%s: %s\n" % (key, value)
        headerpo.target = headervalue
        return headerpo
