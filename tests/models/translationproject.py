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
from translate.misc.multistring import multistring

from django.db import IntegrityError

from pytest_pootle.factories import (
    LanguageDBFactory, ProjectDBFactory, TranslationProjectFactory)

from pootle.core.plugin import getter
from pootle.core.delegate import tp_tool
from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject
from pootle_translationproject.utils import TPTool


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
                             templates, complex_ttk):
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

    # Create an empty template translation project for project0.
    TranslationProjectFactory(project=project0, language=templates)

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
def test_tp_stats_created_from_template(po_directory, tutorial, templates):
    language = LanguageDBFactory()
    tp = TranslationProject.objects.create(language=language, project=tutorial)
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
def test_cannot_be_inited_from_templates(project0):
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
def test_tp_tool_move(language0, project0, templates):
    tp = project0.translationproject_set.get(language=language0)
    original_stores = list(tp.stores.all())

    TPTool(project0).move(tp, templates)
    assert tp.language == templates
    assert (
        tp.pootle_path
        == tp.directory.pootle_path
        == "/%s/%s/" % (templates.code, project0.code))
    assert tp.directory.parent == templates.directory

    # all of the stores and their directories are updated
    for store in original_stores:
        store = Store.objects.get(pk=store.pk)
        assert store.pootle_path.startswith(tp.pootle_path)
        assert store.parent.pootle_path.startswith(tp.pootle_path)

    assert not Store.objects.filter(
        pootle_path__startswith="/%s/%s"
        % (language0.code, project0.code))
    assert not Directory.objects.filter(
        pootle_path__startswith="/%s/%s/"
        % (language0.code, project0.code))

    # calling with already set language does nothing
    assert TPTool(project0).move(tp, templates) is None


@pytest.mark.django_db
def test_tp_tool_bad(po_directory, tp0, templates, english):
    other_project = ProjectDBFactory(source_language=english)
    other_tp = TranslationProjectFactory(
        project=other_project,
        language=LanguageDBFactory())
    tp_tool = TPTool(tp0.project)

    with pytest.raises(ValueError):
        tp_tool.check_tp(other_tp)

    with pytest.raises(ValueError):
        tp_tool.set_parents(tp0.directory, other_tp.directory)

    with pytest.raises(ValueError):
        tp_tool.set_parents(other_tp.directory, tp0.directory)

    with pytest.raises(ValueError):
        tp_tool.move(other_tp, templates)

    with pytest.raises(ValueError):
        tp_tool.clone(other_tp, templates)

    with pytest.raises(ValueError):
        # cant set tp to a language if a tp already exists
        tp_tool.move(
            tp0, Language.objects.get(code="language1"))

    with pytest.raises(ValueError):
        # cant clone tp to a language if a tp already exists
        tp_tool.clone(
            tp0, Language.objects.get(code="language1"))


def _test_tp_match(source_tp, target_tp):
    source_stores = []
    for store in source_tp.stores.live():
        source_stores.append(store.pootle_path)
        update_path = (
            "/%s/%s"
            % (target_tp.language.code,
               store.pootle_path[(len(source_tp.language.code) + 2):]))
        updated = Store.objects.get(pootle_path=update_path)
        assert store.state == updated.state
        updated_units = updated.units
        for i, unit in enumerate(store.units):
            updated_unit = updated_units[i]
            assert unit.source == updated_unit.source
            assert unit.target == updated_unit.target
            assert unit.state == updated_unit.state
            assert unit.getcontext() == updated_unit.getcontext()
            assert unit.getlocations() == updated_unit.getlocations()
            assert unit.hasplural() == updated_unit.hasplural()
    for store in target_tp.stores.live():
        source_path = (
            "/%s/%s"
            % (source_tp.language.code,
               store.pootle_path[(len(target_tp.language.code) + 2):]))
        assert source_path in source_stores


@pytest.mark.django_db
def test_tp_tool_clone(po_directory, tp0, templates):
    new_lang = LanguageDBFactory()
    tp_tool = TPTool(tp0.project)
    _test_tp_match(tp0, tp_tool.clone(tp0, new_lang))


@pytest.mark.django_db
def test_tp_tool_update(po_directory, tp0, templates):
    new_lang = LanguageDBFactory()
    tp0_tool = TPTool(tp0.project)
    new_tp = tp0.project.translationproject_set.create(
        language=new_lang)

    # this will clone stores/directories as new_tp is empty
    tp0_tool.update_from_tp(tp0, new_tp)
    _test_tp_match(tp0, new_tp)
    tp0_tool.update_from_tp(tp0, new_tp)

    tp0.stores.first().delete()
    tp0.stores.first().units.first().delete()
    unit = tp0.stores.first().units.first()
    unit.source = multistring(["NEW TARGET", "NEW TARGETS"])
    unit.target = "NEW TARGET"
    unit.context = "something-else"
    unit.save()
    newunit = unit.__class__()
    newunit.source = multistring(["OTHER NEW TARGET", "OTHER NEW TARGETS"])
    newunit.target = "OTHER NEW TARGET"
    newunit.context = "something-else-again"
    unit.store.addunit(newunit)

    tp0_tool.update_from_tp(tp0, new_tp)
    _test_tp_match(tp0, new_tp)

    # doing another update does nothing
    tp0_tool.update_from_tp(tp0, new_tp)
    _test_tp_match(tp0, new_tp)


@pytest.mark.django_db
def test_tp_tool_getter(project0_directory, project0):
    assert tp_tool.get(Project) is TPTool
    assert isinstance(project0.tp_tool, TPTool)


@pytest.mark.django_db
def test_tp_tool_custom_getter(project0, no_tp_tool_):

    class CustomTPTool(TPTool):
        pass

    @getter(tp_tool, sender=Project, weak=False)
    def custom_tp_tool_getter(**kwargs_):
        return CustomTPTool

    assert tp_tool.get(Project) is CustomTPTool
    assert isinstance(project0.tp_tool, CustomTPTool)


@pytest.mark.django_db
def test_tp_tool_gets(project0, tp0):
    assert project0.tp_tool[tp0.language.code] == tp0
    assert project0.tp_tool.get(tp0.language.code) == tp0
    assert project0.tp_tool.get("TP_DOES_NOT_EXIST") is None
    assert project0.tp_tool.get("TP_DOES_NOT_EXIST", "FOO") == "FOO"

    with pytest.raises(tp0.DoesNotExist):
        project0.tp_tool["DOES_NOT_EXIST"]
