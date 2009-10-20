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

from django.forms.util import ErrorList
from django.utils.translation import ugettext as _

from pootle_misc.baseurl import l

def form_set_as_table(formset, link=None, linkfield='code'):
    """Create an HTML table from the formset. The first form in the
    formset is used to obtain a list of the fields that need to be
    displayed. All these fields not appearing in 'exclude' will be
    placed into consecutive columns.

    Errors, if there are any, appear in the row above the form which
    triggered any errors.

    If the forms are based on database models, the order of the
    columns is determined by the order of the fields in the model
    specification."""
    def add_header(result, fields, form):
        result.append('<tr>\n')
        for field in fields:
            result.append('<th>')
            if form.fields[field].label is not None:
                result.append(_(form.fields[field].label))
            result.append('</th>\n')
        result.append('</tr>\n')

    def add_errors(result, fields, form):
        # If the form has errors, then we'll add a table row with the
        # errors.
        if len(form.errors) > 0:
            result.append('<tr>\n')
            for field in fields:
                result.append('<td>')
                result.append(form.errors.get(field, ErrorList()).as_ul())
                result.append('</td>\n')
            result.append('</tr>\n')

    def add_widgets(result, fields, form, link):
        result.append('<tr>\n')
        for i, field in enumerate(fields):
            result.append('<td>')
            # Include a hidden element containing the form's id to the
            # first column.
            if i == 0:
                result.append(form['id'].as_hidden())

            """
            'link' indicates whether we put the first field as a link or as widget
            """
            if field == linkfield and linkfield in form.initial and link :
                if callable(link):
                    result.append(link(form.instance))
                    result.append(form[field].as_hidden())
                else:     
                    link = l(link % form.initial[linkfield])
                    result.append("<a href='"+link+"'>"+form.initial[linkfield]+"</a>")
                    result.append(form[field].as_hidden())
            else:
                result.append(form[field].as_widget())
            result.append('</td>\n')
        result.append('</tr>\n')

    result = []
    first_form = formset.forms[0]
    # Get the fields of the form, but filter our the 'id' field,
    # since we don't want to print a table column for it.
    fields = [field for field in first_form.fields if field != 'id']
    add_header(result, fields, first_form)
    for form in formset.forms:
        add_errors(result, fields, form)
        add_widgets(result, fields, form, link)
    return u''.join(result)


