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

import time
from datetime import datetime
from lxml     import objectify

from spelt.models.xml_model import XMLModel

class Root(XMLModel):
    """
    This class represents a word root as represented in the XML language database.
    """

    # CONSTRUCTORS #
    def __init__(self, value=None, remarks=None, id=0, pos_id=0, user_id=0, date=None, elem=None):
        """Constructor.

            @type  value:   basestring
            @param value:   The actual word root text
            @type  remarks: basestring
            @param remarks: Arbitrary user remarks
            @type  id:      int
            @param id:      Unique identifier of the word root
            @type  pos_id:  int
            @param pos_id:  The word root's part-of-speech's ID
            @type  user_id: int
            @param user_id: The ID of the user that added/changed the root
            @type  date:    datetime.datetime
            @param date:    The last modification date of the word root
            """
        assert value is None or isinstance(value, basestring)
        assert remarks is None or isinstance(remarks, basestring)
        assert isinstance(id, int)
        assert isinstance(pos_id, int)
        assert isinstance(user_id, int)
        assert date is None or isinstance(date, datetime)

        super(Root, self).__init__(
            tag='root',
            values=['value', 'remarks'],
            attribs=['id', 'pos_id', 'user_id', 'date'],
            elem=elem
        )

        if date is None:
            date = datetime.now()

        if elem is None:
            self.value   = value
            self.remarks = remarks
            self.id      = id
            self.pos_id  = pos_id
            self.user_id = user_id
            if date is not None:
                self.date = date
            else:
                self.date = datetime.now()
        else:
            if not hasattr(self, 'value'):
                self.value = value
            if not hasattr(self, 'remarks'):
                self.remarks = remarks
            if not hasattr(self, 'id'):
                self.id = id
            else:
                # Make sure that the ID is registered with the ID manager.
                self.id = self.id
            if not hasattr(self, 'pos_id'):
                self.pos_id = pos_id
            if not hasattr(self, 'user_id'):
                self.user_id = user_id
            if not hasattr(self, 'date'):
                self.date = date


    # METHODS #
    def validate_data(self):
        """See XMLModel.validate_data()."""
        assert len(self.value) > 0
        assert self.remarks is None or isinstance(self.remarks, basestring) or isinstance(self.remarks, objectify.NoneElement)
        assert isinstance(self.id, int)
        assert isinstance(self.pos_id, int)
        assert isinstance(self.user_id, int)
        assert isinstance(self._date, datetime)

    # SPECIAL METHODS #
    def __eq__(self, rhs):
        return self.id == rhs.id

    def __hash__(self):
        return self.id

    def __setattr__(self, name, value):
        if name == 'date':
            if isinstance(value, datetime):
                value = str(int( time.mktime(value.timetuple()) ))
            elif isinstance(value, int) or isinstance(value, basestring):
                value = str(value)

        super(Root, self).__setattr__(name, value)
