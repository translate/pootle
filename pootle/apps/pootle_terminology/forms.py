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
from django.utils.translation import ugettext as _

from pootle_store.forms import MultiStringFormField
from pootle_store.models import Store, Unit


def term_unit_form_factory(terminology_store):
    store_pk = terminology_store.pk
    # Set store for new terms
    qs = Store.objects.filter(pk=store_pk)

    class TermUnitForm(forms.ModelForm):
        store = forms.ModelChoiceField(queryset=qs, initial=store_pk,
                                       widget=forms.HiddenInput)
        index = forms.IntegerField(required=False, widget=forms.HiddenInput)
        source_f = MultiStringFormField(required=False, textarea=False)

        class Meta:
            model = Unit  # FIXME: terminology should use its own model!
            fields = ('index', 'source_f', 'store',)

        def clean_index(self):
            # Assign new terms an index value
            value = self.cleaned_data['index']

            if self.instance.id is None:
                value = terminology_store.max_index() + 1

            return value

        def clean_source_f(self):
            value = self.cleaned_data['source_f']

            if value:
                existing = terminology_store.findid(value[0])

                if existing and existing.id != self.instance.id:
                    raise forms.ValidationError(_('This term already exists '
                                                  'in this file.'))
                self.instance.setid(value[0])

            return value

    return TermUnitForm
