# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.shortcuts import render
from django.urls import reverse

from pootle.core.decorators import get_path_obj, permission_required
from pootle_app.views.admin import util
from pootle_store.models import Store, Unit

from .forms import term_unit_form_factory


def get_terminology_filename(translation_project):
    try:
        # See if a terminology store already exists
        return translation_project.stores.live().filter(
            name__startswith='pootle-terminology.',
        ).values_list('name', flat=True)[0]
    except IndexError:
        pass

    return (
        'pootle-terminology.%s'
        % translation_project.project.filetypes.first().extension)


def manage_store(request, ctx, language, term_store):
    TermUnitForm = term_unit_form_factory(term_store)
    template_name = 'translation_projects/terminology/manage.html'
    return util.edit(request, template_name, Unit, ctx,
                     None, None, queryset=term_store.units, can_delete=True,
                     form=TermUnitForm)


@get_path_obj
@permission_required('administrate')
def manage(request, translation_project):
    ctx = {
        'page': 'admin-terminology',

        'browse_url': reverse('pootle-tp-browse', kwargs={
            'language_code': translation_project.language.code,
            'project_code': translation_project.project.code,
        }),
        'translate_url': reverse('pootle-tp-translate', kwargs={
            'language_code': translation_project.language.code,
            'project_code': translation_project.project.code,
        }),

        'translation_project': translation_project,
        'language': translation_project.language,
        'project': translation_project.project,
        'source_language': translation_project.project.source_language,
        'directory': translation_project.directory,
    }

    if translation_project.project.is_terminology:
        # Which file should we edit?
        stores = list(Store.objects.live().filter(
            translation_project=translation_project,
        ))
        if len(stores) == 1:
            # There is only one, and we're not going to offer file-level
            # activities, so let's just edit the one that is there.
            return manage_store(request, ctx, ctx['language'], stores[0])
        elif len(stores) > 1:
            for store in stores:
                path_length = len(translation_project.pootle_path)
                store.nice_name = store.pootle_path[path_length:]

            ctx['stores'] = stores
            return render(request,
                          "translation_projects/terminology/stores.html", ctx)

    try:
        terminology_filename = get_terminology_filename(translation_project)
        term_store = Store.objects.get(
            pootle_path=translation_project.pootle_path + terminology_filename,
        )
        return manage_store(request, ctx, ctx['language'], term_store)
    except Store.DoesNotExist:
        return render(request, "translation_projects/terminology/manage.html",
                      ctx)
