#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
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

import os

from translate.storage.xliff import xlifffile

from django.shortcuts import get_object_or_404
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext

from pootle_misc.baseurl import redirect
from pootle_app.models.permissions import get_matching_permissions, check_permission
from pootle_misc.util import paginate
from pootle_profile.models import get_profile

from pootle_store.models import Store, Unit
from pootle_store.forms import unit_form_factory

def export_as_xliff(request, pootle_path):
    #FIXME: cache this
    if pootle_path[0] != '/':
        pootle_path = '/' + pootle_path
    store = get_object_or_404(Store, pootle_path=pootle_path)

    outputstore = store.convert(xlifffile)
    outputstore.switchfile(store.name, createifmissing=True)
    encoding = getattr(store.file.store, "encoding", "UTF-8")
    content_type = "application/x-xliff; charset=UTF-8"
    response = HttpResponse(str(outputstore), content_type=content_type)
    filename, ext = os.path.splitext(store.name)
    filename += os.path.extsep + 'xlf'
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    return response

def download(request, pootle_path):
    if pootle_path[0] != '/':
        pootle_path = '/' + pootle_path
    store = get_object_or_404(Store, pootle_path=pootle_path)
    store.sync(update_translation=True, create=True)
    return redirect('/export/' + store.real_path)

    step_queryset = store.units
def get_current_units(request, step_queryset):
    """returns current active unit, and in case of POST previously active unit"""
    edit_unit = None
    prev_unit = None
    pager = None
    # GET gets priority
    if 'unit' in request.GET:
        # load a specific unit in GET
        try:
            edit_id = int(request.GET['unit'])
            edit_unit = step_queryset.get(id=edit_id)
        except (Unit.DoesNotExist, ValueError):
            pass
    elif 'page' in request.GET:
        # load first unit in a specific page
        pager = paginate(request, step_queryset, items=10)
        edit_unit = pager.object_list[0]
    elif 'id' in request.POST and 'index' in request.POST:
        # GET doesn't specify a unit try POST
        prev_id = int(request.POST['id'])
        prev_index = int(request.POST['index'])
        back = request.POST.get('back', False)
        if back:
            queryset = step_queryset.filter(index__lte=prev_index).order_by('-index')
        else:
            queryset = step_queryset.filter(index__gte=prev_index).order_by('index')

        for unit in queryset.iterator():
            if edit_unit is None and prev_unit is not None:
                edit_unit = unit
                break
            if unit.id == prev_id:
                prev_unit = unit
        if edit_unit is None and prev_unit is not None:
            # probably prev_unit was last unit in chain.
            #FIXME: maybe we want to retain the show end of query behavior?
            if back:
                edit_unit = prev_unit

    if edit_unit is None:
        # all methods failed, get first unit in queryset
        edit_unit = step_queryset.iterator().next()

    return prev_unit, edit_unit, pager

def translate_page(request, units_queryset):
    cantranslate = check_permission("translate", request)
    cansuggest = check_permission("suggest", request)
    translation_project = request.translation_project
    language = translation_project.language

    try:
        prev_unit, edit_unit, pager = get_current_units(request, step_queryset)
    except StopIteration:
        return translate_end(request, translation_project)

    # time to process POST submission
    form = None
    if request.POST and prev_unit is not None and \
           ((cantranslate and 'submit' in request.POST) or \
            (cansuggest and 'suggest' in request.POST)):
        form_class = unit_form_factory(language, len(prev_unit.source.strings))
        form = form_class(request.POST, instance=prev_unit)
        if form.is_valid():
            if cantranslate and 'submit' in request.POST:
                form.save()
            elif cansuggest:
                prev_unit.add_suggestion(form.cleaned_data['target_f'], get_profile(request.user))
        else:
            # form failed, don't skip to next unit
            edit_unit = prev_unit

    # only create form for edit_unit if prev_unit was processed successfully
    if form is None or form.is_valid():
        form_class = unit_form_factory(language, len(edit_unit.source.strings))
        form = form_class(instance=edit_unit)

    if pager is None:
        store = edit_unit.store
        page = store.units.filter(index__lt=edit_unit.index).count() / 10 + 1
        pager = paginate(request, store.units, items=10, page=page)

    context = {
        'form': form,
        'unit': edit_unit,
        'store': store,
        'pager': pager,
        'language': language,
        'translation_project': store.translation_project,
        }
    return render_to_response('store/translate.html', context, context_instance=RequestContext(request))

def translate(request, pootle_path):
    if pootle_path[0] != '/':
        pootle_path = '/' + pootle_path
    store = get_object_or_404(Store, pootle_path=pootle_path)
    request.translation_project = store.translation_project
    request.permissions = get_matching_permissions(get_profile(request.user), request.translation_project.directory)

    return translate_page(request, store.units)
