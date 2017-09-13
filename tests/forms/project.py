# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_app.forms import ProjectForm
from pootle_format.models import Format
from pootle_project.models import (PROJECT_CHECKERS, RESERVED_PROJECT_CODES,
                                   Project)


@pytest.mark.parametrize('reserved_code', RESERVED_PROJECT_CODES)
@pytest.mark.django_db
def test_clean_code_invalid(reserved_code, format_registry):
    form_data = {
        'code': reserved_code,
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'fullname': 'Foo',
        'fs_plugin': "localfs",
        'fs_mapping': "/<language_code>.<ext>",
        'fs_url': "{POOTLE_TRANSLATION_DIRECTORY}%s" % reserved_code,
        'filetypes': [format_registry["po"]["pk"]],
        'source_language': 1}
    form = ProjectForm(form_data)
    assert not form.is_valid()
    assert 'code' in form.errors
    assert len(form.errors.keys()) == 1


@pytest.mark.django_db
def test_clean_code_blank_invalid(format_registry):
    form_data = {
        'code': '  ',
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'fullname': 'Foo',
        'fs_plugin': "localfs",
        'fs_url': "{POOTLE_TRANSLATION_DIRECTORY}foo",
        'fs_mapping': "/<language_code>.<ext>",
        'filetypes': [format_registry["po"]["pk"]],
        'source_language': 1}
    form = ProjectForm(form_data)
    assert not form.is_valid()
    assert 'code' in form.errors
    assert len(form.errors.keys()) == 1


@pytest.mark.django_db
def test_clean_localfiletype_invalid(format_registry):
    form_data = {
        'code': 'foo',
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'fullname': 'Foo',
        'fs_plugin': "localfs",
        'fs_url': "{POOTLE_TRANSLATION_DIRECTORY}foo",
        'fs_mapping': "/<language_code>.<ext>",
        'filetypes': ["NO_SUCH_FORMAT"],
        'source_language': 1}
    form = ProjectForm(form_data)
    assert not form.is_valid()
    assert 'filetypes' in form.errors
    assert len(form.errors.keys()) == 1


@pytest.mark.django_db
def test_project_form_bad_filetype_removal(format_registry):
    form_data = {
        'fullname': "Project 0",
        'code': "project0",
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'disabled': False,
        'fs_plugin': "localfs",
        'fs_url': "{POOTLE_TRANSLATION_DIRECTORY}project0",
        'fs_mapping': "/<language_code>.<ext>",
        'filetypes': [Format.objects.get(name="xliff").pk],
        'source_language': 1,
        'screenshot_search_prefix': "",
        'ignoredfiles': "",
        'report_email': ""}
    form = ProjectForm(form_data, instance=Project.objects.get(code="project0"))
    assert not form.is_valid()
    assert 'filetypes' in form.errors
    assert len(form.errors.keys()) == 1


@pytest.mark.django_db
def test_project_form_change_filetypes(format_registry):
    filetype_names = ["xliff", "po", "ts"]
    filetypes = []
    for filetype in filetype_names:
        filetypes.append(Format.objects.get(name=filetype).pk)
    form_data = {
        'fullname': "Project 0",
        'code': "project0",
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'disabled': False,
        'filetypes': filetypes,
        'fs_plugin': "localfs",
        'fs_url': "{POOTLE_TRANSLATION_DIRECTORY}project0",
        'fs_mapping': "/<language_code>.<ext>",
        'source_language': 1,
        'screenshot_search_prefix': "",
        'ignoredfiles': "",
        'report_email': ""}
    project0 = Project.objects.get(code="project0")
    form = ProjectForm(form_data, instance=project0)
    assert form.is_valid()
    form.save()
    assert (
        list(project0.filetypes.values_list("pk", flat=True))
        == filetypes)


@pytest.mark.django_db
def test_form_project_plugin_missing(format_registry):
    form_data = {
        'code': 'foo0',
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'fullname': 'Foo',
        'fs_url': "{POOTLE_TRANSLATION_DIRECTORY}foo0",
        'fs_mapping': "/<language_code>.<ext>",
        'filetypes': [format_registry["po"]["pk"]],
        'source_language': 1}
    form = ProjectForm(form_data)
    assert not form.is_valid()
    assert 'fs_plugin' in form.errors
    assert len(form.errors.keys()) == 1


@pytest.mark.django_db
def test_form_project_plugin_invalid(format_registry):
    form_data = {
        'code': 'foo0',
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'fullname': 'Foo',
        'fs_plugin': "DOES NOT EXIST",
        'fs_url': "{POOTLE_TRANSLATION_DIRECTORY}foo0",
        'fs_mapping': "/<language_code>.<ext>",
        'filetypes': [format_registry["po"]["pk"]],
        'source_language': 1}
    form = ProjectForm(form_data)
    assert not form.is_valid()
    assert 'fs_plugin' in form.errors
    assert len(form.errors.keys()) == 1


@pytest.mark.django_db
def test_form_project_fs_url(format_registry):
    form_data = {
        'code': 'foo0',
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'fullname': 'Foo',
        'fs_plugin': "localfs",
        'fs_url': "{POOTLE_TRANSLATION_DIRECTORY}foo0",
        'fs_mapping': "/<language_code>.<ext>",
        'filetypes': [format_registry["po"]["pk"]],
        'source_language': 1}
    form = ProjectForm(form_data)
    assert form.is_valid()
    form_data["fs_url"] = "/foo/bar/baz"
    form = ProjectForm(form_data)
    assert form.is_valid()
    form_data["fs_url"] = "foo/bar/baz"
    form = ProjectForm(form_data)
    assert not form.is_valid()
    assert form.errors.keys() == ["fs_url"]
    form_data["fs_url"] = ""
    form = ProjectForm(form_data)
    assert not form.is_valid()
    assert form.errors.keys() == ["fs_url"]


@pytest.mark.django_db
def test_form_project_fs_mapping(format_registry):
    form_data = {
        'code': 'foo0',
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'fullname': 'Foo',
        'fs_plugin': "localfs",
        'fs_url': "{POOTLE_TRANSLATION_DIRECTORY}foo0",
        'fs_mapping': "/<language_code>.<ext>",
        'filetypes': [format_registry["po"]["pk"]],
        'source_language': 1}
    form = ProjectForm(form_data)
    assert form.is_valid()
    form_data["fs_mapping"] = "<language_code>.<ext>"
    form = ProjectForm(form_data)
    assert not form.is_valid()
    assert 'fs_mapping' in form.errors
    form_data["fs_mapping"] = "/<language_code>"
    form = ProjectForm(form_data)
    assert not form.is_valid()
    assert 'fs_mapping' in form.errors
    form_data["fs_mapping"] = "/<foo_code>.<ext>"
    form = ProjectForm(form_data)
    assert not form.is_valid()
    assert 'fs_mapping' in form.errors


@pytest.mark.django_db
def test_form_project_template_name(format_registry):
    form_data = {
        'code': 'foo0',
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'fullname': 'Foo',
        'fs_plugin': "localfs",
        'fs_url': "{POOTLE_TRANSLATION_DIRECTORY}foo0",
        'fs_mapping': "/<language_code>.<ext>",
        'filetypes': [format_registry["po"]["pk"]],
        'source_language': 1}
    form = ProjectForm(form_data)
    assert form.is_valid()
    assert form.cleaned_data["template_name"] == ""
    project = form.save()
    assert project.lang_mapper.get_upstream_code("templates") == "templates"
    form_data["template_name"] = "foo"
    form = ProjectForm(instance=project, data=form_data)
    assert form.is_valid()
    form.save()
    del project.__dict__["lang_mapper"]
    assert project.lang_mapper.get_upstream_code("templates") == "foo"
    form_data["template_name"] = ""
    form = ProjectForm(instance=project, data=form_data)
    assert form.is_valid()
    form.save()
    del project.__dict__["lang_mapper"]
    assert project.lang_mapper.get_upstream_code("templates") == "templates"
