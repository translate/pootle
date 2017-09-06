# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import timedelta

import pytest

from pytest_pootle.factories import StoreDBFactory

from translate.filters.decorators import Category

from django.db.models import Max

from pootle.core.delegate import crud, review
from pootle.core.signals import update_checks, update_data
from pootle_data.models import StoreChecksData
from pootle_data.store_data import (
    StoreChecksDataCRUD, StoreDataTool, StoreDataUpdater)
from pootle_statistics.models import Submission
from pootle_store.constants import FUZZY, OBSOLETE, TRANSLATED, UNTRANSLATED
from pootle_store.models import Suggestion
from pootle_store.models import QualityCheck, Unit


def _calc_word_counts(units):
    expected = dict(
        total_words=0, translated_words=0, fuzzy_words=0)
    for unit in units:
        expected["total_words"] += unit.unit_source.source_wordcount
        if unit.state == TRANSLATED:
            expected["translated_words"] += unit.unit_source.source_wordcount
        elif unit.state == FUZZY:
            expected["fuzzy_words"] += unit.unit_source.source_wordcount
    return expected


@pytest.mark.django_db
def test_data_store_checks_data_crud():
    store_data_crud = crud.get(StoreChecksData)
    assert isinstance(store_data_crud, StoreChecksDataCRUD)
    assert store_data_crud.qs.count() == StoreChecksData.objects.count()


@pytest.mark.django_db
def test_data_store_updater(store0):
    data_tool = StoreDataTool(store0)
    updater = StoreDataUpdater(data_tool)
    assert updater.tool.context == store0
    assert isinstance(store0.data_tool.updater, StoreDataUpdater)


@pytest.mark.django_db
def test_data_store_util_wordcount(store0):
    WORDCOUNT_KEYS = ["total_words", "fuzzy_words", "translated_words"]
    # stats should always be correct
    original_stats = _calc_word_counts(store0.units)
    update_data = store0.data_tool.updater.get_store_data()
    for k in WORDCOUNT_KEYS:
        assert update_data[k] == original_stats[k]
        assert getattr(store0.data, k) == original_stats[k]
    # make a translated unit fuzzy
    unit = store0.units.filter(state=TRANSLATED).first()
    unit.state = FUZZY
    unit.save()
    updated_stats = _calc_word_counts(store0.units)
    update_data = store0.data_tool.updater.get_store_data()
    for k in WORDCOUNT_KEYS:
        assert update_data[k] == updated_stats[k]
    for k in WORDCOUNT_KEYS:
        assert getattr(store0.data, k) == updated_stats[k]
    assert (
        update_data["fuzzy_words"]
        == store0.data.fuzzy_words
        == (original_stats["fuzzy_words"]
            + unit.unit_source.source_wordcount))
    assert (
        update_data["translated_words"]
        == store0.data.translated_words
        == (original_stats["translated_words"]
            - unit.unit_source.source_wordcount))


@pytest.mark.django_db
def test_data_store_util_max_unit_revision(store0):
    original_revision = store0.unit_set.aggregate(
        revision=Max("revision"))["revision"]
    update_data = store0.data_tool.updater.get_store_data()
    assert (
        update_data["max_unit_revision"]
        == store0.data.max_unit_revision
        == store0.data_tool.updater.get_max_unit_revision()
        == original_revision)
    unit = store0.units.first()
    unit.target = "SOMETHING ELSE"
    unit.save()
    update_data = store0.data_tool.updater.get_store_data()
    assert update_data["max_unit_revision"] == unit.revision
    assert store0.data.max_unit_revision == unit.revision

    # if you pass the unit it always gives the unit.revision
    other_unit = store0.units.exclude(pk=unit.pk).first()
    store0.data_tool.update(max_unit_revision=other_unit.revision)
    assert store0.data.max_unit_revision == other_unit.revision


@pytest.mark.django_db
def test_data_store_util_max_unit_mtime(store0):
    original_mtime = store0.unit_set.aggregate(
        mtime=Max("mtime"))["mtime"]
    update_data = store0.data_tool.updater.get_store_data()
    assert (
        update_data["max_unit_mtime"]
        == store0.data.max_unit_mtime
        == store0.data_tool.updater.get_max_unit_mtime()
        == original_mtime)
    unit = store0.units.first()
    unit.target = "SOMETHING ELSE"
    unit.save()
    update_data = store0.data_tool.updater.get_store_data()
    assert (
        update_data["max_unit_mtime"].replace(microsecond=0)
        == unit.mtime.replace(microsecond=0))
    assert (
        store0.data.max_unit_mtime.replace(microsecond=0)
        == unit.mtime.replace(microsecond=0))

    # if you pass the unit it always gives the unit.mtime
    other_unit = store0.units.exclude(pk=unit.pk).first()
    store0.data_tool.update(max_unit_mtime=other_unit.mtime)
    assert (
        store0.data.max_unit_mtime.replace(microsecond=0)
        == other_unit.mtime.replace(microsecond=0))


@pytest.mark.django_db
def test_data_store_updater_last_created(store0):
    units = store0.units.exclude(creation_time__isnull=True)
    original_created_unit = (
        units.order_by('-creation_time', '-revision', '-pk').first())
    update_data = store0.data_tool.updater.get_store_data()
    assert(
        update_data["last_created_unit"]
        == store0.data.last_created_unit_id
        == store0.data_tool.updater.get_last_created_unit()
        == original_created_unit.id)
    original_created_unit.creation_time = None
    original_created_unit.save()
    update_data = store0.data_tool.updater.get_store_data()
    assert(
        update_data["last_created_unit"]
        == store0.data.last_created_unit_id
        == store0.data_tool.updater.get_last_created_unit()
        != original_created_unit.id)
    # you can directly set the last created_unit_id
    store0.data_tool.update(last_created_unit=original_created_unit.id)
    update_data = store0.data_tool.updater.get_store_data()
    assert(
        store0.data.last_created_unit_id
        == original_created_unit.id)
    # but the updater still calculates correctly
    assert(
        update_data["last_created_unit"]
        == store0.data_tool.updater.get_last_created_unit()
        != original_created_unit.id)


@pytest.mark.django_db
def test_data_store_util_last_submission(store0):
    original_submission = Submission.objects.filter(
        unit__store=store0).latest()
    update_data = store0.data_tool.updater.get_store_data()
    assert(
        update_data["last_submission"]
        == store0.data.last_submission_id
        == store0.data_tool.updater.get_last_submission()
        == original_submission.id)
    original_submission.delete()
    # you can directly set the last submission_id
    store0.data_tool.update(last_submission=original_submission.id)
    update_data = store0.data_tool.updater.get_store_data()
    assert(
        store0.data.last_submission_id
        == original_submission.id)
    # but the updater still calculates correctly
    assert(
        update_data["last_submission"]
        == store0.data_tool.updater.get_last_submission()
        != original_submission.id)


@pytest.mark.django_db
def test_data_store_util_suggestion_count(store0, member):
    suggestions = Suggestion.objects.filter(
        unit__store=store0,
        unit__state__gt=OBSOLETE,
        state__name="pending")
    original_suggestion_count = suggestions.count()
    update_data = store0.data_tool.updater.get_store_data()
    assert(
        update_data["pending_suggestions"]
        == store0.data.pending_suggestions
        == store0.data_tool.updater.get_pending_suggestions()
        == original_suggestion_count)
    unit = store0.units.filter(
        state__gt=OBSOLETE,
        suggestion__state__name="pending").first()
    unit_suggestion_count = unit.suggestion_set.filter(
        state__name="pending").count()
    sugg, added = review.get(Suggestion)().add(
        unit,
        "Another suggestion for %s" % (unit.target or unit.source),
        user=member)

    # unit now has an extra suggestion
    assert (
        unit.suggestion_set.filter(state__name="pending").count()
        == unit_suggestion_count + 1)
    store0.data.refresh_from_db()
    update_data = store0.data_tool.updater.get_store_data()
    assert(
        update_data["pending_suggestions"]
        == store0.data.pending_suggestions
        == store0.data_tool.updater.get_pending_suggestions()
        == original_suggestion_count + 1)
    store0.data_tool.update(pending_suggestions=1000000)
    update_data = store0.data_tool.updater.get_store_data()
    assert(
        store0.data.pending_suggestions
        == 1000000)
    assert(
        update_data["pending_suggestions"]
        == store0.data_tool.updater.get_pending_suggestions()
        == original_suggestion_count + 1)


@pytest.mark.django_db
def test_data_store_critical_checks(store0):
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
    update_checks.send(
        unit.__class__,
        instance=unit,
        keep_false_positives=True)
    update_data.send(
        unit.store.__class__,
        instance=unit.store,
        keep_false_positives=True)
    assert (
        store0.data.critical_checks
        == check_count + unit_critical - 1)


@pytest.mark.django_db
def test_data_store_updater_fields(store0, stats_data_dict, stats_data_types):
    """Ensure we can get/set only some fields"""
    data_type = stats_data_types
    result = store0.data_tool.updater.get_store_data(fields=[data_type])
    original_values = {
        k: getattr(store0.data, k)
        for k in stats_data_dict}
    if data_type in store0.data_tool.updater.fk_fields:
        match = "%s_id" % data_type
    else:
        match = data_type
    assert (
        getattr(store0.data, match)
        == result[data_type])
    assert data_type in result.keys()
    if data_type in store0.data_tool.updater.fk_fields:
        new_value = None
    elif isinstance(result[data_type], int):
        new_value = result[data_type] + 5
    else:
        new_value = result[data_type] + timedelta(seconds=5)
    kwargs = {
        "fields": [data_type],
        data_type: "FOO"}
    result = store0.data_tool.updater.get_store_data(**kwargs)
    assert result[data_type] == "FOO"
    kwargs[data_type] = new_value
    store0.data_tool.updater.update(**kwargs)
    # refresh fks
    store0.data.refresh_from_db()
    for k, v in original_values.items():
        if k == data_type:
            assert getattr(store0.data, k) == new_value
        else:
            assert (
                getattr(store0.data, k)
                == original_values[k])


def _calculate_checks(qc_qs):
    checks = {}
    checks_values = qc_qs.exclude(false_positive=True).values_list(
        "category", "name")
    for category, name in checks_values:
        checks[(category, name)] = checks.get((category, name), 0) + 1
    return checks


@pytest.mark.django_db
def test_data_store_updater_checks(store0):
    qc_qs = QualityCheck.objects
    qc_qs = (
        qc_qs.filter(unit__store=store0)
             .filter(unit__state__gt=UNTRANSLATED)
             .exclude(false_positive=True))
    original_checks = _calculate_checks(qc_qs.all())
    check_data = store0.check_data.all().values_list("category", "name", "count")
    assert len(check_data) == len(original_checks)
    for (category, name), count in original_checks.items():
        assert (category, name, count) in check_data
    unit = store0.units.exclude(
        qualitycheck__isnull=True,
        qualitycheck__name__in=["xmltags", "endpunc"]).first()
    original_unit_target = unit.target
    unit.target = "<foo></bar>;"
    unit.save()
    checks = _calculate_checks(qc_qs.all())
    check_data = store0.check_data.all().values_list("category", "name", "count")

    assert len(check_data) == len(checks)
    for (category, name), count in checks.items():
        assert (category, name, count) in check_data

    unit = Unit.objects.get(id=unit.id)
    unit.target = original_unit_target
    unit.save()

    check_data = store0.check_data.all().values_list("category", "name", "count")

    assert len(check_data) == len(original_checks)
    for (category, name), count in original_checks.items():
        assert (category, name, count) in check_data


@pytest.mark.django_db
def test_data_store_updater_no_fields(store0):
    assert (
        store0.data_tool.updater.get_store_data(fields=[])
        == dict(fields=[], max_unit_revision=0))
    orig_words = store0.data.total_words
    store0.data.total_words = orig_words + 3
    store0.data.save()
    store0.data_tool.update()
    assert store0.data.total_words == orig_words
    store0.data.total_words = orig_words + 3
    store0.data.save()
    store0.data_tool.update(fields=[])
    assert store0.data.total_words == orig_words + 3


@pytest.mark.django_db
def test_data_store_updater_defaults(tp0):
    store = StoreDBFactory(
        name="store_with_no_units.po",
        parent=tp0.directory,
        translation_project=tp0)
    fields = store.data_tool.updater.aggregate_fields
    aggregate_data = store.data_tool.updater.get_aggregate_data(
        fields=fields)
    for k in fields:
        if k in store.data_tool.updater.aggregate_defaults:
            assert (
                aggregate_data[k]
                == store.data_tool.updater.aggregate_defaults[k])
