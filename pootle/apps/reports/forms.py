# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms
from django.utils.translation import ugettext_lazy as _

from accounts.models import CURRENCIES

from .models import PaidTask, PaidTaskTypes


class UserRatesForm(forms.Form):
    username = forms.CharField(widget=forms.HiddenInput())
    currency = forms.ChoiceField(
        label=_("Currency"),
        choices=CURRENCIES,
        initial=CURRENCIES[0],
        widget=forms.Select(attrs={'class': 'rate'})
    )
    rate = forms.FloatField(
        label=_("Translation Rate"),
        widget=forms.TextInput(attrs={'step': '0.01', 'type': 'number',
                                      'class': 'rate'}),
    )
    review_rate = forms.FloatField(
        label=_("Review Rate"),
        widget=forms.TextInput(attrs={'step': '0.01', 'type': 'number',
                                      'class': 'rate'}),
    )
    hourly_rate = forms.FloatField(
        label=_("Hourly Rate"),
        widget=forms.TextInput(attrs={'step': '0.01', 'type': 'number',
                                      'class': 'rate'}),
    )
    effective_from = forms.DateField(
        label=_("Effective from"),
        widget=forms.DateInput(attrs={'placeholder': 'YYYY-MM-DD'}),
        required=False,
    )


class PaidTaskForm(forms.ModelForm):
    class Meta(object):
        model = PaidTask
        fields = ('task_type', 'amount', 'rate', 'datetime', 'description',
                  'user')
        widgets = {
            'user': forms.HiddenInput(),
            'rate': forms.HiddenInput(attrs={
                'id': 'id_paid_task_rate'
            }),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(PaidTaskForm, self).__init__(*args, **kwargs)

        if user is not None and user.hourly_rate == 0:
            choices = [item for item in self.fields['task_type'].choices
                       if item[0] != PaidTaskTypes.HOURLY_WORK]
            self.fields['task_type'].choices = choices
