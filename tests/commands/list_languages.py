# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import call_command

from pootle_store.models import Unit


@pytest.mark.cmd
@pytest.mark.django_db
def test_list_languages_af_es_fr(capfd, afrikaans_tutorial, spanish_tutorial,
                                 french_tutorial):
    """Full site list of active languages"""
    call_command('list_languages')
    out, err = capfd.readouterr()
    assert 'af' in out
    assert 'es' in out
    assert 'fr' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_list_languages_project(capfd):
    """Languages on a specific project"""
    call_command('list_languages', '--project=project0')
    out, err = capfd.readouterr()
    assert 'language0' in out
    assert 'language1' in out
    assert 'af' not in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_list_languages_modified_since(capfd, afrikaans_tutorial,
                                       spanish_tutorial, french_tutorial):
    """Languages modified since a revision"""
    fr_units = Unit.objects.filter(
        store__translation_project__language=french_tutorial.language)
    fr_revision = max(fr_units.values_list("revision", flat=True))
    call_command('list_languages', '--modified-since=%d' % (fr_revision - 1))
    out, err = capfd.readouterr()
    assert 'af' not in out
    assert 'es' not in out
    assert 'fr' in out
