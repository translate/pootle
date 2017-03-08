# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest

from translate.filters import checks

from django.db import IntegrityError

from pytest_pootle.factories import (
    LanguageDBFactory, ProjectDBFactory, TranslationProjectFactory)

from pootle.core.delegate import revision
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject


@pytest.mark.django_db
def test_tp_create_fail(po_directory, tutorial, english):

    # Trying to create a TP with no Language raises a RelatedObjectDoesNotExist
    # which can be caught with Language.DoesNotExist
    with pytest.raises(Language.DoesNotExist):
        TranslationProject.objects.create()

    # TP needs a project set too...
    with pytest.raises(Project.DoesNotExist):
        TranslationProject.objects.create(language=english)

    # There is already an english tutorial was automagically set up
    with pytest.raises(IntegrityError):
        TranslationProject.objects.create(project=tutorial, language=english)


@pytest.mark.django_db
def test_tp_create_templates(project0_nongnu, project0,
                             templates, no_templates_tps, complex_ttk):
    # As there is a tutorial template it will automatically create stores for
    # our new TP
    template_tp = TranslationProject.objects.create(
        language=templates, project=project0)
    template = Store.objects.create(
        name="foo.pot",
        translation_project=template_tp,
        parent=template_tp.directory)
    project0.treestyle = "nongnu"
    project0.save()
    template.update(complex_ttk)
    template.sync()
    tp = TranslationProject.objects.create(
        project=project0, language=LanguageDBFactory())
    tp.init_from_templates()
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
def test_tp_create_with_files(project0_directory, project0, store0, settings):
    # lets add some files by hand

    trans_dir = settings.POOTLE_TRANSLATION_DIRECTORY
    language = LanguageDBFactory()
    tp_dir = os.path.join(trans_dir, "%s/project0" % language.code)
    os.makedirs(tp_dir)

    with open(os.path.join(tp_dir, "store0.po"), "w") as f:
        f.write(store0.serialize())

    TranslationProject.objects.create(project=project0, language=language)


@pytest.mark.django_db
def test_tp_empty_stats(project0_nongnu, project0, templates):
    """Tests if empty stats is initialized when translation project (new language)
    is added for a project with existing but empty template translation project.
    """

    # Create a new language to test.
    language = LanguageDBFactory()
    tp = TranslationProject.objects.create(
        language=language, project=project0)
    tp.init_from_templates()

    # There are no files on disk so TP was not automagically filled.
    assert list(tp.stores.all()) == []

    # Check if zero stats is calculated and available.
    stats = tp.data_tool.get_stats()
    assert stats['total'] == 0
    assert stats['translated'] == 0
    assert stats['fuzzy'] == 0
    assert stats['suggestions'] == 0
    assert stats['critical'] == 0


@pytest.mark.django_db
def test_tp_stats_created_from_template(po_directory, templates, tutorial):
    os.mkdir(os.path.join(tutorial.get_real_path(), "foolang"))
    language = LanguageDBFactory(code="foolang")
    tp = TranslationProject.objects.get(language=language, project=tutorial)
    tp.init_from_templates()
    assert tp.stores.all().count() == 1
    stats = tp.data_tool.get_stats()
    assert stats['total'] == 2  # there are 2 words in test template
    assert stats['translated'] == 0
    assert stats['fuzzy'] == 0
    assert stats['suggestions'] == 0
    assert stats['critical'] == 0


@pytest.mark.django_db
def test_can_be_inited_from_templates(po_directory, tutorial, templates):
    language = LanguageDBFactory()
    tp = TranslationProject(project=tutorial, language=language)
    assert tp.can_be_inited_from_templates()


@pytest.mark.django_db
def test_cannot_be_inited_from_templates(project0, no_templates_tps):
    language = LanguageDBFactory()
    tp = TranslationProject(project=project0, language=language)
    assert not tp.can_be_inited_from_templates()


@pytest.mark.django_db
def test_tp_checker(po_directory, tp_checker_tests):
    language = Language.objects.get(code="language0")
    checker_name_, project = tp_checker_tests
    tp = TranslationProject.objects.create(project=project, language=language)

    checkerclasses = [
        checks.projectcheckers.get(tp.project.checkstyle,
                                   checks.StandardChecker)
    ]
    assert [x.__class__ for x in tp.checker.checkers] == checkerclasses


@pytest.mark.django_db
def test_tp_create_with_none_treestyle(po_directory, english, templates, settings):
    project = ProjectDBFactory(
        source_language=english,
        treestyle='pootle_fs')
    language = LanguageDBFactory()
    TranslationProjectFactory(
        language=templates, project=project)

    tp = TranslationProject.objects.create(
        project=project, language=language)

    assert not tp.abs_real_path
    assert not os.path.exists(
        os.path.join(
            settings.POOTLE_TRANSLATION_DIRECTORY,
            project.code))

    tp.save()
    assert not tp.abs_real_path
    assert not os.path.exists(
        os.path.join(
            settings.POOTLE_TRANSLATION_DIRECTORY,
            project.code))


@pytest.mark.django_db
def test_tp_cache_on_delete(tp0):
    proj_revision = revision.get(
        tp0.project.directory.__class__)(
            tp0.project.directory)
    orig_revision = proj_revision.get("stats")
    tp0.delete()
    assert (
        proj_revision.get("stats")
        != orig_revision)
