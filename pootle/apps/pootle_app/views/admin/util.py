#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2012 Zuza Software Foundation
#
# This file is part of translate.
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

from django.core.exceptions import PermissionDenied
from django.forms.models import modelformset_factory
from django.forms.util import ErrorList
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _

from pootle_app.models.permissions import (get_matching_permissions,
                                           check_permission)
from pootle_misc.baseurl import l
from pootle_misc.util import paginate
from pootle_profile.models import get_profile


# XXX: Move to pootle_misc?
def user_is_admin(f):
    def decorated_f(request, *args, **kwargs):
        if not request.user.is_superuser:
            raise PermissionDenied(_("You do not have rights to administer "
                                     "Pootle."))
        else:
            return f(request, *args, **kwargs)

    return decorated_f


def has_permission(permission_code):
    def wrap_f(f):
        def decorated_f(request, path_obj, *args, **kwargs):
            profile = get_profile(request.user)
            request.permissions = get_matching_permissions(profile,
                                                           path_obj.directory)

            if check_permission(permission_code, request):
                return f(request, path_obj, *args, **kwargs)
            else:
                raise PermissionDenied(_("You do not have rights to "
                                         "administer %s.", path_obj.fullname))

        return decorated_f

    return wrap_f


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

    def add_widgets(result, fields, form, link, zebra):
        result.append('<tr class="%s">\n' % zebra)
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
                    link = l(link % form.initial[linkfield])
                    result.append("<a href='"+link+"'>"+form.initial[linkfield]+"</a>")
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
        for i, form in enumerate(formset.forms):
            if i % 2:
                zebra = "odd"
            else:
                zebra = "even"

            add_errors(result, fields, form)
            add_widgets(result, fields, form, link, zebra)

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
    construct a formset process its submission."""

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


def edit(request, template, model_class, model_args={},
         link=None, linkfield='code', queryset=None, **kwargs):
    formset, msg, objects = process_modelformset(request, model_class,
                                                 queryset=queryset, **kwargs)
    template_vars = {
            "formset_text": mark_safe(form_set_as_table(formset, link, linkfield)),
            "formset": formset,
            "objects": objects,
            "error_msg": msg,
    }

    #FIXME: this should be done through an extra context argument
    if 'translation_project' in model_args:
        template_vars['translation_project'] = model_args['translation_project']
    if 'project' in model_args:
        template_vars["project"] = model_args['project']
    if 'language' in model_args:
        template_vars['language'] = model_args['language']
    if 'source_language' in model_args:
        template_vars['source_language'] = model_args['source_language']
    if 'directory' in model_args:
        template_vars['directory'] = model_args['directory']
    if 'navitems' in model_args:
        template_vars["navitems"] = model_args['navitems']
    if 'feed_path' in model_args:
        template_vars["feed_path"] = model_args['feed_path']

    return render_to_response(template, template_vars,
                              context_instance=RequestContext(request))
