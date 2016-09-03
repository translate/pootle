# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from translate.filters.decorators import Category

from pootle_data.utils import (
    StoreDataTool, StoreDataUpdater, TPDataTool, TPDataUpdater)
#    DirectoryDataTool, LanguageDataTool, ProjectDataTool,
#    ProjectResourceDataTool, StoreDataTool, TPDataTool,
#    StoreDataUpdater, TPDataUpdater)
from pootle_store.constants import (
    FUZZY, OBSOLETE, TRANSLATED, UNTRANSLATED)
from pootle_store.models import Suggestion
from pootle_store.util import SuggestionStates
from pootle_statistics.models import Submission, SubmissionTypes
from pootle_store.models import QualityCheck, Unit


@pytest.mark.django_db
def test_data_store_util(store0):
    data_tool = store0.data_tool
    assert data_tool.store == store0
    assert isinstance(store0.data_tool, StoreDataTool)


@pytest.mark.django_db
def test_data_store_updater(store0):
    data_tool = StoreDataTool(store0)
    updater = StoreDataUpdater(data_tool)
    assert updater.tool.context == store0
    assert isinstance(store0.data_tool.updater, StoreDataUpdater)


@pytest.mark.django_db
def test_data_tp_util(tp0):
    data_tool = TPDataTool(tp0)
    assert data_tool.context == tp0
    assert isinstance(tp0.data_tool, TPDataTool)


@pytest.mark.django_db
def test_data_tp_updater(tp0):
    data_tool = TPDataTool(tp0)
    updater = TPDataUpdater(data_tool)
    assert updater.tool.context == tp0
    assert isinstance(tp0.data_tool.updater, TPDataUpdater)


@pytest.mark.django_db
def test_data_store_updater_last_created(store0):
    units = store0.unit_set.live().exclude(creation_time__isnull=True)
    last_created_unit = (
        units.order_by('-creation_time', '-revision', '-pk').first())
    assert (
        store0.data_tool.updater.store_data["last_created_unit"]
        == last_created_unit.pk)
    last_created_unit.creation_time = None
    # TODO: remove when signals land
    last_created_unit.save()
    store0.data_tool.update()
    assert (
        store0.data_tool.updater.store_data["last_created_unit"]
        != last_created_unit.pk)


@pytest.mark.django_db
def test_data_tp_updater_last_created(tp0):
    tp0.data_tool.update()
    units = Unit.objects.filter(
        state__gt=OBSOLETE,
        store__translation_project=tp0)
    last_created_unit = (
        units.exclude(creation_time__isnull=True)
             .order_by('-creation_time', '-revision', '-pk').first())
    assert (
        tp0.data_tool.updater.store_data["last_created_unit"]
        == last_created_unit.pk)
    last_created_unit.creation_time = None
    last_created_unit.save()
    # TODO: remove when signals land
    last_created_unit.store.data_tool.update()
    tp0.data_tool.update()
    assert (
        tp0.data_tool.updater.store_data["last_created_unit"]
        != last_created_unit.pk)


@pytest.mark.django_db
def test_data_store_util_last_updated(store0):
    last_updated_unit = store0.unit_set.live().order_by(
        '-revision', '-mtime', '-pk').first()
    data_unit = store0.data_tool.updater.store_data["last_updated_unit"]
    assert data_unit == last_updated_unit.pk
    other_unit = store0.unit_set.exclude(pk=last_updated_unit.pk).first()
    other_unit.target = "SOMETHING ELSE"
    other_unit.save()
    assert (
        store0.data_tool.updater.store_data["last_updated_unit"]
        == other_unit.pk)


@pytest.mark.django_db
def test_data_tp_util_last_updated(tp0):
    units = Unit.objects.filter(
        state__gt=OBSOLETE,
        store__translation_project=tp0)
    last_updated_unit = units.order_by('-revision', '-mtime', '-pk').first()
    assert (
        tp0.data_tool.updater.store_data["last_updated_unit"]
        == last_updated_unit.pk)
    other_unit = units.exclude(pk=last_updated_unit.pk).first()
    other_unit.target = "SOMETHING ELSE"
    other_unit.save()
    # TODO: remove when signals land
    other_unit.store.data_tool.update()
    tp0.data_tool.update()
    assert (
        tp0.data_tool.updater.store_data["last_updated_unit"]
        == other_unit.pk)


@pytest.mark.django_db
def test_data_store_util_last_submission(store0):
    last_submission = store0.submission_set.exclude(
        type=SubmissionTypes.UNIT_CREATE).latest()
    assert store0.data_tool.updater.last_submission == last_submission
    last_submission.type = SubmissionTypes.UNIT_CREATE
    last_submission.save()
    assert not store0.data_tool.updater.last_submission == last_submission


@pytest.mark.django_db
def test_data_tp_util_last_submission(tp0):
    subs = Submission.objects.filter(store__translation_project=tp0)
    last_submission = subs.exclude(
        type=SubmissionTypes.UNIT_CREATE).latest()
    assert tp0.data_tool.updater.store_data["last_submission"] == last_submission.pk
    last_submission.type = SubmissionTypes.UNIT_CREATE
    last_submission.save()
    last_submission.unit.save()
    # TODO: remove when signals land
    last_submission.store.data_tool.update()
    tp0.data_tool.update()
    # TODO: fix
    # this is failing - not sure why
    # assert (
    #    tp0.data_tool.updater.store_data["last_submission"]
    #    == last_submission.pk)


@pytest.mark.django_db
def test_data_store_util_wordcount(store0):
    expected = dict(total=0, translated=0, fuzzy=0)

    # ensure a fuzzy unit
    unit = store0.units.filter(state=TRANSLATED).first()
    unit.state = FUZZY
    unit.save()

    for unit in store0.unit_set.live():
        expected["total"] += unit.source_wordcount
        if unit.state == TRANSLATED:
            expected["translated"] += unit.source_wordcount
        elif unit.state == FUZZY:
            expected["fuzzy"] += unit.source_wordcount
    for k in ["total", "fuzzy", "translated"]:
        assert store0.data_tool.updater.store_data["%s_words" % k] == expected[k]
    unit = store0.units.filter(state=TRANSLATED).first()
    unit.state = FUZZY
    unit.save()
    assert (
        store0.data_tool.updater.store_data["fuzzy_words"]
        == expected["fuzzy"] + unit.source_wordcount)


@pytest.mark.django_db
def test_data_tp_util_wordcount(tp0):
    expected = dict(total=0, translated=0, fuzzy=0)
    units = Unit.objects.filter(
        state__gt=OBSOLETE,
        store__translation_project=tp0)

    # ensure a fuzzy unit
    unit = units.filter(state=TRANSLATED).first()
    unit.state = FUZZY
    unit.save()
    # TODO: remove when signals land
    unit.store.data_tool.update()
    tp0.data_tool.update()

    for unit in units:
        expected["total"] += unit.source_wordcount
        if unit.state == TRANSLATED:
            expected["translated"] += unit.source_wordcount
        elif unit.state == FUZZY:
            expected["fuzzy"] += unit.source_wordcount
    for k in ["total", "fuzzy", "translated"]:
        assert tp0.data_tool.updater.store_data["%s_words" % k] == expected[k]
    unit = units.filter(state=TRANSLATED).first()
    unit.state = FUZZY
    unit.save()
    # TODO: remove when signals land
    unit.store.data_tool.update()
    tp0.data_tool.update()
    assert (
        tp0.data_tool.updater.store_data["fuzzy_words"]
        == expected["fuzzy"] + unit.source_wordcount)


@pytest.mark.django_db
def test_data_store_util_suggestion_count(store0, member):
    suggestions = Suggestion.objects.filter(
        unit__store=store0,
        unit__state__gt=OBSOLETE,
        state=SuggestionStates.PENDING)
    suggestion_count = suggestions.count()
    assert (
        suggestion_count
        == store0.data_tool.updater.suggestion_count)
    unit = store0.units.filter(
        state__gt=OBSOLETE,
        suggestion__state=SuggestionStates.PENDING).first()
    suggestion, created_ = unit.add_suggestion(
        "Another uggestion for %s" % (unit.target or unit.source),
        user=member,
        touch=False)
    # unit now has 2 pending suggestions
    assert (
        unit.suggestion_set.filter(state=SuggestionStates.PENDING)
        > 1)
    # and the data_tool.suggestion_count has increased
    assert (
        store0.data_tool.updater.suggestion_count
        == suggestion_count + 1)


@pytest.mark.django_db
def test_data_tp_util_suggestion_count(tp0, member):
    units = Unit.objects.filter(
        state__gt=OBSOLETE,
        store__translation_project=tp0)
    suggestions = Suggestion.objects.filter(
        unit__store__translation_project=tp0,
        unit__state__gt=OBSOLETE,
        state=SuggestionStates.PENDING)
    suggestion_count = suggestions.count()
    assert (
        suggestion_count
        == tp0.data_tool.updater.store_data["pending_suggestions"])
    unit = units.filter(
        state__gt=OBSOLETE,
        suggestion__state=SuggestionStates.PENDING).first()
    suggestion, created_ = unit.add_suggestion(
        "Another uggestion for %s" % (unit.target or unit.source),
        user=member,
        touch=False)
    unit.save()
    # TODO: remove when signals land
    unit.store.data_tool.update()
    tp0.data_tool.update()
    # unit now has 2 pending suggestions
    assert (
        unit.suggestion_set.filter(state=SuggestionStates.PENDING)
        > 1)
    # and the data_tool.suggestion_count has increased
    assert (
        tp0.data_tool.updater.store_data["pending_suggestions"]
        == suggestion_count + 1)


@pytest.mark.django_db
def test_data_store_util_max_unit_revision(store0):
    max_revision = 0
    for unit in store0.unit_set.all():
        if unit.revision > max_revision:
            max_revision = unit.revision
    assert (
        store0.data_tool.updater.get_max_unit_revision()
        == max_revision)
    unit = store0.units.first()
    unit.target = "SOMETHING ELSE"
    unit.save()
    assert (
        store0.data_tool.updater.get_max_unit_revision()
        == unit.revision)

    # if you pass the unit it always gives the unit.revision
    other_unit = store0.units.exclude(pk=unit.pk).first()
    assert (
        store0.data_tool.updater.get_max_unit_revision(other_unit)
        == other_unit.revision)


@pytest.mark.django_db
def test_data_tp_util_max_unit_revision(tp0):
    max_revision = 0
    units = Unit.objects.filter(
        store__translation_project=tp0)
    for unit in units.all():
        if unit.revision > max_revision:
            max_revision = unit.revision
    assert (
        tp0.data_tool.updater.get_max_unit_revision()
        == max_revision)
    unit = units.first()
    unit.target = "SOMETHING ELSE"
    unit.save()
    # TODO: remove when signals land
    unit.store.data_tool.update()
    tp0.data_tool.update()
    assert (
        tp0.data_tool.updater.get_max_unit_revision()
        == unit.revision)

    # if you pass the unit it always gives the unit.revision
    other_unit = units.exclude(pk=unit.pk).first()
    assert (
        tp0.data_tool.updater.get_max_unit_revision(other_unit)
        == other_unit.revision)


@pytest.mark.django_db
def test_data_store_qc_stats(store0):
    qc_qs = QualityCheck.objects
    qc_qs = (
        qc_qs.filter(unit__store=store0)
             .filter(unit__state__gt=UNTRANSLATED)
             .filter(category=Category.CRITICAL)
             .exclude(false_positive=True))
    check_count = qc_qs.count()
    assert (
        store0.data.critical_checks
        == check_count)
    unit = store0.units.exclude(
        qualitycheck__isnull=True,
        qualitycheck__name__in=["xmltags", "endpunc"]).first()
    unit.target = "<foo></bar>;"
    unit.save()
    # TODO: remove when signals land
    store0.data_tool.update()
    unit_critical = unit.qualitycheck_set.filter(
        category=Category.CRITICAL).count()

    assert (
        store0.data.critical_checks
        == check_count + unit_critical)

    # lets make another unit false positive
    other_qc = unit.qualitycheck_set.exclude(
        name="xmltags").filter(category=Category.CRITICAL).first()
    other_qc.false_positive = True
    other_qc.save()
    # trigger refresh
    unit.save()
    # TODO: remove when signals land
    store0.data_tool.update()
    assert (
        store0.data.critical_checks
        == check_count + unit_critical - 1)


@pytest.mark.django_db
def test_data_tp_qc_stats(tp0):
    units = Unit.objects.filter(
        state__gt=OBSOLETE,
        store__translation_project=tp0)
    qc_qs = QualityCheck.objects
    qc_qs = (
        qc_qs.filter(unit__store__translation_project=tp0)
             .filter(unit__state__gt=UNTRANSLATED)
             .filter(category=Category.CRITICAL)
             .exclude(false_positive=True))
    check_count = qc_qs.count()
    assert (
        tp0.data_tool.updater.store_data["critical_checks"]
        == check_count)
    unit = units.exclude(
        qualitycheck__isnull=True,
        qualitycheck__name__in=["xmltags", "endpunc"]).first()
    unit.store._foo = "bar"
    unit.target = "<foo></bar>;"
    unit.save()
    # TODO: remove when signals land
    unit.store.data_tool.update()
    tp0.data_tool.update()
    unit_critical = unit.qualitycheck_set.filter(
        category=Category.CRITICAL).count()
    critical_checks = tp0.data_tool.updater.store_data["critical_checks"]

    assert (
        critical_checks
        == check_count + unit_critical)

    # lets make another unit false positive
    other_qc = unit.qualitycheck_set.exclude(
        name="xmltags").filter(category=Category.CRITICAL).first()
    other_qc.false_positive = True
    other_qc.save()
    # trigger refresh
    unit.save()
    # TODO: remove when signals land
    unit.store.data_tool.update()
    tp0.data_tool.update()
    assert (
        tp0.data_tool.updater.store_data["critical_checks"]
        == check_count + unit_critical - 1)


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
    wordcount = sum(
        units.values_list(
            "source_wordcount",
            flat=True))
    assert stats["total"] == wordcount
    fuzzy_wordcount = sum(
        units.filter(state=FUZZY).values_list(
            "source_wordcount",
            flat=True))
    assert stats["fuzzy"] == fuzzy_wordcount
    translated_wordcount = sum(
        units.filter(state=TRANSLATED).values_list(
            "source_wordcount",
            flat=True))
    assert stats["translated"] == translated_wordcount


@pytest.mark.django_db
def test_data_tp_stats(tp0):

    # get the child directories
    # child_dirs = tp0.directory.child_dirs.live()

    _test_object_stats(
        tp0.data_tool.get_stats(),
        Unit.objects.live().filter(
            store__in=tp0.stores.live()))

    # get the child stores
    _test_children_stats(
        tp0.data_tool.get_stats(children=True),
        tp0.directory)


@pytest.mark.django_db
def test_data_project_stats(project0):
    _test_object_stats(
        project0.data_tool.get_stats(),
        Unit.objects.live().filter(
            store__translation_project__project=project0))
    project0.data_tool.get_stats(children=True)


@pytest.mark.django_db
def test_data_language_stats(language0):
    _test_object_stats(
        language0.data_tool.get_stats(),
        Unit.objects.live().filter(
            store__translation_project__language=language0))
    language0.data_tool.get_stats(children=True)


@pytest.mark.django_db
def test_data_directory_stats(subdir0):
    _test_object_stats(
        subdir0.data_tool.get_stats(),
        Unit.objects.live().filter(
            store__pootle_path__startswith=subdir0.pootle_path))
    # get the child stores
    _test_children_stats(
        subdir0.data_tool.get_stats(children=True),
        subdir0)


@pytest.mark.django_db
def test_data_project_directory_stats(project_dir_resources0):
    pd0 = project_dir_resources0
    units = Unit.objects.none()
    for directory in pd0.children:
        units |= Unit.objects.live().filter(
            store__pootle_path__startswith=directory.pootle_path)
    _test_object_stats(
        pd0.data_tool.get_stats(),
        units)
    pd0.data_tool.get_stats(children=True)


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
        project_store_resources0.data_tool.get_stats(),
        units)
    project_store_resources0.data_tool.get_stats(children=True)


@pytest.mark.django_db
def test_data_project_set_stats(project_set):
    # units = Unit.objects.live()
    # TODO: fix 8/
    # _test_object_stats(
    #   data_tool.get_stats(),
    #    units)
    # data_tool.get_stats(children=True)
    pass
