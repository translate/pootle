# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import review
from pootle_store.models import Suggestion
from pootle_translationproject.contextmanagers import update_tp_after


class CriticalCheckTest(object):

    def __init__(self, unit):
        self.unit = unit

    def _test_check_data(self, original, updated):
        # check data
        assert (
            updated["store_checks_data"]["xmltags"]
            == original["store_checks_data"].get("xmltags", 0) + 1)
        assert (
            updated["tp_checks_data"]["xmltags"]
            == original["tp_checks_data"].get("xmltags", 0) + 1)

    def _test_scores(self, original, updated):
        # scores
        assert (
            updated["store_score"]["score"]
            > original["store_score"]["score"])
        assert (
            updated["store_score"]["translated"]
            > original["store_score"]["translated"])
        assert (
            updated["tp_score"]["score"]
            > original["tp_score"]["score"])
        assert (
            updated["tp_score"]["translated"]
            > original["tp_score"]["translated"])

    def _test_data(self, original, updated):
        # store and tp data
        assert (
            updated["store_data"]["critical_checks"]
            == original["store_data"]["critical_checks"] + 2)
        assert (
            updated["store_data"]["translated_words"]
            > original["store_data"]["translated_words"])
        assert (
            updated["store_data"]["pending_suggestions"]
            == original["store_data"]["pending_suggestions"])
        assert (
            updated["tp_data"]["critical_checks"]
            == original["tp_data"]["critical_checks"] + 2)
        assert (
            updated["tp_data"]["translated_words"]
            > original["tp_data"]["translated_words"])
        assert (
            updated["tp_data"]["pending_suggestions"]
            == original["tp_data"]["pending_suggestions"])

    def _test_revisions(self, original, updated):
        # unit and directory revisions
        assert updated["unit_revision"] > original["unit_revision"]
        assert (
            updated["store_data"]["max_unit_revision"]
            == updated["tp_data"]["max_unit_revision"]
            == updated["unit_revision"])
        assert (
            updated["unit_revision"]
            > original["store_data"]["max_unit_revision"])
        assert (
            updated["unit_revision"]
            > original["tp_data"]["max_unit_revision"])
        assert (
            updated["dir_revision"][0].value
            != original["dir_revision"][0].value)
        assert (
            updated["dir_revision"][0].pk
            == original["dir_revision"][0].pk)
        assert (
            updated["tp_dir_revision"][0].value
            != original["tp_dir_revision"][0].value)
        assert (
            updated["tp_dir_revision"][0].pk
            == original["tp_dir_revision"][0].pk)


class SuggestionAddTest(object):

    def __init__(self, unit):
        self.unit = unit

    def _test_check_data(self, original, updated):
        # check data
        assert (
            updated["store_checks_data"]
            == original["store_checks_data"])
        assert (
            updated["tp_checks_data"]
            == original["tp_checks_data"])

    def _test_scores(self, original, updated):
        # scores
        assert (
            updated["store_score"]["score"]
            == original["store_score"]["score"])
        assert (
            updated["store_score"]["translated"]
            == original["store_score"]["translated"])
        assert (
            updated["tp_score"]["score"]
            == original["tp_score"]["score"])
        assert (
            updated["tp_score"]["translated"]
            == original["tp_score"]["translated"])

    def _test_data(self, original, updated):
        # store and tp data
        assert (
            updated["store_data"]["critical_checks"]
            == original["store_data"]["critical_checks"])
        assert (
            updated["store_data"]["translated_words"]
            == original["store_data"]["translated_words"])
        assert (
            updated["store_data"]["pending_suggestions"]
            == original["store_data"]["pending_suggestions"] + 1)
        assert (
            updated["tp_data"]["critical_checks"]
            == original["tp_data"]["critical_checks"])
        assert (
            updated["tp_data"]["translated_words"]
            == original["tp_data"]["translated_words"])
        assert (
            updated["tp_data"]["pending_suggestions"]
            == original["tp_data"]["pending_suggestions"] + 1)

    def _test_revisions(self, original, updated):
        # unit and directory revisions
        assert updated["unit_revision"] == original["unit_revision"]
        assert (
            updated["store_data"]["max_unit_revision"]
            == original["store_data"]["max_unit_revision"])
        assert (
            updated["dir_revision"][0].value
            != original["dir_revision"][0].value)
        assert (
            updated["dir_revision"][0].pk
            == original["dir_revision"][0].pk)
        assert (
            updated["tp_dir_revision"][0].value
            != original["tp_dir_revision"][0].value)
        assert (
            updated["tp_dir_revision"][0].pk
            == original["tp_dir_revision"][0].pk)


class SuggestionAcceptTest(object):

    def __init__(self, unit):
        self.unit = unit

    def _test_check_data(self, original, updated):
        # check data
        assert (
            updated["store_checks_data"]
            == original["store_checks_data"])
        assert (
            updated["tp_checks_data"]
            == original["tp_checks_data"])

    def _test_scores(self, original, updated):
        # scores
        assert (
            updated["store_score"]["score"]
            > original["store_score"]["score"])
        assert (
            updated["store_score"]["translated"]
            > original["store_score"]["translated"])
        assert (
            updated["tp_score"]["score"]
            > original["tp_score"]["score"])
        assert (
            updated["tp_score"]["translated"]
            > original["tp_score"]["translated"])

    def _test_data(self, original, updated):
        # store and tp data
        assert (
            updated["store_data"]["critical_checks"]
            == original["store_data"]["critical_checks"])
        assert (
            updated["store_data"]["translated_words"]
            > original["store_data"]["translated_words"])
        assert (
            updated["store_data"]["pending_suggestions"]
            == original["store_data"]["pending_suggestions"] - 1)
        assert (
            updated["tp_data"]["critical_checks"]
            == original["tp_data"]["critical_checks"])
        assert (
            updated["tp_data"]["translated_words"]
            > original["tp_data"]["translated_words"])
        assert (
            updated["tp_data"]["pending_suggestions"]
            == original["tp_data"]["pending_suggestions"] - 1)

    def _test_revisions(self, original, updated):
        # unit and directory revisions
        assert updated["unit_revision"] > original["unit_revision"]
        assert (
            updated["store_data"]["max_unit_revision"]
            == updated["unit_revision"])
        assert (
            updated["store_data"]["max_unit_revision"]
            > original["store_data"]["max_unit_revision"])
        assert (
            updated["dir_revision"][0].value
            != original["dir_revision"][0].value)
        assert (
            updated["dir_revision"][0].pk
            == original["dir_revision"][0].pk)
        assert (
            updated["tp_dir_revision"][0].value
            != original["tp_dir_revision"][0].value)
        assert (
            updated["tp_dir_revision"][0].pk
            == original["tp_dir_revision"][0].pk)


class SuggestionRejectTest(object):

    def __init__(self, unit):
        self.unit = unit

    def _test_check_data(self, original, updated):
        # check data
        assert (
            updated["store_checks_data"]
            == original["store_checks_data"])
        assert (
            updated["tp_checks_data"]
            == original["tp_checks_data"])

    def _test_scores(self, original, updated):
        # scores
        assert (
            updated["store_score"]["score"]
            > original["store_score"]["score"])
        assert (
            updated["store_score"]["translated"]
            == original["store_score"]["translated"])
        assert (
            updated["tp_score"]["score"]
            > original["tp_score"]["score"])
        assert (
            updated["tp_score"]["translated"]
            == original["tp_score"]["translated"])

    def _test_data(self, original, updated):
        # store and tp data
        assert (
            updated["store_data"]["critical_checks"]
            == original["store_data"]["critical_checks"])
        assert (
            updated["store_data"]["translated_words"]
            == original["store_data"]["translated_words"])
        assert (
            updated["store_data"]["pending_suggestions"]
            == original["store_data"]["pending_suggestions"] - 1)
        assert (
            updated["tp_data"]["critical_checks"]
            == original["tp_data"]["critical_checks"])
        assert (
            updated["tp_data"]["translated_words"]
            == original["tp_data"]["translated_words"])
        assert (
            updated["tp_data"]["pending_suggestions"]
            == original["tp_data"]["pending_suggestions"] - 1)

    def _test_revisions(self, original, updated):
        # unit and directory revisions
        assert updated["unit_revision"] == original["unit_revision"]
        assert (
            updated["store_data"]["max_unit_revision"]
            == original["store_data"]["max_unit_revision"])
        assert (
            updated["dir_revision"][0].value
            != original["dir_revision"][0].value)
        assert (
            updated["dir_revision"][0].pk
            == original["dir_revision"][0].pk)
        assert (
            updated["tp_dir_revision"][0].value
            != original["tp_dir_revision"][0].value)
        assert (
            updated["tp_dir_revision"][0].pk
            == original["tp_dir_revision"][0].pk)


@pytest.mark.django_db
def test_contextmanager_update_tp_after_checks(tp0, store0, member,
                                               update_unit_test):

    # unit save
    unit = store0.units.exclude(
        qualitycheck__name="xmltags").first()
    with update_unit_test(CriticalCheckTest(unit)):
        with update_tp_after(tp0):
            unit.target = "<bad></target>."
            unit.save(user=member)

    # unit updated by update
    unit = store0.units.exclude(pk=unit.pk).exclude(
        qualitycheck__name="xmltags").first()
    store0.data.refresh_from_db()
    ttk = store0.deserialize(store0.serialize())
    ttk_unit = ttk.findid(unit.unitid)
    ttk_unit.target = "<bad></target>."
    with update_unit_test(CriticalCheckTest(unit)):
        with update_tp_after(tp0):
            store0.update(
                store=ttk,
                store_revision=store0.data.max_unit_revision + 1,
                user=member)


@pytest.mark.django_db
def test_contextmanager_update_tp_after_suggestion(tp0, store0, member,
                                                   update_unit_test):
    unit = store0.units.first()
    sugg_review = review.get(Suggestion)

    with update_unit_test(SuggestionAddTest(unit)):
        with update_tp_after(tp0):
            sugg_text = str(unit.source_f).replace("U", "X")
            sugg1, created_ = review.get(Suggestion)().add(
                unit,
                sugg_text,
                user=member)

    with update_unit_test(SuggestionAcceptTest(unit)):
        with update_tp_after(tp0):
            sugg_review(suggestions=[sugg1], reviewer=member).accept()

    unit = store0.units.exclude(pk=unit.pk).first()
    with update_unit_test(SuggestionAddTest(unit)):
        with update_tp_after(tp0):
            sugg_text = str(unit.source_f).replace("U", "X")
            sugg1, created_ = review.get(Suggestion)().add(
                unit,
                sugg_text,
                user=member)

    with update_unit_test(SuggestionRejectTest(unit)):
        with update_tp_after(tp0):
            sugg_review(suggestions=[sugg1], reviewer=member).reject()
