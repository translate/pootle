# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

import pytest


JSON_OBJECTS = (
    3,
    "four",
    u"five ☠ ",
    "six \n seven ",
    [9, 10],
    (11, 12, 13),
    OrderedDict(foo="bar", foo2="baz"),
    [1, "two", OrderedDict(three=3)])


@pytest.fixture(params=JSON_OBJECTS)
def json_objects(request):
    return request.param
