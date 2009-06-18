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


def form_set_as_table(formset, link=None):
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
            result.append(unicode(form.fields[field].label))
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
            if field == 'code' and 'code' in form.initial and link :
                from pootle_misc.baseurl import l
                link = l(link % form.initial['code'])
                result.append("<a href='"+link+"'><span >"+form.initial['code']+" </span></a>")
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

################################################################################

def add_prefix(prefix, name, num=None):
    if num is None:
        return '%s-%s' % (prefix, name)
    else:
        return '%s-%s-%s' % (prefix, num, name)

class FakeQuery(list):
    """A list that appears to be a Django QuerySet. This is so that we can
    pass lists to where QuerySets are expected."""
    def all(self):
        return self

def get_formset_objects(query, prefix, model_class):
    """Find all id elements in the query which are prefixed with 'prefix'
    and use these as ids (that is, primary keys) in the Django method
    in_bulk to obtain a list of the objects in 'model_class' which
    have these ids.

    Wrap the final result in a FakeQuery to make the result usable
    where Django expects Querysets."""
    # Read the total number of forms. For this to work, a
    # ManagementForm has to be present. Perhaps we should rather try
    # to instantiate a ManagementForm and use that to get this value?
    length = int(query[add_prefix(prefix, 'TOTAL_FORMS')])
    # Enumerate the values [0, length), using the numbers as indices
    # to construct keys which are used to look up values in the HTTP
    # query dictionary.
    ids = [int(query[add_prefix(prefix, 'id', i)]) for i in xrange(length)]
    # model_class.objects.in_bulk(ids) returns a dictionary mapping
    # ids->objects.
    id_object_map = model_class.objects.in_bulk(ids)
    # We only care about the objects, but we want the retain the order
    # of the ids as they appear in 'ids'. Thus, we enumerate 'ids' and
    # pick out the corresponding objects in id_object_map; this gives
    # us our objects in the right sequence. Now Wrap everything in the
    # FakeQuery class to simluate a Django QuerySet.
    return FakeQuery(id_object_map[id] for id in ids)

def init_formset_from_data(formset_class, data):
    """Initialize a formset using the ids in 'data'. Now Django is
    supposed to be able to do this. What happens though, is that you
    pass a queryset to your formset class and Django matches the forms
    in your post data one for one, in sequence to the data in your
    QuerySet. So, imagine that your post data has ids [1, 6, 10, 20]
    and your queryset has ids [1, 2, 3, 4] (as might happen if you
    pass MyModel.objects.all()), then Django will erroneously
    instantiate the objects with ids [1, 2, 3, 4] and associate those
    instances with your form data.

    Not terribly good. What if the data has changed since we last
    looked?

    init_formset_from_data deals with this by first looking for all
    the ids, asking Django to instantiate these objects via in_bulk
    and passing the resulting (fake) QuerySet to the formset class."""

    # Note that Django's modelformset_factory doesn't allow you to set
    # the prefix to be used with a formset. The default, at least in
    # Django 1.0 is 'form'.
    queryset = get_formset_objects(data, 'form', formset_class.model)
    return formset_class(data, queryset=queryset)

################################################################################

def choices_from_models(seq):
    return [(-1, '')] + [(item.id, unicode(item)) for item in seq]

def selected_model(model_class, field):
    try:
        return model_class.objects.get(pk=field.data)
    except model_class.DoesNotExist:
        return None


