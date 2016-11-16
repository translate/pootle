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
from pootle_translationproject.views import TPBrowseView
from virtualfolder.panels import VFolderPanel


@pytest.mark.django_db
def test_panel_tp_table(tp0, rf, member):
    request = rf.get('/language0/project0/')
    request.user = member
    request.permissions = get_matching_permissions(
        request.user,
        tp0.directory)
    view = TPBrowseView(
        kwargs=dict(
            language_code=tp0.language.code,
            project_code=tp0.project.code))
    view.request = request
    view.object = view.get_object()
    lang_panels = panels.gather(TPBrowseView)
    assert lang_panels.keys() == ["children", "vfolders"]
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


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_panel_tp_vfolder_table(tp0, rf, member):
    request = rf.get('/language0/project0/')
    request.user = member
    request.permissions = get_matching_permissions(
        request.user,
        tp0.directory)
    view = TPBrowseView(
        kwargs=dict(
            language_code=tp0.language.code,
            project_code=tp0.project.code))
    view.request = request
    view.object = view.get_object()
    lang_panels = panels.gather(TPBrowseView)
    assert lang_panels.keys() == ["children", "vfolders"]
    assert lang_panels["vfolders"] == VFolderPanel
    panel = VFolderPanel(view)
    assert panel.panel_name == "vfolder"
    assert (
        panel.cache_key
        == ("panel.%s.%s"
            % (panel.panel_name, view.cache_key)))
    table = view.vfolders_data_view.table_data["children"]
    assert panel.table == table
    assert panel.get_context_data() == dict(
        table=table, can_translate=view.can_translate)
    content = loader.render_to_string(
        panel.template_name, context=panel.get_context_data())
    assert (
        panel.content
        == panel.update_times(content))


@pytest.mark.django_db
def test_panel_tp_subdir_table(subdir0, rf, member):
    request = rf.get(subdir0.pootle_path)
    request.user = member
    request.permissions = get_matching_permissions(
        request.user,
        subdir0)
    view = TPBrowseView(
        kwargs=dict(
            language_code=subdir0.tp.language.code,
            project_code=subdir0.tp.project.code,
            dir_path=subdir0.tp_path[1:]))
    view.request = request
    view.object = view.get_object()
    lang_panels = panels.gather(TPBrowseView)
    assert lang_panels.keys() == ["children", "vfolders"]
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
def test_panel_tp_no_vfolders_table(tp0, rf, member, no_vfolders):
    request = rf.get('/language0/project0/')
    request.user = member
    request.permissions = get_matching_permissions(
        request.user,
        tp0.directory)
    view = TPBrowseView(
        kwargs=dict(
            language_code=tp0.language.code,
            project_code=tp0.project.code))
    view.request = request
    view.object = view.get_object()
    lang_panels = panels.gather(TPBrowseView)
    assert lang_panels.keys() == ["children", "vfolders"]
    assert lang_panels["vfolders"] == VFolderPanel
    panel = VFolderPanel(view)
    assert panel.panel_name == "vfolder"
    assert panel.table == ""
    view.vfolders_data_view = None
    assert panel.table == ""
