# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import call_command
from django.db.models import Min

from pootle.core.models import Revision


@pytest.mark.cmd
@pytest.mark.django_db
def test_changed_languages_noargs(capfd, afrikaans_tutorial, french_tutorial):
    """Get changed languages since last sync."""
    call_command('changed_languages')
    out, err = capfd.readouterr()
    assert "(no known changes)" in err
    revision = Revision.get()
    assert (
        ("Will show languages changed between revisions %d (exclusive) and "
         "%d (inclusive)"
         % (revision, revision))
        in err)


@pytest.mark.cmd
@pytest.mark.django_db
def test_changed_languages_since_revision(capfd, afrikaans_tutorial,
                                          french_tutorial):
    """Changed languages since a given revision"""
    # Everything
    rev = afrikaans_tutorial.stores.aggregate(
        rev=Min('last_sync_revision'))['rev'] - 1
    call_command('changed_languages', '--after-revision=%s' % rev)
    out, err = capfd.readouterr()
    assert "af,fr" in out
    # End revisions
    rev = french_tutorial.stores.aggregate(
        rev=Min('last_sync_revision'))['rev'] - 1
    call_command('changed_languages', '--after-revision=%s' % rev)
    out, err = capfd.readouterr()
    assert "af" not in out
    assert "fr" in out
