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


@pytest.fixture
def english():
    """Require the English language."""
    from pootle_language.models import Language

    return Language.objects.get(code="en")


@pytest.fixture
def templates():
    """Require the special Templates language."""
    from pootle_language.models import Language

    return Language.objects.get(code="templates")


@pytest.fixture
def afrikaans():
    """Require the Afrikaans language."""
    return _require_language('af', 'Afrikaans')


@pytest.fixture
def italian():
    """Require the Italian language."""
    return _require_language('it', 'Italian')


@pytest.fixture
def language0():
    """language0 Language"""
    from pootle_language.models import Language

    return Language.objects.get(code="language0")


@pytest.fixture
def language1():
    """language1 Language"""
    from pootle_language.models import Language

    return Language.objects.get(code="language1")
