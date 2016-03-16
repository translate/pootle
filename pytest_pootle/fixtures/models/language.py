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
    if created:
        language.save()
    return language


@pytest.fixture(scope="session")
def english():
    """Require the English language."""
    from pootle_language.models import Language
    return Language.objects.get(code="en")


@pytest.fixture
def templates():
    """Require the special Templates language."""
    return _require_language("templates", "Templates")


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
    """Require the Italian language."""
    return _require_language('it', 'Italian')


@pytest.fixture
def russian(english):
    """Require the Russian language."""
    return _require_language('ru', 'Russian')


# due to issues with tests not having a clean slate ie:
# (https://github.com/translate/pootle/issues/3898)
# please do not use the klingon fixtures 8)
@pytest.fixture
def klingon(english):
    """Require the Klingon language."""
    return _require_language('kl', 'Klingon')


@pytest.fixture
def klingon_vpw(english):
    """Require the Klingon language (VPW dialect)."""
    return _require_language('kl_VPW', 'Klingon vegan peace warriors')
