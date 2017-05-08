# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import review
from pootle.core.utils.timezone import localdate
from pootle_store.constants import UNTRANSLATED
from pootle_store.models import Suggestion


@pytest.mark.django_db
def test_user_tp_score_update_suggestions(store0, member, member2):
    unit = store0.units.filter(state=UNTRANSLATED)[0]
    suggestions = review.get(Suggestion)
    suggestion_text = "made a suggestion!"

    # member adds a suggestion
    # score and sugg increase
    current_score = member.scores.get(
        tp=store0.translation_project,
        date=localdate())
    old_suggested = current_score.suggested

    old_score = round(current_score.score, 2)
    old_suggested = current_score.suggested
    old_translated = current_score.translated
    old_reviewed = current_score.reviewed
    sugg, added = suggestions().add(
        unit, suggestion_text, user=member)
    current_score = member.scores.get(
        tp=store0.translation_project,
        date=localdate())
    assert round(current_score.score, 2) == old_score
    assert (
        current_score.suggested
        == old_suggested + unit.unit_source.source_wordcount)
    assert current_score.translated == old_translated
    assert current_score.reviewed == old_reviewed

    # member2 reviews members suggestion
    # score and review increase
    m2_score = member2.scores.get(
        tp=store0.translation_project,
        date=localdate())
    old_m2_score = round(m2_score.score, 2)
    old_m2_suggested = m2_score.suggested
    old_m2_translated = m2_score.translated
    old_m2_reviewed = m2_score.reviewed
    suggestions([sugg], member2).accept()
    m2_score = member2.scores.get(
        tp=store0.translation_project,
        date=localdate())
    assert round(m2_score.score, 2) > old_m2_score
    assert (
        m2_score.reviewed
        == old_m2_reviewed + unit.unit_source.source_wordcount)
    assert m2_score.suggested == old_m2_suggested
    assert m2_score.translated == old_m2_translated


@pytest.mark.django_db
def test_user_tp_score_update_translated(store0, member, member2):
    # member translates another unit, by suggesting and
    # accepting own suggestion
    # score, suggested and translated increase
    suggestion_text = "made a suggestion!"
    suggestions = review.get(Suggestion)
    current_score = member.scores.get(
        tp=store0.translation_project,
        date=localdate())
    old_score = round(current_score.score, 2)
    old_suggested = current_score.suggested
    old_translated = current_score.translated
    old_reviewed = current_score.reviewed
    m2_score = member2.scores.get(
        tp=store0.translation_project,
        date=localdate())
    m2_old_score = round(m2_score.score, 2)
    m2_suggested = m2_score.suggested
    m2_translated = m2_score.translated
    m2_reviewed = m2_score.reviewed
    unit = store0.units.filter(state=UNTRANSLATED)[0]
    sugg, added = suggestions().add(
        unit, suggestion_text, user=member)
    suggestions([sugg], member2).accept()
    current_score = member.scores.get(
        tp=store0.translation_project,
        date=localdate())
    assert round(current_score.score, 2) > old_score
    assert current_score.reviewed == old_reviewed
    assert (
        current_score.suggested
        == old_suggested + unit.unit_source.source_wordcount)
    assert (
        current_score.translated
        == old_translated + unit.unit_source.source_wordcount)
    m2_score = member2.scores.get(
        tp=store0.translation_project,
        date=localdate())
    assert round(m2_score.score, 2) > m2_old_score
    assert m2_score.suggested == m2_suggested
    assert m2_score.translated == m2_translated
    assert (
        m2_score.reviewed
        == m2_reviewed + unit.unit_source.source_wordcount)


@pytest.mark.django_db
def test_user_tp_score_update_rejects(store0, member, member2):
    # member makes another suggestion then member2 rejects
    suggestion_text = "made a suggestion!"
    suggestions = review.get(Suggestion)
    current_score = member.scores.get(
        tp=store0.translation_project,
        date=localdate())
    old_score = round(current_score.score, 2)
    old_suggested = current_score.suggested
    old_translated = current_score.translated
    old_reviewed = current_score.reviewed
    m2_score = member2.scores.get(
        tp=store0.translation_project,
        date=localdate())
    m2_old_score = round(m2_score.score, 2)
    m2_suggested = m2_score.suggested
    m2_translated = m2_score.translated
    m2_reviewed = m2_score.reviewed
    unit = store0.units.filter(state=UNTRANSLATED)[0]
    sugg, added = suggestions().add(
        unit, suggestion_text, user=member)
    suggestions([sugg], member2).reject()
    current_score = member.scores.get(
        tp=store0.translation_project,
        date=localdate())
    assert round(current_score.score, 2) == old_score
    assert current_score.reviewed == old_reviewed
    assert current_score.translated == old_translated
    assert (
        current_score.suggested
        == old_suggested + unit.unit_source.source_wordcount)
    m2_score = member2.scores.get(
        tp=store0.translation_project,
        date=localdate())
    assert round(m2_score.score, 2) > m2_old_score
    assert m2_score.suggested == m2_suggested
    assert m2_score.translated == m2_translated
    assert (
        m2_score.reviewed
        == m2_reviewed + unit.unit_source.source_wordcount)
