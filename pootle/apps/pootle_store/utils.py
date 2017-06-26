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
from django.utils.functional import cached_property

from pootle.core.delegate import site, states, unitid
from pootle.core.mail import send_mail
from pootle.core.signals import update_data, update_scores
from pootle.core.utils.timezone import datetime_min, localdate, make_aware
from pootle.i18n.gettext import ugettext as _
from pootle_statistics.models import (
    MUTED, UNMUTED, SubmissionFields, SubmissionTypes)

from .constants import TRANSLATED
from .models import Suggestion


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
        self.unit = dict(
            source_f=unit.source_f,
            target_f=unit.target_f,
            context=unit.context,
            revision=unit.revision,
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
        self.reviewer = reviewer or User.objects.get_system_user()
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

    @cached_property
    def states(self):
        return states.get(Suggestion)

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
            or translation == unit.target
            or unit.get_suggestions().filter(target_f=translation).exists())
        if dont_add:
            return (None, False)
        if isinstance(user, User):
            user = user.id
        user = user or User.objects.get_system_user().id
        try:
            suggestion = Suggestion.objects.pending().get(
                unit=unit,
                user_id=user,
                target_f=translation)
            return (suggestion, False)
        except Suggestion.DoesNotExist:
            suggestion = Suggestion.objects.create(
                unit=unit,
                user_id=user,
                state_id=self.states["pending"],
                target=translation,
                creation_time=make_aware(timezone.now()))
        return (suggestion, True)

    def update_unit_on_accept(self, suggestion, target=None):
        unit = suggestion.unit
        unit.target = target or suggestion.target
        if unit.isfuzzy():
            unit.state = TRANSLATED
        unit.save(
            user=suggestion.user,
            changed_with=self.review_type,
            reviewed_by=self.reviewer)

    def accept_suggestion(self, suggestion, target=None):
        suggestion.state_id = self.states["accepted"]
        suggestion.reviewer = self.reviewer
        old_revision = suggestion.unit.revision
        self.update_unit_on_accept(suggestion, target=target)
        if suggestion.unit.revision > old_revision:
            suggestion.submission_set.add(
                *suggestion.unit.submission_set.filter(
                    revision=suggestion.unit.revision))
            suggestion.review_time = suggestion.unit.mtime
        else:
            suggestion.review_time = timezone.now()
        suggestion.save()

    def reject_suggestion(self, suggestion):
        store = suggestion.unit.store
        suggestion.state_id = self.states["rejected"]
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

    def accept_suggestions(self, target=None):
        for suggestion in self.suggestions:
            self.accept_suggestion(suggestion, target=target)

    def accept(self, comment="", target=None):
        self.accept_suggestions(target=target)
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
        subs = list(subs)
        if not subs:
            return
        self.unit.submission_set.bulk_create(subs)
        update_scores.send(
            self.unit.store.__class__,
            instance=self.unit.store,
            users=[sub.submitter_id for sub in subs],
            date=localdate(self.unit.mtime))

    def sub_comment_update(self, **kwargs):
        _kwargs = dict(
            creation_time=self.unit.mtime,
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
            creation_time=self.unit.mtime,
            unit=self.unit,
            submitter=self.unit.change.submitted_by,
            field=SubmissionFields.SOURCE,
            type=self.unit.change.changed_with,
            old_value=self.original.source or "",
            new_value=self.unit.source_f)
        _kwargs.update(kwargs)
        return self.create_submission(**_kwargs)

    def sub_target_update(self, **kwargs):
        submitter = (
            self.unit.change.submitted_by
            if self.unit.change.submitted_by
            else self.unit.change.reviewed_by)
        _kwargs = dict(
            creation_time=self.unit.mtime,
            unit=self.unit,
            submitter=submitter,
            field=SubmissionFields.TARGET,
            type=self.unit.change.changed_with,
            old_value=self.original.target or "",
            new_value=self.unit.target_f)
        _kwargs.update(kwargs)
        return self.create_submission(**_kwargs)

    def sub_state_update(self, **kwargs):
        reviewed_on = self.unit.change.reviewed_on
        submitted_on = (
            self.unit.change.submitted_on
            or datetime_min)
        is_review = (
            reviewed_on
            and (reviewed_on > submitted_on))
        if is_review:
            submitter = self.unit.change.reviewed_by
        else:
            submitter = self.unit.change.submitted_by
        _kwargs = dict(
            creation_time=self.unit.mtime,
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
