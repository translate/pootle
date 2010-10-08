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

from django.conf import settings
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response
from django.template import RequestContext
from django import forms
from django.db.transaction import commit_on_success

from translate.tools.poterminology import TerminologyExtractor

from pootle_app.views.language.view import get_translation_project
from pootle_app.views.admin import util
from pootle_store.models import Store, Unit, PARSED, LOCKED
from pootle_store.forms import unit_form_factory
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

def get_terminology_filename(translation_project):
    try:
        # see if a terminology store already exists
        return translation_project.stores.filter(name__startswith='pootle-terminology.').values_list('name', flat=True)[0]
    except IndexError:
        pass
    if translation_project.project.is_monolingual():
        # terminology is a virtual store, so extension is not really important
        # but to avoid confusion we will not use monolingual extensions
        return 'pootle-terminology.po'
    return 'pootle-terminology.' + translation_project.project.localfiletype

@commit_on_success
@get_translation_project
@util.has_permission('administrate')
def extract(request, translation_project):
    """generate glossary of common keywords and phrases from translation project"""
    template_vars = {
        'translation_project': translation_project,
        'language': translation_project.language,
        'project': translation_project.project,
        'directory': translation_project.directory,

        }
    terminology_filename = get_terminology_filename(translation_project)
    if request.method == 'POST' and request.POST['extract']:
        extractor = TerminologyExtractor(accelchars=translation_project.checker.config.accelmarkers,
                                         sourcelanguage=str(translation_project.project.source_language.code))
        for store in translation_project.stores.iterator():
            if store.name.startswith('pootle-terminology.'):
                continue
            extractor.processunits(store.units, store.pootle_path)
        terms = extractor.extract_terms(create_termunit=create_termunit)
        termunits = extractor.filter_terms(terms, nonstopmin=2)
        store, created = Store.objects.get_or_create(parent=translation_project.directory,
                                                     translation_project=translation_project,
                                                     name=terminology_filename)
        # lock file
        oldstate = store.state
        store.state = LOCKED
        store.save()

        if not created:
            store.units.delete()

        # calculate maximum terms
        maxunits = int(translation_project.getquickstats()['totalsourcewords'] * 0.02)
        maxunits = min(max(settings.MIN_AUTOTERMS, maxunits), settings.MAX_AUTOTERMS)
        for index, (score, unit) in enumerate(termunits[:maxunits]):
            unit.store = store
            unit.index = index
            #FIXME: what to do with score?
            unit.save()
            for suggestion in unit.pending_suggestions:
                unit.add_suggestion(suggestion)

        # unlock file
        store.state = oldstate
        if store.state < PARSED:
            store.state = PARSED
        store.save()

        template_vars['store'] = store
        template_vars['termcount'] = len(termunits)
        return redirect(translation_project.pootle_path + 'terminology_manage.html')
    return render_to_response("terminology/extract.html", template_vars, context_instance=RequestContext(request))

@get_translation_project
@util.has_permission('administrate')
def manage(request, translation_project):
    template_vars = {
        "translation_project": translation_project,
        "language": translation_project.language,
        "project": translation_project.project,
        "source_language": translation_project.project.source_language,
        "directory": translation_project.directory,
        'formid': 'terminology-manage',
        'submitname': 'changeterminology',
        }
    try:
        terminology_filename = get_terminology_filename(translation_project)
        term_store = Store.objects.get(pootle_path=translation_project.pootle_path + terminology_filename)
        template_vars['store'] = term_store

        #HACKISH: Django won't allow excluding form fields already defined in parent class, manually extra fields.
        unit_form_class = unit_form_factory(translation_project.language, 1)
        del(unit_form_class.base_fields['target_f'])
        del(unit_form_class.base_fields['id'])
        del(unit_form_class.base_fields['translator_comment'])
        del(unit_form_class.base_fields['state'])
        del(unit_form_class.declared_fields['target_f'])
        del(unit_form_class.declared_fields['id'])
        del(unit_form_class.declared_fields['translator_comment'])
        del(unit_form_class.declared_fields['state'])

        class TermUnitForm(unit_form_class):
            # set store for new terms
            store = forms.ModelChoiceField(queryset=Store.objects.filter(pk=term_store.pk), initial=term_store.pk, widget=forms.HiddenInput)
            index = forms.IntegerField(required=False, widget=forms.HiddenInput)

            def clean_index(self):
                # assign new terms an index value
                value = self.cleaned_data['index']
                if self.instance.id is None:
                    value = term_store.max_index() + 1
                return value

            def clean_source_f(self):
                value = super(TermUnitForm, self).clean_source_f()
                if value:
                    existing = term_store.findid(value[0])
                    if existing and existing.id != self.instance.id:
                        raise forms.ValidationError(_('Please correct the error below.'))
                    self.instance.setid(value[0])
                return value

        return util.edit(request, 'terminology/manage.html', Unit, template_vars, None, None,
                         queryset=term_store.units, can_delete=True, form=TermUnitForm,
                         exclude=['state', 'target_f', 'id', 'translator_comment'])
    except Store.DoesNotExist:
        return render_to_response("terminology/manage.html", template_vars,
                                  context_instance=RequestContext(request))
