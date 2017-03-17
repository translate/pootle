# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import datetime

from django.conf import settings

from pootle_log.utils import LogEvent

from pootle_score.scores import (CommentUpdatedScore, SuggestionAddedScore,
                                 SuggestionAcceptedScore,
                                 SuggestionRejectedScore,
                                 StateUpdatedScore, TargetUpdatedScore)


def test_suggestion_accepted_score():
    class DummyUnit(object):
        def __init__(self, source_wordcount):
            self.source_wordcount = source_wordcount

    class DummySuggestion(object):
        def __init__(self, unit):
            self.unit = unit

    ts = datetime.now()
    unit = DummyUnit(3)
    suggestion = DummySuggestion(unit)
    event = LogEvent(unit, None, ts, "suggestion_accepted", suggestion)
    score = SuggestionAcceptedScore(event)
    assert score.reviewed == unit.source_wordcount
    assert score.score == settings.POOTLE_SCORES['SUGGESTION_ACCEPT']
    assert score.suggested == 0
    assert score.translated == 0
