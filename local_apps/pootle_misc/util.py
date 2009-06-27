#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2009 Zuza Software Foundation
#
# This file is part of Pootle.
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

from django.core.cache import cache
import logging

def getfromcache(function):
    def _getfromcache(self, *args, **kwargs):
        key = self.pootle_path + ":" + function.__name__
        result = cache.get(key)
        if result is None:
            logging.debug("cache miss for %s", key)
            result = function(self, *args, **kwargs)
            cache.set(key, result)
        return result
    return _getfromcache
