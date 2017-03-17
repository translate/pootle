# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings

from pootle_store.constants import FUZZY, TRANSLATED, UNTRANSLATED


class EventScore(object):

    score = 0
    reviewed = 0
    translated = 0
    suggested = 0

    def __init__(self, event):
        self.event = event

    @property
    def unit(self):
        return self.event.unit

    def get_score(self):
        return dict(
            score=self.score,
            translated=self.translated,
            reviewed=self.reviewed,
            suggested=self.suggested)


class BaseSuggestionScore(EventScore):

    @property
    def suggestion(self):
        return self.event.value


class SuggestionReviewScore(BaseSuggestionScore):

    @property
    def reviewed(self):
        return self.suggestion.unit.source_wordcount


class SuggestionAddedScore(BaseSuggestionScore):
    score = 0

    @property
    def suggested(self):
        return self.suggestion.unit.source_wordcount


class SuggestionAcceptedScore(SuggestionReviewScore):
    score = settings.POOTLE_SCORES['SUGGESTION_ACCEPT']


class SuggestionRejectedScore(SuggestionReviewScore):
    score = settings.POOTLE_SCORES['SUGGESTION_REJECT']


class TargetUpdatedScore(EventScore):
    score = settings.POOTLE_SCORES['TARGET_UPDATED']

    @property
    def translated(self):
        return self.unit.source_wordcount


class SubmissionEventScore(EventScore):
    @property
    def submission(self):
        return self.event.value


class StateUpdatedScore(SubmissionEventScore):

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
    def translated(self):
        return (
            self.submission.old_value == UNTRANSLATED
            and self.submission.new_value == TRANSLATED)

    @property
    def untranslated(self):
        return (
            (self.submission.old_value == FUZZY
             or self.submission.old_value == TRANSLATED)
            and self.submission.new_value == FUZZY)

    @property
    def is_review(self):
        return self.fuzzied or self.unfuzzied

    @property
    def reviewed(self):
        if self.is_review:
            return self.unit.source_wordcount

    @property
    def score(self):
        if self.translated:
            return settings.POOTLE_SCORES['STATE_TRANSLATED']
        elif self.fuzzied:
            return settings.POOTLE_SCORES['STATE_FUZZY']
        elif self.unfuzzied:
            return settings.POOTLE_SCORES['STATE_UNFUZZY']
        elif self.untranslated:
            return settings.POOTLE_SCORES['STATE_UNTRANSLATED']


class CommentUpdatedScore(SubmissionEventScore):
    @property
    def score(self):
        return settings.POOTLE_SCORES['COMMENT_UPDATED']
