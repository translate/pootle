# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.models import Revision
from pootle_store.models import Unit


@pytest.mark.django_db
def test_max_revision(revision, project0_nongnu, store0):
    """Tests `max_revision()` gets the latest revision."""

    initial_max_revision = Unit.max_revision()
    initial_revision = Revision.get()
    assert initial_max_revision == initial_revision

    # Let's make 10 translation updates, this must also update their revision
    # numbers
    unit = store0.units.first()
    for i in range(10):
        unit.target = str(i)
        unit.save()
        unit.refresh_from_db()

    end_max_revision = Unit.max_revision()
    end_revision = Revision.get()
    assert end_max_revision == end_revision
    assert end_max_revision != initial_max_revision

    assert end_revision != initial_revision
    assert end_revision == 10 + initial_revision


@pytest.mark.django_db
def test_revision_incr(store0):
    """Tests revision is incremented when units change."""
    previous_revision = Revision.get()
    db_unit = store0.units.exclude(target_f="").first()
    db_unit.target = "CHANGED"
    db_unit.save()
    assert db_unit.revision != previous_revision
    assert Revision.get() != previous_revision
    assert db_unit.revision == Revision.get()

    db_unit.refresh_from_db()
    previous_revision = Revision.get()
    db_unit.target = ""
    db_unit.save()
    assert db_unit.revision != previous_revision
    assert Revision.get() != previous_revision
    assert db_unit.revision == Revision.get()
