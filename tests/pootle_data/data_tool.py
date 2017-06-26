# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.db.models import Sum

from pootle.core.delegate import data_tool, revision
from pootle_app.models import Directory
from pootle_data.apps import PootleDataConfig
from pootle_data.models import StoreChecksData, StoreData, TPChecksData
from pootle_data.store_data import StoreDataTool
from pootle_data.utils import DataTool
from pootle_language.models import Language
from pootle_project.models import Project, ProjectResource, ProjectSet
from pootle_store.constants import FUZZY, OBSOLETE, TRANSLATED
from pootle_store.models import Unit
from virtualfolder.delegate import vfolders_data_tool


@pytest.mark.django_db
def test_data_tool_store(store0):
    assert data_tool.get() is None
    assert data_tool.get(store0.__class__) is StoreDataTool
    assert isinstance(store0.data_tool, StoreDataTool)
    assert store0.data_tool.context is store0


@pytest.mark.django_db
def test_data_tool_obsolete_resurrect_store(store0):
    assert store0.check_data.count()
    orig_stats = store0.data_tool.get_stats()
    store0.makeobsolete()
    assert store0.data.total_words == 0
    assert store0.data.critical_checks == 0
    assert not store0.check_data.count()
    assert store0.data_tool.get_stats() != orig_stats
    assert store0.data.max_unit_revision
    store0.resurrect()
    assert store0.data.total_words
    assert store0.check_data.count()
    assert store0.data.critical_checks


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

    assert stats["translated"] == store0.data.translated_words
    assert stats["fuzzy"] == store0.data.fuzzy_words
    assert stats["total"] == store0.data.total_words
    assert stats["critical"] == store0.data.critical_checks
    assert stats["suggestions"] == store0.data.pending_suggestions
    assert stats["children"] == {}
    last_submission_info = (
        store0.data.last_submission.get_submission_info())
    assert (
        sorted(stats["last_submission"].items())
        == sorted(last_submission_info.items()))
    last_created_unit_info = (
        store0.data.last_created_unit.get_last_created_unit_info())
    assert (
        sorted(stats["last_created_unit"].items())
        == sorted(last_created_unit_info.items()))


@pytest.mark.django_db
def test_data_tool_store_get_checks(store0):
    checks = store0.data_tool.get_checks()
    assert (
        sorted(checks.items())
        == sorted(store0.check_data.values_list("name", "count")))


@pytest.mark.django_db
def test_data_tool_tp_get_stats(tp0):
    stats = tp0.data_tool.get_stats(include_children=False)

    assert "children" not in stats
    assert stats["translated"] == tp0.data.translated_words
    assert stats["fuzzy"] == tp0.data.fuzzy_words
    assert stats["total"] == tp0.data.total_words
    assert stats["critical"] == tp0.data.critical_checks
    assert stats["suggestions"] == tp0.data.pending_suggestions
    last_submission_info = (
        tp0.data.last_submission.get_submission_info())
    assert (
        sorted(stats["last_submission"].items())
        == sorted(last_submission_info.items()))
    last_created_unit_info = (
        tp0.data.last_created_unit.get_last_created_unit_info())
    assert (
        sorted(stats["last_created_unit"].items())
        == sorted(last_created_unit_info.items()))


@pytest.mark.django_db
def test_data_tool_tp_get_stats_with_children(tp0):
    stats = tp0.data_tool.get_stats()

    assert stats["translated"] == tp0.data.translated_words
    assert stats["fuzzy"] == tp0.data.fuzzy_words
    assert stats["total"] == tp0.data.total_words
    assert stats["critical"] == tp0.data.critical_checks
    assert stats["suggestions"] == tp0.data.pending_suggestions
    last_submission_info = (
        tp0.data.last_submission.get_submission_info())
    assert (
        sorted(stats["last_submission"].items())
        == sorted(last_submission_info.items()))
    last_created_unit_info = (
        tp0.data.last_created_unit.get_last_created_unit_info())
    assert (
        sorted(stats["last_created_unit"].items())
        == sorted(last_created_unit_info.items()))

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


@pytest.mark.django_db
def test_data_tool_tp_get_checks(tp0):
    checks = tp0.data_tool.get_checks()
    assert (
        sorted(checks.items())
        == sorted(tp0.check_data.values_list("name", "count")))


def _test_children_stats(stats, directory):
    child_stores = directory.child_stores.live()
    child_dirs = directory.child_dirs.live()
    # same roots
    children = (
        list(child_stores.values_list("name", flat=True))
        + list(child_dirs.values_list("name", flat=True)))
    assert (
        sorted(stats["children"].keys())
        == (sorted(children)))

    for store in child_stores:
        _test_unit_stats(
            stats["children"][store.name],
            store.units)


def _test_object_stats(stats, stores):
    assert "children" not in stats
    _test_unit_stats(
        stats,
        stores)


def _test_unit_stats(stats, units):
    units = units.exclude(
        store__translation_project__language__code="templates"
    ).exclude(store__obsolete=True)
    wordcount = sum(
        units.filter(state__gt=OBSOLETE).values_list(
            "unit_source__source_wordcount",
            flat=True))
    assert stats["total"] == wordcount
    fuzzy_wordcount = sum(
        units.filter(state=FUZZY).values_list(
            "unit_source__source_wordcount",
            flat=True))
    assert stats["fuzzy"] == fuzzy_wordcount
    translated_wordcount = sum(
        units.filter(state=TRANSLATED).values_list(
            "unit_source__source_wordcount",
            flat=True))
    assert stats["translated"] == translated_wordcount


@pytest.mark.django_db
def test_data_tp_stats(tp0):

    # get the child directories
    # child_dirs = tp0.directory.child_dirs.live()

    _test_object_stats(
        tp0.data_tool.get_stats(include_children=False),
        Unit.objects.live().filter(
            store__in=tp0.stores.live()))

    # get the child stores
    _test_children_stats(
        tp0.data_tool.get_stats(),
        tp0.directory)


@pytest.mark.django_db
def test_data_project_stats(project0):
    units = (
        Unit.objects.live().filter(
            store__translation_project__project=project0).exclude(
                store__translation_project__language__code="templates"))
    _test_object_stats(
        project0.data_tool.get_stats(include_children=False),
        units)
    child_stats = project0.data_tool.get_stats()
    non_templates_tps = project0.translationproject_set.exclude(
        language__code="templates")
    assert (
        len(child_stats["children"])
        == non_templates_tps.count())
    for tp in non_templates_tps.iterator():
        stat_code = "%s-%s" % (tp.language.code, project0.code)
        assert stat_code in child_stats["children"]
        child = child_stats["children"][stat_code]
        tp_stats = tp.data_tool.get_stats(include_children=False)
        for k in ["fuzzy", "total", "translated", "suggestions", "critical"]:
            assert child[k] == tp_stats[k]


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_data_cache_keys(language0, project0, subdir0, vfolder0):
    # language
    assert language0.data_tool.ns == "pootle.data"
    assert language0.data_tool.sw_version == PootleDataConfig.version
    assert (
        '%s.%s.%s'
        % (language0.data_tool.cache_key_name,
           language0.code,
           revision.get(Language)(language0).get(key="stats"))
        == language0.data_tool.cache_key)
    # project
    assert project0.data_tool.ns == "pootle.data"
    assert project0.data_tool.sw_version == PootleDataConfig.version
    assert (
        '%s.%s.%s'
        % (project0.data_tool.cache_key_name,
           project0.code,
           revision.get(Project)(project0.directory).get(key="stats"))
        == project0.data_tool.cache_key)
    # directory
    assert subdir0.data_tool.ns == "pootle.data"
    assert subdir0.data_tool.sw_version == PootleDataConfig.version
    assert (
        '%s.%s.%s'
        % (subdir0.data_tool.cache_key_name,
           subdir0.pootle_path,
           revision.get(Directory)(subdir0).get(key="stats"))
        == subdir0.data_tool.cache_key)
    # projectresource
    resource_path = "%s%s" % (project0.pootle_path, subdir0.path)
    projectresource = ProjectResource(
        Directory.objects.none(),
        resource_path,
        context=project0)
    assert projectresource.data_tool.ns == "pootle.data"
    assert projectresource.data_tool.sw_version == PootleDataConfig.version
    assert (
        '%s.%s.%s'
        % (projectresource.data_tool.cache_key_name,
           resource_path,
           revision.get(ProjectResource)(projectresource).get(key="stats"))
        == projectresource.data_tool.cache_key)
    # projectset
    projectset = ProjectSet(Project.objects.all())
    assert projectset.data_tool.ns == "pootle.data"
    assert projectset.data_tool.sw_version == PootleDataConfig.version
    assert (
        '%s.%s.%s'
        % (projectset.data_tool.cache_key_name,
           "ALL",
           revision.get(ProjectSet)(projectset).get(key="stats"))
        == projectset.data_tool.cache_key)
    # vfolders
    vfdata = vfolders_data_tool.get(Directory)(subdir0)
    assert vfdata.ns == "virtualfolder"
    assert vfdata.sw_version == PootleDataConfig.version
    assert (
        '%s.%s.%s'
        % (vfdata.cache_key_name,
           subdir0.pootle_path,
           revision.get(subdir0.__class__)(subdir0).get(key="stats"))
        == vfdata.cache_key)


@pytest.mark.django_db
def test_data_language_stats(language0, request_users):
    user = request_users["user"]
    units = Unit.objects.live()
    units = units.filter(store__translation_project__language=language0)
    if not user.is_superuser:
        units = units.exclude(store__translation_project__project__disabled=True)
    _test_object_stats(
        language0.data_tool.get_stats(include_children=False, user=user),
        units)
    language0.data_tool.get_stats(user=user)


@pytest.mark.django_db
def test_data_directory_stats(subdir0):
    filtered_units = Unit.objects.live().filter(
        store__pootle_path__startswith=subdir0.pootle_path)
    filtered_units = filtered_units.exclude(store__parent=subdir0)
    _test_object_stats(
        subdir0.data_tool.get_stats(include_children=False),
        filtered_units)
    # get the child stores
    _test_children_stats(
        subdir0.data_tool.get_stats(),
        subdir0)


@pytest.mark.django_db
def test_data_project_directory_stats(project_dir_resources0):
    pd0 = project_dir_resources0
    units = Unit.objects.none()
    for directory in pd0.children:
        units |= Unit.objects.live().filter(
            store__pootle_path__startswith=directory.pootle_path)
    _test_object_stats(
        pd0.data_tool.get_stats(include_children=False),
        units)
    pd0.data_tool.get_stats()


@pytest.mark.django_db
def test_data_project_store_stats(project_store_resources0):
    units = Unit.objects.none()
    for store in project_store_resources0.children:
        units |= Unit.objects.live().filter(
            store__pootle_path=(
                "%s%s"
                % (store.parent.pootle_path,
                   store.name)))
    _test_object_stats(
        project_store_resources0.data_tool.get_stats(include_children=False),
        units)
    project_store_resources0.data_tool.get_stats()


@pytest.mark.django_db
def test_data_project_set_stats(project_set):
    units = Unit.objects.live().exclude(
        store__translation_project__project__disabled=True
    ).exclude(store__obsolete=True)
    units = units.exclude(store__is_template=True)
    stats = project_set.data_tool.get_stats(include_children=False)
    _test_object_stats(
        stats,
        units)
    project_set.data_tool.get_stats()


def _calculate_check_data(check_data):
    data = {}
    for check in check_data.iterator():
        data[check.name] = data.get(check.name, 0) + check.count
    return data


@pytest.mark.django_db
def test_data_tool_project_get_checks(project0):
    assert (
        project0.data_tool.get_checks()
        == _calculate_check_data(
            TPChecksData.objects.filter(tp__project=project0)))


@pytest.mark.django_db
def test_data_tool_directory_get_checks(subdir0):
    expected = StoreChecksData.objects.filter(
        store__pootle_path__startswith=subdir0.pootle_path)
    expected = expected.exclude(store__parent=subdir0)
    assert (
        subdir0.data_tool.get_checks()
        == _calculate_check_data(expected))


@pytest.mark.django_db
def test_data_tool_language_get_checks(language0, request_users):
    user = request_users["user"]
    check_data = TPChecksData.objects.filter(tp__language=language0)
    if not user.is_superuser:
        check_data = check_data.exclude(
            tp__project__disabled=True)
    assert (
        language0.data_tool.get_checks(user=user)
        == _calculate_check_data(check_data))


@pytest.mark.django_db
def test_data_project_directory_get_checks(project_dir_resources0):
    pd0 = project_dir_resources0
    checks_data = StoreChecksData.objects.none()
    for directory in pd0.children:
        checks_data |= StoreChecksData.objects.filter(
            store__state__gt=OBSOLETE,
            store__pootle_path__startswith=directory.pootle_path)
    assert (
        sorted(pd0.data_tool.get_checks().items())
        == sorted(_calculate_check_data(checks_data).items()))
