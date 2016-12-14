# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.browser import (
    make_language_item, make_project_list_item, make_xlanguage_item)
from pootle.core.views.browse import StatsDisplay
from pootle_app.models import Directory
from pootle_misc.util import cmp_by_last_activity
from pootle_project.models import ProjectResource, ProjectSet
from pootle_project.views import ProjectBrowseView, ProjectsBrowseView
from pootle_store.models import Store


def _test_view_project_children(view, project):
    request = view.request
    kwargs = view.kwargs
    resource_path = (
        "%(dir_path)s%(filename)s" % kwargs)
    project_path = (
        "%s/%s"
        % (kwargs["project_code"], resource_path))
    if not (kwargs["dir_path"] or kwargs["filename"]):
        obj = project
    elif not kwargs["filename"]:
        obj = ProjectResource(
            Directory.objects.live().filter(
                pootle_path__regex="^/.*/%s$" % project_path),
            pootle_path="/projects/%s" % project_path)
    else:
        obj = ProjectResource(
            Store.objects.live().filter(
                pootle_path__regex="^/.*/%s$" % project_path),
            pootle_path="/projects/%s" % project_path)

    item_func = (
        make_xlanguage_item
        if (kwargs["dir_path"]
            or kwargs["filename"])
        else make_language_item)
    items = [
        item_func(item)
        for item
        in obj.get_children_for_user(request.user)
    ]
    stats = obj.data_tool.get_stats(user=request.user)
    stats = StatsDisplay(obj, stats=stats).stats
    for item in items:
        if item["code"] in stats["children"]:
            item["stats"] = stats["children"][item["code"]]
    items.sort(cmp_by_last_activity)
    assert view.object_children == items


@pytest.mark.django_db
def test_view_project_children(project0, rf, request_users):
    request = rf.get('/projects/project0/')
    request.user = request_users["user"]
    view = ProjectBrowseView(
        kwargs=dict(
            project_code=project0.code,
            dir_path="",
            filename=""))
    view.request = request
    view.object = view.get_object()
    assert view.object == project0
    _test_view_project_children(view, project0)


@pytest.mark.django_db
def test_view_project_subdir_children(project0, subdir0, rf, request_users):
    request = rf.get('/projects/project0/subdir0/')
    request.user = request_users["user"]
    view = ProjectBrowseView(
        kwargs=dict(
            project_code=project0.code,
            dir_path=subdir0.tp_path[1:],
            filename=""))
    view.request = request
    view.object = view.get_object()
    assert isinstance(view.object, ProjectResource)
    _test_view_project_children(view, project0)


@pytest.mark.django_db
def test_view_project_store_children(project0, store0, rf, request_users):
    request = rf.get('/projects/project0/store0.po')
    request.user = request_users["user"]
    view = ProjectBrowseView(
        kwargs=dict(
            project_code=project0.code,
            dir_path="",
            filename=store0.name))
    view.request = request
    view.object = view.get_object()
    assert isinstance(view.object, ProjectResource)
    _test_view_project_children(view, project0)


@pytest.mark.django_db
def test_view_project_set_children(project0, store0, rf, request_users):
    request = rf.get('/projects/')
    request.user = request_users["user"]
    view = ProjectsBrowseView()
    view.request = request
    view.object = view.get_object()
    assert isinstance(view.object, ProjectSet)
    items = [
        make_project_list_item(project)
        for project
        in view.object.children]
    view.add_child_stats(items)
    items.sort(cmp_by_last_activity)
    assert view.object_children == items
