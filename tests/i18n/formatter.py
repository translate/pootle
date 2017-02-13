# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest
from babel.support import Format

from django.utils.translation import override

from pootle.i18n.formatter import (_clean_zero, get_locale_formats, number,
                                   percent)


@pytest.mark.parametrize('language', [
    'af', 'en-za', 'en-us',  # Normal
    'son',  # Missing in babel
])
def test_get_locale_formats(language):
    with override(language):
        assert isinstance(get_locale_formats(), Format)


def test__clean_zero():
    assert _clean_zero(None) == 0
    assert _clean_zero('') == 0
    assert _clean_zero(0) == 0
    assert _clean_zero(3.1415) == 3.1415


@pytest.mark.parametrize('language, expected', [
    ('en-gb', '1,000.5'),  # Normal
    ('gl', '1.000,5'),  # Galician (inverted wrt en-us)
    ('af-za', u'1\u00a0000,5'),  # Major difference
    ('son', '1,000.5'),  # Missing
])
def test_number(language, expected):
    with override(language):
        assert number('1000.5') == expected


@pytest.mark.parametrize('language, expected', [
    ('en-gb', '1,000%'),  # Normal
    ('gl', '1.000%'),  # Galician (inverted wrt en-us)
    ('af-za', u'1\u00a0000%'),  # Major difference
    ('son', '1,000%'),  # Missing
])
def test_percent(language, expected):
    with override(language):
        assert percent(10.005) == expected


@pytest.mark.parametrize('language, expected', [
    ('en-gb', '1,000.5%'),  # Normal
    ('gl', '1.000,5%'),  # Galician (inverted wrt en-us)
    ('af-za', u'1\u00a0000,5%'),  # Major difference
    ('son', '1,000.5%'),  # Missing
])
def test_percent_format(language, expected):
    with override(language):
        assert percent(10.005, '#,##0.0%') == expected
