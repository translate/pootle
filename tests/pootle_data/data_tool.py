# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.db.models import Sum

from pootle.core.delegate import data_tool
from pootle_data.models import StoreData
from pootle_data.store_data import StoreDataTool
from pootle_data.utils import DataTool


@pytest.mark.django_db
def test_data_tool_store(store0):
    assert data_tool.get() is None
    assert data_tool.get(store0.__class__) is StoreDataTool
    assert isinstance(store0.data_tool, StoreDataTool)
    assert store0.data_tool.context is store0


@pytest.mark.django_db
def test_data_tool_base_tool():
    foo = object()
    base_tool = DataTool(foo)
    assert base_tool.context is foo
    assert base_tool.get_stats() == dict(children={})
    assert base_tool.get_stats(include_children=False) == {}
    assert base_tool.get_checks() == {}
    assert base_tool.object_stats == {}
    assert base_tool.children_stats == {}
    assert base_tool.updater is None


@pytest.mark.django_db
def test_data_tool_store_get_stats(store0):
    stats = store0.data_tool.get_stats()

    # TODO: remove when old stats are removed
    old_stats = store0.get_stats()

    assert (
        sorted(old_stats.keys())
        == sorted(stats.keys()))

    assert stats["translated"] == store0.data.translated_words
    assert stats["fuzzy"] == store0.data.fuzzy_words
    assert stats["total"] == store0.data.total_words
    assert stats["critical"] == store0.data.critical_checks
    assert stats["suggestions"] == store0.data.pending_suggestions
    assert stats["children"] == {}
    assert stats["is_dirty"] is False
    # this is the actually last updated unit - called "lastaction"
    last_submission_info = (
        store0.data.last_submission.get_submission_info())
    assert (
        sorted(stats["lastaction"].items())
        == sorted(last_submission_info.items()))
    # apparently "updated" means created
    last_updated_info = (
        store0.data.last_created_unit.get_last_updated_info())
    assert (
        sorted(stats["lastupdated"].items())
        == sorted(last_updated_info.items()))


@pytest.mark.django_db
def test_data_tool_store_get_checks(store0):
    checks = store0.data_tool.get_checks()
    old_checks = store0._get_checks()

    # TODO: remove when old_checks are removed
    assert (
        sorted(checks.items())
        == sorted(old_checks["checks"].items()))

    assert (
        sorted(checks.items())
        == sorted(store0.check_data.values_list("name", "count")))


@pytest.mark.django_db
def test_data_tool_tp_get_stats(tp0):
    stats = tp0.data_tool.get_stats(include_children=False)

    # TODO: remove when old stats are removed
    old_stats = tp0.get_stats(include_children=False)
    assert (
        sorted(old_stats.keys())
        == sorted(stats.keys()))

    assert "children" not in stats
    assert stats["translated"] == tp0.data.translated_words
    assert stats["fuzzy"] == tp0.data.fuzzy_words
    assert stats["total"] == tp0.data.total_words
    assert stats["critical"] == tp0.data.critical_checks
    assert stats["suggestions"] == tp0.data.pending_suggestions
    assert stats["is_dirty"] is False
    # this is the actually last updated unit - called "lastaction"
    last_submission_info = (
        tp0.data.last_submission.get_submission_info())
    assert (
        sorted(stats["lastaction"].items())
        == sorted(last_submission_info.items()))
    # apparently "updated" means created
    last_updated_info = (
        tp0.data.last_created_unit.get_last_updated_info())
    assert (
        sorted(stats["lastupdated"].items())
        == sorted(last_updated_info.items()))


@pytest.mark.django_db
def test_data_tool_tp_get_stats_with_children(tp0):
    stats = tp0.data_tool.get_stats()

    # TODO: remove when old stats are removed
    old_stats = tp0.get_stats()
    assert (
        sorted(old_stats.keys())
        == sorted(stats.keys()))

    assert stats["translated"] == tp0.data.translated_words
    assert stats["fuzzy"] == tp0.data.fuzzy_words
    assert stats["total"] == tp0.data.total_words
    assert stats["critical"] == tp0.data.critical_checks
    assert stats["suggestions"] == tp0.data.pending_suggestions
    # this is the actually last updated unit - called "lastaction"
    last_submission_info = (
        tp0.data.last_submission.get_submission_info())
    assert (
        sorted(stats["lastaction"].items())
        == sorted(last_submission_info.items()))
    # apparently "updated" means created
    last_updated_info = (
        tp0.data.last_created_unit.get_last_updated_info())
    assert (
        sorted(stats["lastupdated"].items())
        == sorted(last_updated_info.items()))

    for directory in tp0.directory.child_dirs.all():
        dir_stats = stats["children"][directory.name]
        store_data = StoreData.objects.filter(
            store__pootle_path__startswith=directory.pootle_path)
        aggregate_mapping = dict(
            total="total_words",
            fuzzy="fuzzy_words",
            translated="translated_words",
            suggestions="pending_suggestions",
            critical="critical_checks")
        for k, v in aggregate_mapping.items():
            assert (
                dir_stats[k]
                == store_data.aggregate(**{k: Sum(v)})[k])
