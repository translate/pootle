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

from spelt.common            import _
from spelt.common.exceptions import *

class IDManager(object):
    """
    This class contains some helper-methods to manage its _id member. It
    maintains a list of used ID's and also the maximum ID used so far. It's
    a very good idea to call del_id() when an instance dies to free up the
    ID it used.

    It turns out this class adds a house-of-cards effect to the models. Don't
    mess with ID's unless you think you have to. HERE BE DRAGONS.
    """

    # ACCESSORS #
    def _set_id(self, v):
        if self._id > 0:
            self.__class__.del_id(self._id)
            self._id = self.__class__.get_id(v)
        else:
            self._id = self.__class__.get_id(v, strict=False)

    id = property(lambda self: self._id, _set_id)

    # CONSTRUCTOR #
    def __init__(self):
        if not hasattr(self.__class__, 'ids'):
            self.__class__.ids = set()
        if not hasattr(self.__class__, 'max_id'):
            self.__class__.max_id = 0
        self._id = 0

    def __del__(self):
        self.__class__.del_id(self._id)

    # CLASS/STATIC METHODS #
    @classmethod
    def get_id(cls, requested=None, strict=True):
        """Get a valid ID for this XML model.
            If the preferred (requested) ID is available, it is returned,
            otherwise the lowest integer (> 0) is returned.
            @type  requested: int
            @param requested: The preferred ID.
            @type  strict:    bool
            @param strict:    Whether or not _only_ the requested ID will be
                excepted. If the requested ID is already used, a IDUsedError
                is raised. (Default: True)
            """

        if not requested is None and requested > 0:
            if requested not in cls.ids:
                if requested > cls.max_id:
                    cls.max_id = requested
                cls.ids.add(requested)
                return requested
            elif strict:
                raise IDUsedError(str(requested))

        cls.max_id += 1
        cls.ids.add(cls.max_id)
        return cls.max_id

    @classmethod
    def del_id(cls, id, strict=False):
        if not id in cls.ids:
            if strict:
                raise UnknownIDError(str(id))
            else:
                return

        cls.ids.remove(id)

        if id == cls.max_id:
            cls.max_id -= 1

    @classmethod
    def is_used_id(cls, id):
        return id in cls.ids
