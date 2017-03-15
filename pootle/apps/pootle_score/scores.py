# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import wordcount
from pootle_store.constants import FUZZY, TRANSLATED


SCORE_SUGGESTION_ACCEPT = .1
SCORE_SUGGESTION_REJECT = .1
SCORE_COMMENT_UPDATED = .1
SCORE_TARGET_UPDATED = .3
SCORE_STATE_TRANSLATED = .6
SCORE_STATE_FUZZY = .1
SCORE_STATE_UNFUZZY = .1


class EventScore(object):

    score = 0
    reviewed_words = 0
    translated_words = 0
    suggested_words = 0

    def __init__(self, event):
        self.event = event

    @property
    def unit(self):
        return self.event.unit

    @property
    def wc(self):
        return wordcount.get(self.unit.__class__)

    def get_score(self):
        return dict(
            score=self.score,
            translated_words=self.translated_words,
            reviewed_words=self.reviewed_words)


class BaseSuggestionScore(EventScore):

    @property
    def suggestion(self):
        return self.event.value


class SuggestionReviewScore(BaseSuggestionScore):

    @property
    def reviewed_words(self):
        return self.wc(self.suggestion.target_f)


class SuggestionAddedScore(BaseSuggestionScore):
    score = 0

    @property
    def suggested_words(self):
        return self.wc(self.suggestion.target_f)


class SuggestionAcceptedScore(SuggestionReviewScore):
    score = SCORE_SUGGESTION_ACCEPT


class SuggestionRejectedScore(SuggestionReviewScore):
    score = SCORE_SUGGESTION_REJECT


class TargetUpdatedScore(EventScore):
    score = SCORE_TARGET_UPDATED

    @property
    def translated_words(self):
        return self.wc(self.unit.target_f)


class StateUpdatedScore(EventScore):

    @property
    def fuzzied(self):
        return (
            self.submission.old_value == TRANSLATED
            and self.submission.new_value == FUZZY)

    @property
    def unfuzzied(self):
        return (
            self.submission.old_value == FUZZY
            and self.submission.new_value == TRANSLATED)

    @property
    def submission(self):
        return self.event.value

    @property
    def is_review(self):
        return self.fuzzied or self.unfuzzied

    @property
    def reviewed_words(self):
        if self.is_review:
            return self.wc(self.unit.target_f)

    @property
    def score(self):
        if self.translated:
            return SCORE_STATE_TRANSLATED
        elif self.fuzzied:
            return SCORE_STATE_FUZZY
        elif self.unfuzzied:
            return SCORE_STATE_UNFUZZY
