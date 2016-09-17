# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from translate.filters.decorators import Category

from pootle_data.store_data import StoreDataTool
from pootle_store.constants import (
    FUZZY, OBSOLETE, TRANSLATED, UNTRANSLATED)
from pootle_store.models import Suggestion
from pootle_store.util import SuggestionStates
from pootle_statistics.models import SubmissionTypes
from pootle_store.models import QualityCheck


@pytest.mark.django_db
def test_data_store_util(store0):
    data_tool = StoreDataTool(store0)
    assert data_tool.store == store0


@pytest.mark.django_db
def test_data_store_util_last_created(store0):
    last_created_unit = (
        store0.unit_set.live()
                       .exclude(creation_time__isnull=True)
                       .order_by('-creation_time', '-revision').first())
    assert StoreDataTool(store0).last_created_unit == last_created_unit
    last_created_unit.creation_time = None
    last_created_unit.save()
    assert not StoreDataTool(store0).last_created_unit == last_created_unit


@pytest.mark.django_db
def test_data_store_util_last_updated(store0):
    last_updated_unit = store0.unit_set.live().order_by(
        '-revision', '-mtime').first()
    assert StoreDataTool(store0).last_updated_unit == last_updated_unit
    other_unit = store0.unit_set.exclude(pk=last_updated_unit.pk).first()
    other_unit.target = "SOMETHING ELSE"
    other_unit.save()
    assert StoreDataTool(store0).last_updated_unit == other_unit


@pytest.mark.django_db
def test_data_store_util_last_submission(store0):
    last_submission = store0.submission_set.exclude(
        type=SubmissionTypes.UNIT_CREATE).latest()
    assert StoreDataTool(store0).last_submission == last_submission
    last_submission.type = SubmissionTypes.UNIT_CREATE
    last_submission.save()
    assert not StoreDataTool(store0).last_submission == last_submission


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
    assert (
        sorted(StoreDataTool(store0).wordcount.items())
        == sorted(expected.items()))

    unit = store0.units.filter(state=TRANSLATED).first()
    unit.state = FUZZY
    unit.save()
    assert (
        StoreDataTool(store0).wordcount["fuzzy"]
        == expected["fuzzy"] + unit.source_wordcount)


@pytest.mark.django_db
def test_data_store_util_suggestion_count(store0, member):
    suggestions = Suggestion.objects.filter(
        unit__store=store0, unit__state__gt=OBSOLETE,
        state=SuggestionStates.PENDING)
    suggestion_count = suggestions.count()
    assert suggestion_count == StoreDataTool(store0).suggestion_count
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
        StoreDataTool(store0).suggestion_count
        == suggestion_count + 1)


@pytest.mark.django_db
def test_data_store_util_max_unit_revision(store0):
    max_revision = 0
    for unit in store0.unit_set.all():
        if unit.revision > max_revision:
            max_revision = unit.revision
    assert (
        StoreDataTool(store0).get_max_unit_revision()
        == max_revision)
    unit = store0.units.first()
    unit.target = "SOMETHING ELSE"
    unit.save()
    assert (
        StoreDataTool(store0).get_max_unit_revision()
        == unit.revision)

    # if you pass the unit it always gives the unit.revision
    other_unit = store0.units.exclude(pk=unit.pk).first()
    assert (
        StoreDataTool(store0).get_max_unit_revision(other_unit)
        == other_unit.revision)


@pytest.mark.django_db
def test_data_store_qc_stats(store0):
    qc_qs = QualityCheck.objects
    qc_qs = (
        qc_qs.filter(unit__store=store0)
             .filter(unit__state__gt=UNTRANSLATED)
             .exclude(false_positive=True))
    checks = dict(critical_count=0, checks={})
    for check in qc_qs:
        if check.category == Category.CRITICAL:
            checks["critical_count"] += 1
        if check.name not in checks["checks"]:
            checks["checks"][check.name] = 1
        else:
            checks["checks"][check.name] += 1
    assert (
        StoreDataTool(store0).checks["critical_count"]
        == checks["critical_count"])
    assert (
        sorted(StoreDataTool(store0).checks["checks"].items())
        == sorted(checks["checks"].items()))

    # no xml errors in test env
    assert (
        "xmltags" not in StoreDataTool(store0).checks["checks"])
    unit = store0.units.exclude(qualitycheck__isnull=True)[0]
    unit.target = "<foo></bar>;"
    unit.save()
    # we have an xml error now
    assert "xmltags" in StoreDataTool(store0).checks["checks"]
    num_of_checks = sum(
        c for c in StoreDataTool(store0).checks["checks"].values())
    # lets make another unit false positive
    other_qc = unit.qualitycheck_set.exclude(name="xmltags").first()
    other_qc.false_positive = True
    other_qc.save()
    # xml error is still there, and checks have decreased by 1
    assert "xmltags" in StoreDataTool(store0).checks["checks"]
    assert (
        sum(c for c in StoreDataTool(store0).checks["checks"].values())
        == num_of_checks - 1)
