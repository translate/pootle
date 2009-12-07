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

class User(XMLModel):
    """
    This class represents user from the language database.
    """

    # CONSTRUCTORS #
    def __init__(self, name='<unknown>', id=0, elem=None):
        """Constructor.
            @type  name: basestring
            @param name: User's name (default None)
            @type  id: int
            @param id: The user's unique identifier (default None)
            """
        assert name is None or isinstance(name, basestring)
        assert isinstance(id, int)

        super(User, self).__init__(tag='user', values=['name'], attribs=['id'], elem=elem)

        if elem is None:
            self.name = name
            self.id   = id
        else:
            if not hasattr(self, 'name'):
                self.name = name
            if not hasattr(self, 'id'):
                self.id = id
            else:
                # Make sure that the ID is registered with the ID manager.
                self.id = self.id

    # METHODS #
    def validate_data(self):
        """See XMLModel.validate_data()."""
        assert isinstance(self.id, int)
        assert isinstance(unicode(self.name), basestring) and len(unicode(self.name)) > 0

    # SPECIAL METHODS #
    def __eq__(self, rhs):
        return self.id == rhs.id

    def __hash__(self):
        return self.id
