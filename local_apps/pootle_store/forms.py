#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2010 Zuza Software Foundation
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

"""Form fields required for handling translation files"""
import re

from django import forms
from django.utils.translation import get_language, ugettext as _
from django.utils.safestring import mark_safe

from translate.misc.multistring import multistring

from pootle_store.models import Unit
from pootle_store.util import FUZZY, TRANSLATED, UNTRANSLATED

############## text cleanup and highlighting #########################
FORM_RE = re.compile('\r\n|\r|\n|\t|\\\\')
def highlight_whitespace(text):
    """make whitespace chars visible"""
    def replace(match):
        submap = {
            '\r\n': '\\r\\n\n',
            '\r': '\\r\n',
            '\n': '\\n\n',
            '\t': '\\t\t',
            '\\': '\\\\',
            }
        return submap[match.group()]
    return FORM_RE.sub(replace, text)

FORM_UNRE = re.compile('\r|\n|\t|\\\\r|\\\\n|\\\\t|\\\\\\\\')
def unhighlight_whitespace(text):
    """replace visible whitespace with proper whitespace"""
    def replace(match):
        submap = {
            '\t': '',
            '\n': '',
            '\r': '',
            '\\t': '\t',
            '\\n': '\n',
            '\\r': '\r',
            '\\\\': '\\',
            }
        return submap[match.group()]
    return FORM_UNRE.sub(replace, text)

class MultiStringWidget(forms.MultiWidget):
    """Custom Widget for editing multistrings, expands number of text
    area based on number of plural forms"""
    def __init__(self, attrs=None, nplurals=1, textarea=True):
        if textarea:
            widget = forms.Textarea
        else:
            widget = forms.TextInput

        widgets = [widget(attrs=attrs) for i in xrange(nplurals)]
        super(MultiStringWidget, self).__init__(widgets, attrs)

    def format_output(self, rendered_widgets):
        if len(rendered_widgets) == 1:
            return mark_safe(rendered_widgets[0])

        output = ''
        for i, widget in enumerate(rendered_widgets):
            output += '<p class="translation-text-headers" lang="%s">%s</p>' % (get_language(), _('Plural Form %d', i))
            output += widget
        return mark_safe(output)

    def decompress(self, value):
        if value is None:
            return [None] * len(self.widgets)
        elif isinstance(value, multistring):
            return [highlight_whitespace(string) for string in value.strings]
        elif isinstance(value, list):
            return [highlight_whitespace(string) for string in value]
        elif isinstance(value, basestring):
            return [highlight_whitespace(value)]
        else:
            raise ValueError

class HiddenMultiStringWidget(MultiStringWidget):
    """uses hidden input instead of text areas"""
    def __init__(self, attrs=None, nplurals=1):
        widgets = [forms.HiddenInput(attrs=attrs) for i in xrange(nplurals)]
        super(MultiStringWidget, self).__init__(widgets, attrs)

    def format_output(self, rendered_widgets):
        return super(MultiStringWidget, self).format_output(rendered_widgets)

    def __call__(self):
        #HACKISH: Django is inconsistent in how it handles
        # Field.widget and Field.hidden_widget, it expects widget to
        # be an instantiated object and hidden_widget to be a class,
        # since we need to specify nplurals at run time we can let
        # django instantiate hidden_widget.
        #
        # making the object callable let's us get away with forcing an
        # object where django expects a class
        return self

class MultiStringFormField(forms.MultiValueField):
    def __init__(self, nplurals=1, attrs=None, textarea=True, *args, **kwargs):
        self.widget = MultiStringWidget(nplurals=nplurals, attrs=attrs, textarea=textarea)
        self.hidden_widget = HiddenMultiStringWidget(nplurals=nplurals)
        fields = [forms.CharField() for i in range(nplurals)]
        super(MultiStringFormField, self).__init__(fields=fields, *args, **kwargs)

    def compress(self, data_list):
        return [unhighlight_whitespace(string) for string in data_list]


def unit_form_factory(language, snplurals=1):
    if snplurals > 1:
        tnplurals = language.nplurals
    else:
        tnplurals = 1
    target_attrs = {
        'lang': language.code,
        'dir': language.get_direction(),
        'class': 'translation expanding focusthis',
        'rows': 5,
        'tabindex': 10,
        }
    comment_attrs = {
        'lang': language.code,
        'dir': language.get_direction(),
        'class': 'comments expanding',
        'rows': 1,
        'tabindex': 15,
        }

    fuzzy_attrs = {
        'accesskey': 'f',
        'class': 'fuzzycheck',
        'tabindex': 13,
        }

    class UnitForm(forms.ModelForm):
        class Meta:
            model = Unit
            exclude = ['store']

        id = forms.IntegerField(required=False)
        source_f = MultiStringFormField(nplurals=snplurals, required=False, textarea=False)
        target_f = MultiStringFormField(nplurals=tnplurals, required=False, attrs=target_attrs)
        state = forms.BooleanField(required=False,
                label=_('Fuzzy'),
                widget=forms.CheckboxInput(attrs=fuzzy_attrs, check_test=lambda x: x == FUZZY))
        translator_comment = forms.CharField(required=False,
                widget=forms.Textarea(attrs=comment_attrs),
                label=_("Translator comment"))
        developer_comment = forms.CharField(required=False,
                widget=forms.Textarea(attrs=comment_attrs))

        def clean_source_f(self):
            value = self.cleaned_data['source_f']
            if self.instance.source.strings != value:
                self.instance._source_updated = True
            return value

        def clean_target_f(self):
            value = self.cleaned_data['target_f']
            if self.instance.target.strings != value:
                self.instance._target_updated = True
            return value

        def clean_state(self):
            value = self.cleaned_data['state']
            if value:
                return FUZZY
            elif self.instance.state != FUZZY:
                return self.instance.state
            else:
                return TRANSLATED

    return UnitForm
