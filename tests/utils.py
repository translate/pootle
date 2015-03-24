#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Random utilities for tests."""


def formset_dict(data):
    """Convert human readable POST dictionary into brain dead django
    formset dictionary.
    """
    new_data = {
        'form-TOTAL_FORMS': len(data),
        'form-INITIAL_FORMS': 0,
    }

    for i in range(len(data)):
        for key, value in data[i].iteritems():
            new_data["form-%d-%s" % (i, key)] = value

    return new_data


def items_equal(left, right):
    """Returns `True` if items in `left` list are equal to items in
    `right` list.
    """
    try:
        return sorted(left) == sorted(right)
    except TypeError:  # non-iterable
        return False
