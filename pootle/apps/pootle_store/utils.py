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

from pootle.core.delegate import site
from pootle.core.mail import send_mail
from pootle.core.signals import update_data
from pootle.i18n.gettext import ugettext as _
from pootle_comment.forms import UnsecuredCommentForm
from pootle_statistics.models import (
    Submission, SubmissionFields, SubmissionTypes)

from .constants import FUZZY, TRANSLATED
from .models import Suggestion, SuggestionStates


User = get_user_model()


class SuggestionsReview(object):
    accept_email_template = 'editor/email/suggestions_accepted_with_comment.txt'
    accept_email_subject = _(u"Suggestion accepted with comment")
    reject_email_template = 'editor/email/suggestions_rejected_with_comment.txt'
    reject_email_subject = _(u"Suggestion rejected with comment")

    def __init__(self, suggestions=None, reviewer=None):
        self.suggestions = suggestions
        self.reviewer = reviewer

    @property
    def users_and_suggestions(self):
        users = {}
        for suggestion in self.suggestions:
            users[suggestion.user] = users.get(suggestion.user, [])
            users[suggestion.user].append(suggestion)
        return users

    def add_comments(self, comment):
        for suggestion in self.suggestions:
            UnsecuredCommentForm(
                suggestion,
                dict(comment=comment,
                     user=self.reviewer)).save()

    def add(self, unit, translation, user=None, touch=True,
            similarity=None, mt_similarity=None):
        """Adds a new suggestion to the unit.

        :param translation: suggested translation text
        :param user: user who is making the suggestion. If it's ``None``,
            the ``system`` user will be used.
        :param touch: whether to update the unit's timestamp after adding
            the suggestion or not.
        :param similarity: human similarity for the new suggestion.
        :param mt_similarity: MT similarity for the new suggestion.

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
                state=SuggestionStates.PENDING,
                target=translation,
                creation_time=timezone.now())
            self.create_submission(
                suggestion,
                SubmissionTypes.SUGG_ADD,
                user,
                similarity=similarity,
                mt_similarity=mt_similarity).save()
            if touch:
                unit.save()
        return (suggestion, True)

    def create_submission(self, suggestion, suggestion_type, user, **kwargs):
        return Submission(
            creation_time=kwargs.get("creation_time", suggestion.creation_time),
            translation_project=suggestion.unit.store.translation_project,
            submitter=user,
            unit=suggestion.unit,
            store=suggestion.unit.store,
            type=suggestion_type,
            suggestion=suggestion,
            similarity=kwargs.get("similarity"),
            mt_similarity=kwargs.get("mt_similarity"))

    def accept_suggestion(self, suggestion):
        unit = suggestion.unit
        translation_project = unit.store.translation_project

        # Save for later
        old_state = unit.state
        old_target = unit.target

        # Update some basic attributes so we can create submissions. Note
        # these do not conflict with `ScoreLog`'s interests, so it's safe
        unit.target = suggestion.target
        if unit.state == FUZZY:
            unit.state = TRANSLATED

        current_time = timezone.now()
        suggestion.state = SuggestionStates.ACCEPTED
        suggestion.reviewer = self.reviewer
        suggestion.review_time = current_time
        suggestion.save()
        create_subs = OrderedDict()
        if old_state != unit.state:
            create_subs[SubmissionFields.STATE] = [old_state, unit.state]
        create_subs[SubmissionFields.TARGET] = [old_target, unit.target]
        subs_created = []
        for field in create_subs:
            kwargs = {
                'creation_time': current_time,
                'translation_project': translation_project,
                'submitter': self.reviewer,
                'unit': unit,
                'store': unit.store,
                'field': field,
                'type': SubmissionTypes.SUGG_ACCEPT,
                'old_value': create_subs[field][0],
                'new_value': create_subs[field][1],
            }
            if field == SubmissionFields.TARGET:
                kwargs['suggestion'] = suggestion

            subs_created.append(Submission(**kwargs))
        if subs_created:
            unit.submission_set.add(*subs_created, bulk=False)

        # FIXME: remove such a dependency on `ScoreLog`
        # Update current unit instance's attributes
        # important to set these attributes after saving Submission
        # because in the `ScoreLog` we need to access the unit's certain
        # attributes before it was saved
        # THIS NEEDS TO GO ^^
        unit.submitted_by = suggestion.user
        unit.submitted_on = current_time
        unit.reviewed_by = self.reviewer
        unit.reviewed_on = unit.submitted_on
        unit._log_user = self.reviewer
        unit.save()

    def reject_suggestion(self, suggestion):
        store = suggestion.unit.store
        suggestion.state = SuggestionStates.REJECTED
        suggestion.review_time = timezone.now()
        suggestion.reviewer = self.reviewer
        suggestion.save()
        self.create_submission(
            suggestion,
            SubmissionTypes.SUGG_REJECT,
            self.reviewer,
            creation_time=suggestion.review_time).save()

        update_data.send(store.__class__, instance=store)

    def accept_suggestions(self):
        for suggestion in self.suggestions:
            self.accept_suggestion(suggestion)

    def accept(self, comment=""):
        self.accept_suggestions()
        if self.should_notify(comment):
            self.notify_suggesters(rejected=False, comment=comment)
        if comment:
            self.add_comments(comment=comment)

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
        if comment:
            self.add_comments(comment)

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
