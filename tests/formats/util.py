# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pytest_pootle.factories import ProjectDBFactory, TranslationProjectFactory

from pootle.core.delegate import formats
from pootle_format.exceptions import UnrecognizedFiletype
from pootle_format.models import Format
from pootle_store.models import Store


@pytest.mark.django_db
def test_format_util(project0):

    filetype_tool = project0.filetype_tool
    assert list(filetype_tool.filetypes.all()) == list(project0.filetypes.all())

    assert filetype_tool.filetype_extensions == [u"po"]
    assert filetype_tool.template_extensions == [u"pot"]
    assert filetype_tool.valid_extensions == [u"po", u"pot"]

    xliff = Format.objects.get(name="xliff")
    project0.filetypes.add(xliff)
    assert filetype_tool.filetype_extensions == [u"po", u"xliff"]
    assert filetype_tool.template_extensions == [u"pot", u"xliff"]
    assert filetype_tool.valid_extensions == [u"po", u"xliff", u"pot"]


@pytest.mark.django_db
def test_format_chooser(project0):
    registry = formats.get()
    po = Format.objects.get(name="po")
    po2 = registry.register("special_po_2", "po")
    po3 = registry.register("special_po_3", "po")
    xliff = Format.objects.get(name="xliff")
    project0.filetypes.add(xliff)
    project0.filetypes.add(po2)
    project0.filetypes.add(po3)
    filetype_tool = project0.filetype_tool
    from pootle.core.debug import debug_sql
    with debug_sql():
        assert filetype_tool.choose_filetype("foo.po") == po
    assert filetype_tool.choose_filetype("foo.pot") == po
    assert filetype_tool.choose_filetype("foo.xliff") == xliff

    # push po to the back of the queue
    project0.filetypes.remove(po)
    project0.filetypes.add(po)
    assert filetype_tool.choose_filetype("foo.po") == po2
    assert filetype_tool.choose_filetype("foo.pot") == po
    assert filetype_tool.choose_filetype("foo.xliff") == xliff

    with pytest.raises(UnrecognizedFiletype):
        filetype_tool.choose_filetype("foo.bar")


@pytest.mark.django_db
def test_format_add_project_filetype(project0, po2):
    project = project0
    project.filetype_tool.add_filetype(po2)
    assert po2 in project.filetypes.all()

    # adding a 2nd time does nothing
    project.filetype_tool.add_filetype(po2)
    assert project.filetypes.filter(pk=po2.pk).count() == 1


@pytest.mark.django_db
def test_format_set_store_filetype(project0):
    project = project0
    store = Store.objects.exclude(is_template=True).filter(
        translation_project__project=project).first()
    store_name = store.name
    registry = formats.get()
    filetypes = project.filetype_tool

    # register po2
    po2 = registry.register(
        "special_po_2", "po", template_extension="pot2")

    # filetype must be recognized for project
    with pytest.raises(UnrecognizedFiletype):
        filetypes.set_store_filetype(store, po2)

    # add the filetype to the project
    filetypes.add_filetype(po2)

    # set the store's filetype
    filetypes.set_store_filetype(store, po2)

    # the filetype is changed, but the extension is the same
    store = Store.objects.get(pk=store.pk)
    assert store.filetype == po2
    assert store.name == store_name

    # register po3 - different extension
    po3 = registry.register(
        "special_po_3", "po3", template_extension="pot3")
    filetypes.add_filetype(po3)
    filetypes.set_store_filetype(store, po3)

    # the filetype is changed, and the extension
    store = Store.objects.get(pk=store.pk)
    assert store.filetype == po3
    assert store.name.endswith(".po3")
    assert store.pootle_path.endswith(".po3")


@pytest.mark.django_db
def test_format_set_template_store_filetype(po_directory, templates, po):
    project = ProjectDBFactory(source_language=templates)
    filetypes = project.filetype_tool
    tp = TranslationProjectFactory(language=templates, project=project)
    registry = formats.get()
    store = Store.objects.create(
        name="mystore.pot",
        translation_project=tp,
        parent=tp.directory)
    store_name = store.name
    assert store.filetype == po
    assert store.is_template
    assert store.name.endswith(".pot")

    # register po2 - same template extension
    po2 = registry.register(
        "special_po_2", "po2", template_extension="pot")
    filetypes.add_filetype(po2)
    filetypes.set_store_filetype(store, po2)

    # the filetype is changed, but the extension is the same
    store = Store.objects.get(pk=store.pk)
    assert store.filetype == po2
    assert store.name == store_name

    # register po3 - same template extension
    po3 = registry.register(
        "special_po_3", "po", template_extension="pot3")
    filetypes.add_filetype(po3)
    filetypes.set_store_filetype(store, po3)

    # the filetype and extension are changed
    store = Store.objects.get(pk=store.pk)
    assert store.filetype == po3
    assert store.name.endswith(".pot3")

    # does nothing
    filetypes.set_store_filetype(store, po3)
    assert store.filetype == po3


@pytest.mark.django_db
def test_format_set_native_store_filetype(po_directory, templates,
                                          language0, po2, english):
    project = ProjectDBFactory(source_language=english)
    filetypes = project.filetype_tool
    registry = formats.get()
    templates_tp = TranslationProjectFactory(language=templates, project=project)
    lang_tp = TranslationProjectFactory(language=language0, project=project)
    template = Store.objects.create(
        name="mystore.pot3.pot",
        translation_project=templates_tp,
        parent=templates_tp.directory)
    store = Store.objects.create(
        name="mystore.po3.po",
        translation_project=lang_tp,
        parent=lang_tp.directory)

    # register po2 - not native template extension
    filetypes.add_filetype(po2)

    filetypes.set_store_filetype(store, po2)
    assert store.name.endswith(".po3.po2")
    assert store.filetype == po2
    filetypes.set_store_filetype(template, po2)
    assert template.name.endswith(".pot3.pot2")
    assert template.filetype == po2

    # register po3 - native template extension
    po3 = registry.register(
        "special_po_3", "po3", template_extension="pot3")
    filetypes.add_filetype(po3)

    # in this case extension is just removed
    filetypes.set_store_filetype(store, po3)
    assert not store.name.endswith(".po3.po3")
    assert store.name.endswith(".po3")
    assert store.filetype == po3
    filetypes.set_store_filetype(template, po3)
    assert not template.name.endswith(".pot3.pot3")
    assert template.name.endswith(".pot3")
    assert template.filetype == po3


@pytest.mark.django_db
def test_format_set_tp_from_store_filetype(po_directory, templates,
                                           language0, po, po2):
    project = ProjectDBFactory(source_language=templates)
    filetypes = project.filetype_tool
    registry = formats.get()
    templates_tp = TranslationProjectFactory(language=templates, project=project)
    lang_tp = TranslationProjectFactory(language=language0, project=project)
    template = Store.objects.create(
        name="mystore.pot",
        translation_project=templates_tp,
        parent=templates_tp.directory)
    store = Store.objects.create(
        name="mystore.po",
        translation_project=lang_tp,
        parent=lang_tp.directory)
    po3 = registry.register(
        "special_po_3", "po3", template_extension="pot3")
    filetypes.add_filetype(po2)
    filetypes.add_filetype(po3)

    # this does nothing as the stores are currently po
    filetypes.set_tp_filetype(lang_tp, po3, from_filetype=po2)
    store = Store.objects.get(pk=store.pk)
    assert store.filetype == po
    assert store.name.endswith(".po")
    filetypes.set_tp_filetype(templates_tp, po3, from_filetype=po2)
    template = Store.objects.get(pk=template.pk)
    assert template.filetype == po
    assert template.name.endswith(".pot")

    # it works if we switch to po2 first
    filetypes.set_tp_filetype(lang_tp, po2, from_filetype=po)
    filetypes.set_tp_filetype(templates_tp, po2, from_filetype=po)
    filetypes.set_tp_filetype(lang_tp, po3, from_filetype=po2)
    store = Store.objects.get(pk=store.pk)
    assert store.filetype == po3
    assert store.name.endswith(".po3")
    filetypes.set_tp_filetype(templates_tp, po3, from_filetype=po2)
    template = Store.objects.get(pk=template.pk)
    assert template.filetype == po3
    assert template.name.endswith(".pot3")


@pytest.mark.django_db
def test_format_set_templates_tp_filetype(po_directory, templates, po2):
    project = ProjectDBFactory(source_language=templates)
    filetypes = project.filetype_tool
    registry = formats.get()
    templates_tp = TranslationProjectFactory(language=templates, project=project)
    template = Store.objects.create(
        name="mystore.pot",
        translation_project=templates_tp,
        parent=templates_tp.directory)
    filetypes.add_filetype(po2)
    filetypes.set_tp_filetype(templates_tp, po2)
    template = Store.objects.get(pk=template.pk)
    assert template.filetype == po2
    assert template.name.endswith(".pot2")
    po3 = registry.register(
        "special_po_3", "po3", template_extension="pot3")
    filetypes.add_filetype(po3)
    filetypes.set_tp_filetype(templates_tp, po3)
    template = Store.objects.get(pk=template.pk)
    assert template.filetype == po3
    assert template.name.endswith(".pot3")


@pytest.mark.django_db
def test_format_set_tp_filetype(po_directory, english, language0, po2):
    project = ProjectDBFactory(source_language=english)
    filetypes = project.filetype_tool
    registry = formats.get()
    lang_tp = TranslationProjectFactory(language=language0, project=project)
    store = Store.objects.create(
        name="mystore.po",
        translation_project=lang_tp,
        parent=lang_tp.directory)
    filetypes.add_filetype(po2)
    filetypes.set_tp_filetype(lang_tp, po2)
    store = Store.objects.get(pk=store.pk)
    assert store.filetype == po2
    assert store.name.endswith(".po2")
    po3 = registry.register(
        "special_po_3", "po3", template_extension="pot")
    filetypes.add_filetype(po3)
    filetypes.set_tp_filetype(lang_tp, po3)
    store = Store.objects.get(pk=store.pk)
    assert store.filetype == po3
    assert store.name.endswith(".po3")


@pytest.mark.django_db
def test_format_set_template_tp_matching_filetype(po_directory, templates,
                                                  po, po2, english):
    project = ProjectDBFactory(source_language=english)
    filetypes = project.filetype_tool
    tp = TranslationProjectFactory(project=project, language=templates)
    filetypes.add_filetype(po2)

    template5 = Store.objects.create_by_path(
        "/templates/%s/subdir/store5.pot" % project.code)

    assert template5.filetype == po
    filetypes.set_tp_filetype(tp, po2, matching="store5")

    # doesnt match - because its in a subdir
    template5 = Store.objects.get(pk=template5.pk)
    assert template5.filetype == po

    filetypes.set_tp_filetype(tp, po2, matching="*store5")
    template5 = Store.objects.get(pk=template5.pk)
    assert template5.filetype == po2

    filetypes.set_tp_filetype(tp, po, matching="*/*5")
    template5 = Store.objects.get(pk=template5.pk)
    assert template5.filetype == po


@pytest.mark.django_db
def test_format_set_tp_matching_filetype(tp0, po, po2):
    project = tp0.project
    project.filetype_tool.add_filetype(po2)

    store5 = tp0.stores.get(name="store5.po")
    assert store5.filetype == po
    project.filetype_tool.set_tp_filetype(tp0, po2, matching="store5")

    # doesnt match - because its in a subdir
    store5 = Store.objects.get(pk=store5.pk)
    assert store5.filetype == po

    project.filetype_tool.set_tp_filetype(tp0, po2, matching="*store5")
    store5 = Store.objects.get(pk=store5.pk)
    assert store5.filetype == po2

    project.filetype_tool.set_tp_filetype(tp0, po, matching="*/*5")
    store5 = Store.objects.get(pk=store5.pk)
    assert store5.filetype == po


@pytest.mark.django_db
def test_format_set_project_filetypes(templates_project0,
                                      dummy_project_filetypes, po2):
    project = templates_project0.project
    template_tp = templates_project0
    other_tps = project.translationproject_set.exclude(
        pk=template_tp.pk)
    filetype_tool = project.filetype_tool
    result = filetype_tool.result

    with pytest.raises(UnrecognizedFiletype):
        filetype_tool.set_filetypes(po2)

    filetype_tool.add_filetype(po2)
    filetype_tool.set_filetypes(po2)

    assert result[0] == (template_tp, po2, None, None)
    for i, tp in enumerate(other_tps):
        assert result[i + 1] == (tp, po2, None, None)

    # test getting from_filetype
    result.clear()
    filetype_tool.set_filetypes(po2, from_filetype="foo")
    assert result[0] == (template_tp, po2, "foo", None)
    for i, tp in enumerate(other_tps):
        assert result[i + 1] == (tp, po2, "foo", None)

    # test getting match
    result.clear()
    filetype_tool.set_filetypes(po2, matching="bar")
    assert result[0] == (template_tp, po2, None, "bar")
    for i, tp in enumerate(other_tps):
        assert result[i + 1] == (tp, po2, None, "bar")

    # test getting both
    result.clear()
    filetype_tool.set_filetypes(po2, from_filetype="foo", matching="bar")
    assert result[0] == (template_tp, po2, "foo", "bar")
    for i, tp in enumerate(other_tps):
        assert result[i + 1] == (tp, po2, "foo", "bar")
