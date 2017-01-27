# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django import forms
from django.forms.models import modelformset_factory
from django.forms.utils import ErrorList
from django.shortcuts import render
from django.utils.safestring import mark_safe

from pootle.core.paginator import paginate
from pootle.i18n.gettext import ugettext as _


def form_set_as_table(formset, link=None, linkfield='code'):
    """Create an HTML table from the formset. The first form in the
    formset is used to obtain a list of the fields that need to be
    displayed.

    Errors, if there are any, appear in the row above the form which
    triggered any errors.

    If the forms are based on database models, the order of the
    columns is determined by the order of the fields in the model
    specification.
    """

    def add_header(result, fields, form):
        result.append('<tr>\n')
        for field in fields:
            widget = form.fields[field].widget
            widget_name = widget.__class__.__name__

            if widget.is_hidden or \
               widget_name in ('CheckboxInput', 'SelectMultiple'):
                result.append('<th class="sorttable_nosort">')
            else:
                result.append('<th>')

            if widget_name in ('CheckboxInput',):
                result.append(form[field].as_widget())
                result.append(form[field].label_tag())
            elif form.fields[field].label is not None and not widget.is_hidden:
                result.append(unicode(form.fields[field].label))

            result.append('</th>\n')
        result.append('</tr>\n')

    def add_footer(result, fields, form):
        result.append('<tr>\n')
        for field in fields:
            field_obj = form.fields[field]
            result.append('<td>')

            if field_obj.label is not None and not field_obj.widget.is_hidden:
                result.append(unicode(field_obj.label))

            result.append('</td>\n')
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
        result.append('<tr class="item">\n')
        for i, field in enumerate(fields):
            result.append('<td class="%s">' % field)
            # Include a hidden element containing the form's id to the
            # first column.
            if i == 0:
                result.append(form['id'].as_hidden())

            # `link` indicates whether we put the first field as a link or as
            # widget
            if field == linkfield and linkfield in form.initial and link:
                if callable(link):
                    result.append(link(form.instance))
                result.append(form[field].as_hidden())
            else:
                result.append(form[field].as_widget())

            result.append('</td>\n')
        result.append('</tr>\n')

    result = []
    try:
        first_form = formset.forms[0]
        # Get the fields of the form, but filter our the 'id' field,
        # since we don't want to print a table column for it.
        fields = [field for field in first_form.fields if field != 'id']

        result.append('<thead>\n')
        add_header(result, fields, first_form)
        result.append('</thead>\n')
        result.append('<tfoot>\n')
        add_footer(result, fields, first_form)
        result.append('</tfoot>\n')

        result.append('<tbody>\n')

        # Do not display the delete checkbox for the 'add a new entry' form.
        if formset.extra_forms:
            formset.forms[-1].fields['DELETE'].widget = forms.HiddenInput()

        for form in formset.forms:
            add_errors(result, fields, form)
            add_widgets(result, fields, form, link)

        result.append('</tbody>\n')
    except IndexError:
        result.append('<tr>\n')
        result.append('<td>\n')
        result.append(_('No files in this project.'))
        result.append('</td>\n')
        result.append('</tr>\n')

    return u''.join(result)


def process_modelformset(request, model_class, queryset, **kwargs):
    """With the Django model class `model_class` and the given `queryset`,
    construct a formset process its submission.
    """

    # Create a formset class for the model `model_class` (i.e. it will contain
    # forms whose contents are based on the fields of `model_class`);
    # parameters for the construction of the forms used in the formset should
    # be in kwargs.
    formset_class = modelformset_factory(model_class, **kwargs)

    if queryset is None:
        queryset = model_class.objects.all()

    # If the request is a POST, we want to possibly update our data
    if request.method == 'POST' and request.POST:
        # Create a formset from all the 'model_class' instances whose values
        # will be updated using the contents of request.POST
        objects = paginate(request, queryset)
        formset = formset_class(request.POST, queryset=objects.object_list)

        # Validate all the forms in the formset
        if formset.is_valid():
            # If all is well, Django can save all our data for us
            formset.save()
        else:
            # Otherwise, complain to the user that something went wrong
            return formset, _("There are errors in the form. Please review "
                              "the problems below."), objects

        # Hack to force reevaluation of same query
        queryset = queryset.filter()

    objects = paginate(request, queryset)

    return formset_class(queryset=objects.object_list), None, objects


def edit(request, template, model_class, ctx=None,
         link=None, linkfield='code', queryset=None, **kwargs):
    formset, msg, objects = process_modelformset(request, model_class,
                                                 queryset=queryset, **kwargs)
    if ctx is None:
        ctx = {}

    ctx.update({
        'formset_text': mark_safe(form_set_as_table(formset, link, linkfield)),
        'formset': formset,
        'objects': objects,
        'error_msg': msg,
        'can_add': kwargs.get('extra', 1) != 0,
    })

    return render(request, template, ctx)
