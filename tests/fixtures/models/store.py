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

    return store


@pytest.fixture(scope='session')
def po_directory(request):
    """Sets up a tmp directory with test PO files."""
    from django.conf import settings
    from pootle_store.models import fs

    test_base_dir = tempfile.mkdtemp()

    projects = [dirname for dirname
                in os.listdir(settings.POOTLE_TRANSLATION_DIRECTORY)
                if dirname != '.tmp']

    for project in projects:
        src_dir = os.path.join(settings.POOTLE_TRANSLATION_DIRECTORY, project)

        # Copy files over the temporal dir
        shutil.copytree(src_dir, os.path.join(test_base_dir, project))

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
    return _require_store(afrikaans_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY, 'tutorial.po')


@pytest.fixture
def en_tutorial_po(settings, english_tutorial, system):
    """Require the /en/tutorial/tutorial.po store."""
    return _require_store(english_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY, 'tutorial.po')


@pytest.fixture
def it_tutorial_po(settings, italian_tutorial, system):
    """Require the /it/tutorial/tutorial.po store."""
    return _require_store(italian_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY, 'tutorial.po')


@pytest.fixture
def af_tutorial_subdir_po(settings, afrikaans_tutorial, system):
    """Require the /af/tutorial/subdir/tutorial.po store."""
    return _require_store(afrikaans_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'subdir/tutorial.po')


@pytest.fixture
def issue_2401_po(settings, afrikaans_tutorial, system):
    """Require the /af/tutorial/tutorial.po store."""
    return _require_store(afrikaans_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'issue_2401.po')


@pytest.fixture
def fr_tutorial_subdir_to_remove_po(settings, french_tutorial, system):
    """Require the /fr/tutorial/subdir_to_remove/tutorial.po store."""
    return _require_store(french_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'subdir_to_remove/tutorial.po')


@pytest.fixture
def fr_tutorial_remove_sync_po(settings, french_tutorial, system):
    """Require the /fr/tutorial/remove_sync_tutorial.po store."""
    return _require_store(french_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'remove_sync_tutorial.po')


@pytest.fixture
def es_tutorial_subdir_remove_po(settings, spanish_tutorial, system):
    """Require the /es/tutorial/subdir/remove_tutorial.po store."""
    return _require_store(spanish_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'subdir/remove_tutorial.po')


@pytest.fixture
def ru_tutorial_po(settings, russian_tutorial, system):
    """Require the /ru/tutorial/tutorial.po store."""
    return _require_store(russian_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY, 'tutorial.po')


@pytest.fixture
def ru_update_save_changed_units_po(settings, russian_tutorial, system):
    """Require the /ru/tutorial/tutorial.po store."""
    return _require_store(russian_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'update_save_changed_units.po')


@pytest.fixture
def ru_update_set_last_sync_revision_po(settings, russian_tutorial, system):
    """Require the /ru/tutorial/tutorial.po store."""
    return _require_store(russian_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'update_set_last_sync_revision.po')


@pytest.fixture
def af_vfolder_test_browser_defines_po(settings, afrikaans_vfolder_test,
                                       system):
    """Require the /af/vfolder_test/browser/defines.po store."""
    return _require_store(afrikaans_vfolder_test,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'browser/defines.po')
