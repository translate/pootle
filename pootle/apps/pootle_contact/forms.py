#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from django import forms
from django.conf import settings
from django.utils.translation import ugettext_lazy as _

from contact_form.forms import ContactForm

from pootle.core.forms import MathCaptchaForm


class PootleContactForm(MathCaptchaForm, ContactForm):

    subject = forms.CharField(
        max_length=100,
        label=_(u'Summary'),
        widget=forms.TextInput(
            attrs={'placeholder': _('Please enter your message summary')}
        ),
    )

    def __init__(self, *args, **kwargs):
        super(PootleContactForm, self).__init__(*args, **kwargs)

        self.fields['name'].label = _(u'Name')
        name_placeholder = _('Please enter your name')
        self.fields['name'].widget.attrs['placeholder'] = name_placeholder

        self.fields['email'].label = _(u'Email address')
        email_placeholder = _('Please enter your email address')
        self.fields['email'].widget.attrs['placeholder'] = email_placeholder

        self.fields['body'].label = _(u'Message')
        body_placeholder = _('Please enter your message')
        self.fields['body'].widget.attrs['placeholder'] = body_placeholder

        self.fields.keyOrder = ['name', 'email', 'subject', 'body',
                                'captcha_answer', 'captcha_token']

        if self.request.user.is_authenticated():
            del self.fields['captcha_answer']
            del self.fields['captcha_token']

    def from_email(self):
        return u'%s <%s>' % (
            self.cleaned_data['name'],
            self.cleaned_data['email']
        )


class PootleReportForm(PootleContactForm):
    """Contact form used to report errors on strings."""

    report_email = forms.EmailField(
        max_length=254,
        required=False,
        widget=forms.HiddenInput(),
    )

    def __init__(self, *args, **kwargs):
        super(PootleReportForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder += ['report_email']

    def recipient_list(self):
        # Try to report string error to the report email for the project
        # (injected in the 'report_email' field with initial values). If the
        # project doesn't have a report email then fall back to the global
        # string errors report email.
        if self.cleaned_data['report_email']:
            return [self.cleaned_data['report_email']]
        return [settings.POOTLE_REPORT_STRING_ERRORS_EMAIL]
