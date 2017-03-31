# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model
from django.utils.functional import cached_property

from pootle_statistics.models import (
    Submission, SubmissionFields, SubmissionTypes)
from pootle_store.models import Suggestion, UnitSource


class LogEvent(object):

    def __init__(self, unit, user, timestamp, action, value,
                 old_value=None, revision=None, **kwargs):
        self.unit = unit
        self.user = user
        self.timestamp = timestamp
        self.action = action
        self.value = value
        self.old_value = old_value
        self.revision = revision


class Log(object):

    @property
    def created_units(self):
        return UnitSource.objects.select_related("unit", "created_by")

    @property
    def suggestions(self):
        return Suggestion.objects.select_related(
            "unit", "user", "reviewer", "state", "unit__unit_source")

    @property
    def submissions(self):
        return Submission.objects.select_related(
            "unit", "submitter", "unit__unit_source")

    @cached_property
    def event(self):
        return LogEvent

    @cached_property
    def subfields(self):
        return {
            getattr(SubmissionFields, n): n.lower()
            for n
            in ["SOURCE", "TARGET", "STATE", "COMMENT", "CHECK"]}

    @cached_property
    def subtypes(self):
        return {
            getattr(SubmissionTypes, n): n.lower()
            for n in ["WEB", "UPLOAD", "SYSTEM"]}

    def filter_path(self, qs, path=None, field="unit__store__pootle_path"):
        return (
            qs.filter(**{"%s__startswith" % field: path})
            if path is not None
            else qs)

    def filter_store(self, qs, store=None, field="unit__store_id"):
        return (
            qs.filter(**{field: store})
            if store is not None
            else qs)

    def filter_timestamps(self, qs, start=None, end=None, field="creation_time"):
        if start is not None:
            qs = qs.filter(**{"%s__gte" % field: start})
        if end is not None:
            qs = qs.filter(**{"%s__lt" % field: end})
        return qs

    def filter_users(self, qs, users=None,
                     field="submitter_id", include_meta=False):
        if not users:
            meta_users = get_user_model().objects.META_USERS
            return (
                qs.exclude(
                    **{"%s__username__in" % field: meta_users})
                if not include_meta
                else qs)
        return (
            qs.filter(**{field: list(users).pop()})
            if len(users) == 1
            else qs.filter(**{"%s__in" % field: users}))

    def filtered_suggestions(self, **kwargs):
        suggestions = self.filter_store(
            self.suggestions,
            kwargs.get("store"))
        suggestions = self.filter_path(
            suggestions, kwargs.get("path"))
        added_suggestions = (
            self.filter_users(
                suggestions,
                kwargs.get("users"),
                field="user_id",
                include_meta=kwargs.get("include_meta"))
            & self.filter_timestamps(
                suggestions,
                start=kwargs.get("start"),
                end=kwargs.get("end")))
        reviewed_suggestions = (
            self.filter_users(
                suggestions,
                kwargs.get("users"),
                field="reviewer_id",
                include_meta=kwargs.get("include_meta"))
            & self.filter_timestamps(
                suggestions,
                start=kwargs.get("start"),
                end=kwargs.get("end"),
                field="review_time"))
        return added_suggestions | reviewed_suggestions

    def filtered_submissions(self, **kwargs):
        submissions = self.filter_store(
            self.submissions,
            kwargs.get("store"))
        submissions = (
            self.filter_users(
                submissions,
                kwargs.get("users"),
                include_meta=kwargs.get("include_meta")))
        submissions = self.filter_path(
            submissions, kwargs.get("path"))
        submissions = (
            self.filter_timestamps(
                submissions,
                start=kwargs.get("start"),
                end=kwargs.get("end")))
        return submissions

    def filtered_created_units(self, **kwargs):
        created_units = self.filter_store(
            self.created_units,
            kwargs.get("store"))
        created_units = self.filter_users(
            created_units,
            kwargs.get("users"),
            field="created_by_id",
            include_meta=kwargs.get("include_meta"))
        created_units = self.filter_path(
            created_units,
            kwargs.get("path"))
        created_units = self.filter_timestamps(
            created_units,
            start=kwargs.get("start"),
            end=kwargs.get("end"),
            field="unit__creation_time")
        return created_units

    def get_created_units(self, **kwargs):
        for created_unit in self.filtered_created_units(**kwargs):
            yield self.event(
                created_unit.unit,
                created_unit.created_by,
                created_unit.unit.creation_time,
                "unit_created",
                created_unit)

    def get_submissions(self, **kwargs):
        for submission in self.filtered_submissions(**kwargs):
            event_name = "state_changed"
            if submission.field == SubmissionFields.CHECK:
                event_name = (
                    "check_muted"
                    if submission.new_value == "0"
                    else "check_unmuted")
            elif submission.field == SubmissionFields.TARGET:
                event_name = "target_updated"
            elif submission.field == SubmissionFields.SOURCE:
                event_name = "source_updated"
            elif submission.field == SubmissionFields.COMMENT:
                event_name = "comment_updated"
            yield self.event(
                submission.unit,
                submission.submitter,
                submission.creation_time,
                event_name,
                submission)

    def get_suggestions(self, **kwargs):
        users = kwargs.get("users")
        for suggestion in self.filtered_suggestions(**kwargs):
            add_event = (
                ((not kwargs.get("start")
                  or (suggestion.creation_time >= kwargs.get("start")))
                 and (not kwargs.get("end")
                      or (suggestion.creation_time < kwargs.get("end")))
                 and (not users
                      or (suggestion.user_id in users))))
            review_event = (
                not suggestion.state.name == "pending"
                and ((not kwargs.get("start")
                      or (suggestion.review_time >= kwargs.get("start")))
                     and (not kwargs.get("end")
                          or (suggestion.review_time < kwargs.get("end")))
                     and (not users
                          or (suggestion.reviewer_id in users))))
            if add_event:
                yield self.event(
                    suggestion.unit,
                    suggestion.user,
                    suggestion.creation_time,
                    "suggestion_created",
                    suggestion)
            if review_event:
                event_name = (
                    "suggestion_accepted"
                    if suggestion.state.name == "accepted"
                    else "suggestion_rejected")
                yield self.event(
                    suggestion.unit,
                    suggestion.reviewer,
                    suggestion.review_time,
                    event_name,
                    suggestion)

    def get_events(self, **kwargs):
        for event in self.get_created_units(**kwargs):
            yield event
        for event in self.get_suggestions(**kwargs):
            yield event
        for event in self.get_submissions(**kwargs):
            yield event


class StoreLog(Log):

    def __init__(self, store):
        self.store = store

    @property
    def created_units(self):
        return super(
            StoreLog, self).created_units.filter(unit__store_id=self.store.id)

    @property
    def suggestions(self):
        return super(
            StoreLog, self).suggestions.filter(unit__store_id=self.store.id)

    @property
    def submissions(self):
        return super(
            StoreLog, self).submissions.filter(unit__store_id=self.store.id)

    def filter_store(self, qs, store=None, field="unit__store_id"):
        return qs


class UnitLog(Log):

    def __init__(self, unit):
        self.unit = unit

    @property
    def created_units(self):
        return super(
            UnitLog, self).created_units.filter(unit_id=self.unit.id)

    @property
    def suggestions(self):
        return super(
            UnitLog, self).suggestions.filter(unit_id=self.unit.id)

    @property
    def submissions(self):
        return super(
            UnitLog, self).submissions.filter(unit_id=self.unit.id)

    def filter_store(self, qs, store=None, field="unit__store_id"):
        return qs
