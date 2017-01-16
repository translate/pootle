# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_app.forms import LanguageForm


@pytest.mark.parametrize('specialchars', [
    ' ',
    ' abcde ',
    ' ab cd',
    ' abcde',
    'abcde ',
    ' a b c d e ',
    ' a b c d e ',
])
@pytest.mark.django_db
def test_clean_specialchars_whitespace(specialchars):
    """Tests whitespace is accepted in special characters."""
    form_data = {
        'code': 'foo',
        'fullname': 'Foo',
        'checkstyle': 'foo',
        'nplurals': '2',
        'specialchars': specialchars,
    }
    form = LanguageForm(form_data)
    assert form.is_valid()
    assert ' ' in form.cleaned_data['specialchars']


@pytest.mark.parametrize('specialchars, count_char', [
    (' abcde     ', ' '),
    (' aaaaaaaaaa', 'a'),
    ('āéĩøøøøøøü', u'ø'),
])
@pytest.mark.django_db
def test_clean_specialchars_unique(specialchars, count_char):
    """Tests special characters are unique."""
    form_data = {
        'code': 'foo',
        'fullname': 'Foo',
        'checkstyle': 'foo',
        'nplurals': '2',
        'specialchars': specialchars,
    }
    form = LanguageForm(form_data)
    assert form.is_valid()
    assert form.cleaned_data['specialchars'].count(count_char) == 1


@pytest.mark.django_db
def test_specialchars_can_be_blank():
    """Test that a blank special character field is valid."""
    form_data = {
        'code': 'foo',
        'fullname': 'Foo',
        'checkstyle': 'foo',
        'nplurals': '2',
        'specialchars': '',
    }
    form = LanguageForm(form_data)
    assert form.is_valid()
    assert form.cleaned_data['specialchars'] == ''
