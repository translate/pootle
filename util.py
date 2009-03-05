#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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

"""Some code helpers."""

undefined = lambda: None

def lazy(result_name):
    """This is used to create an attribute whose value is
    lazily computed. The parameter names an object variable that
    will be used to hold the lazily computed value. At the start,
    this variable should hold the value undefined.

    TODO: Replace this with a nice Python descriptor.

    class Person(object):
        def __init__(self):
            self.name = 'John'
            self.surname = 'Doe'
            self._fullname = undefined

        @lazy('_fullname')
        def _get_fullname(self):
            return self.name + ' ' + self.surname
    """

    def lazify(f):
        def evaluator(self):
          result = getattr(self, result_name)
          if result is not undefined:
            return result
          else:
            setattr(self, result_name, f(self))
            return getattr(self, result_name)
        return evaluator
    return lazify
