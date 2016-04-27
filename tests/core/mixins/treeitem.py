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
