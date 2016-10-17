# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings
from django.template import loader

from pootle.core.delegate import site
from pootle.core.mail import send_mail
from pootle.i18n.gettext import ugettext as _
from pootle_comment.forms import UnsecuredCommentForm


class SuggestionsReview(object):
    accept_email_template = 'editor/email/suggestions_accepted_with_comment.txt'
    accept_email_subject = _(u"Suggestion accepted with comment")
    reject_email_template = 'editor/email/suggestions_rejected_with_comment.txt'
    reject_email_subject = _(u"Suggestion rejected with comment")

    def __init__(self, suggestions, reviewer):
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

    def accept_suggestions(self):
        for suggestion in self.suggestions:
            suggestion.unit.accept_suggestion(
                suggestion,
                suggestion.unit.store.translation_project,
                self.reviewer)

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
            dict(suggestions=suggestions,
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
            suggestion.unit.reject_suggestion(
                suggestion,
                suggestion.unit.store.translation_project,
                self.reviewer)

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
