#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from django.db.transaction import commit_on_success
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import ugettext as _

from pootle.core.decorators import get_path_obj, permission_required
from pootle_app.views.admin import util
from pootle_store.models import Store, Unit, PARSED, LOCKED


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
        termunit.addnote("(poterminology) %s (%d)\n" % (filename, count),
                         'translator')
    return termunit


def get_terminology_filename(translation_project):
    try:
        # See if a terminology store already exists.
        return translation_project.stores.filter(name__startswith='pootle-terminology.').values_list('name', flat=True)[0]
    except IndexError:
        pass
    if translation_project.project.is_monolingual:
        # Terminology is a virtual store, so extension is not really important
        # but to avoid confusion we will not use monolingual extensions.
        return 'pootle-terminology.po'
    return 'pootle-terminology.' + translation_project.project.localfiletype


@commit_on_success
@get_path_obj
@permission_required('administrate')
def extract(request, translation_project):
    """Generate glossary of common keywords and phrases from translation
    project.
    """
    template_vars = {
        'translation_project': translation_project,
        'language': translation_project.language,
        'project': translation_project.project,
        'directory': translation_project.directory,
    }
    if request.method == 'POST' and request.POST['extract']:
        from translate.tools.poterminology import TerminologyExtractor
        terminology_extractor_params = {
            'accelchars': translation_project.checker.config.accelmarkers,
            'sourcelanguage': str(translation_project.project.source_language.code),
        }
        extractor = TerminologyExtractor(**terminology_extractor_params)
        for store in translation_project.stores.iterator():
            if store.is_terminology:
                continue
            extractor.processunits(store.units, store.pootle_path)
        terms = extractor.extract_terms(create_termunit=create_termunit)
        termunits = extractor.filter_terms(terms, nonstopmin=2)
        create_criteria = {
            'parent': translation_project.directory,
            'translation_project': translation_project,
            'name': get_terminology_filename(translation_project),
        }
        store, created = Store.objects.get_or_create(**create_criteria)
        # Lock file.
        oldstate = store.state
        store.state = LOCKED
        store.save()

        if not created:
            store.units.delete()

        # Calculate maximum terms.
        maxunits = int(translation_project.getquickstats()['totalsourcewords'] * 0.02)
        maxunits = min(max(settings.MIN_AUTOTERMS, maxunits), settings.MAX_AUTOTERMS)
        for index, (score, unit) in enumerate(termunits[:maxunits]):
            unit.store = store
            unit.index = index
            #FIXME: what to do with score?
            unit.save()
            for suggestion in unit.pending_suggestions:
                # Touch=True which saves unit on every call.
                unit.add_suggestion(suggestion)

        # Unlock file.
        store.state = oldstate
        if store.state < PARSED:
            store.state = PARSED
        store.save()

        template_vars['store'] = store
        template_vars['termcount'] = len(termunits)
        from pootle_misc.baseurl import redirect
        return redirect(translation_project.pootle_path +
                        'terminology_manage.html')
    return render_to_response("terminology/extract.html", template_vars,
                              context_instance=RequestContext(request))


def manage_store(request, template_vars, language, term_store):
    from django import forms
    from pootle_store.forms import unit_form_factory
    unit_form_class = unit_form_factory(language)

    # XXX: Review this
    # HACKISH: Django won't allow excluding form fields already defined in
    # the parent class, manually extra fields.
    del(unit_form_class.base_fields['target_f'])
    del(unit_form_class.base_fields['id'])
    del(unit_form_class.base_fields['state'])
    del(unit_form_class.declared_fields['target_f'])
    del(unit_form_class.declared_fields['id'])
    del(unit_form_class.declared_fields['state'])

    class TermUnitForm(unit_form_class):
        # Set store for new terms.
        qs = Store.objects.filter(pk=term_store.pk)
        store = forms.ModelChoiceField(queryset=qs, initial=term_store.pk,
                                       widget=forms.HiddenInput)
        index = forms.IntegerField(required=False, widget=forms.HiddenInput)

        def clean_index(self):
            # Assign new terms an index value.
            value = self.cleaned_data['index']

            if self.instance.id is None:
                value = term_store.max_index() + 1
            return value

        def clean_source_f(self):
            value = super(TermUnitForm, self).clean_source_f()

            if value:
                existing = term_store.findid(value[0])

                if existing and existing.id != self.instance.id:
                    raise forms.ValidationError(_('This term already exists '
                                                  'in this file.'))
                self.instance.setid(value[0])

            return value

    #TODO 'submitted_by' and 'commented_by' had to be excluded in order to get
    # terminology editing working. When the schema can be changed again this
    # exclusion should be removed and change the schema accordingly.
    return util.edit(request, 'terminology/manage.html', Unit, template_vars,
                     None, None, queryset=term_store.units, can_delete=True,
                     form=TermUnitForm, exclude=['state', 'target_f', 'id',
                        'translator_comment', 'submitted_by', 'commented_by'])


@get_path_obj
@permission_required('administrate')
def manage(request, translation_project, path=None):
    template_vars = {
        "translation_project": translation_project,
        "language": translation_project.language,
        "project": translation_project.project,
        "source_language": translation_project.project.source_language,
        "directory": translation_project.directory,
    }
    if translation_project.project.is_terminology:
        if path:
            try:
                path = translation_project.pootle_path + path
                store = Store.objects.get(pootle_path=path)
                return manage_store(request, template_vars,
                                    translation_project.language, store)
            except Store.DoesNotExist:
                # FIXME   flash message and show list?
                pass

        # Which file should we edit?
        stores = list(Store.objects.filter(translation_project=translation_project))
        if len(stores) == 1:
            # There is only one, and we're not going to offer file-level
            # activities, so let's just edit the one that is there.
            return manage_store(request, template_vars,
                                translation_project.language, stores[0])
        elif len(stores) > 1:
            for store in stores:
                length = len(translation_project.pootle_path)
                store.nice_name = store.pootle_path[length:]

            template_vars['stores'] = stores
            return render_to_response("terminology/stores.html", template_vars,
                                      context_instance=RequestContext(request))

    try:
        get_criteria = {
            'pootle_path': (translation_project.pootle_path +
                            get_terminology_filename(translation_project))
        }
        term_store = Store.objects.get(**get_criteria)

        return manage_store(request, template_vars,
                            translation_project.language, term_store)
    except Store.DoesNotExist:
        return render_to_response("terminology/manage.html", template_vars,
                                  context_instance=RequestContext(request))
