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

VALID_STATUSES = ('classified', 'ignored', 'rejected', 'todo')

class SurfaceForm(XMLModel):
    """
    This class represents a surface form word (a word with a root).
    """

    # CONSTRUCTORS #
    def __init__(self, value='', status='', id=0, user_id=0, date=None, source_id=0, root_id=0, elem=None):
        """
        Constructor.
            @type  value:     basestring
            @param value:     The surface form word.
            @type  id:        int
            @param id:        A unique identifier for the instance.
            @type  status:    str
            @param status:    The classification status of the surface form word.
            @type  user_id:   int
            @param user_id:   The user that classified the word.
            @type  date:      datetime.datetime
            @param date:      Date of classification.
            @type  source_id: int
            @param source_id: Source associated with this word.
            @type  root_id:   int
            @param root_id:   ID of the root word for this structure.
            """
        assert isinstance(value, basestring)
        assert isinstance(status, str)
        assert isinstance(id, int)
        assert isinstance(user_id, int)
        assert date is None or isinstance(date, datetime)
        assert isinstance(source_id, int)
        assert isinstance(root_id, int)

        super(SurfaceForm, self).__init__(
            tag='surface_form',
            values=['value', 'status'],
            attribs=['id', 'user_id', 'date', 'source_id', 'root_id'],
            elem=elem
        )

        if date is None:
            date = datetime.now()

        if elem is None:
            self.value     = value
            self.status    = status
            self.id        = id
            self.user_id   = user_id
            self.date      = date
            self.source_id = source_id
            self.root_id   = root_id
        else:
            if not hasattr(self, 'value'):
                self.value = value
            if not hasattr(self, 'status'):
                self.status = status
            if not hasattr(self, 'id'):
                self.id = id
            else:
                # Make sure that the ID is registered with the ID manager.
                self.id = self.id
            if not hasattr(self, 'user_id'):
                self.user_id = user_id
            if not hasattr(self, 'date'):
                self.date = date
            if not hasattr(self, 'source_id'):
                self.source_id = source_id
            if not hasattr(self, 'root_id'):
                self.root_id = root_id

    # METHODS #
    def validate_data(self):
        """See XMLModel.validate_data()."""
        assert isinstance(unicode(self.value), basestring) and len(self.value) > 0
        assert isinstance(str(self.status), str)           and self.status in VALID_STATUSES
        assert isinstance(self.id, int)                    and self.id > 0
        assert isinstance(self.user_id, int)               and self.user_id > 0
        assert isinstance(self._date, datetime)
        assert isinstance(self.source_id, int)

    # SPECIAL METHODS #
    def __eq__(self, rhs):
        return hash(self) == hash(rhs)

    def __hash__(self):
        return hash('%s_%s' % (self.value, self.root_id))

    def __setattr__(self, name, value):
        if name == 'date':
            if isinstance(value, datetime):
                value = str(int( time.mktime(value.timetuple()) ))
            elif isinstance(value, int) or isinstance(value, basestring):
                value = str(value)

        super(SurfaceForm, self).__setattr__(name, value)
