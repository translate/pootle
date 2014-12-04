#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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
from django.utils.translation import ugettext_lazy as _

from contact_form.forms import ContactForm

from pootle.core.forms import MathCaptchaForm


class EvernoteContactForm(MathCaptchaForm, ContactForm):

    subject = forms.CharField(
        max_length=100,
        label=_(u'Summary'),
        widget=forms.TextInput(
            attrs={'placeholder': _('Please enter your message summary')}
        ),
    )

    def __init__(self, *args, **kwargs):
        super(EvernoteContactForm, self).__init__(*args, **kwargs)

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
