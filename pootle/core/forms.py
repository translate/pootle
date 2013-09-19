#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010-2014 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

import base64
import json
import logging
import re
import time
from hashlib import sha1
from random import randint

from django import forms
from django.conf import settings
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from pootle_misc.util import jsonify


# MathCaptchaForm Copyright (c) 2007, Dima Dogadaylo (www.mysoftparade.com)
# Copied from http://djangosnippets.org/snippets/506/
# GPL compatible According to djangosnippets terms and conditions
class MathCaptchaForm(forms.Form):
    """Lightweight mathematical captcha where human is asked to solve
    a simple mathematical calculation like 3+5=?. It don't use database
    and don't require external libraries.

    From concatenation of time, question, answer, settings.SITE_URL and
    settings.SECRET_KEY is built hash that is validated on each form
    submission. It makes impossible to "record" valid captcha form
    submission and "replay" it later - form will not be validated
    because captcha will be expired.

    For more info see:
    http://www.mysoftparade.com/blog/improved-mathematical-captcha/
    """
    captcha_answer = forms.CharField(
        max_length=2,
        required=True,
        widget=forms.TextInput(attrs={'size': '2'}),
        label='',
    )
    captcha_token = forms.CharField(
        max_length=200,
        required=True,
        widget=forms.HiddenInput(),
    )

    A_RE = re.compile("^(\d+)$")

    def __init__(self, *args, **kwargs):
        """Initialize captcha_question and captcha_token for the form."""
        super(MathCaptchaForm, self).__init__(*args, **kwargs)

        # Reset captcha for unbound forms.
        if not self.data:
            self.reset_captcha()

    def reset_captcha(self):
        """Generate new question and valid token for it, reset previous answer
        if any.
        """
        q, a = self._generate_captcha()
        expires = time.time() + getattr(settings, 'CAPTCHA_EXPIRES_SECONDS',
                                        60*60)
        token = self._make_token(q, a, expires)
        self.initial['captcha_token'] = token
        self._plain_question = q
        # Reset captcha fields for bound form.
        if self.data:
            def _reset():
                self.data['captcha_token'] = token
                self.data['captcha_answer'] = ''
            if hasattr(self.data, '_mutable') and not self.data._mutable:
                self.data._mutable = True
                _reset()
                self.data._mutable = False
            else:
                _reset()

        self.fields['captcha_answer'].label = mark_safe(self.knotty_question)

    def _generate_captcha(self):
        """Generate question and return it along with correct answer."""
        a, b = randint(1, 9), randint(1, 9)
        return ("%s+%s" % (a, b), a+b)

    def _make_token(self, q, a, expires):
        data = base64.urlsafe_b64encode(jsonify({'q': q, 'expires': expires}))
        return self._sign(q, a, expires) + data

    def _sign(self, q, a, expires):
        plain = [getattr(settings, 'SITE_URL', ''), settings.SECRET_KEY,
                 q, a, expires]
        plain = "".join([str(p) for p in plain])
        return sha1(plain).hexdigest()

    @property
    def plain_question(self):
        return self._plain_question

    @property
    def knotty_question(self):
        """Wrap plain_question in some invisibe for humans markup with random
        nonexisted classes, that makes life of spambots a bit harder because
        form of question is vary from request to request.
        """
        digits = self._plain_question.split('+')
        return "+".join(['<span class="captcha-random-%s">%s</span>' %
                         (randint(1, 9), d) for d in digits])

    def clean_captcha_token(self):
        t = self._parse_token(self.cleaned_data['captcha_token'])
        if time.time() > t['expires']:
            raise forms.ValidationError(_("Time to answer has expired"))
        self._plain_question = t['q']
        return t

    def _parse_token(self, t):
        try:
            sign, data = t[:40], t[40:]
            data = json.loads(base64.urlsafe_b64decode(str(data)))
            return {
                'q': data['q'],
                'expires': float(data['expires']),
                'sign': sign,
            }
        except Exception as e:
            logging.info("Captcha error: %r" % e)
            # l10n for bots? Rather not.
            raise forms.ValidationError("Invalid captcha!")

    def clean_captcha_answer(self):
        a = self.A_RE.match(self.cleaned_data.get('captcha_answer'))
        if not a:
            raise forms.ValidationError(_("Enter a number"))
        return int(a.group(0))

    def clean(self):
        """Check captcha answer."""
        cd = self.cleaned_data
        # Don't check captcha if no answer.
        if 'captcha_answer' not in cd:
            return cd

        t = cd.get('captcha_token')
        if t:
            form_sign = self._sign(t['q'], cd['captcha_answer'],
                                   t['expires'])
            if form_sign != t['sign']:
                self._errors['captcha_answer'] = [_("Incorrect")]
        else:
            self.reset_captcha()
        return super(MathCaptchaForm, self).clean()
