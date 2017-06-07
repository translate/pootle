# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model
from django.utils.functional import cached_property

from pootle.core.delegate import comparable_event
from pootle.core.proxy import BaseProxy
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


class ComparableLogEvent(BaseProxy):

    _special_names = (x for x in BaseProxy._special_names
                      if x not in ["__lt__", "__gt__", "__call__"])

    def __cmp__(self, other):
        # valuable revisions are authoritative
        if self.revision is not None and other.revision is not None:
            if self.revision > other.revision:
                return 1
            elif self.revision < other.revision:
                return -1

        # timestamps have the next priority
        if self.timestamp and other.timestamp:
            if self.timestamp > other.timestamp:
                return 1
            elif self.timestamp < other.timestamp:
                return -1
        elif self.timestamp:
            return 1
        elif other.timestamp:
            return -1

        # conditions below are applied for events with equal timestamps
        # or without any
        if self.action == other.action == 'suggestion_created':
            if self.value.pk > other.value.pk:
                return 1
            elif self.value.pk < other.value.pk:
                return -1

        if self.unit.pk > other.unit.pk:
            return 1
        elif self.unit.pk < other.unit.pk:
            return -1

        return 0


class Log(object):
    include_meta = False

    @property
    def source_qs(self):
        return UnitSource.objects

    @property
    def suggestion_qs(self):
        return Suggestion.objects.exclude(creation_time__isnull=True)

    @property
    def submission_qs(self):
        return Submission.objects

    @property
    def created_units(self):
        return self.source_qs.select_related("unit", "created_by")

    @property
    def suggestions(self):
        return self.suggestion_qs.select_related(
            "unit", "user", "reviewer", "state", "unit__unit_source")

    @property
    def submissions(self):
        return self.submission_qs.select_related(
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
                     field="submitter_id", include_meta=None):
        if not users:
            if include_meta is None and self.include_meta or include_meta:
                return qs
            else:
                meta_users = get_user_model().objects.META_USERS
                return qs.exclude(**{"%s__username__in" % field: meta_users})

        return (
            qs.filter(**{field: list(users).pop()})
            if len(users) == 1
            else qs.filter(**{"%s__in" % field: users}))

    def filtered_suggestions(self, **kwargs):
        suggestions = self.suggestions
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
        suggestions = (added_suggestions | reviewed_suggestions)
        suggestions = self.filter_store(
            suggestions,
            kwargs.get("store"))
        suggestions = self.filter_path(
            suggestions,
            kwargs.get("path"))
        if kwargs.get("only") and kwargs["only"].get("suggestion"):
            suggestions = suggestions.only(*kwargs["only"]["suggestion"])
        return suggestions

    def filtered_submissions(self, **kwargs):
        ordered = kwargs.get("ordered", True)
        submissions = (
            self.filter_users(
                self.submissions,
                kwargs.get("users"),
                include_meta=kwargs.get("include_meta")))
        submissions = self.filter_path(
            submissions, kwargs.get("path"))
        submissions = (
            self.filter_timestamps(
                submissions,
                start=kwargs.get("start"),
                end=kwargs.get("end")))
        submissions = self.filter_store(
            submissions,
            kwargs.get("store"))
        if kwargs.get("only") and kwargs["only"].get("submission"):
            submissions = submissions.only(*kwargs["only"]["submission"])
        if ordered is False:
            submissions = submissions.order_by()
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

    def get_created_unit_events(self, **kwargs):
        for created_unit in self.filtered_created_units(**kwargs):
            yield self.event(
                created_unit.unit,
                created_unit.created_by,
                created_unit.unit.creation_time,
                "unit_created",
                created_unit)

    def get_submission_events(self, **kwargs):
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
                submission,
                revision=submission.revision)

    def get_suggestion_events(self, **kwargs):
        users = kwargs.get("users")
        for suggestion in self.filtered_suggestions(**kwargs):
            add_event = (
                ((not kwargs.get("start")
                  or (suggestion.creation_time
                      and suggestion.creation_time >= kwargs.get("start")))
                 and (not kwargs.get("end")
                      or (suggestion.creation_time
                          and suggestion.creation_time < kwargs.get("end")))
                 and (not users
                      or (suggestion.user_id in users))))
            review_event = (
                not suggestion.is_pending
                and ((not kwargs.get("start")
                      or (suggestion.review_time
                          and suggestion.review_time >= kwargs.get("start")))
                     and (not kwargs.get("end")
                          or (suggestion.review_time
                              and suggestion.review_time < kwargs.get("end")))
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
                    if suggestion.is_accepted
                    else "suggestion_rejected")
                yield self.event(
                    suggestion.unit,
                    suggestion.reviewer,
                    suggestion.review_time,
                    event_name,
                    suggestion)

    def get_events(self, **kwargs):
        event_sources = kwargs.pop("event_sources",
                                   ("submission", "suggestion", "unit_source"))
        if "unit_source" in event_sources:
            for event in self.get_created_unit_events(**kwargs):
                yield event
        if "suggestion" in event_sources:
            for event in self.get_suggestion_events(**kwargs):
                yield event
        if "submission" in event_sources:
            for event in self.get_submission_events(**kwargs):
                yield event


class StoreLog(Log):
    include_meta = True

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
    include_meta = True

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


class GroupedEvents(object):
    def __init__(self, log):
        self.log = log

    def sorted_events(self, start=None, end=None, users=None, reverse=False):
        comparable_event_class = comparable_event.get(self.log.__class__)
        events = sorted(
            (comparable_event_class(x)
             for x in self.log.get_events(start=start,
                                          end=end,
                                          users=users)), reverse=reverse)
        for event in events:
            yield event


class UserLog(Log):

    def __init__(self, user):
        self.user = user

    @property
    def source_qs(self):
        return self.user.created_units

    @property
    def suggestion_qs(self):
        return (
            self.user.suggestions.exclude(creation_time__isnull=True).all()
            | self.user.reviews.all())

    @property
    def submission_qs(self):
        return self.user.submission_set
