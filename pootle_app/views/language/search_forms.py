#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

"""Helper methods for search functionality."""

from django import forms
from django.forms.formsets import formset_factory, BaseFormSet
from django.forms.util import ValidationError
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

class SearchForm(forms.Form):
    text = forms.CharField(widget=forms.TextInput(attrs={'size':'15'}))

    def as_p(self):
        return '<label class="inputHint" for="%(for_label)s">%(title)s</label>%(text)s' % {
            'title':     self.initial['title'],
            'for_label': self['text'].auto_id,
            'text':      self['text'].as_widget()
            }

    def as_hidden(self):
        return ''.join(field.as_hidden() for field in self)

class AdvancedSearchForm(forms.Form):
    selected    = forms.BooleanField(required=False)

    def as_table(self):
        from Pootle.i18n import gettext, util

        return '<tr><td>%(selected)s<label dir="%(uidir)s" for="%(for_label)s">%(text)s</label></td></tr>' % {
            'selected':  self['selected'].as_widget(),
            'uidir':     util.language_dir(gettext.get_active().language.code),
            'for_label': self['selected'].auto_id,
            'text':      self.initial['text'],
            }

    def as_hidden(self):
        return ''.join(field.as_hidden() for field in self)

class BaseAdvancedSearchFormSet(BaseFormSet):
    def as_hidden(self):
        "Returns this formset rendered as a hidden set of HTML widgets"
        forms = u' '.join([form.as_hidden() for form in self.forms])
        return mark_safe(u'\n'.join([unicode(self.management_form), forms]))

AdvancedSearchFormSet = formset_factory(AdvancedSearchForm, BaseAdvancedSearchFormSet, extra=0)

def get_advanced_search_field_data():
    return [
        {'selected': True,  'text': _('Source Text'), 'name': 'source'   },
        {'selected': True,  'text': _('Target Text'), 'name': 'target'   },
        {'selected': False, 'text': _('Comments'),    'name': 'comments' },
        {'selected': False, 'text': _('Locations'),   'name': 'locations'},
        ]

#def are_advanced_options_default(advanced_form):
#    return advanced_form.forms[0]['']

def mark_nodefault(request, result):
    """Set 'extra_class' to the CSS class 'nodefaultsearch' if we
    detect that a field in our advanced search form differs from
    its default value.

    We only do this for POSTs, since the user will only ever
    navigate searches using form submissions."""
    if request.method == 'POST':
        for form in result['advanced_search_form'].forms:
            if form.initial['selected'] != form['selected'].data:
                result['extra_class'] = 'nodefaultsearch'
                return result
    return result

# TBD: Init the search forms from a SearchState object?
def get_search_form(request, search_text=None):
    try:
        advanced_search_form = AdvancedSearchFormSet(data=request.POST,
                                                     initial=get_advanced_search_field_data())
    except ValidationError:
        advanced_search_form = AdvancedSearchFormSet(initial=get_advanced_search_field_data())

    return mark_nodefault(request, {
        'search_form':           SearchForm(data=request.POST,
                                            initial={'title': _('Search'), 'text': search_text or ''}),
        'advanced_search_form':  advanced_search_form,
        'advanced_search_title': _('Advanced Search'),
        'extra_class':           ''
        })


