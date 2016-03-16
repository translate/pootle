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

from django.db import IntegrityError

from pootle_language.models import Language
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject


@pytest.mark.django_db
def test_tp_create_fail(tutorial, english):

    # Trying to create a TP with no Project raises a RelatedObjectDoesNotExist
    # which can be caught with Project.DoesNotExist
    with pytest.raises(Project.DoesNotExist):
        TranslationProject.objects.create()

    # TP needs a lang set too...
    with pytest.raises(Language.DoesNotExist):
        TranslationProject.objects.create(project=tutorial)

    # There is already an english tutorial was automagically set up
    with pytest.raises(IntegrityError):
        TranslationProject.objects.create(project=tutorial, language=english)


@pytest.mark.django_db
def test_tp_create_templates(tutorial, klingon_vpw, templates):
    # As there is a tutorial template it will automatically create stores for
    # our new TP
    template_tp = TranslationProject.objects.get(
        language=templates, project=tutorial)
    tp = TranslationProject.objects.create(
        project=tutorial, language=klingon_vpw)
    assert tp.stores.count() == template_tp.stores.count()
    assert (
        [(s, t)
         for s, t
         in template_tp.stores.first().units.values_list("source_f",
                                                         "target_f")]
        == [(s, t)
            for s, t
            in tp.stores.first().units.values_list("source_f",
                                                   "target_f")])


@pytest.mark.django_db
def test_tp_create_with_files(tutorial, klingon, settings):
    # lets add some files by hand

    trans_dir = settings.POOTLE_TRANSLATION_DIRECTORY

    shutil.copytree(
        os.path.join(trans_dir, "tutorial/en"),
        os.path.join(trans_dir, "tutorial/kl"))

    TranslationProject.objects.create(project=tutorial, language=klingon)

    shutil.rmtree(os.path.join(trans_dir, "tutorial/kl"))


@pytest.mark.django_db
def test_tp_empty_stats():
    """Tests if empty stats is initialized when translation project (new language)
    is added for a project with existing but empty template translation project.
    """
    from pootle_project.models import Project
    from pootle_language.models import Language
    from pootle_translationproject.models import TranslationProject
    from pytest_pootle.factories import LanguageFactory, TranslationProjectFactory

    # Create an empty template translation project for project0.
    project = Project.objects.get(code="project0")
    english = Language.objects.get(code="en")
    TranslationProjectFactory(project=project, language=english)

    # Create a new language to test.
    language = LanguageFactory()
    tp, created = TranslationProject.objects.get_or_create(language=language,
                                                           project=project)

    # There are no files on disk so TP was not automagically filled.
    assert list(tp.stores.all()) == []

    # Check if zero stats is calculated and available.
    stats = tp.get_stats()
    assert stats['total'] == 0
    assert stats['translated'] == 0
    assert stats['fuzzy'] == 0
    assert stats['suggestions'] == 0
    assert stats['critical'] == 0


@pytest.mark.django_db
def test_tp_stats_created_from_template(tutorial, fish, templates):
    tp = TranslationProject.objects.create(project=tutorial, language=fish)
    assert tp.stores.all().count() == 1
    stats = tp.get_stats()
    assert stats['total'] == 2  # there are 2 words in test template
    assert stats['translated'] == 0
    assert stats['fuzzy'] == 0
    assert stats['suggestions'] == 0
    assert stats['critical'] == 0


@pytest.mark.django_db
def test_tp_checker(tp_checker_tests):
    from translate.filters import checks

    language = Language.objects.get(code="language0")
    checker_name, project = tp_checker_tests
    tp = TranslationProject.objects.create(project=project, language=language)

    checkerclasses = [
        checks.projectcheckers.get(tp.project.checkstyle,
                                   checks.StandardChecker)
    ]
    assert [x.__class__ for x in tp.checker.checkers] == checkerclasses
