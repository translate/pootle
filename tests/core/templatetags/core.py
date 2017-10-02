# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.templatetags.core import map_to_lengths


def test_map_to_length_empty_list():
    assert map_to_lengths([]) == []


def test_map_to_length_one_element():
    assert map_to_lengths(['foo']) == [3]


def test_map_to_length_multiple_elements():
    assert map_to_lengths(['foobar', 'foo', 'f']) == [6, 3, 1]
