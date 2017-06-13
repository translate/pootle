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

from pootle.core.browser import make_directory_item, make_store_item
from pootle.core.debug import memusage
from pootle.core.forms import PathsSearchForm
from pootle.core.signals import update_revisions
from pootle.core.url_helpers import split_pootle_path
from pootle.core.views.browse import StatsDisplay
from pootle_app.models import Directory
from pootle_store.models import Store
from pootle_translationproject.views import TPBrowseView


def _test_view_tp_children(view, obj):
    request = view.request
    if obj.tp_path == "/":
        data_obj = obj.tp
    else:
        data_obj = obj
    stats = StatsDisplay(
        data_obj,
        stats=data_obj.data_tool.get_stats(user=request.user)).stats
    assert stats == view.stats
    stores = view.tp.stores
    if obj.tp_path != "/":
        stores = stores.filter(
            tp_path__startswith=obj.tp_path)
    vf_stores = stores.filter(
        vfolders__isnull=False).exclude(parent=obj)
    dirs_with_vfolders = set(
        split_pootle_path(path)[2].split("/")[0]
        for path
        in vf_stores.values_list("pootle_path", flat=True))
    directories = [
        make_directory_item(
            child,
            **(dict(sort="priority")
               if child.name in dirs_with_vfolders
               else {}))
        for child in obj.get_children()
        if isinstance(child, Directory)]
    stores = [
        make_store_item(child)
        for child in obj.get_children()
        if isinstance(child, Store)]
    items = directories + stores
    for item in items:
        if item["code"] in stats["children"]:
            item["stats"] = stats["children"][item["code"]]
        elif item["title"] in stats["children"]:
            item["stats"] = stats["children"][item["title"]]
    assert view.object_children == items


@pytest.mark.django_db
def test_view_tp_children(tp0, rf, request_users):
    request = rf.get('/language0/project0/')
    request.user = request_users["user"]
    view = TPBrowseView(
        kwargs=dict(
            language_code=tp0.language.code,
            project_code=tp0.project.code))
    view.request = request
    view.object = view.get_object()
    obj = view.object
    assert obj == tp0.directory
    _test_view_tp_children(view, obj)


@pytest.mark.django_db
def test_view_tp_subdir_children(subdir0, rf, request_users):
    request = rf.get(subdir0.pootle_path)
    request.user = request_users["user"]
    view = TPBrowseView(
        kwargs=dict(
            language_code=subdir0.tp.language.code,
            project_code=subdir0.tp.project.code,
            dir_path=subdir0.tp_path[1:]))
    view.request = request
    view.object = view.get_object()
    obj = view.object
    assert obj == subdir0
    _test_view_tp_children(view, obj)


@pytest.mark.django_db
def test_view_tp_paths_bad(tp0, client, request_users):
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    url = reverse(
        "pootle-tp-paths",
        kwargs=dict(
            project_code=tp0.project.code,
            language_code=tp0.language.code))
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
def test_view_tp_paths(tp0, store0, client, request_users):
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    url = reverse(
        "pootle-tp-paths",
        kwargs=dict(
            project_code=tp0.project.code,
            language_code=tp0.language.code))
    response = client.post(
        url,
        data=dict(q="tore"),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    result = json.loads(response.content)
    path_form = PathsSearchForm(context=tp0, data=dict(q="tore"))
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
def test_view_tp_garbage(tp0, store0, client, request_users):
    args = [tp0.language.code, tp0.project.code]
    url = reverse("pootle-tp-browse", args=args)
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.get(url)
    response = client.get(url)
    assert response.status_code == 200
    failed = []
    for i in xrange(0, 2):
        with memusage() as usage:
            client.get(url)
        try:
            assert usage["used"] == 0
        except:
            failed.append((i, usage["used"]))
    assert not failed


@pytest.mark.pootle_memusage
@pytest.mark.django_db
def test_view_tp_directory_garbage(subdir0, client, request_users):
    tp = subdir0.translation_project
    args = [tp.language.code, tp.project.code, "%s/" % subdir0.name]
    url = reverse("pootle-tp-browse", args=args)
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
def test_view_tp_store_garbage(store0, client, request_users):
    tp = store0.translation_project
    args = [tp.language.code, tp.project.code, store0.name]
    url = reverse("pootle-tp-store-browse", args=args)
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
