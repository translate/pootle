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
    """Python descriptor for marshalling GET/POST state into Python
    variables and back.

    The descriptor is given a name (see __init__) which it uses to
    read its state from a dictionary (containing GET/POST variables).

    The descriptor stores its state within the object from which it is
    invoked using its own name prefix with an underscore (so if x is a
    descripor in class Foo, and foo is an instance of Foo, then the
    actual value of x is stored in foo._x). If its state is missing
    from its host object (i.e. if _x is not an attribute of foo), the
    descriptor will return its default value (so foo.x will give a
    default value).

    This is a base class which will marshal strings from and to a
    GET/POST dictionary.

    How-To Guide for descriptors: http://users.rcn.com/python/download/Descriptor.htm
    """
    default_value = None

    def __init__(self, var_name):
        self.var_name = var_name

    def _member_name(self):
        """Return the name that we'll use to store this descriptor's
        data under in its host object. A decriptor foo will have its
        data stored under _foo."""
        return '_' + self.var_name

    def __get__(self, obj, type=None):
        return getattr(obj, self._member_name(), self.default_value)

    def __set__(self, obj, value):
        setattr(obj, self._member_name(), value)

    def __delete__(self, obj):
        delattr(obj, self._member_name())

    def add_to_dict(self, obj, dct):
        """If the descriptor's value is not equal to its default
        value, then encode it to a string and store it in the GET/POST
        dictionary C{dct}."""
        value = self.__get__(obj)
        if value != self.default_value:
            dct[self.var_name] = self._encode(value)

    def read_from_params(self, obj, params):
        """Read the value of this descriptor from the GET/POST
        dictionary C{params}, decode it and use it to set the
        descriptor value."""
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
    """Read a GET/POST variable into an integer. The descriptor's
    default value is supplied when initializing an IntValue. This
    value is used when the descriptor has no state stored in its host
    object or when the GET/POST variable doesn't decode to an integer.

        >>> class Foo(object):
        ...     bar = IntValue('bar', 1)
        >>> foo = Foo()
        >>> foo.bar
        1
        >>> foo.__class__.bar._decode('10')
        10
        >>> foo.__class__.bar._decode('a')
        1
        >>> foo.__class__.bar._encode(20)
        '20'
        >>> foo.__class__.bar.read_from_params(foo, {'bar': '5'})
        >>> foo.bar
        5
        >>> get_vars = {}
        >>> foo.__class__.bar.add_to_dict(foo, get_vars)
        >>> get_vars
        {'bar': '5'}
    """
    def __init__(self, var_name, default_value):
        super(IntValue, self).__init__(var_name)
        self.default_value = default_value

    def _decode(self, value):
        try:
            return int(value)
        except ValueError:
            return self.default_value

    def _encode(self, value):
        assert isinstance(value, int)
        return str(value)

class ChoiceValue(Value):
    """Read a string GET/POST variable ensuring that it matches one of
    the choices specified when constructing this object. If not, set
    this descriptor value to the first choice.

        >>> class Foo(object):
        ...     bar = ChoiceValue('bar', ('chocolate', 'strawberry', 'caramel'))
        >>> foo = Foo()
        >>> foo.__class__.bar._decode('strawberry')
        'strawberry'
        >>> foo.__class__.bar._decode('banana')
        'chocolate'
    """

    def __init__(self, var_name, choices):
        super(ChoiceValue, self).__init__(var_name)
        self.default_value = choices[0]
        self._choices = choices

    def _decode(self, value):
        if value in self._choices:
            return value
        else:
            return self.default_value

    def _encode(self, value):
        if value in self._choices:
            return value
        else:
            return self.default_value

class ListValue(Value):
    """Read a comma separated GET/POST variable into a Python list of
    strings.

        >>> class Foo(object):
        ...     bar = ListValue('bar')
        >>> foo = Foo()
        >>> foo.__class__.bar._decode('a,b,c')
        ['a', 'b', 'c']
        >>> foo.__class__.bar._encode(['a', 'b', 'c'])
        'a,b,c'
        >>> foo.__class__.bar.read_from_params(foo, {'bar': 'x,y,z'})
        >>> foo.bar
        ['x', 'y', 'z']
        >>> get_vars = {}
        >>> foo.__class__.bar.add_to_dict(foo, get_vars)
        >>> get_vars
        {'bar': 'x,y,z'}
    """
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
    """Base class for classes which, using any of the *Value classes
    as descriptors, will read GET or POST variables intelligently.

    To see an example implementation, look for TranslatePageState."""

    def get_descriptors(self):
        """Return a list of all the *Value descriptors (all defined
        above) that are defined in the class of the current object as
        well as its superclasses.

        Thus, if we have the following subclass:

            >>> class FooState(State):
            ...     bar = IntValue('bar', 0)
            ...     baz = ListValue('baz')
            >>> state = FooState()
            >>> sorted(state.get_descriptors())
            ['bar', 'baz']
        """
        return get_descriptors(self.__class__, [], set())

    def iter_items(self):
        """Iterate through all the *Value descriptors returning
        (descriptor name, descriptor value) pairs.

            >>> class FooState(State):
            ...     bar = IntValue('bar', 0)
            ...     baz = ListValue('baz')
            >>> state = FooState(bar=1, baz=['a', 'b', 'c'])
            >>> sorted(list(state.iter_items()))
            [('bar', 1), ('baz', ['a', 'b', 'c'])]
        """
        for member in self.get_descriptors():
            yield member.var_name, getattr(self, member.var_name)

    def as_dict(self):
        return dict(self.iter_items())

    def __init__(self, data={}, **initial):
        """Initialize a state object possibly reading initial state
        from C{data} (which is in raw text) and overriding those
        values with the keyword parameters C{initial} (these
        parameters are not raw, so for an IntValue, you'd pass an
        integer).
        """
        for member in self.get_descriptors():
            member.read_from_params(self, data)
        for key, value in initial.iteritems():
            setattr(self, key, value)

    def encode(self):
        """Encode all the state members in this object to a GET/POST
        dictionary."""
        result = {}
        for member in self.get_descriptors():
            member.add_to_dict(self, result)
        return result
