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

from .unit import _update_translation


@pytest.mark.django_db
def test_max_revision(revision, project0_nongnu, store0):
    """Tests `max_revision()` gets the latest revision."""
    store0.sync()

    # update a store first, initial_revision = 1 after this update
    store0.update(store0.file.store)

    initial_max_revision = Unit.max_revision()
    initial_revision = Revision.get()
    assert initial_max_revision == initial_revision

    # Let's make 10 translation updates, this must also update their revision
    # numbers
    for i in range(10):
        _update_translation(store0, 0, {'target': str(i)},
                            sync=False)

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
    db_unit = _update_translation(store0, 0, {'target': [u'Fleisch']},
                                  sync=False)

    assert db_unit.revision != previous_revision
    assert Revision.get() != previous_revision
    assert db_unit.revision == Revision.get()

    previous_revision = Revision.get()

    db_unit = _update_translation(store0, 0, {'target': u'Lachs'},
                                  sync=False)

    assert db_unit.revision != previous_revision
    assert Revision.get() != previous_revision
    assert db_unit.revision == Revision.get()
