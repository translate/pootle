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

from pootle_app.models import Directory
from pootle_project.models import Project
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject


@pytest.mark.django_db
def test_get_children(tutorial, afrikaans):
    """Ensure that retrieved child objects have a correct type."""
    def _all_children_are_directories_or_stores(item):
        for child in item.children:
            if isinstance(child, Directory):
                _all_children_are_directories_or_stores(child)
            else:
                assert isinstance(child, Store)

    for tp in tutorial.children:
        assert isinstance(tp, TranslationProject)
        _all_children_are_directories_or_stores(tp)

    for tp in afrikaans.children:
        assert isinstance(tp, TranslationProject)
        _all_children_are_directories_or_stores(tp)


@pytest.mark.django_db
def test_get_parents(af_tutorial_subdir_po, af_tutorial_po,
                     afrikaans_tutorial, afrikaans, tutorial):
    """Ensure that retrieved parent objects have a correct type."""
    parents = af_tutorial_subdir_po.get_parents()
    assert len(parents) == 1
    assert isinstance(parents[0], Directory)

    parents = af_tutorial_po.get_parents()
    assert len(parents) == 1
    assert isinstance(parents[0], TranslationProject)

    parents = afrikaans_tutorial.get_parents()
    assert len(parents) == 1
    assert isinstance(parents[0], Project)

    parents = afrikaans_tutorial.directory.get_parents()
    assert len(parents) == 1
    assert isinstance(parents[0], Project)

    parents = tutorial.directory.get_parents()
    assert len(parents) == 0

    parents = afrikaans.directory.get_parents()
    assert len(parents) == 0
