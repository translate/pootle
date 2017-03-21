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
    score_setting = 0
    score = 0
    reviewed = 0
    translated = 0
    suggested = 0

    def __init__(self, event):
        self.event = event

    @property
    def unit(self):
        return self.event.unit

    @property
    def score(self):
        return (
            self.score_setting
            * self.unit.unit_source.source_wordcount)

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
        return self.suggestion.unit.unit_source.source_wordcount


class SuggestionCreatedScore(BaseSuggestionScore):
    score_setting = settings.POOTLE_SCORES['suggestion_add']

    @property
    def suggested(self):
        return self.suggestion.unit.unit_source.source_wordcount


class SuggestionAcceptedScore(SuggestionReviewScore):
    score_setting = settings.POOTLE_SCORES['suggestion_accept']


class SuggestionRejectedScore(SuggestionReviewScore):
    score_setting = settings.POOTLE_SCORES['suggestion_reject']


class TargetUpdatedScore(EventScore):
    score_setting = settings.POOTLE_SCORES['target_updated']

    @property
    def translated(self):
        return self.unit.unit_source.source_wordcount


class SubmissionEventScore(EventScore):

    @property
    def submission(self):
        return self.event.value


class StateUpdatedScore(SubmissionEventScore):

    @property
    def state_fuzzied(self):
        return (
            self.submission.old_value == TRANSLATED
            and self.submission.new_value == FUZZY)

    @property
    def state_unfuzzied(self):
        return (
            self.submission.old_value == FUZZY
            and self.submission.new_value == TRANSLATED)

    @property
    def translated(self):
        return (
            self.unit.unit_source.source_wordcount
            if (self.submission.old_value == UNTRANSLATED
                and self.submission.new_value == TRANSLATED)
            else 0)

    @property
    def is_review(self):
        return self.state_fuzzied or self.state_unfuzzied

    @property
    def reviewed(self):
        return (
            self.unit.unit_source.source_wordcount
            if self.is_review
            else 0)

    @property
    def score_setting(self):
        if self.translated:
            return settings.POOTLE_SCORES['state_translated']
        elif self.state_fuzzied:
            return settings.POOTLE_SCORES['state_fuzzy']
        elif self.state_unfuzzied:
            return settings.POOTLE_SCORES['state_unfuzzy']


class CommentUpdatedScore(SubmissionEventScore):
    score_setting = settings.POOTLE_SCORES['comment_updated']
