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
def test_changed_languages_noargs(capfd):
    """Get changed languages since last sync."""
    revision = Revision.get()
    call_command('changed_languages')
    out, err = capfd.readouterr()
    assert out == u'language0,language1,templates\n'
    assert (
        ("Will show languages changed between revisions -1 (exclusive) and "
         "%d (inclusive)"
         % (revision))
        in err)


@pytest.mark.cmd
@pytest.mark.django_db
def test_changed_languages_noargs_nochanges(capfd, project0_nongnu, store0):
    """Get changed languages since last sync."""
    unit = store0.units.first()
    unit.target = "CHANGED"
    unit.save()
    store0.sync()
    revision = Revision.get()
    out, err = capfd.readouterr()
    call_command('changed_languages')
    out, err = capfd.readouterr()
    assert "(no known changes)" in err
    assert (
        ("Will show languages changed between revisions %d (exclusive) and "
         "%d (inclusive)"
         % (revision, revision))
        in err)


@pytest.mark.cmd
@pytest.mark.django_db
def test_changed_languages_since_revision(capfd, project0_nongnu, tp0):
    """Changed languages since a given revision"""
    # Everything
    for store in tp0.stores.all():
        store.sync()
    rev = tp0.stores.aggregate(
        rev=Min('last_sync_revision'))['rev'] - 1
    call_command('changed_languages', '--after-revision=%s' % rev)
    out, err = capfd.readouterr()
    assert out == u'language0,language1\n'

    # End revisions
    revision = Revision.get()
    unit = tp0.stores.first().units.first()
    unit.target = "NEW TARGET"
    unit.save()
    call_command('changed_languages', '--after-revision=%s' % revision)
    out, err = capfd.readouterr()
    assert out == u'language0\n'
