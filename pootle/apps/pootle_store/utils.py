# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

from django.conf import settings
from django.contrib.auth import get_user_model
from django.template import loader
from django.utils import timezone

from pootle.core.delegate import site, unitid
from pootle.core.mail import send_mail
from pootle.core.signals import update_data
from pootle.core.utils.timezone import make_aware
from pootle.i18n.gettext import ugettext as _
from pootle_statistics.models import (
    MUTED, UNMUTED, SubmissionFields, SubmissionTypes)

from .constants import TRANSLATED
from .models import Suggestion, SuggestionState, UnitChange


User = get_user_model()


class UnitWordcount(object):

    def __init__(self, counter):
        self.counter = counter

    def count(self, string):
        return self.counter(string)

    def count_words(self, strings):
        return sum(self.count(string) for string in strings)


class DefaultUnitid(object):

    def __init__(self, unit):
        self.unit = unit

    @property
    def changed(self):
        return (
            self.unit.source_updated
            or self.unit.context_updated)

    @property
    def unit_sync_class(self):
        return self.unit.store.syncer.unit_sync_class

    def getid(self):
        return self.unit_sync_class(
            self.unit).convert().getid()


class UnitUniqueId(object):

    def __init__(self, unit):
        self.unit = unit

    @property
    def format_name(self):
        return self.unit.store.filetype.name

    @property
    def format_unitid(self):
        format_unitids = unitid.gather(self.unit.__class__)
        return (
            format_unitids[self.format_name](self.unit)
            if self.format_name in format_unitids
            else format_unitids["default"](self.unit))

    @property
    def changed(self):
        return self.format_unitid.changed

    def getid(self):
        return self.format_unitid.getid()


class FrozenUnit(object):
    """Freeze unit vars for comparison"""

    def __init__(self, unit):
        submitter = (
            unit.change.submitted_by
            if unit.changed
            else None)
        self.unit = dict(
            source_f=unit.source_f,
            target_f=unit.target_f,
            context=unit.context,
            revision=unit.revision,
            submitter=submitter,
            state=unit.state,
            pk=unit.pk,
            translator_comment=unit.translator_comment)

    @property
    def context(self):
        return self.unit["context"]

    @property
    def pk(self):
        return self.unit["pk"]

    @property
    def revision(self):
        return self.unit["revision"]

    @property
    def source(self):
        return self.unit["source_f"]

    @property
    def state(self):
        return self.unit["state"]

    @property
    def submitter(self):
        return self.unit["submitter"]

    @property
    def target(self):
        return self.unit["target_f"]

    @property
    def translator_comment(self):
        return self.unit["translator_comment"]


class SuggestionsReview(object):
    accept_email_template = 'editor/email/suggestions_accepted_with_comment.txt'
    accept_email_subject = _(u"Suggestion accepted with comment")
    reject_email_template = 'editor/email/suggestions_rejected_with_comment.txt'
    reject_email_subject = _(u"Suggestion rejected with comment")

    def __init__(self, suggestions=None, reviewer=None, review_type=None):
        self.suggestions = suggestions
        self.reviewer = reviewer
        self._review_type = review_type

    @property
    def review_type(self):
        return (
            SubmissionTypes.SYSTEM
            if self._review_type is None
            else self._review_type)

    @property
    def users_and_suggestions(self):
        users = {}
        for suggestion in self.suggestions:
            users[suggestion.user] = users.get(suggestion.user, [])
            users[suggestion.user].append(suggestion)
        return users

    def add(self, unit, translation, user=None):
        """Adds a new suggestion to the unit.

        :param translation: suggested translation text
        :param user: user who is making the suggestion. If it's ``None``,
            the ``system`` user will be used.

        :return: a tuple ``(suggestion, created)`` where ``created`` is a
            boolean indicating if the suggestion was successfully added.
            If the suggestion already exists it's returned as well.
        """
        dont_add = (
            not filter(None, translation)
            or translation == unit.target)
        if dont_add:
            return (None, False)
        user = user or User.objects.get_system_user()
        pending = SuggestionState.objects.get(name="pending")
        try:
            suggestion = Suggestion.objects.pending().get(
                unit=unit,
                user=user,
                target_f=translation)
            return (suggestion, False)
        except Suggestion.DoesNotExist:
            suggestion = Suggestion.objects.create(
                unit=unit,
                user=user,
                state_id=pending.id,
                target=translation,
                creation_time=make_aware(timezone.now()))
        return (suggestion, True)

    def update_unit_on_accept(self, suggestion):
        unit = suggestion.unit
        unit.submitted_on = suggestion.review_time
        unit.reviewed_by = self.reviewer
        unit.reviewed_on = unit.submitted_on
        unit.target = suggestion.target
        if unit.isfuzzy():
            unit.state = TRANSLATED
        unit.save(
            submitted_by=suggestion.user,
            submitted_on=suggestion.review_time,
            changed_with=self.review_type,
            reviewed_by=self.reviewer,
            reviewed_on=suggestion.review_time)

    def accept_suggestion(self, suggestion, update_unit):
        accepted = SuggestionState.objects.get(name="accepted")
        suggestion.state_id = accepted.id
        suggestion.reviewer = self.reviewer
        suggestion.review_time = make_aware(timezone.now())
        if update_unit:
            self.update_unit_on_accept(suggestion)
        suggestion.save()

    def reject_suggestion(self, suggestion):
        store = suggestion.unit.store
        rejected = SuggestionState.objects.get(name="rejected")
        suggestion.state_id = rejected.id
        suggestion.review_time = make_aware(timezone.now())
        suggestion.reviewer = self.reviewer
        suggestion.save()
        unit = suggestion.unit
        if unit.changed:
            # if the unit is translated and suggestion was rejected
            # set the reviewer info
            unit.change.reviewed_by = self.reviewer
            unit.change.reviewed_on = suggestion.review_time
            unit.change.save()
        update_data.send(store.__class__, instance=store)

    def accept_suggestions(self, update_unit):
        for suggestion in self.suggestions:
            self.accept_suggestion(suggestion, update_unit)

    def accept(self, update_unit=True, comment=""):
        self.accept_suggestions(update_unit)
        if self.should_notify(comment):
            self.notify_suggesters(rejected=False, comment=comment)

    def build_absolute_uri(self, url):
        return site.get().build_absolute_uri(url)

    def get_email_message(self, suggestions, comment, template):
        for suggestion in suggestions:
            suggestion.unit_url = (
                self.build_absolute_uri(
                    suggestion.unit.get_translate_url()))
        return loader.render_to_string(
            template,
            context=dict(suggestions=suggestions,
                         comment=comment))

    def notify_suggesters(self, rejected=True, comment=""):
        for suggester, suggestions in self.users_and_suggestions.items():
            if rejected:
                template = self.reject_email_template
                subject = self.reject_email_subject
            else:
                template = self.accept_email_template
                subject = self.accept_email_subject
            self.send_mail(template, subject, suggester, suggestions, comment)

    def reject_suggestions(self):
        for suggestion in self.suggestions:
            self.reject_suggestion(suggestion)

    def reject(self, comment=""):
        self.reject_suggestions()
        if self.should_notify(comment):
            self.notify_suggesters(rejected=True, comment=comment)

    def send_mail(self, template, subject, suggester, suggestions, comment):
        send_mail(
            subject,
            self.get_email_message(
                suggestions,
                comment,
                template),
            from_email=None,
            recipient_list=[suggester.email],
            fail_silently=True)

    def should_notify(self, comment):
        return (
            comment
            and settings.POOTLE_EMAIL_FEEDBACK_ENABLED)


class UnitLifecycle(object):

    def __init__(self, unit):
        self.unit = unit

    @property
    def original(self):
        return self.unit._frozen

    @property
    def submission_model(self):
        return self.unit.submission_set.model

    def create_submission(self, **kwargs):
        _kwargs = dict(
            translation_project=self.unit.store.translation_project,
            unit=self.unit,
            revision=self.unit.revision)
        _kwargs.update(kwargs)
        return self.submission_model(**_kwargs)

    def sub_mute_qc(self, **kwargs):
        quality_check = kwargs["quality_check"]
        submitter = kwargs["submitter"]
        _kwargs = dict(
            creation_time=make_aware(timezone.now()),
            submitter=submitter,
            field=SubmissionFields.CHECK,
            type=SubmissionTypes.WEB,
            old_value=UNMUTED,
            new_value=MUTED,
            quality_check=quality_check)
        _kwargs.update(kwargs)
        return self.create_submission(**_kwargs)

    def sub_unmute_qc(self, **kwargs):
        quality_check = kwargs["quality_check"]
        submitter = kwargs["submitter"]
        _kwargs = dict(
            creation_time=make_aware(timezone.now()),
            submitter=submitter,
            field=SubmissionFields.CHECK,
            type=SubmissionTypes.WEB,
            old_value=MUTED,
            new_value=UNMUTED,
            quality_check=quality_check)
        _kwargs.update(kwargs)
        return self.create_submission(**_kwargs)

    def save_subs(self, subs):
        if subs:
            self.unit.submission_set.bulk_create(subs)

    def sub_comment_update(self, **kwargs):
        _kwargs = dict(
            creation_time=self.unit.change.commented_on,
            unit=self.unit,
            submitter=self.unit.change.commented_by,
            field=SubmissionFields.COMMENT,
            type=self.unit.change.changed_with,
            old_value=self.original.translator_comment or "",
            new_value=self.unit.translator_comment or "")
        _kwargs.update(kwargs)
        return self.create_submission(**_kwargs)

    def sub_source_update(self, **kwargs):
        _kwargs = dict(
            creation_time=self.unit.change.submitted_on,
            unit=self.unit,
            submitter=self.unit.change.submitted_by,
            field=SubmissionFields.SOURCE,
            type=self.unit.change.changed_with,
            old_value=self.original.source or "",
            new_value=self.unit.source_f)
        _kwargs.update(kwargs)
        return self.create_submission(**_kwargs)

    def sub_target_update(self, **kwargs):
        _kwargs = dict(
            creation_time=self.unit.change.submitted_on,
            unit=self.unit,
            submitter=self.unit.change.submitted_by,
            field=SubmissionFields.TARGET,
            type=self.unit.change.changed_with,
            old_value=self.original.target or "",
            new_value=self.unit.target_f)
        _kwargs.update(kwargs)
        return self.create_submission(**_kwargs)

    def sub_state_update(self, **kwargs):
        is_review = (
            self.unit.change.reviewed_on
            and (self.unit.change.reviewed_on
                 > self.unit.change.submitted_on))
        if is_review:
            submitter = self.unit.change.reviewed_by
            creation_time = self.unit.change.reviewed_on
        else:
            submitter = self.unit.change.submitted_by
            creation_time = self.unit.change.submitted_on

        _kwargs = dict(
            creation_time=creation_time,
            unit=self.unit,
            submitter=submitter,
            field=SubmissionFields.STATE,
            type=self.unit.change.changed_with,
            old_value=self.original.state,
            new_value=self.unit.state)
        _kwargs.update(kwargs)
        return self.create_submission(**_kwargs)

    def update(self, updates):
        self.save_subs(self.create_subs(updates))

    def create_subs(self, updates):
        for name, update in updates.items():
            yield getattr(self, "sub_%s" % name)(**update)

    def calculate_change(self, **kwargs):
        updates = OrderedDict()
        if self.unit.comment_updated:
            updates["comment_update"] = kwargs
        if self.unit.source_updated:
            updates["source_update"] = kwargs
        if self.unit.target_updated:
            updates["target_update"] = kwargs
        if self.unit.state_updated:
            updates["state_update"] = kwargs
        return updates

    def change(self, **kwargs):
        self.update(self.calculate_change(**kwargs))
