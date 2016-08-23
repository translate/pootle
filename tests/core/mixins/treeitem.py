# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_app.models import Directory
from pootle_project.models import Project
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject


@pytest.mark.django_db
def test_get_children(project0, language0):
    """Ensure that retrieved child objects have a correct type."""
    def _all_children_are_directories_or_stores(item):
        for child in item.children:
            if isinstance(child, Directory):
                _all_children_are_directories_or_stores(child)
            else:
                assert isinstance(child, Store)

    for tp in project0.children:
        assert isinstance(tp, TranslationProject)
        _all_children_are_directories_or_stores(tp)

    for tp in language0.children:
        assert isinstance(tp, TranslationProject)
        _all_children_are_directories_or_stores(tp)


@pytest.mark.django_db
def test_get_parents(po_directory, project0, language0, tp0, store0, subdir0,
                     no_vfolders):
    """Ensure that retrieved parent objects have a correct type."""

    subdir_store = subdir0.child_stores.first()
    parents = subdir_store.get_parents()
    assert len(parents) == 1
    assert isinstance(parents[0], Directory)

    parents = store0.get_parents()
    assert len(parents) == 1
    assert isinstance(parents[0], TranslationProject)

    parents = tp0.get_parents()
    assert len(parents) == 1
    assert isinstance(parents[0], Project)

    parents = tp0.directory.get_parents()
    assert len(parents) == 1
    assert isinstance(parents[0], Project)

    parents = project0.directory.get_parents()
    assert len(parents) == 0

    parents = language0.directory.get_parents()
    assert len(parents) == 0
