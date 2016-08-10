# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms

from pootle.i18n.gettext import ugettext as _
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

        class Meta(object):
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
