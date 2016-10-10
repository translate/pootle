# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from translate.misc.multistring import multistring

from pootle.core.utils.multistring import (PLURAL_PLACEHOLDER, SEPARATOR,
                                           parse_multistring)


@pytest.mark.parametrize('invalid_value', [None, [], (), 69, 69L])
def test_parse_multistring_invalid(invalid_value):
    """Tests parsing doesn't support non-string values"""
    with pytest.raises(ValueError):
        parse_multistring(invalid_value)


@pytest.mark.parametrize('db_string, expected_ms, is_plural', [
    ('foo bar', multistring('foo bar'), False),
    ('foo%s' % SEPARATOR, multistring(['foo', '']), True),
    ('foo%s%s' % (SEPARATOR, PLURAL_PLACEHOLDER), multistring('foo'), True),
    ('foo%sbar' % SEPARATOR, multistring(['foo', 'bar']), True),
    ('foo%sbar%sbaz' % (SEPARATOR, SEPARATOR),
     multistring(['foo', 'bar', 'baz']), True),
])
def test_parse_multistring(db_string, expected_ms, is_plural):
    parsed_ms = parse_multistring(db_string)
    assert parsed_ms == expected_ms
    assert parsed_ms.plural == is_plural
