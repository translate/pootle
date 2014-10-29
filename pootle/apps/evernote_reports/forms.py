#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
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

from pootle.models.user import CURRENCIES
from evernote_reports.models import PaidTask, PaidTaskTypes


class UserRatesForm(forms.Form):
    username = forms.CharField(widget=forms.HiddenInput())
    currency = forms.ChoiceField(
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
    class Meta:
        model = PaidTask
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
