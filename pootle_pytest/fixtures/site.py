# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import shutil

import pytest


@pytest.fixture
def site_matrix(request, system, settings):

    from pootle_pytest.factories import (
        ProjectFactory, DirectoryFactory, LanguageFactory,
        TranslationProjectFactory, StoreFactory, UnitFactory)

    from pootle_store.models import UNTRANSLATED, TRANSLATED, FUZZY, OBSOLETE

    # create root and projects directories
    DirectoryFactory(name="projects", parent=DirectoryFactory(parent=None))

    # add 2 languages
    languages = [LanguageFactory() for i in range(0, 2)]

    for i in range(0, 2):
        # add 2 projects
        project = ProjectFactory(source_language=languages[0])

        for language in languages:
            # add a TP to the project for each language
            tp = TranslationProjectFactory(project=project, language=language)

            for i in range(0, 3):
                # add 3 stores
                store = StoreFactory(translation_project=tp)

                # add 8 units to each store
                for state in [UNTRANSLATED, TRANSLATED, FUZZY, OBSOLETE]:
                    for i in range(0, 2):
                        UnitFactory(store=store, state=state)

    def _teardown():
        # required to get clean slate 8/
        for trans_dir in os.listdir(settings.POOTLE_TRANSLATION_DIRECTORY):
            if trans_dir.startswith("project"):
                shutil.rmtree(
                    os.path.join(
                        settings.POOTLE_TRANSLATION_DIRECTORY, trans_dir))

    request.addfinalizer(_teardown)
