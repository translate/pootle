# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.functional import cached_property

from pootle_statistics.models import SubmissionFields, SubmissionTypes


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
