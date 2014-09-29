#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2011 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from pootle.core.decorators import get_path_obj, permission_required
from pootle.core.url_helpers import split_pootle_path
from pootle_app.views.admin import util
from pootle_store.models import Store, Unit, PARSED, LOCKED

from .forms import term_unit_form_factory


def create_termunit(term, unit, targets, locations, sourcenotes, transnotes,
                    filecounts):
    termunit = Unit()
    termunit.source = term
    termunit.setid(term)

    if unit is not None:
        termunit.merge(unit)

    termunit.pending_suggestions = []

    for target in targets.keys():
        if target != termunit.target:
            termunit.pending_suggestions.append(target)

    for location in locations:
        termunit.addlocation(location)

    for sourcenote in sourcenotes:
        termunit.addnote(sourcenote, "developer")

    for filename, count in filecounts.iteritems():
        termunit.addnote('(poterminology) %s (%d)\n' % (filename, count),
                         'translator')

    return termunit


def get_terminology_filename(translation_project):
    try:
        # See if a terminology store already exists
        return translation_project.stores.filter(
            name__startswith='pootle-terminology.',
        ).values_list('name', flat=True)[0]
    except IndexError:
        pass
    if translation_project.project.is_monolingual:
        # Terminology is a virtual store, so extension is not really important
        # but to avoid confusion we will not use monolingual extensions.
        return 'pootle-terminology.po'
    return 'pootle-terminology.' + translation_project.project.localfiletype


@transaction.atomic
@get_path_obj
@permission_required('administrate')
def extract(request, translation_project):
    """Generate glossary of common keywords and phrases from translation
    project.
    """
    ctx = {
        'page': 'admin-terminology',

        'translation_project': translation_project,
        'language': translation_project.language,
        'project': translation_project.project,
        'directory': translation_project.directory,
    }
    terminology_filename = get_terminology_filename(translation_project)

    if request.method == 'POST' and request.POST['extract']:
        from translate.tools.poterminology import TerminologyExtractor
        extractor = TerminologyExtractor(
            accelchars=translation_project.checker.config.accelmarkers,
            sourcelanguage=str(translation_project.project.source_language.code)
        )

        for store in translation_project.stores.iterator():
            if store.is_terminology:
                continue
            extractor.processunits(store.units, store.pootle_path)

        terms = extractor.extract_terms(create_termunit=create_termunit)
        termunits = extractor.filter_terms(terms, nonstopmin=2)

        store, created = Store.objects.get_or_create(
            parent=translation_project.directory,
            translation_project=translation_project,
            name=terminology_filename,
        )

        # Lock file
        oldstate = store.state
        store.state = LOCKED
        store.save()

        if not created:
            store.units.delete()

        # Calculate maximum terms.
        maxunits = int(translation_project.get_total_wordcount() * 0.02)
        maxunits = min(max(settings.MIN_AUTOTERMS, maxunits),
                       settings.MAX_AUTOTERMS)
        for index, (score, unit) in enumerate(termunits[:maxunits]):
            unit.store = store
            unit.index = index
            #FIXME: what to do with score?
            unit.save()
            for suggestion in unit.pending_suggestions:
                # Touch=True which saves unit on every call
                unit.add_suggestion(suggestion)

        # Unlock file
        store.state = oldstate
        if store.state < PARSED:
            store.state = PARSED
        store.save()

        ctx.update({
            'store': store,
            'termcount': len(termunits),
        })

        path_args = split_pootle_path(translation_project.pootle_path)[:2]
        return redirect(reverse('pootle-terminology-manage', args=path_args))

    return render(request, "translation_projects/terminology/extract.html", ctx)


def manage_store(request, ctx, language, term_store):
    TermUnitForm = term_unit_form_factory(term_store)
    template_name = 'translation_projects/terminology/manage.html'
    return util.edit(request, template_name, Unit, ctx,
                     None, None, queryset=term_store.units, can_delete=True,
                     form=TermUnitForm)


@get_path_obj
@permission_required('administrate')
def manage(request, translation_project, path=None):
    ctx = {
        'page': 'admin-terminology',

        'translation_project': translation_project,
        'language': translation_project.language,
        'project': translation_project.project,
        'source_language': translation_project.project.source_language,
        'directory': translation_project.directory,
    }

    if translation_project.project.is_terminology:
        if path:
            pootle_path = translation_project.pootle_path + path
            store = get_object_or_404(Store, pootle_path=pootle_path)
            return manage_store(request, ctx, ctx['language'], store)

        # Which file should we edit?
        stores = list(Store.objects.filter(
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
            return render(request, "translation_projects/terminology/stores.html", ctx)

    try:
        terminology_filename = get_terminology_filename(translation_project)
        term_store = Store.objects.get(
            pootle_path=translation_project.pootle_path + terminology_filename,
        )
        return manage_store(request, ctx, ctx['language'], term_store)
    except Store.DoesNotExist:
        return render(request, "translation_projects/terminology/manage.html", ctx)
