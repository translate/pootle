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

from django.shortcuts import render_to_response
from django.template import RequestContext
from django.forms.models import modelformset_factory
from django.db.transaction import commit_on_success

from translate.tools.poterminology import TerminologyExtractor

from pootle_app.views.language.view import get_translation_project
from pootle_app.views.admin.util import has_permission
from pootle_misc.util import paginate
from pootle_store.models import Store, Unit, PARSED
from pootle_misc.baseurl import redirect

def create_termunit(term, unit, targets, locations, sourcenotes, transnotes, filecounts):
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
        termunit.addnote("(poterminology) %s (%d)\n" % (filename, count), 'translator')
    return termunit

@commit_on_success
@get_translation_project
@has_permission('administrate')
def extract(request, translation_project):
    """generate glossary of common keywords and phrases from translation project"""
    template_vars = {'translation_project': translation_project}
    if request.method == 'POST' and request.POST['extract']:
        extractor = TerminologyExtractor()
        for store in translation_project.stores.iterator():
            if store.name == 'pootle-terminology.po':
                continue
            extractor.processunits(store.units, store.pootle_path)
        terms = extractor.extract_terms(create_termunit=create_termunit)
        termunits = extractor.filter_terms(terms)
        store, created = Store.objects.get_or_create(parent=translation_project.directory, translation_project=translation_project,
                                                     name="pootle-terminology.po")
        if created:
            store.state = PARSED
            store.save()
        else:
            store.units.delete()

        for score, unit in termunits:
            unit.store = store
            unit.index = score
            unit.save()
            for suggestion in unit.pending_suggestions:
                unit.add_suggestion(suggestion)
        template_vars['store'] = store
        template_vars['termcount'] = len(termunits)
        return redirect(translation_project.pootle_path + 'terminology_manage.html')
    return render_to_response("terminology/extract.html", template_vars, context_instance=RequestContext(request))

@get_translation_project
@has_permission('administrate')
def manage(request, translation_project):
    template_vars = {
        "translation_project": translation_project,
        "language": translation_project.language,
        "project": translation_project.project,
        "directory": translation_project.directory,
        }
    try:
        store = Store.objects.get(pootle_path=translation_project.pootle_path + 'pootle-terminology.po')
        UnitFormSet = modelformset_factory(Unit, can_delete=True, extra=0,
                                           exclude=["index", "id", "source_f", "target_f", "developer_comment", "translator_comment", "fuzzy"])


        if request.method == 'POST' and request.POST['submit']:
            objects = paginate(request, store.units)
            formset = UnitFormSet(request.POST, queryset=objects.object_list)
            if formset.is_valid():
                formset.save()

        #FIXME: we should display errors if formset is not valid
        objects = paginate(request, store.units)
        formset = UnitFormSet(queryset=objects.object_list)
        template_vars["formset"] =  formset
        template_vars["pager"] = objects
        template_vars["store"] = store
    except Store.DoesNotExist:
        pass

    return render_to_response("terminology/manage.html", template_vars,
                              context_instance=RequestContext(request))
