# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pytest_pootle.factories import (
    LanguageDBFactory, ProjectDBFactory, TranslationProjectFactory)

from translate.misc.multistring import multistring

from pootle.core.plugin import getter
from pootle.core.delegate import tp_tool
from pootle.core.url_helpers import split_pootle_path
from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_store.models import Store
from pootle_translationproject.utils import TPTool


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
        pootle_path__startswith="/%s/%s/"
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


def _test_tp_match(source_tp, target_tp, project=None, update=False):
    source_stores = []
    for store in source_tp.stores.live():
        source_stores.append(store.pootle_path)
        project_code = (
            project and project.code or source_tp.project.code)
        store_path = "".join(split_pootle_path(store.pootle_path)[2:])
        update_path = (
            "/%s/%s/%s"
            % (target_tp.language.code,
               project_code,
               store_path))
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
        store_path = "".join(split_pootle_path(store.pootle_path)[2:])
        source_path = (
            "/%s/%s/%s"
            % (source_tp.language.code,
               source_tp.project.code,
               store_path))
        assert source_path in source_stores
    if not update:
        assert source_tp.stores.count() == target_tp.stores.count()


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
    _test_tp_match(tp0, new_tp, update=True)
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
    _test_tp_match(tp0, new_tp, update=True)

    # doing another update does nothing
    tp0_tool.update_from_tp(tp0, new_tp)
    _test_tp_match(tp0, new_tp, update=True)


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


@pytest.mark.django_db
def test_tp_tool_move_project(language0, project0, project1, templates):
    tp = project0.translationproject_set.get(language=language0)
    original_stores = list(tp.stores.all())

    TPTool(project0).move(tp, templates, project1)
    assert tp.language == templates
    assert (
        tp.pootle_path
        == tp.directory.pootle_path
        == "/%s/%s/" % (templates.code, project1.code))
    assert tp.directory.parent == templates.directory

    # all of the stores and their directories are updated
    for store in original_stores:
        store.refresh_from_db()
        assert store.pootle_path.startswith(tp.pootle_path)
        assert store.parent.pootle_path.startswith(tp.pootle_path)

    assert not Store.objects.filter(
        pootle_path__startswith="/%s/%s"
        % (language0.code, project0.code))
    assert not Directory.objects.filter(
        pootle_path__startswith="/%s/%s/"
        % (language0.code, project0.code))


@pytest.mark.django_db
def test_tp_tool_clone_project(tp0, project1):
    new_lang = LanguageDBFactory()
    tp_tool = TPTool(tp0.project)
    _test_tp_match(
        tp0,
        tp_tool.clone(tp0, new_lang, project1),
        project1)


@pytest.mark.django_db
def test_tp_tool_clone_project_same_lang(tp0, english):
    new_proj = ProjectDBFactory(source_language=english)
    tp_tool = TPTool(tp0.project)
    _test_tp_match(
        tp0,
        tp_tool.clone(tp0, tp0.language, new_proj),
        new_proj)
