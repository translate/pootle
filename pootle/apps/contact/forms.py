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

    field_order = ['name', 'email', 'subject', 'body', 'captcha_answer',
                   'captcha_token']

    subject = forms.CharField(
        max_length=100,
        label=_(u'Summary'),
        widget=forms.TextInput(
            attrs={'placeholder': _('Please enter your message summary')}
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

    def from_email(self):
        return u'%s <%s>' % (
            self.cleaned_data['name'],
            settings.DEFAULT_FROM_EMAIL,
        )

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

    report_email = forms.EmailField(
        max_length=254,
        required=False,
        widget=forms.HiddenInput(),
    )

    def recipient_list(self):
        # Try to report string error to the report email for the project
        # (injected in the 'report_email' field with initial values). If the
        # project doesn't have a report email then fall back to the global
        # string errors report email.
        if self.cleaned_data['report_email']:
            return [self.cleaned_data['report_email']]

        report_email = getattr(settings, 'POOTLE_CONTACT_REPORT_EMAIL',
                               settings.POOTLE_CONTACT_EMAIL)
        return [report_email]
