# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.functional import cached_property
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from pootle.core.delegate import event_formatters, profile
from pootle.i18n.gettext import ugettext as _
from pootle_store.constants import STATES_MAP
from pootle_store.fields import to_python


class FormattedEvent(object):

    def __init__(self, event):
        self.event = event

    @property
    def event_types(self):
        return {
            1: mark_safe(
                '<i title="%s" class="icon icon-web-translate"></i>'
                % _("Web update")),
            5: mark_safe(
                '<i title="%s" class="icon icon-file"></i>'
                % _("File sync"))}

    @property
    def avatar(self):
        return self.user_profile.avatar

    @property
    def timestamp(self):
        return self.event.timestamp

    @cached_property
    def user_profile(self):
        return profile.get(self.user.__class__)(self.user)

    @property
    def user(self):
        return self.event.user

    @property
    def formatted_unit(self):
        return mark_safe('<a href="">%s</a>' % self.event.value.unit.id)

    @property
    def change(self):
        return ""

    @property
    def formatted_revision(self):
        return ""

    @property
    def changes(self):
        return ((self.message, self.change), )

    @property
    def revision(self):
        return None

    @property
    def css_class(self):
        return ""


class FormattedSubmissionEvent(FormattedEvent):

    @property
    def formatted_revision(self):
        if self.revision:
            return " (r%s)" % self.revision
        else:
            return ""

    @property
    def method(self):
        return self.event_types[self.event.value.type]

    @property
    def revision(self):
        return self.event.value.revision


class UnitCreatedEvent(FormattedEvent):

    @property
    def action(self):
        return _("Unit created")

    @property
    def method(self):
        if self.event.value.created_with:
            return self.event_types[self.event.value.created_with]
        return self.event_types[5]

    @property
    def message(self):
        return mark_safe(
            _("Unit %s created"
              % (self.formatted_unit)))


class UnitStateChangedEvent(FormattedSubmissionEvent):

    @property
    def css_class(self):
        return "evt-state-changed"

    @property
    def action(self):
        return _("State changed")

    @property
    def message(self):
        if self.event.value.revision:
            revision = " (r%s)" % self.event.value.revision
        else:
            revision = ""
        return mark_safe(
            _("State changed for %s%s"
              % (self.formatted_unit,
                 revision)))

    @property
    def change(self):
        message = format_html(
            u"{} <span class='timeline-arrow'></span> {}",
            STATES_MAP[int(to_python(self.event.value.old_value))],
            STATES_MAP[int(to_python(self.event.value.new_value))])
        return message


class UnitSourceUpdatedEvent(FormattedSubmissionEvent):

    @property
    def action(self):
        return _("Source updated")

    @property
    def message(self):
        return mark_safe(
            _("Translation updated for %s at revision %s"
              % (self.formatted_unit, self.event.value.revision)))

    @property
    def change(self):
        return self.event.value.new_value


class UnitTargetUpdatedEvent(FormattedSubmissionEvent):

    @property
    def action(self):
        return _("Translation updated")

    @property
    def message(self):
        return mark_safe(
            _("%s for %s%s"
              % (self.action,
                 self.formatted_unit,
                 self.formatted_revision)))

    @property
    def change(self):
        return self.event.value.new_value


class SuggestionAddedEvent(FormattedEvent):

    @property
    def action(self):
        return _("Suggestion added")

    @property
    def message(self):
        return mark_safe(
            _("Suggestion (%s) added for %s"
              % (self.event.value.id, self.formatted_unit)))

    @property
    def method(self):
        return self.event_types[1]

    @property
    def change(self):
        return self.event.value.target


class SuggestionAcceptedEvent(FormattedEvent):

    @property
    def action(self):
        return _("Suggestion (%s) accepted" % self.event.value.id)

    @property
    def message(self):
        return mark_safe(
            _("%s for %s"
              % (self.action, self.formatted_unit)))

    @property
    def method(self):
        return self.event_types[1]


class SuggestionRejectedEvent(FormattedEvent):

    @property
    def action(self):
        return _("Suggestion (%s) rejected" % self.event.value.id)

    @property
    def message(self):
        return mark_safe(
            _("%s for %s"
              % (self.action, self.formatted_unit)))

    @property
    def method(self):
        return self.event_types[1]


class CheckMutedEvent(FormattedEvent):

    @property
    def message(self):
        return mark_safe(
            _('Check "%s" muted for %s'
              % (self.event.value.quality_check.name, self.formatted_unit)))

    @property
    def method(self):
        return self.event_types[1]


class CheckUnmutedEvent(FormattedEvent):

    @property
    def message(self):
        return mark_safe(
            _('Check "%s" unmuted for %s'
              % (self.event.value.quality_check.name, self.formatted_unit)))

    @property
    def method(self):
        return self.event_types[1]


class CommentUpdatedEvent(FormattedEvent):

    @property
    def message(self):
        return mark_safe(
            _('Comment updated for %s' % self.formatted_unit))

    @property
    def method(self):
        return ""


class GroupedRejectionEvent(FormattedEvent):

    def __init__(self, context, events):
        self.context = context
        self.events = events

    @property
    def action(self):
        return _("%s suggestions rejected " % len(self.events))

    @property
    def formatted_unit(self):
        formatted = (
            "(%s)"
            % (", ".join(str(ev.value.unit.id) for ev in self.events)))
        return formatted

    @property
    def method(self):
        return ""

    @property
    def user(self):
        for event in self.events:
            return event.user

    @property
    def changes(self):
        return ((self.action, ""))


class GroupedCreationEvent(FormattedEvent):

    def __init__(self, context, events):
        self.context = context
        self.events = events

    @property
    def action(self):
        return _("%s units created" % len(self.events))

    @property
    def formatted_unit(self):
        formatted = (
            "(%s)"
            % (", ".join(str(ev.value.unit.id) for ev in self.events)))
        return formatted

    @property
    def method(self):
        return ""

    @property
    def user(self):
        for event in self.events:
            return event.user

    @property
    def changes(self):
        return ((self.action, ""))


class GroupedEvent(FormattedEvent):

    def __init__(self, context, events):
        self.context = context
        self.events = events

    @property
    def formatters(self):
        return event_formatters.gather(self.context.__class__)

    @cached_property
    def event_group(self):
        from itertools import groupby
        groups = []
        creation_group = []
        reject_groups = {}
        grouped_events = groupby(
            self.events,
            key=lambda x: (x.timestamp, x.unit))
        for (unit, timestamp), events in grouped_events:
            events = list(events)
            actions = [ev.action for ev in events]
            event_group = []
            if "suggestion_created" in actions:
                for event in events:
                    if event.action == "suggestion_created":
                        event_group.append(
                            self.formatters["suggestion_created"](event))
            if "suggestion_accepted" in actions:
                for event in events:
                    if event.action == "suggestion_accepted":
                        event_group.append(
                            self.formatters["suggestion_accepted"](event))
            if "suggestion_rejected" in actions:
                for event in events:
                    if event.action == "suggestion_rejected":
                        reject_groups[str(event.value.unit.id)] = reject_groups.get(
                            str(event.value.unit.id), [])
                        reject_groups[str(event.value.unit.id)].append(event)
            for event in events:
                if event.action == "unit_created":
                    creation_group.append(event)
            for event in events:
                if event.action == "source_updated":
                    event_group.append(self.formatters["source_updated"](event))
            for event in events:
                if event.action == "target_updated":
                    event_group.append(self.formatters["target_updated"](event))
            for event in events:
                if event.action == "state_changed":
                    event_group.append(self.formatters["state_changed"](event))
            groups.append(event_group)
        if creation_group:
            _creation_group = []
            if len(creation_group) == 1:
                _creation_group.append(
                    self.formatters["unit_created"](event))
            else:
                _creation_group.append(
                    self.formatters["grouped_creation"](
                        self.context, creation_group))
            groups.append(_creation_group)
        _reject_groups = []
        for k, v in reject_groups.items():
            _reject_groups.append(
                self.formatters["grouped_rejection"](self.context, v))
        if _reject_groups:
            groups.append(_reject_groups)
        return groups

    @property
    def message(self):
        return mark_safe(
            "<ul>%s</ul>"
            % ", ".join(ev.action for ev in self.event_group))

    @property
    def change(self):
        return mark_safe(
            "<ul>%s</ul>"
            % "".join(
                "<li>%s<li>"
                % ev.change for ev in self.event_group))

    @property
    def changes(self):
        _changes = []
        for group in self.event_group:
            if not group:
                continue
            revision = max(ev.revision or 0 for ev in group)
            if revision:
                revision = " (r%s)" % revision
            else:
                revision = ""
            message = (", ".join(ev.action for ev in group)).lower().capitalize()
            message = mark_safe(
                "%s for %s%s"
                % (message,
                   group[0].formatted_unit, revision))
            changes = "".join(
                ('<li class="%s">%s<li>'
                 % (ev.css_class, ev.change))
                for ev in group if ev.change)
            if changes:
                change = mark_safe("<ul>%s</ul>" % changes)
            else:
                change = ""
            _changes.append((message, change))
        return _changes

    @property
    def method(self):
        for group in self.event_group:
            if group:
                return group[0].method
        return ""

    @property
    def avatar(self):
        return self.user_profile.avatar

    @property
    def timestamp(self):
        for event in self.events:
            if event.timestamp:
                return event.timestamp.replace(second=0)

    @cached_property
    def user_profile(self):
        return profile.get(self.user.__class__)(self.user)

    @property
    def user(self):
        for event in self.events:
            return (
                event.value.user
                if event.action == "suggestion_accepted"
                else event.user)

    @property
    def committer_avatar(self):
        return self.committer_profile.tiny_avatar

    @cached_property
    def committer_profile(self):
        return profile.get(self.committer.__class__)(self.committer)

    @property
    def committer(self):
        for event in self.events:
            if event.action == "suggestion_accepted":
                return event.user

    @property
    def formatted_unit(self):
        return mark_safe('<a href="">%s</a>' % self.event.value.unit.id)


base_formatters = dict(
    group=GroupedEvent,
    grouped_creation=GroupedCreationEvent,
    grouped_rejection=GroupedRejectionEvent,
    unit_created=UnitCreatedEvent,
    state_changed=UnitStateChangedEvent,
    source_updated=UnitSourceUpdatedEvent,
    target_updated=UnitTargetUpdatedEvent,
    suggestion_created=SuggestionAddedEvent,
    suggestion_accepted=SuggestionAcceptedEvent,
    suggestion_rejected=SuggestionRejectedEvent,
    comment_updated=CommentUpdatedEvent,
    check_muted=CheckMutedEvent,
    check_unmuted=CheckUnmutedEvent)
