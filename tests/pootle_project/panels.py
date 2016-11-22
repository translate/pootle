# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.template import loader

from pootle.core.browser import get_table_headings
from pootle.core.delegate import panels
from pootle_app.models.permissions import get_matching_permissions
from pootle_app.panels import ChildrenPanel
from pootle_project.views import ProjectBrowseView, ProjectsBrowseView


@pytest.mark.django_db
def test_panel_project_table(project0, rf, member):
    request = rf.get('/projects/project0/')
    request.user = member
    request.permissions = get_matching_permissions(
        request.user,
        project0.directory)
    view = ProjectBrowseView(
        kwargs=dict(
            project_code=project0.code,
            dir_path=None,
            filename=None))
    view.request = request
    view.object = view.get_object()
    lang_panels = panels.gather(ProjectBrowseView)
    assert lang_panels.keys() == ["children"]
    assert lang_panels["children"] == ChildrenPanel
    panel = ChildrenPanel(view)
    assert panel.panel_name == "children"
    assert (
        panel.cache_key
        == ("panel.%s.%s"
            % (panel.panel_name, view.cache_key)))

    table = {
        'id': view.view_name,
        'fields': panel.table_fields,
        'headings': get_table_headings(panel.table_fields),
        'rows': view.object_children}

    assert panel.table == table
    assert panel.get_context_data() == dict(
        table=table, can_translate=view.can_translate)
    content = loader.render_to_string(
        panel.template_name, context=panel.get_context_data())
    assert (
        panel.content
        == panel.update_times(content))


@pytest.mark.django_db
def test_panel_projects_table(rf, member, project0):
    request = rf.get('/projects/')
    request.user = member
    request.permissions = get_matching_permissions(
        request.user,
        project0.directory.parent)
    view = ProjectsBrowseView()
    view.request = request
    view.object = view.get_object()
    lang_panels = panels.gather(ProjectsBrowseView)
    assert lang_panels.keys() == ["children"]
    assert lang_panels["children"] == ChildrenPanel
    panel = ChildrenPanel(view)
    assert panel.panel_name == "children"
    assert (
        panel.cache_key
        == ("panel.%s.%s"
            % (panel.panel_name, view.cache_key)))

    table = {
        'id': view.view_name,
        'fields': panel.table_fields,
        'headings': get_table_headings(panel.table_fields),
        'rows': view.object_children}

    assert panel.table == table
    assert panel.get_context_data() == dict(
        table=table, can_translate=view.can_translate)
    content = loader.render_to_string(
        panel.template_name, context=panel.get_context_data())
    assert (
        panel.content
        == panel.update_times(content))


@pytest.mark.django_db
def test_panel_project_store_table(project0, store0, rf, member):
    request = rf.get('/projects/project0/store0')
    request.user = member
    request.permissions = get_matching_permissions(
        request.user,
        project0.directory.parent)
    view = ProjectBrowseView(
        kwargs=dict(
            project_code=project0.code,
            dir_path="",
            filename=store0.name))
    view.request = request
    view.object = view.get_object()
    lang_panels = panels.gather(ProjectBrowseView)
    assert lang_panels.keys() == ["children"]
    assert lang_panels["children"] == ChildrenPanel
    panel = ChildrenPanel(view)
    assert panel.panel_name == "children"
    assert (
        panel.cache_key
        == ("panel.%s.%s"
            % (panel.panel_name, view.cache_key)))

    table = {
        'id': view.view_name,
        'fields': panel.table_fields,
        'headings': get_table_headings(panel.table_fields),
        'rows': view.object_children}

    assert panel.table == table
    assert panel.get_context_data() == dict(
        table=table, can_translate=view.can_translate)
    content = loader.render_to_string(
        panel.template_name, context=panel.get_context_data())
    assert (
        panel.content
        == panel.update_times(content))
