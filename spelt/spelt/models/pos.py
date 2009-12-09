#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of Spelt.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from lxml import objectify

from spelt.models.xml_model import XMLModel

class PartOfSpeech(XMLModel):
    """
    This class represents a part-of-speech section from the language database.
    """

    # CONSTRUCTORS #
    def __init__(self, name=None, shortcut=None, remarks=None, id=0, elem=None):
        """Constructor.
            @type  name:     basestring
            @param name:     Name of the part-of-spe (default None)
            @type  shortcut: basestring
            @param shortcut: Keyboard shortcut or abbreviation (default None)
            @type  remarks:  basestring
            @param remarks:  Remarks for use by the end-user (default None)
            @type  id:       int
            @param id:       Unique identifier of this part-of-speech (default None)
            """
        assert name is None or isinstance(name, basestring)
        assert shortcut is None or isinstance(shortcut, basestring)
        assert remarks is None or isinstance(remarks, basestring)
        assert isinstance(id, int)

        super(PartOfSpeech, self).__init__(
            tag='part_of_speech',
            values=['name', 'shortcut', 'remarks'],
            attribs=['id'],
            elem=elem
        )

        if elem is None:
            self.name = name
            self.shortcut = shortcut
            self.remarks = remarks
            self.id = id
        else:
            if not hasattr(self, 'name'):
                self.name = name
            if not hasattr(self, 'shortcut'):
                self.shortcut = shortcut
            if not hasattr(self, 'remarks'):
                self.remarks = remarks
            if not hasattr(self, 'id'):
                self.id = id
            else:
                # Make sure that the ID is registered with the ID manager.
                self.id = self.id

    # METHODS #
    def validate_data(self):
        """See XMLModel.validate_data()."""
        assert len(self.name) > 0
        assert self.shortcut is None or len(self.shortcut) > 0
        assert isinstance(self.id, int)

    # SPECIAL METHODS #
    def __eq__(self, rhs):
        return self.id == rhs.id

    def __hash__(self):
        return self.id
