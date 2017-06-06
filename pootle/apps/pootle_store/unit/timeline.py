# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict
from itertools import groupby

from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.html import format_html

from accounts.proxy import DisplayUser
from pootle.core.delegate import event_formatters, grouped_events
from pootle.core.proxy import BaseProxy
from pootle.i18n.gettext import ugettext_lazy as _
from pootle_checks.constants import CHECK_NAMES
from pootle_comment import get_model as get_comment_model
from pootle_log.utils import GroupedEvents, UnitLog
from pootle_statistics.models import (
    Submission, SubmissionFields, SubmissionTypes)
from pootle_store.constants import STATES_MAP
from pootle_store.fields import to_python
from pootle_store.models import Suggestion


ACTION_ORDER = {
    'unit_created': 0,
    'suggestion_created': 5,
    'suggestion_rejected': 5,
    'source_updated': 10,
    'state_changed': 10,
    'target_updated': 20,
    'suggestion_accepted': 25,
    'comment_updated': 30,
    'check_muted': 40,
    'check_unmuted': 40,
}


class UnitTimelineLog(UnitLog):
    @property
    def suggestion_qs(self):
        return Suggestion.objects


class SuggestionEvent(object):
    def __init__(self, suggestion, **kwargs):
        self.suggestion = suggestion

    @property
    def comment(self):
        comments = get_comment_model().objects.for_model(Suggestion)
        comments = comments.filter(
            object_pk=self.suggestion.id).values_list("comment", flat=True)
        if comments:
            return comments[0]

    @cached_property
    def user(self):
        return DisplayUser(self.suggestion.user.username,
                           self.suggestion.user.full_name)


class SuggestionAddedEvent(SuggestionEvent):

    @property
    def context(self):
        return dict(
            value=self.suggestion.target,
            description=_(u"Added suggestion"))


class SuggestionAcceptedEvent(SuggestionEvent):

    def __init__(self, suggestion, **kwargs):
        super(SuggestionAcceptedEvent, self).__init__(suggestion)

    @property
    def context(self):
        params = {
            'author': self.user.author_link}
        sugg_accepted_desc = _(u'Accepted suggestion from %(author)s', params)

        if self.comment:
            params.update({
                'comment': format_html(u'<span class="comment">{}</span>',
                                       self.comment),
            })
            sugg_accepted_desc = _(
                u'Accepted suggestion from %(author)s '
                u'with comment: %(comment)s',
                params)

        target = self.suggestion.target
        submission = self.suggestion.submission_set.filter(
            field=SubmissionFields.TARGET).first()
        if submission:
            target = submission.new_value
        return dict(
            value=target,
            translation=True,
            description=format_html(sugg_accepted_desc))


class SuggestionRejectedEvent(SuggestionEvent):

    @property
    def context(self):
        params = {
            'author': self.user.author_link}
        sugg_rejected_desc = _(u'Rejected suggestion from %(author)s', params)

        if self.comment:
            params.update({
                'comment': format_html(u'<span class="comment">{}</span>',
                                       self.comment),
            })
            sugg_rejected_desc = _(
                u'Rejected suggestion from %(author)s '
                u'with comment: %(comment)s',
                params)

        return dict(
            value=self.suggestion.target,
            description=format_html(sugg_rejected_desc))


class SubmissionEvent(object):
    def __init__(self, submission, **kwargs):
        self.submission = submission


class TargetUpdatedEvent(SubmissionEvent):
    @property
    def context(self):
        suggestion_accepted = (self.submission.suggestion_id
                               and self.submission.suggestion.is_accepted)
        if suggestion_accepted:
            return None

        return dict(
            value=self.submission.new_value,
            translation=True)


class UnitCreatedEvent(object):
    def __init__(self, unit_source, **kwargs):
        self.unit_source = unit_source
        self.target_event = kwargs.get("target_event")

    @property
    def context(self):
        ctx = dict(description=_(u"Unit created"))
        if self.target_event is not None:
            if self.target_event.value.old_value != '':
                ctx['value'] = self.target_event.value.old_value
                ctx['translation'] = True
        else:
            if self.unit_source.unit.istranslated():
                ctx['value'] = self.unit_source.unit.target
                ctx['translation'] = True

        return ctx


class UnitStateChangedEvent(SubmissionEvent):

    @property
    def context(self):
        return dict(
            value=format_html(
                u"{} <span class='timeline-arrow'></span> {}",
                STATES_MAP[int(to_python(self.submission.old_value))],
                STATES_MAP[int(to_python(self.submission.new_value))]),
            state=True)


class CommentUpdatedEvent(SubmissionEvent):
    @property
    def context(self):
        if self.submission.new_value:
            return dict(
                value=self.submission.new_value,
                sidetitle=_(u"Comment:"),
                comment=True)

        return dict(description=_(u"Removed comment"))


class CheckEvent(SubmissionEvent):
    @cached_property
    def check_name(self):
        return self.submission.quality_check.name

    @cached_property
    def check_url(self):
        return u''.join(
            [reverse('pootle-checks-descriptions'),
             '#', self.check_name])

    @property
    def check_link(self):
        return format_html(u"<a href='{}'>{}</a>", self.check_url,
                           CHECK_NAMES[self.check_name])


class CheckMutedEvent(CheckEvent):
    @property
    def context(self):
        return dict(
            description=format_html(_(
                u"Muted %(check_name)s check",
                {'check_name': self.check_link})))


class CheckUnmutedEvent(CheckEvent):
    @property
    def context(self):
        return dict(
            description=format_html(_(
                u"Unmuted %(check_name)s check",
                {'check_name': self.check_link})))


class Timeline(object):

    def __init__(self, obj):
        self.object = obj
        self.log = UnitTimelineLog(self.object)
        self.events_adapter = grouped_events.get(self.log.__class__)(self.log)

    def grouped_events(self, **kwargs):
        groups = []
        target_event = None
        for __, group in self.events_adapter.grouped_events(**kwargs):
            event_group = EventGroup(group, target_event)
            if event_group.target_event:
                target_event = event_group.target_event
            if event_group.events:
                groups.append(event_group.context)

        return groups


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


class EventGroup(object):
    def __init__(self, log_events, related_target_event=None):
        self.log_events = OrderedDict()
        self.related_target_event = related_target_event
        self.log_event_class = None
        for event in log_events:
            if self.log_event_class is None:
                self.log_event_class = event.__class__
            self.log_events[event.action] = event

    @cached_property
    def event_formatters(self):
        return event_formatters.gather(self.log_event_class)

    @property
    def target_event(self):
        return self.log_events.get('target_updated')

    @property
    def context_event(self):
        event = self.log_events.get('suggestion_accepted')
        if event is not None:
            return event
        event = self.log_events.get('target_updated')
        if event is not None:
            return event
        if len(self.log_events) > 0:
            return self.log_events.values()[0]

        return None

    @property
    def events(self):
        events = []
        for event_action in self.log_events:
            event_formatter_class = self.event_formatters.get(event_action)
            if event_formatter_class is not None:
                ctx = event_formatter_class(
                    self.log_events[event_action].value,
                    target_event=self.related_target_event).context
                if ctx is not None:
                    events.append(ctx)
        return events

    @property
    def user(self):
        if 'suggestion_accepted' in self.log_events:
            return self.log_events['suggestion_accepted'].user
        return self.context_event.user

    @property
    def context(self):
        return {
            'events': self.events,
            'via_upload': self.via_upload,
            'datetime': self.context_event.timestamp,
            'user': DisplayUser(
                self.user.username,
                self.user.full_name,
                self.user.email),
        }

    @property
    def via_upload(self):
        if isinstance(self.context_event.value, Submission):
            return self.context_event.value == SubmissionTypes.UPLOAD
        return False
