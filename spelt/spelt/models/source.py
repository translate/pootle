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

from spelt.common import _

from spelt.models.xml_model import XMLModel


class Source(XMLModel):
    """
    This class represents a source for a word
    """

    # CONSTRUCTORS #
    def __init__(self, name=None, filename=None, desc=None, id=0, date=None, import_user_id=0, elem=None):
        """Constructor.
            @type  name:           basestring
            @param name:           The source's name (default None).
            @type  filename:       basestring
            @param filename:       The filename of the source (default None).
            @type  desc:           basestring
            @param desc:           Description (default None).
            @type  id:             int
            @param id:             ID from XML file (default None).
            @type  date:           datetime.datetime
            @param date:           A timestamp string representing the date the source was added (default None).
            @type  import_user_id: int
            @param import_user_id: The ID of the user that imported the source (right? (default None).
            """
        super(Source, self).__init__(
            tag='source',
            attribs=['id', 'date', 'import_user_id'],
            values=['name', 'filename', 'description'],
            elem=elem
        )

        # Check that date is a valid timestamp
        if date is None:
            date = datetime.now()

        if elem is None:
            self.name           = name
            self.filename       = filename
            self.description    = desc
            self.date           = date
            self.import_user_id = import_user_id
            self.id             = id
        else:
            if not hasattr(self, 'name'):
                self.name = name
            if not hasattr(self, 'filename'):
                self.filename = filename
            if not hasattr(self, 'description'):
                self.description = desc
            if not hasattr(self, 'id'):
                self.id = id
            else:
                # Make sure that the ID is registered with the ID manager.
                self.id = self.id
            if not hasattr(self, 'date'):
                self.date = date
            if not hasattr(self, 'import_user_id'):
                self.import_user_id = import_user_id

    # METHODS #
    def validate_data(self):
        """See XMLModel.validate_data()."""
        assert len(self.name) > 0
        assert isinstance(self.id, int)
        assert isinstance(self._date, datetime) and len(self.date) > 0
        assert isinstance(self.import_user_id, int)

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

        super(Source, self).__setattr__(name, value)
