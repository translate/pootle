#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
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


def make_method_key(model, method, key):
    """Creates a cache key for model's `method` method.

    :param model: A model instance
    :param method: Method name to cache
    :param key: a unique key to identify the object to be cached
    """
    prefix = 'method-cache'
    name = (model.__name__ if hasattr(model, '__name__')
                           else model.__class__.__name__)
    return u':'.join([prefix, name, method, key])
