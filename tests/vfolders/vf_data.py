# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.browser import get_table_headings
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
    assert (
        vf_data.all_stats
        == vf_data.vfolder_data_tool.get_stats(user=user))
    assert vf_data.stats["children"] == vf_data.all_stats
    # ordering?
    rows = [
        make_vfolder_dict(dir0, *vf)
        for vf
        in vf_data.all_stats.items()]
    for i, row in enumerate(vf_data.table_items):
        assert rows[i] == row
    expected_table_data = dict(
        children=dict(
            id='vfolders',
            fields=vf_data.table_fields,
            headings=get_table_headings(vf_data.table_fields),
            rows=vf_data.table_items))
    assert vf_data.table_data == expected_table_data
