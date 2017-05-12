# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from itertools import groupby

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.urls import reverse
from django.utils.functional import cached_property

from accounts.proxy import DisplayUser
from pootle_comment import get_model as get_comment_model

from pootle.core.proxy import BaseProxy
from pootle_checks.constants import CHECK_NAMES
from pootle_log.utils import GroupedEvents, UnitLog
from pootle_statistics.models import (
    Submission, SubmissionFields, SubmissionTypes)
from pootle_statistics.proxy import SubmissionProxy
from pootle_store.constants import STATES_MAP
from pootle_store.fields import to_python
from pootle_store.models import Suggestion


ACTION_ORDER = {
    'unit_created': 0,
    'suggestion_created': 5,
    'suggestion_rejected': 5,
    'suggestion_accepted': 5,
    'source_updated': 10,
    'state_changed': 10,
    'target_updated': 20,
    'comment_updated': 30,
    'check_muted': 40,
    'check_unmuted': 40,
}


class UnitTimelineLog(UnitLog):
    pass


class SuggestionEvent(object):

    def __init__(self, submission_type, username, full_name, comment):
        self.submission_type = submission_type
        self.username = username
        self.full_name = full_name
        self.comment = comment

    @cached_property
    def user(self):
        return DisplayUser(self.username, self.full_name)


class TimelineEntry(object):

    def __init__(self, submission):
        self.submission = submission

    @property
    def entry_dict(self):
        return {
            'field': self.submission.field,
            'field_name': self.submission.field_name,
            'type': self.submission.type}

    def base_entry(self):
        entry = self.entry_dict
        entry['new_value'] = to_python(self.submission.new_value)
        return entry

    def qc_entry(self):
        entry = self.entry_dict
        check_name = self.submission.qc_name
        check_url = (
            u''.join(
                [reverse('pootle-checks-descriptions'),
                 '#', check_name]))
        entry.update(
            {'check_name': check_name,
             'check_display_name': CHECK_NAMES[check_name],
             'checks_url': check_url})
        return entry

    def state_change_entry(self):
        entry = self.entry_dict
        entry['old_value'] = STATES_MAP[int(to_python(self.submission.old_value))]
        entry['new_value'] = STATES_MAP[int(to_python(self.submission.new_value))]
        return entry

    def suggestion_entry(self):
        entry = self.entry_dict
        entry.update({'suggestion_text': self.submission.suggestion_target})
        return entry

    @property
    def entry(self):
        if self.submission.field == SubmissionFields.STATE:
            return self.state_change_entry()
        elif self.submission.suggestion:
            return self.suggestion_entry()
        elif self.submission.qc_name:
            return self.qc_entry()
        return self.base_entry()


class Timeline(object):

    entry_class = TimelineEntry
    fields = SubmissionProxy.timeline_fields

    def __init__(self, ob):
        self.object = ob

    @property
    def grouped_entries(self):
        grouped_entries = self.get_grouped_entries()
        grouped_entries = self.add_creation_entry(grouped_entries)
        grouped_entries.reverse()
        return grouped_entries

    @property
    def submissions(self):
        submission_filter = (
            Q(field__in=[SubmissionFields.TARGET, SubmissionFields.STATE,
                         SubmissionFields.COMMENT, SubmissionFields.NONE]))
        subs = (
            Submission.objects.filter(unit=self.object)
                              .filter(submission_filter))
        if self.object.changed and self.object.change.commented_on:
            subs = subs.exclude(
                field=SubmissionFields.COMMENT,
                creation_time=self.object.change.commented_on)
        return subs.order_by("id")

    @cached_property
    def submissions_values(self):
        return list(self.submissions.values(*self.fields))

    @property
    def suggestion_ids(self):
        return list(set([
            x["suggestion_id"]
            for x in self.submissions_values
            if x["suggestion_id"]
        ]))

    @cached_property
    def comment_dict(self):
        Comment = get_comment_model()
        return dict([
            # we need convert `object_pk` because it is TextField
            (int(x[0]), x[1])
            for x in Comment.objects.for_model(Suggestion)
                                    .filter(object_pk__in=self.suggestion_ids)
                                    .values_list("object_pk", "comment")
        ])

    def add_creation_entry(self, grouped_entries):
        User = get_user_model()
        created = {
            'created': True,
            'submitter': User.objects.get_system_user()}
        created['datetime'] = self.object.creation_time
        grouped_entries[:0] = [created]
        return grouped_entries

    def get_grouped_entries(self):
        grouped_entries = []
        grouped_timeline = groupby(
            self.submissions_values,
            key=lambda item: "\001".join([
                str(x) for x in
                [
                    item['submitter_id'],
                    item['creation_time'],
                    item['suggestion_id'],
                ]
            ])
        )

        # Target field timeline entry should go first
        def target_field_should_be_first(x):
            return 0 if x["field"] == SubmissionFields.TARGET else 1

        # Group by submitter id and creation_time because
        # different submissions can have same creation time
        for __, values in grouped_timeline:
            entry_group = {'entries': []}
            values = sorted(values, key=target_field_should_be_first)
            for item in values:
                if "submitter" not in entry_group:
                    entry_group['submitter'] = DisplayUser(
                        item["submitter__username"],
                        item["submitter__full_name"],
                        item["submitter__email"])
                if "datetime" not in entry_group:
                    entry_group['datetime'] = item['creation_time']
                via_upload = item["type"] == SubmissionTypes.UPLOAD
                entry_group["via_upload"] = via_upload
                entry_group['entries'].append(self.get_entry(item))
            grouped_entries.append(entry_group)
        return grouped_entries

    def get_entry(self, item):
        item["suggestion_comment"] = self.comment_dict.get(
            item["suggestion_id"])
        return self.entry_class(SubmissionProxy(item)).entry


class ComparableUnitTimelineLogEvent(BaseProxy):
    _special_names = (x for x in BaseProxy._special_names
                      if x not in ["__lt__", "__gt__"])

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
        action_order = ACTION_ORDER[self.action] - ACTION_ORDER[other.action]
        if action_order > 0:
            return 1
        elif action_order < 0:
            return -1
        if self.action == other.action:
            if self.value.pk > other.value.pk:
                return 1
            elif self.value.pk < other.value.pk:
                return -1

        return 0


class UnitTimelineGroupedEvents(GroupedEvents):
    def grouped_events(self, start=None, end=None, users=None):
        def _group_id(event):
            user_id = event.user.id
            if event.action == 'suggestion_accepted':
                user_id = event.value.user_id
            return '%s\001%s' % (event.timestamp, user_id)

        return groupby(
            self.sorted_events(
                start=start,
                end=end,
                users=users,
                reverse=True),
            key=_group_id)
