# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import base64
import json
import logging
import re
import time
from hashlib import sha1
from random import randint

from django import forms
from django.conf import settings
from django.core.paginator import Paginator
from django.core.validators import MinLengthValidator
from django.utils.safestring import mark_safe

from pootle.core.delegate import paths
from pootle.i18n.gettext import ugettext as _, ugettext_lazy

from .utils.json import jsonify


class PathsSearchForm(forms.Form):
    step = 20
    q = forms.CharField(max_length=255)
    page = forms.IntegerField(required=False)

    def __init__(self, *args, **kwargs):
        self.context = kwargs.pop("context")
        min_length = kwargs.pop("min_length", 3)
        super(PathsSearchForm, self).__init__(*args, **kwargs)
        validators = [
            v for v in self.fields['q'].validators
            if not isinstance(v, MinLengthValidator)]
        validators.append(MinLengthValidator(min_length))
        self.fields["q"].validators = validators

    @property
    def paths_util(self):
        return paths.get(self.context.__class__)

    def search(self, *la, **kwa):
        q = self.cleaned_data["q"]
        page = self.cleaned_data["page"] or 1
        offset = (page - 1) * self.step
        results = self.paths_util(
            self.context,
            q,
            show_all=kwa.get("show_all", False)).paths
        return dict(
            more_results=len(results) > (offset + self.step),
            results=results[offset:offset + self.step])


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

    A_RE = re.compile("^(\d+)$")

    captcha_answer = forms.CharField(
        max_length=2, required=True,
        widget=forms.TextInput(attrs={'size': '2'}), label='')
    captcha_token = forms.CharField(max_length=200, required=True,
                                    widget=forms.HiddenInput())

    def __init__(self, *args, **kwargs):
        """Initalise captcha_question and captcha_token for the form."""
        super(MathCaptchaForm, self).__init__(*args, **kwargs)

        # reset captcha for unbound forms
        if not self.data:
            self.reset_captcha()

    def reset_captcha(self):
        """Generate new question and valid token for it, reset previous answer
        if any.
        """
        q, a = self._generate_captcha()
        expires = time.time() + \
            getattr(settings, 'CAPTCHA_EXPIRES_SECONDS', 60*60)
        token = self._make_token(q, a, expires)
        self.initial['captcha_token'] = token
        self._plain_question = q
        # reset captcha fields for bound form
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
            return {'q': data['q'],
                    'expires': float(data['expires']),
                    'sign': sign}
        except Exception as e:
            logging.info("Captcha error: %r", e)
            # l10n for bots? Rather not
            raise forms.ValidationError("Invalid captcha!")

    def clean_captcha_answer(self):
        a = self.A_RE.match(self.cleaned_data.get('captcha_answer'))
        if not a:
            raise forms.ValidationError(_("Enter a number"))
        return int(a.group(0))

    def clean(self):
        """Check captcha answer."""
        cd = self.cleaned_data
        # don't check captcha if no answer
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


class PaginatingForm(forms.Form):
    page_field = "page_no"
    per_page_field = "results_per_page"
    page_no = forms.IntegerField(
        required=False,
        initial=1,
        min_value=1,
        max_value=100)
    results_per_page = forms.IntegerField(
        required=False,
        initial=10,
        min_value=10,
        max_value=100,
        widget=forms.NumberInput(attrs=dict(step=10)))


class FormWithActionsMixin(forms.Form):
    action_choices = ()
    action_field = "actions"
    comment_field = "comment"
    select_all_field = "select_all"
    actions = forms.ChoiceField(
        required=False,
        label=ugettext_lazy("With selected"),
        widget=forms.Select(attrs={'class': 'js-select2'}),
        choices=(
            ("", "----"),
            ("reject", _("Reject")),
            ("accept", _("Accept"))))
    comment = forms.CharField(
        label=ugettext_lazy("Add comment"),
        required=False,
        widget=forms.Textarea(attrs=dict(rows=2)))
    select_all = forms.BooleanField(
        required=False,
        label=ugettext_lazy(
            "Select all items matching filter criteria, including those not "
            "shown"),
        widget=forms.CheckboxInput(
            attrs={"class": "js-formtable-select-all"}))

    def __init__(self, *args, **kwargs):
        super(FormWithActionsMixin, self).__init__(*args, **kwargs)
        if self.comment_field != "comment":
            del self.fields["comment"]
        self.fields[self.action_field].choices = self.action_choices

    def should_save(self):
        return (
            self.is_valid()
            and self.cleaned_data.get(self.action_field)
            and self.cleaned_data.get(self.search_field))


class FormtableForm(PaginatingForm, FormWithActionsMixin):
    search_field = None
    msg_err_no_action = _("You must specify an action to take")
    msg_err_no_search_field = _("A valid search field must be specified")

    def __init__(self, *args, **kwargs):
        super(FormtableForm, self).__init__(*args, **kwargs)
        if not self.search_field or self.search_field not in self.fields:
            raise ValueError(self.msg_err_no_search_field)
        self._search_filters = {}
        self._results_per_page = self.fields[self.per_page_field].initial
        self._page_no = self.fields[self.page_field].initial

    @property
    def filter_fields(self):
        return [k for k in self.fields if k.startswith("filter_")]

    def count_choices(self, choices):
        return choices.count()

    def clean(self):
        if self.per_page_field in self.errors:
            del self.errors[self.per_page_field]
            self.cleaned_data[self.per_page_field] = (
                self.fields[self.per_page_field].initial)
        if self.page_field in self.errors:
            del self.errors[self.page_field]
            self.cleaned_data[self.page_field] = (
                self.fields[self.page_field].initial)

        # set the page_no if not set
        self.cleaned_data[self.page_field] = (
            self.cleaned_data.get(self.page_field)
            or self.fields[self.page_field].initial)

        # set the results_per_page if not set
        self.cleaned_data[self.per_page_field] = (
            self.cleaned_data.get(self.per_page_field)
            or self.fields[self.per_page_field].initial)

        # if you select members of the search_field or check
        # select_all, you must specify an action
        missing_action = (
            (self.cleaned_data[self.search_field]
             or self.cleaned_data[self.select_all_field])
            and not self.cleaned_data[self.action_field])
        if missing_action:
            self.add_error(
                self.action_field,
                forms.ValidationError(self.msg_err_no_action))
        self._search_filters = {
            k: v
            for k, v in self.cleaned_data.items()
            if k in self.filter_fields}

        # limit the search_field queryset to criteria
        self.fields[self.search_field].queryset = self.search()

        # validate and update the pagination if required
        should_validate_pagination = (
            (self.cleaned_data[self.page_field]
             != self.fields[self.page_field].initial
             or (self.cleaned_data[self.per_page_field]
                 != self.fields[self.per_page_field].initial)))
        if should_validate_pagination:
            self.cleaned_data[self.per_page_field] = (
                self.cleaned_data[self.per_page_field]
                - self.cleaned_data[self.per_page_field] % 10)
            self._page_no = self.valid_page_no(
                self.fields[self.search_field].queryset,
                self.cleaned_data[self.page_field],
                self.cleaned_data[self.per_page_field])
            self.cleaned_data[self.page_field] = self._page_no
            should_update_data = (
                self.page_field in self.data
                and self.data[self.page_field] != self._page_no)
            if should_update_data:
                # update the initial if necessary
                self.data = self.data.copy()
                self.data[self.page_field] = self._page_no
        self._page_no = self.cleaned_data[self.page_field]
        self._results_per_page = self.cleaned_data[self.per_page_field]

    def valid_page_no(self, choices, page_no, results_per_page):
        max_page = (
            self.count_choices(choices)
            / float(results_per_page))
        # add an extra page if number of choices is not divisible
        max_page = (
            int(max_page) + 1
            if not max_page.is_integer()
            else int(max_page))
        # ensure page_no is within range 1 - max
        return max(1, min(page_no, max_page))

    def search(self):
        """Filter the total queryset for the search_field using
        any filter_field criteria
        """
        self.is_valid()
        return self.fields[self.search_field].queryset

    def batch(self):
        self.is_valid()
        paginator = Paginator(
            self.fields[self.search_field].queryset,
            self._results_per_page)
        return paginator.page(self._page_no)
