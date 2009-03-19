#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2009 Zuza Software Foundation
# 
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

class Value(object):
    default_value = None

    def __init__(self, var_name):
        self.var_name = var_name

    def _member_name(self):
        return '_' + self.var_name

    def __get__(self, obj, type=None):
        return getattr(obj, self._member_name(), self.default_value)

    def __set__(self, obj, value):
        setattr(obj, self._member_name(), value)

    def __delete__(self, obj):
        delattr(obj, self._member_name())

    def add_to_dict(self, obj, dct):
        value = self.__get__(obj)
        if value != self.default_value:
            dct[self.var_name] = self._encode(value)

    def read_from_params(self, obj, params):
        try:
            self.__set__(obj, self._decode(params[self.var_name]))
        except KeyError:
            pass

    def _decode(self, value):
        return value

    def _encode(self, value):
        return value

    def __repr__(self):
        return "Value<%s>" % self.var_name

class BooleanValue(Value):
    default_value = False

    def _decode(self, value):
        if value == 'True':
            return True
        else:
            return False

    def _encode(self, value):
        if value:
            return 'True'
        else:
            return 'False'

class IntValue(Value):
    def __init__(self, var_name, default_value):
        super(IntValue, self).__init__(var_name)
        self.default_value = default_value

    def _decode(self, value):
        try:
            return int(value)
        except ValueError:
            return self.default_value

    def _encode(self, value):
        return str(value)

class ChoiceValue(Value):
    def __init__(self, var_name, choices):
        super(ChoiceValue, self).__init__(var_name)
        self.default_value = choices[0]
        self._choices = choices

    def _decode(self, value):
        if value in self._choices:
            return value
        else:
            return self.default_value

class ListValue(Value):
    default_value = []

    def _decode(self, value):
        if value in ('', None):
            return []
        else:
            return value.split(',')

    def _encode(self, value):
        return ','.join(str(item) for item in value)

def get_descriptors(cls, descriptors, visited):
    """Enumerate a class and all its subclasses in a depth-first post
    order traversal and collect all the Python descriptors into the
    list 'descriptors'"""
    for base in cls.__bases__:
        if base not in visited:
            visited.add(base)
            descriptors = get_descriptors(base, descriptors, visited)
    descriptors.extend(descriptor for descriptor in cls.__dict__.itervalues()
                       if isinstance(descriptor, Value))
    return descriptors

class State(object):
    def get_descriptors(self):
        return get_descriptors(self.__class__, [], set())

    def iter_items(self):
        for member in self.get_descriptors():
            yield member.var_name, getattr(self, member.var_name)

    def as_dict(self):
        return dict(self.iter_items())

    def __init__(self, data={}, **initial):
        for member in self.get_descriptors():
            member.read_from_params(self, data)
        for key, value in initial.iteritems():
            setattr(self, key, value)

    def encode(self):
        result = {}
        for member in self.get_descriptors():
            member.add_to_dict(self, result)
        return result
