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

from django.utils.translation import ugettext as _
from django import forms
from django.utils.safestring import mark_safe
from pootle_app.models.search import Search

class SearchForm(forms.Form):
    text = forms.CharField(widget=forms.TextInput(attrs={'size':'15'}))

    def as_p(self):
        return mark_safe('<label class="inputHint" for="%(for_label)s">%(title)s</label>%(text)s' % {
            'title':     self.initial['title'],
            'for_label': self['text'].auto_id,
            'text':      self['text'].as_widget()
            })

    def as_hidden(self):
        return mark_safe(''.join(field.as_hidden() for field in self))

class AdvancedSearchForm(forms.Form):
    source = forms.BooleanField(label=_('Source Text'), required=False, initial=True)
    target = forms.BooleanField(label=_('Target Text'), required=False, initial=True)
    notes = forms.BooleanField(label=_('Comments'), required=False, initial= False)
    locations = forms.BooleanField(label=_('Locations'), required=False, initial=False)
    
    def as_hidden(self):
        """Brain dead Django mungles rendering of checkboxes if initial values are routed via as_hidden
        check http://code.djangoproject.com/ticket/9336 for more info"""
        
        def field_hidden(field):
            if field.data:
                return '<input type="hidden" name="%s" value="True" id="id_%s" />' % (field.name, field.name)
            else:
                return ''

        return mark_safe(''.join(field_hidden(field) for field in self))


# TBD: Init the search forms from a SearchState object?
def get_search_form(request, search_text=None):
    if request.method == 'POST':
        advanced_search_form = AdvancedSearchForm(data=request.POST)
    else:
        advanced_search_form = AdvancedSearchForm()

    return  {
        'search_form':           SearchForm(data=request.POST,
                                            initial={'title': _('Search'), 'text': search_text or ''}),
        'advanced_search_form':  advanced_search_form,
        'advanced_search_title': _('Advanced Search'),
        }

def search_from_request(request):
    def get_list(request, name):
        try:
            return request.GET[name].split(',')
        except KeyError:
            return []

    def as_search_field_list(form):
        if form.is_bound and form.is_valid():
            return [key for key in form.cleaned_data if form.cleaned_data[key]]


    search = get_search_form(request)

    kwargs = {}
    kwargs['match_names']         = get_list(request, 'match_names')
    #FIXME: use cleaned_data
    kwargs['search_text']         = search['search_form']['text'].data    
    kwargs['search_fields']       = as_search_field_list(search['advanced_search_form'])
    kwargs['translation_project'] = request.translation_project
    return Search(**kwargs)
