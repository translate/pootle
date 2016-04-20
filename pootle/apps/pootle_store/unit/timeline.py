# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from hashlib import md5
from itertools import groupby

from django.contrib.auth import get_user_model
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from pootle_misc.checks import check_names
from pootle_statistics.models import (
    Submission, SubmissionFields, SubmissionTypes)

from pootle_store.fields import to_python
from pootle_store.util import STATES_MAP


class DisplayUser(object):

    def __init__(self, username, full_name, email=None):
        self.username = username
        self.full_name = full_name
        self.email = email

    @property
    def author_link(self):
        return format_html(
            u'<a href="{}">{}</a>',
            self.get_absolute_url(),
            self.display_name)

    @property
    def display_name(self):
        return (
            self.full_name.strip()
            if self.full_name.strip()
            else self.username)

    def get_absolute_url(self):
        return reverse(
            'pootle-user-profile',
            args=[self.username])

    def gravatar_url(self, size=80):
        email_hash = md5(self.email).hexdigest()
        return (
            'https://secure.gravatar.com/avatar/%s?s=%d&d=mm'
            % (email_hash, size))


class SuggestionEvent(object):

    def __init__(self, submission_type, username, full_name):
        self.submission_type = submission_type
        self.username = username
        self.full_name = full_name

    @cached_property
    def user(self):
        return DisplayUser(self.username, self.full_name)

    @property
    def description(self):
        author_link = self.user.author_link
        description_dict = {
            SubmissionTypes.SUGG_ADD: _(u'Added suggestion'),
            SubmissionTypes.SUGG_ACCEPT: _(u'Accepted suggestion from %s',
                                           author_link),
            SubmissionTypes.SUGG_REJECT: _(u'Rejected suggestion from %s',
                                           author_link)}
        return description_dict.get(self.submission_type, None)


class ProxySubmission(object):

    def __init__(self, values):
        self.values = values

    @property
    def old_value(self):
        return self.values['old_value']

    @property
    def new_value(self):
        return self.values['new_value']

    @property
    def field(self):
        return self.values['field']

    @property
    def field_name(self):
        return SubmissionFields.NAMES_MAP.get(self.field, None)

    @property
    def type(self):
        return self.values['type']

    @property
    def qc_name(self):
        return self.values['quality_check__name']

    @property
    def suggestion(self):
        return self.values['suggestion_id']

    @property
    def suggestion_full_name(self):
        return self.values['suggestion__user__full_name']

    @property
    def suggestion_username(self):
        return self.values['suggestion__user__username']

    @property
    def suggestion_target(self):
        return self.values['suggestion__target_f']


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
             'check_display_name': check_names[check_name],
             'checks_url': check_url})
        return entry

    def state_change_entry(self):
        entry = self.entry_dict
        entry['old_value'] = STATES_MAP[int(to_python(self.submission.old_value))]
        entry['new_value'] = STATES_MAP[int(to_python(self.submission.new_value))]
        return entry

    def suggestion_entry(self):
        entry = self.entry_dict
        suggestion_description = mark_safe(
            SuggestionEvent(
                self.submission.type,
                self.submission.suggestion_username,
                self.submission.suggestion_full_name).description)
        entry.update(
            {'suggestion_text': self.submission.suggestion_target,
             'suggestion_description': suggestion_description})
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
    timeline_fields = [
        "type", "old_value", "new_value", "submitter_id", "creation_time",
        "field", "quality_check_id",
        "submitter__username", "submitter__email", "submitter__full_name",
        "suggestion_id", "suggestion__target_f", "suggestion__user__full_name",
        "suggestion__user__username", "quality_check__name"]

    def __init__(self, object):
        self.object = object

    @property
    def grouped_entries(self):
        grouped_entries = self.get_grouped_timeline_entries()
        grouped_entries = self.add_creation_entry(grouped_entries)
        grouped_entries.reverse()
        return grouped_entries

    @property
    def submissions(self):
        submission_filter = (
            Q(field__in=[SubmissionFields.TARGET, SubmissionFields.STATE,
                         SubmissionFields.COMMENT, SubmissionFields.NONE])
            | Q(type__in=SubmissionTypes.SUGGESTION_TYPES))
        return (
            Submission.objects.filter(unit=self.object)
                              .filter(submission_filter)
                              .exclude(field=SubmissionFields.COMMENT,
                                       creation_time=self.object.commented_on)
                              .order_by("id"))

    def add_creation_entry(self, grouped_entries):
        User = get_user_model()
        has_creation_entry = (
            len(grouped_entries) > 0
            and grouped_entries[0]['datetime'] == self.object.creation_time)
        if has_creation_entry:
            grouped_entries[0]['created'] = True
        else:
            created = {
                'created': True,
                'submitter': User.objects.get_system_user()}
            if self.object.creation_time:
                created['datetime'] = self.object.creation_time
            grouped_entries[:0] = [created]
        return grouped_entries

    def get_grouped_timeline_entries(self):
        grouped_entries = []
        grouped_timeline = groupby(
            self.submissions.values(*self.timeline_fields),
            key=lambda x: ("%d\001%s" % (x['submitter_id'], x['creation_time'])))
        # Group by submitter id and creation_time because
        # different submissions can have same creation time
        for key, values in grouped_timeline:
            entry_group = {'entries': []}
            for item in values:
                if "submitter" not in entry_group:
                    entry_group['submitter'] = DisplayUser(
                        item["submitter__username"],
                        item["submitter__full_name"],
                        item["submitter__email"])
                if "datetime" not in entry_group:
                    entry_group['datetime'] = item['creation_time']
                entry_group['entries'].append(
                    self.get_timeline_entry(item))
            grouped_entries.append(entry_group)
        return grouped_entries

    def get_timeline_entry(self, item):
        return self.entry_class(ProxySubmission(item)).entry
