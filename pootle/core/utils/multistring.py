# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from translate.misc.multistring import multistring


SEPARATOR = "__%$%__%$%__%$%__"
PLURAL_PLACEHOLDER = "__%POOTLE%_$NUMEROUS$__"


def list_empty(strings):
    """Check if list is exclusively made of empty strings.

    useful for detecting empty multistrings and storing them as a
    simple empty string in db.
    """
    for string in strings:
        if len(string) > 0:
            return False
    return True


def parse_multistring(db_string):
    """Parses a `db_string` coming from the DB into a multistring object."""
    if not isinstance(db_string, basestring):
        raise ValueError('Parsing into a multistring requires a string input.')

    strings = db_string.split(SEPARATOR)
    if strings[-1] == PLURAL_PLACEHOLDER:
        strings = strings[:-1]
        plural = True
    else:
        plural = len(strings) > 1
    ms = multistring(strings, encoding="UTF-8")
    ms.plural = plural
    return ms


def unparse_multistring(values):
    """Converts a `values` multistring object or a list of strings back to the
    in-DB multistring representation.
    """
    if not (isinstance(values, multistring) or isinstance(values, list)):
        return values

    try:
        values_list = list(values.strings)
        has_plural_placeholder = getattr(values, 'plural', False)
    except AttributeError:
        values_list = values
        has_plural_placeholder = False

    if list_empty(values_list):
        return ''

    if len(values_list) == 1 and has_plural_placeholder:
        values_list.append(PLURAL_PLACEHOLDER)

    return SEPARATOR.join(values_list)
