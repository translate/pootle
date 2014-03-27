#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

"""Language fixtures.

NOTE: when adding new language fixtures, it should require the
``english`` fixture first, otherwise the behavior can be unpredicted when
creating projects and translation projects later on.
"""

import pytest


def _require_language(code, fullname, plurals=2, plural_equation='(n != 1)'):
    """Helper to get/create a new language."""
    from pootle_language.models import Language

    criteria = {
        'code': code,
        'fullname': fullname,
        'nplurals': plurals,
        'pluralequation': plural_equation,
    }
    language, created = Language.objects.get_or_create(**criteria)

    return language


@pytest.fixture
def english(root):
    """Require the English language."""
    return _require_language('en', 'English')


@pytest.fixture
def templates(root):
    """Require the special Templates language."""
    return _require_language('templates', 'Templates')


@pytest.fixture
def afrikaans(english):
    """Require the Afrikaans language."""
    return _require_language('af', 'Afrikaans')


@pytest.fixture
def arabic(english):
    """Require the Arabic language."""
    return _require_language('ar', 'Arabic')


@pytest.fixture
def fish(english):
    """Require the Fish language ><(((º>"""
    return _require_language(code='fish', fullname='Fish')
