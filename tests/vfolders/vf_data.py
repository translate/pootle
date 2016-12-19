# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.db.models import Sum

from pootle.core.browser import get_table_headings
from virtualfolder.display import VFolderStatsDisplay
from virtualfolder.delegate import vfolders_data_view
from virtualfolder.views import VFoldersDataView, make_vfolder_dict
from virtualfolder.utils import DirectoryVFDataTool


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_vfolder_data_view(tp0, request_users):
    user = request_users["user"]
    dir0 = tp0.directory
    vf_data = vfolders_data_view.get(dir0.__class__)(dir0, user=user)
    assert isinstance(vf_data, VFoldersDataView)
    assert vf_data.context is dir0
    assert isinstance(vf_data.vfolder_data_tool, DirectoryVFDataTool)
    assert vf_data.vfolder_data_tool.context is dir0
    stats = vf_data.vfolder_data_tool.get_stats(user=user)
    assert vf_data.all_stats == VFolderStatsDisplay(dir0, stats=stats).stats
    assert vf_data.stats["children"] == vf_data.all_stats
    # ordering?
    rows = [
        make_vfolder_dict(dir0, *vf)
        for vf
        in vf_data.all_stats.items()]
    for i, row in enumerate(vf_data.table_items):
        assert rows[i] == row
    assert "priority" in vf_data.table_fields
    expected_table_data = dict(
        children=dict(
            id='vfolders',
            fields=vf_data.table_fields,
            headings=get_table_headings(vf_data.table_fields),
            rows=vf_data.table_items))
    assert vf_data.table_data == expected_table_data


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_vfolder_data_checks(subdir0, request_users):
    user = request_users["user"]
    vf_data = vfolders_data_view.get(subdir0.__class__)(subdir0, user=user)
    data_tool = vf_data.vfolder_data_tool
    checks = {}
    cd = data_tool.filter_data(data_tool.checks_data_model)
    if not data_tool.show_all_to(user):
        cd = data_tool.filter_accessible(cd)
    cd = (cd.values_list("store__vfolders", "name")
            .annotate(Sum("count")))
    for vf, name, count in cd:
        checks[vf] = checks.get(vf, {})
        checks[vf][name] = count
    assert checks == data_tool.get_checks(user=user)
