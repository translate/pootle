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

from pootle_comment import get_model as get_comment_model
from pootle_misc.checks import check_names
from pootle_statistics.models import (
    Submission, SubmissionFields, SubmissionTypes)

from pootle_store.fields import to_python
from pootle_store.models import Suggestion
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

    def __init__(self, submission_type, username, full_name, comment):
        self.submission_type = submission_type
        self.username = username
        self.full_name = full_name
        self.comment = comment

    @cached_property
    def user(self):
        return DisplayUser(self.username, self.full_name)

    @property
    def description(self):
        params = {
            'author': self.user.author_link
        }
        sugg_accepted_desc = _(u'Accepted suggestion from %(author)s', params)
        sugg_rejected_desc = _(u'Rejected suggestion from %(author)s', params)

        if self.comment:
            params.update({
                'comment': format_html(u'<span class="comment">{}</span>',
                                       self.comment),
            })
            sugg_accepted_desc = _(
                u'Accepted suggestion from %(author)s '
                u'with comment: %(comment)s',
                params
            )
            sugg_rejected_desc = _(
                u'Rejected suggestion from %(author)s '
                u'with comment: %(comment)s',
                params
            )

        description_dict = {
            SubmissionTypes.SUGG_ADD: _(u'Added suggestion'),
            SubmissionTypes.SUGG_ACCEPT: sugg_accepted_desc,
            SubmissionTypes.SUGG_REJECT: sugg_rejected_desc,
        }

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

    @property
    def suggestion_comment(self):
        return self.values['comment']


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
                self.submission.suggestion_full_name,
                self.submission.suggestion_comment,
            ).description
        )
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
    fields = [
        "type", "old_value", "new_value", "submitter_id", "creation_time",
        "field", "quality_check_id",
        "submitter__username", "submitter__email", "submitter__full_name",
        "suggestion_id", "suggestion__target_f", "suggestion__user__full_name",
        "suggestion__user__username", "quality_check__name"]

    def __init__(self, object):
        self.object = object

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
                         SubmissionFields.COMMENT, SubmissionFields.NONE])
            | Q(type__in=SubmissionTypes.SUGGESTION_TYPES))
        return (
            Submission.objects.filter(unit=self.object)
                              .filter(submission_filter)
                              .exclude(field=SubmissionFields.COMMENT,
                                       creation_time=self.object.commented_on)
                              .order_by("id"))

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
        has_creation_entry = (
            len(grouped_entries) > 0
            and grouped_entries[0]['datetime'] == self.object.creation_time)
        if has_creation_entry:
            grouped_entries[0]['created'] = True
        else:
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
        for key, values in grouped_timeline:
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
        item["comment"] = self.comment_dict.get(item["suggestion_id"])
        return self.entry_class(ProxySubmission(item)).entry
