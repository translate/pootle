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

"""Form fields required for handling translation files"""

from django import forms
from django.utils.translation import get_language, ugettext as _
from django.utils.safestring import mark_safe

from translate.misc.multistring import multistring

from pootle_store.models import Unit

class MultiStringWidget(forms.MultiWidget):
    def __init__(self, attrs=None, nplurals=1):
        widgets = [forms.Textarea(attrs=attrs) for i in xrange(nplurals)]
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
            return value.strings
        else:
            print value
            return value

class MultiStringFormField(forms.MultiValueField):
    def __init__(self, nplurals=1, *args, **kwargs):
        self.widget = MultiStringWidget(nplurals=nplurals)
        fields = [forms.CharField() for i in range(nplurals)]
        super(MultiStringFormField, self).__init__(fields=fields, *args, **kwargs)

    def compress(self, data_list):
        return data_list


def unit_form_factory(snplurals=1, tnplurals=1):
    class UnitForm(forms.ModelForm):
        source_f = MultiStringFormField(nplurals=snplurals, required=False)
        target_f = MultiStringFormField(nplurals=tnplurals, required=False)
        class Meta:
            model = Unit

    return UnitForm
