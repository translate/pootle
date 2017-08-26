# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Fields required for handling translation files"""

from translate.misc.multistring import multistring

from django.db import models

from pootle.core.utils.multistring import (parse_multistring,
                                           unparse_multistring)


# # # # # # # # # String # # # # # # # # # # # # # # #


def to_db(value):
    """Flatten the given value (string, list of plurals or multistring) into
    the database string representation.
    """
    if value is None:
        return None

    return unparse_multistring(value)


def to_python(value):
    """Reconstruct a multistring from the database string representation."""
    if not value:
        return multistring("", encoding="UTF-8")
    elif isinstance(value, multistring):
        return value
    elif isinstance(value, basestring):
        return parse_multistring(value)
    elif isinstance(value, dict):
        return multistring([val for __, val in sorted(value.items())],
                           encoding="UTF-8")
    else:
        return multistring(value, encoding="UTF-8")


class CastOnAssignDescriptor(object):
    """
    A property descriptor which ensures that `field.to_python()` is called on
    _every_ assignment to the field.  This used to be provided by the
    `django.db.models.subclassing.Creator` class, which in turn was used by the
    deprecated-in-Django-1.10 `SubfieldBase` class, hence the reimplementation
    here.
    """

    def __init__(self, field):
        self.field = field

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return obj.__dict__[self.field.name]

    def __set__(self, obj, value):
        obj.__dict__[self.field.name] = self.field.to_python(value)


class MultiStringField(models.Field):
    description = \
        "a field imitating translate.misc.multistring used for plurals"

    def __init__(self, *args, **kwargs):
        super(MultiStringField, self).__init__(*args, **kwargs)

    def get_internal_type(self):
        return "TextField"

    def to_python(self, value):
        return to_python(value)

    def from_db_value(self, value, expression, connection, context):
        return to_python(value)

    def get_prep_value(self, value):
        return to_db(value)

    def get_prep_lookup(self, lookup_type, value):
        if (lookup_type in ('exact', 'iexact') or
            not isinstance(value, basestring)):
            value = self.get_prep_value(value)
        return super(MultiStringField, self).get_prep_lookup(lookup_type,
                                                             value)

    def contribute_to_class(self, cls, name):
        super(MultiStringField, self).contribute_to_class(cls, name)
        setattr(cls, name, CastOnAssignDescriptor(self))
