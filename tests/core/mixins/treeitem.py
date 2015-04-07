#!/usr/bin/env python
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
def test_get_parent(af_tutorial_subdir_po, af_tutorial_po,
                     afrikaans_tutorial, afrikaans, tutorial):
    """Ensure that retrieved parent objects have a correct type."""
    parent = af_tutorial_subdir_po.get_parent()
    assert isinstance(parent, Directory)

    parent = af_tutorial_po.get_parent()
    assert isinstance(parent, TranslationProject)

    parent = afrikaans_tutorial.get_parent()
    assert isinstance(parent, Project)

    parent = afrikaans_tutorial.directory.get_parent()
    assert isinstance(parent, Project)

    parent = tutorial.directory.get_parent()
    assert parent is None

    parent = afrikaans.directory.get_parent()
    assert parent is None
