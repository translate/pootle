# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from translate.filters.decorators import Category

from django.db.models import Max

from pootle_data.tp_data import TPDataTool, TPDataUpdater
from pootle_store.constants import FUZZY, OBSOLETE, TRANSLATED, UNTRANSLATED
from pootle_store.models import Suggestion
from pootle_store.util import SuggestionStates
from pootle_statistics.models import Submission, SubmissionTypes
from pootle_store.models import QualityCheck, Unit

from .data_updater_store import _calc_word_counts


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
def test_data_tp_util_wordcount(tp0):
    WORDCOUNT_KEYS = ["total_words", "fuzzy_words", "translated_words"]
    units = Unit.objects.filter(
        state__gt=OBSOLETE,
        store__translation_project=tp0)
    # stats should always be correct
    original_stats = _calc_word_counts(units.all())
    update_data = tp0.data_tool.updater.get_store_data()
    for k in WORDCOUNT_KEYS:
        assert update_data[k] == original_stats[k]
        assert getattr(tp0.data, k) == original_stats[k]
    # make a translated unit fuzzy
    unit = units.filter(state=TRANSLATED).first()
    unit.state = FUZZY
    unit.save()
    updated_stats = _calc_word_counts(units.all())
    # TODO: remove with signals
    unit.store.data_tool.update()
    update_data = tp0.data_tool.updater.get_store_data()
    for k in WORDCOUNT_KEYS:
        assert update_data[k] == updated_stats[k]
    # TODO: remove with signals
    tp0.data_tool.update()
    for k in WORDCOUNT_KEYS:
        assert getattr(tp0.data, k) == updated_stats[k]
    assert (
        update_data["fuzzy_words"]
        == tp0.data.fuzzy_words
        == original_stats["fuzzy_words"] + unit.source_wordcount)
    assert (
        update_data["translated_words"]
        == tp0.data.translated_words
        == original_stats["translated_words"] - unit.source_wordcount)


# improve me
@pytest.mark.django_db
def test_data_tp_util_max_unit_revision(tp0):
    units = Unit.objects.filter(
        store__translation_project=tp0)
    original_revision = units.aggregate(
        revision=Max("revision"))["revision"]
    update_data = tp0.data_tool.updater.get_store_data()
    assert (
        update_data["max_unit_revision"]
        == tp0.data.max_unit_revision
        == tp0.data_tool.updater.get_max_unit_revision()
        == original_revision)
    unit = units.first()
    unit.target = "SOMETHING ELSE"
    unit.save()
    # TODO: remove with signals
    unit.store.data_tool.update()
    update_data = tp0.data_tool.updater.get_store_data()
    assert update_data["max_unit_revision"] == unit.revision
    # TODO: remove with signals
    tp0.data_tool.update()
    assert tp0.data.max_unit_revision == unit.revision

    # if you pass the unit it always gives the unit.revision
    other_unit = units.exclude(pk=unit.pk).first()
    tp0.data_tool.update(max_unit_revision=other_unit.revision)
    assert tp0.data.max_unit_revision == other_unit.revision


@pytest.mark.django_db
def test_data_tp_updater_last_created(tp0):
    units = Unit.objects.filter(
        state__gt=OBSOLETE,
        store__translation_project=tp0).exclude(creation_time__isnull=True)
    original_created_unit = (
        units.order_by('-creation_time', '-revision', '-pk').first())
    update_data = tp0.data_tool.updater.get_store_data()
    assert(
        update_data["last_created_unit"]
        == tp0.data.last_created_unit_id
        == tp0.data_tool.updater.get_last_created_unit()
        == original_created_unit.id)
    original_created_unit.creation_time = None
    original_created_unit.save()
    # TODO: remove when signals land
    original_created_unit.store.data_tool.update()
    # TODO: remove when signals land
    tp0.data_tool.update()
    update_data = tp0.data_tool.updater.get_store_data()
    assert(
        update_data["last_created_unit"]
        == tp0.data.last_created_unit_id
        == tp0.data_tool.updater.get_last_created_unit()
        != original_created_unit.id)
    # you can directly set the last created_unit_id
    tp0.data_tool.update(last_created_unit=original_created_unit.id)
    update_data = tp0.data_tool.updater.get_store_data()
    assert(
        tp0.data.last_created_unit_id
        == original_created_unit.id)
    # but the updater still calculates correctly
    assert(
        update_data["last_created_unit"]
        == tp0.data_tool.updater.get_last_created_unit()
        != original_created_unit.id)


@pytest.mark.django_db
def test_data_tp_util_last_submission(tp0):
    submissions = (
        Submission.objects.filter(store__translation_project=tp0)
                          .exclude(type=SubmissionTypes.UNIT_CREATE))
    original_submission = submissions.latest()
    update_data = tp0.data_tool.updater.get_store_data()
    assert(
        update_data["last_submission"]
        == tp0.data.last_submission_id
        == tp0.data_tool.updater.get_last_submission()
        == original_submission.id)
    original_submission.type = SubmissionTypes.UNIT_CREATE
    original_submission.save()
    # TODO: remove when signals land
    original_submission.store.data_tool.update()
    # TODO: remove when signals land
    tp0.data_tool.update()
    update_data = tp0.data_tool.updater.get_store_data()
    assert(
        update_data["last_submission"]
        == tp0.data.last_submission_id
        == tp0.data_tool.updater.get_last_submission()
        != original_submission.id)
    # you can directly set the last submission_id
    tp0.data_tool.update(last_submission=original_submission.id)
    update_data = tp0.data_tool.updater.get_store_data()
    assert(
        tp0.data.last_submission_id
        == original_submission.id)
    # but the updater still calculates correctly
    assert(
        update_data["last_submission"]
        == tp0.data_tool.updater.get_last_submission()
        != original_submission.id)


@pytest.mark.django_db
def test_data_tp_util_suggestion_count(tp0, member):
    units = Unit.objects.filter(
        state__gt=OBSOLETE,
        store__translation_project=tp0)
    suggestions = Suggestion.objects.filter(
        unit__store__translation_project=tp0,
        unit__state__gt=OBSOLETE,
        state=SuggestionStates.PENDING)
    original_suggestion_count = suggestions.count()
    update_data = tp0.data_tool.updater.get_store_data()
    assert(
        update_data["pending_suggestions"]
        == tp0.data.pending_suggestions
        == tp0.data_tool.updater.get_pending_suggestions()
        == original_suggestion_count)
    unit = units.filter(
        state__gt=OBSOLETE,
        suggestion__state=SuggestionStates.PENDING).first()
    unit_suggestion_count = unit.suggestion_set.filter(
        state=SuggestionStates.PENDING).count()
    suggestion, created_ = unit.add_suggestion(
        "Another suggestion for %s" % (unit.target or unit.source),
        user=member,
        touch=False)
    # unit now has an extra suggestion
    assert (
        unit.suggestion_set.filter(state=SuggestionStates.PENDING).count()
        == unit_suggestion_count + 1)
    # TODO: remove when signals land
    unit.store.data_tool.update()
    # TODO: remove when signals land
    tp0.data_tool.update()
    update_data = tp0.data_tool.updater.get_store_data()
    assert(
        update_data["pending_suggestions"]
        == tp0.data.pending_suggestions
        == tp0.data_tool.updater.get_pending_suggestions()
        == original_suggestion_count + 1)
    tp0.data_tool.update(pending_suggestions=1000000)
    update_data = tp0.data_tool.updater.get_store_data()
    assert(
        tp0.data.pending_suggestions
        == 1000000)
    assert(
        update_data["pending_suggestions"]
        == tp0.data_tool.updater.get_pending_suggestions()
        == original_suggestion_count + 1)


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
    store_data = tp0.data_tool.updater.get_store_data()
    assert (
        store_data["critical_checks"]
        == tp0.data.critical_checks
        == check_count)
    unit = units.exclude(
        qualitycheck__isnull=True,
        qualitycheck__name__in=["xmltags", "endpunc"]).first()
    unit.target = "<foo></bar>;"
    unit.save()
    # TODO: remove when signals land
    unit.store.data_tool.update()
    # TODO: remove when signals land
    tp0.data_tool.update()
    unit_critical = unit.qualitycheck_set.filter(
        category=Category.CRITICAL).count()
    store_data = tp0.data_tool.updater.get_store_data()
    assert (
        store_data["critical_checks"]
        == tp0.data.critical_checks
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
    # TODO: remove when signals land
    tp0.data_tool.update()
    store_data = tp0.data_tool.updater.get_store_data()
    assert (
        store_data["critical_checks"]
        == tp0.data.critical_checks
        == check_count + unit_critical - 1)
