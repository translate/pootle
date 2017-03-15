# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

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
        return Suggestion.objects.select_related("unit", "user", "reviewer")

    @property
    def submissions(self):
        return Submission.objects.select_related("unit", "submitter")

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

    def filter_user(self, qs, user=None, field="submitter_id"):
        return (
            qs.filter(**{field: user})
            if user is not None
            else qs)

    def filtered_suggestions(self, **kwargs):
        suggestions = self.filter_store(
            self.suggestions,
            kwargs.get("store"))
        suggestions = self.filter_path(
            suggestions, kwargs.get("path"))
        added_suggestions = (
            self.filter_user(
                suggestions,
                kwargs.get("user"),
                field="user_id")
            & self.filter_timestamps(
                suggestions,
                start=kwargs.get("start"),
                end=kwargs.get("end")))
        reviewed_suggestions = (
            self.filter_user(
                suggestions,
                kwargs.get("user"),
                field="reviewer_id")
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
            self.filter_user(
                submissions,
                kwargs.get("user")))
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
        created_units = self.filter_user(
            created_units,
            kwargs.get("user"),
            field="created_by_id")
        created_units = self.filter_path(
            created_units,
            kwargs.get("path"))
        created_units = self.filter_timestamps(
            created_units,
            start=kwargs.get("start"),
            end=kwargs.get("end"),
            field="unit__creation_time")
        return created_units
