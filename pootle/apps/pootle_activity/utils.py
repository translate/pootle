# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import event
from pootle_comment.models import Comment
from pootle_statistics.models import Submission, TranslationActionTypes


class Timeline(object):

    def __init__(self, context):
        self.context = context

    @property
    def comment_model(self):
        return Comment.objects

    @property
    def submission_model(self):
        return Submission.objects

    @property
    def events(self):
        comment_event = event.get(Comment)
        sub_event = event.get(Submission)

        for sub in self.submissions[:10]:
            yield sub_event(sub)

        for comment in self.comments[:10]:
            yield comment_event(comment)


class Event(object):

    def __init__(self, context):
        self.context = context


class CommentEvent(Event):
    action = "commented"

    def __str__(self):
        return str(self.context)

    @property
    def dt(self):
        return self.context.submit_date

    @property
    def user(self):
        return self.context.user


class SubmissionEvent(Event):

    def __str__(self):
        return str(self.context.unit)

    @property
    def dt(self):
        return self.context.creation_time

    @property
    def user(self):
        return self.context.submitter

    @property
    def translation_actions(self):
        return {
            getattr(TranslationActionTypes, x): x.lower()
            for x in dir(TranslationActionTypes)
            if not x.startswith("__")}

    @property
    def action(self):
        taction = self.context.get_submission_info().get(
            "translation_action_type")
        if taction:
            return self.translation_actions.get(taction)


class UserTimeline(Timeline):

    @property
    def submissions(self):
        return self.submission_model.filter(submitter_id=self.context.id)

    @property
    def comments(self):
        return self.comment_model.filter(user_id=self.context.id)


class LanguageTimeline(Timeline):

    @property
    def submissions(self):
        return self.submission_model.filter(
            unit__store__translation_project__language=self.context)

    @property
    def comments(self):
        return []
        return self.comment_model.filter(user_id=self.context.id)


class ProjectTimeline(Timeline):

    @property
    def submissions(self):
        return self.submission_model.filter(
            unit__store__translation_project__project=self.context)

    @property
    def comments(self):
        return []
        return self.comment_model.filter(user_id=self.context.id)


class StoreTimeline(Timeline):

    @property
    def submissions(self):
        return self.submission_model.filter(unit__store=self.context)

    @property
    def comments(self):
        return []
        return self.comment_model.filter(user_id=self.context.id)


class TPTimeline(Timeline):

    @property
    def submissions(self):
        return self.submission_model.filter(
            unit__store__translation_project=self.context)

    @property
    def comments(self):
        return []
        return self.comment_model.filter(user_id=self.context.id)
