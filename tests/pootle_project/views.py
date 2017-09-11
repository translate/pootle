# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json

import pytest

from django.core.urlresolvers import reverse

from pootle.core.browser import (
    make_language_item, make_project_list_item, make_xlanguage_item)
from pootle.core.debug import memusage
from pootle.core.forms import PathsSearchForm
from pootle.core.signals import update_revisions
from pootle.core.views.browse import StatsDisplay
from pootle_app.models import Directory
from pootle_misc.util import cmp_by_last_activity
from pootle_project.models import Project, ProjectResource, ProjectSet
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


@pytest.mark.django_db
def test_view_project_paths_bad(project0, client, request_users):
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    url = reverse(
        "pootle-project-paths",
        kwargs=dict(project_code=project0.code))
    # no xhr header
    response = client.post(url)
    assert response.status_code == 400
    # no query
    response = client.post(
        url, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 400
    # query too short
    response = client.post(
        url,
        data=dict(q="xy"),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 400


@pytest.mark.django_db
def test_view_project_paths(project0, store0, client, request_users):
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    url = reverse(
        "pootle-project-paths",
        kwargs=dict(project_code=project0.code))
    response = client.post(
        url,
        data=dict(q="tore"),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    result = json.loads(response.content)
    path_form = PathsSearchForm(context=project0, data=dict(q="tore"))
    assert path_form.is_valid()
    assert result["items"] == path_form.search(show_all=user.is_superuser)
    assert "store0.po" in result["items"]["results"]

    stores = Store.objects.filter(name=store0.name)
    for store in stores:
        store.obsolete = True
        store.save()
        update_revisions.send(
            store.__class__,
            instance=store,
            keys=["stats"])
    response = client.post(
        url,
        data=dict(q="tore"),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    result = json.loads(response.content)
    assert "store0.po" not in result["items"]["results"]


@pytest.mark.pootle_memusage
@pytest.mark.django_db
def test_view_project_garbage(project0, client, request_users):
    url = reverse(
        "pootle-project-browse",
        kwargs=dict(
            project_code=project0.code,
            dir_path="",
            filename=""))
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.get(url)
    response = client.get(url)
    assert response.status_code == 200
    for i in xrange(0, 2):
        with memusage() as usage:
            client.get(url)
        assert not usage["used"]


@pytest.mark.pootle_memusage
@pytest.mark.django_db
def test_view_project_subdir_garbage(subdir0, client, request_users):
    url = reverse(
        "pootle-project-browse",
        kwargs=dict(
            project_code=subdir0.translation_project.project.code,
            dir_path=subdir0.name,
            filename=""))
    url = "%s/" % url
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.get(url)
    response = client.get(url)
    assert response.status_code == 200
    for i in xrange(0, 2):
        with memusage() as usage:
            client.get(url)
        assert not usage["used"]


@pytest.mark.pootle_memusage
@pytest.mark.django_db
def test_view_project_store_garbage(store0, client, request_users):
    url = reverse(
        "pootle-project-browse",
        kwargs=dict(
            project_code=store0.translation_project.project.code,
            dir_path="",
            filename=store0.name))
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.get(url)
    response = client.get(url)
    assert response.status_code == 200
    for i in xrange(0, 2):
        with memusage() as usage:
            client.get(url)
        assert not usage["used"]


@pytest.mark.django_db
def test_view_projects_api(project0, client, request_users):
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.get(reverse('pootle-xhr-admin-projects'))
    if not user.is_superuser:
        assert response.status_code == 403
        return
    result = json.loads(response.content)
    assert result["count"] == Project.objects.count()

    for project in result["models"]:
        if project["code"] == project0.code:
            assert project["pk"] == project0.pk
            assert project["checkstyle"] == project0.checkstyle
            assert (
                project["screenshot_search_prefix"]
                == project0.screenshot_search_prefix)
            assert project["ignoredfiles"] == project0.ignoredfiles
            assert project["source_language"] == project0.source_language.pk
            assert project["disabled"] == project0.disabled
            assert project["report_email"] == project0.report_email
            assert project["fs_plugin"] == project0.config["pootle_fs.fs_type"]
            assert project["fs_url"] == project0.config["pootle_fs.fs_url"]
            assert (
                project["fs_mapping"]
                == project0.config[
                    "pootle_fs.translation_mappings"]["default"])
            assert (
                project["filetypes"]
                == [str(x)
                    for x
                    in project0.filetypes.values_list("pk", flat=True)])
