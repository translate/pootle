#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 Evernote Corporation
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

import pytest

from pootle.core.models import Revision
from pootle_store.models import Unit

from .unit import _update_translation


@pytest.mark.django_db
def test_max_revision(af_tutorial_po):
    """Tests `max_revision()` gets the latest revision."""
    initial_max_revision = Unit.max_revision()
    initial_revision = Revision.get()
    assert initial_max_revision == initial_revision
    assert initial_max_revision == 0

    # Let's make 10 translation updates, this must also update their
    # revision numbers
    for i in range(10):
        _update_translation(af_tutorial_po, 0, {'target': str(i)},
                            sync=False)

    end_max_revision = Unit.max_revision()
    end_revision = Revision.get()
    assert end_max_revision == end_revision
    assert end_max_revision != initial_max_revision

    assert end_revision != initial_revision
    assert end_revision == 10


@pytest.mark.django_db
def test_revision_incr(af_tutorial_po):
    """Tests revision is incremented when units change."""
    previous_revision = Revision.get()
    db_unit = _update_translation(af_tutorial_po, 0, {'target': [u'Fleisch']},
                                  sync=False)

    assert db_unit.revision != previous_revision
    assert Revision.get() != previous_revision
    assert db_unit.revision == Revision.get()

    previous_revision = Revision.get()

    db_unit = _update_translation(af_tutorial_po, 0, {'target': u'Lachs'},
                                  sync=False)

    assert db_unit.revision != previous_revision
    assert Revision.get() != previous_revision
    assert db_unit.revision == Revision.get()
