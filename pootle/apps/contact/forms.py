# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms
from django.conf import settings

from contact_form.forms import ContactForm as OriginalContactForm

from pootle.core.forms import MathCaptchaForm
from pootle.core.mail import send_mail
from pootle.i18n.gettext import ugettext_lazy as _


class ContactForm(MathCaptchaForm, OriginalContactForm):

    field_order = ['name', 'email', 'email_subject', 'body', 'captcha_answer',
                   'captcha_token']

    email_subject = forms.CharField(
        max_length=100,
        label=_(u'Subject'),
        widget=forms.TextInput(
            attrs={'placeholder': _('Please enter a message subject')}
        ),
    )

    def __init__(self, *args, **kwargs):
        super(ContactForm, self).__init__(*args, **kwargs)

        self.fields['name'].label = _(u'Name')
        name_placeholder = _('Please enter your name')
        self.fields['name'].widget.attrs['placeholder'] = name_placeholder

        self.fields['email'].label = _(u'Email address')
        email_placeholder = _('Please enter your email address')
        self.fields['email'].widget.attrs['placeholder'] = email_placeholder

        self.fields['body'].label = _(u'Message')
        body_placeholder = _('Please enter your message')
        self.fields['body'].widget.attrs['placeholder'] = body_placeholder

        if self.request.user.is_authenticated:
            del self.fields['captcha_answer']
            del self.fields['captcha_token']

    def get_context(self):
        """Get context to render the templates for email subject and body."""
        ctx = super(ContactForm, self).get_context()
        ctx['server_name'] = settings.POOTLE_TITLE
        ctx['ip_address'] = (
            self.request.META.get('HTTP_X_FORWARDED_FOR',
                                  self.request.META.get('REMOTE_ADDR')))
        return ctx

    def recipient_list(self):
        return [settings.POOTLE_CONTACT_EMAIL]

    def save(self, fail_silently=False):
        """Build and send the email message."""
        reply_to = u'%s <%s>' % (
            self.cleaned_data['name'],
            self.cleaned_data['email'],
        )
        kwargs = self.get_message_dict()
        kwargs["headers"] = {"Reply-To": reply_to}
        send_mail(fail_silently=fail_silently, **kwargs)


class ReportForm(ContactForm):
    """Contact form used to report errors on strings."""

    field_order = ['name', 'email', 'context', 'body', 'captcha_answer',
                   'captcha_token']

    subject_template_name = 'contact_form/report_form_subject.txt'
    template_name = 'contact_form/report_form.txt'

    context = forms.CharField(
        label=_(u'String context'),
        required=True,
        disabled=True,
        widget=forms.Textarea(attrs={'rows': 6}),
    )

    def __init__(self, *args, **kwargs):
        self.unit = kwargs.pop('unit', None)
        super(ReportForm, self).__init__(*args, **kwargs)

        self.fields['body'].label = _(u'Question or comment')
        body_placeholder = _('Please enter your question or comment')
        self.fields['body'].widget.attrs['placeholder'] = body_placeholder

        del self.fields['email_subject']

    def get_context(self):
        """Get context to render the templates for email subject and body."""
        ctx = super(ReportForm, self).get_context()

        unit_pk = None
        language_code = None
        project_code = None

        if self.unit:
            unit_pk = self.unit.pk
            language_code = self.unit.store.translation_project.language.code
            project_code = self.unit.store.translation_project.project.code

        ctx.update({
            'unit': unit_pk,
            'language': language_code,
            'project': project_code,
        })
        return ctx

    def recipient_list(self):
        # Try to report string error to the report email for the project. If
        # the project doesn't have a report email then fall back to the global
        # string errors report email.
        if self.unit:
            report_email = (
                self.unit.store.translation_project.project.report_email)
            if report_email:
                return [report_email]

        report_email = getattr(settings, 'POOTLE_CONTACT_REPORT_EMAIL',
                               settings.POOTLE_CONTACT_EMAIL)
        return [report_email]
