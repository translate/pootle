#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

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
def french(english):
    """Require the French language."""
    return _require_language('fr', 'French')


@pytest.fixture
def spanish(english):
    """Require the Spanish language."""
    return _require_language('es', 'Spanish')


@pytest.fixture
def italian(english):
    """Require the Spanish language."""
    return _require_language('it', 'Italian')


@pytest.fixture
def russian(english):
    """Require the Russian language."""
    return _require_language('ru', 'Russian')


@pytest.fixture
def fish(english):
    """Require the Fish language ><(((º>"""
    return _require_language(code='fish', fullname='Fish')
