# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.browser import make_directory_item, make_store_item
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
