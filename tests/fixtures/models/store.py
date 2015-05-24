#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import shutil
import tempfile

import pytest


def _require_store(tp, po_dir, name):
    """Helper to get/create a new store."""
    from pootle_store.models import Store

    file_path = os.path.join(po_dir, tp.real_path, name)
    parent_dir = tp.directory
    pootle_path = tp.pootle_path + name

    try:
        store = Store.objects.get(
            pootle_path=pootle_path,
            translation_project=tp,
        )
    except Store.DoesNotExist:
        store = Store.objects.create(
            file=file_path,
            parent=parent_dir,
            name=name,
            translation_project=tp,
        )
        store.save()

    return store


@pytest.fixture(scope='session')
def po_directory(request):
    """Sets up a tmp directory with test PO files."""
    from django.conf import settings
    from pootle_store.models import fs

    test_base_dir = tempfile.mkdtemp()

    tutorial_dir = os.path.join(settings.POOTLE_TRANSLATION_DIRECTORY, 'tutorial')
    tutorial_test_dir = os.path.join(test_base_dir, 'tutorial')

    # Copy files over the temporal dir
    shutil.copytree(tutorial_dir, tutorial_test_dir)

    # Adjust locations
    settings.POOTLE_TRANSLATION_DIRECTORY = test_base_dir
    fs.location = test_base_dir

    def _cleanup():
        shutil.rmtree(test_base_dir)
    request.addfinalizer(_cleanup)

    return test_base_dir


@pytest.fixture
def af_tutorial_po(settings, afrikaans_tutorial, system):
    """Require the /af/tutorial/tutorial.po store."""
    po_directory = settings.POOTLE_TRANSLATION_DIRECTORY
    return _require_store(afrikaans_tutorial, po_directory, 'tutorial.po')


@pytest.fixture
def af_tutorial_subdir_po(settings, afrikaans_tutorial, system):
    """Require the /af/tutorial/subdir/tutorial.po store."""
    po_directory = settings.POOTLE_TRANSLATION_DIRECTORY
    return _require_store(afrikaans_tutorial, po_directory, 'subdir/tutorial.po')


@pytest.fixture
def fr_tutorial_subdir_to_remove_po(settings, french_tutorial, system):
    """Require the /fr/tutorial/subdir_to_remove/tutorial.po store."""
    po_directory = settings.POOTLE_TRANSLATION_DIRECTORY
    return _require_store(french_tutorial, po_directory, 'subdir_to_remove/tutorial.po')


@pytest.fixture
def fr_tutorial_remove_sync_po(settings, french_tutorial, system):
    """Require the /fr/tutorial/remove_sync_tutorial.po store."""
    po_directory = settings.POOTLE_TRANSLATION_DIRECTORY
    return _require_store(french_tutorial, po_directory, 'remove_sync_tutorial.po')


@pytest.fixture
def es_tutorial_subdir_remove_po(settings, spanish_tutorial, system):
    """Require the /es/tutorial/subdir/remove_tutorial.po store."""
    po_directory = settings.POOTLE_TRANSLATION_DIRECTORY
    return _require_store(spanish_tutorial, po_directory, 'subdir/remove_tutorial.po')
