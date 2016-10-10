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
