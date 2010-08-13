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
import logging

from translate.storage.poxliff import PoXliffFile
from translate.lang import data

from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.translation import to_locale, ugettext as _
from django.utils.translation.trans_real import parse_accept_lang_header
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.core.cache import cache
from django.conf import settings
from django.utils import simplejson
from django.views.decorators.cache import never_cache

from pootle_misc.baseurl import redirect
from pootle_app.models.permissions import get_matching_permissions, check_permission, check_profile_permission
from pootle_misc.util import paginate
from pootle_profile.models import get_profile
from pootle_translationproject.forms import SearchForm
from pootle_statistics.models import Submission
from pootle_app.models import Suggestion as SuggestionStat

from pootle_store.models import Store, Unit
from pootle_store.forms import unit_form_factory, highlight_whitespace
from pootle_store.templatetags.store_tags import highlight_diffs
from pootle_store.util import UNTRANSLATED, FUZZY, TRANSLATED

def export_as_xliff(request, pootle_path):
    #FIXME: cache this
    if pootle_path[0] != '/':
        pootle_path = '/' + pootle_path
    store = get_object_or_404(Store, pootle_path=pootle_path)

    outputstore = store.convert(PoXliffFile)
    outputstore.switchfile(store.name, createifmissing=True)
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
    store.sync(update_translation=True)
    return redirect('/export/' + store.real_path)

####################### Translate Page ##############################

def get_alt_src_langs(request, profile, translation_project):
    language = translation_project.language
    project = translation_project.project
    source_language = project.source_language

    langs = profile.alt_src_langs.exclude(id__in=(language.id, source_language.id)).filter(translationproject__project=project)

    if not profile.alt_src_langs.count():
        from pootle_language.models import Language
        accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        for accept_lang, unused in parse_accept_lang_header(accept):
            if accept_lang == '*':
                continue
            normalized = to_locale(data.normalize_code(data.simplify_to_common(accept_lang)))
            code = to_locale(accept_lang)
            if normalized in ('en', 'en_US', source_language.code, language.code) or \
                   code in ('en', 'en_US', source_language.code, language.code):
                continue
            langs = Language.objects.filter(code__in=(normalized, code), translationproject__project=project)
            if langs.count():
                break
    return langs

def get_non_indexed_search_step_query(form, units_queryset):
    result = units_queryset
    for word in form.cleaned_data['search'].split():
        subresult = units_queryset.none()
        if 'source' in form.cleaned_data['sfields']:
            subresult = subresult | units_queryset.filter(source_f__contains=word)
        if 'target' in form.cleaned_data['sfields']:
            subresult = subresult | units_queryset.filter(target_f__contains=word)
        if 'notes' in form.cleaned_data['sfields']:
            subresult = subresult | units_queryset.filter(developer_comment__contains=word) | \
                     units_queryset.filter(translator_comment__contains=word)
        if 'locations' in form.cleaned_data['sfields']:
            subresult = subresult | units_queryset.filter(locations__contains=word)
        result = subresult & result
    return result

def get_search_step_query(translation_project, form, units_queryset):
    """Narrows down units query to units matching search string"""

    if translation_project.indexer is None:
        logging.debug("No indexer for %s, using database search", translation_project)
        return get_non_indexed_search_step_query(form, units_queryset)

    logging.debug("Found %s indexer for %s, using indexed search",
                  translation_project.indexer.INDEX_DIRECTORY_NAME, translation_project)

    word_querylist = []
    for word in form.cleaned_data['search'].split():
        # Generate a list for the query based on the selected fields
        word_querylist = [(field, word) for field in form.cleaned_data['sfields']]
    paths = units_queryset.order_by().values_list('store__pootle_path', flat=True).distinct()
    path_querylist = [('pofilename', pootle_path) for pootle_path in paths.iterator()]
    cache_key = "search:%s" % str(hash((repr(path_querylist), translation_project.get_mtime(), repr(word_querylist))))

    dbids = cache.get(cache_key)
    if dbids is None:
        searchparts = []
        textquery = translation_project.indexer.make_query(word_querylist, False)
        searchparts.append(textquery)
        pathquery = translation_project.indexer.make_query(path_querylist, False)
        searchparts.append(pathquery)
        limitedquery = translation_project.indexer.make_query(searchparts, True)

        result = translation_project.indexer.search(limitedquery, ['dbid'])
        dbids = [int(item['dbid'][0]) for item in result[:999]]
        cache.set(cache_key, dbids, settings.OBJECT_CACHE_TIMEOUT)
    return units_queryset.filter(id__in=dbids)

def get_step_query(request, units_queryset):
    """Narrows down unit query to units matching conditions in GET and POST"""
    if 'unit' in request.GET or 'page' in request.GET:
        return units_queryset

    if 'unitstates' in request.GET:
        unitstates = request.GET['unitstates'].split(',')
        if unitstates:
            state_queryset = units_queryset.none()
            for unitstate in unitstates:
                if unitstate == 'untranslated':
                    state_queryset = state_queryset | units_queryset.filter(state=UNTRANSLATED)
                elif unitstate == 'translated':
                    state_queryset = state_queryset | units_queryset.filter(state=TRANSLATED)
                elif unitstate == 'fuzzy':
                    state_queryset = state_queryset | units_queryset.filter(state=FUZZY)
            units_queryset = state_queryset

    if 'matchnames' in request.GET:
        matchnames = request.GET['matchnames'].split(',')
        if matchnames:
            match_queryset = units_queryset.none()
            if 'hassuggestion' in matchnames:
                match_queryset = units_queryset.exclude(suggestion=None)
                matchnames.remove('hassuggestion')
            if matchnames:
                match_queryset = match_queryset | units_queryset.filter(
                    qualitycheck__false_positive=False, qualitycheck__name__in=matchnames)
            units_queryset = match_queryset

    return units_queryset.distinct()

def get_current_units(request, step_queryset, units_queryset):
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
        profile = get_profile(request.user)
        unit_rows = profile.get_unit_rows()
        pager = paginate(request, units_queryset, items=unit_rows)
        edit_unit = pager.object_list[0]
    elif 'id' in request.POST and 'index' in request.POST:
        # GET doesn't specify a unit try POST
        prev_id = int(request.POST['id'])
        prev_index = int(request.POST['index'])
        pootle_path = request.POST['pootle_path']
        back = request.POST.get('back', False)
        if back:
            queryset = (step_queryset.filter(store__pootle_path=pootle_path, index__lte=prev_index) | \
                        step_queryset.filter(store__pootle_path__lt=pootle_path)
                        ).order_by('-store__pootle_path', '-index')
        else:
            queryset = (step_queryset.filter(store__pootle_path=pootle_path, index__gte=prev_index) | \
                        step_queryset.filter(store__pootle_path__gt=pootle_path)
                        ).order_by('store__pootle_path', 'index')

        for unit in queryset.iterator():
            if edit_unit is None and prev_unit is not None:
                edit_unit = unit
                break
            if unit.id == prev_id:
                prev_unit = unit
            elif unit.index > prev_index or back and unit.index < prev_index:
                logging.debug("submitting to a unit no longer part of step query, %s:%d", (pootle_path, prev_id))
                # prev_unit no longer part of the query, load it directly
                edit_unit = unit
                prev_unit = Unit.objects.get(store__pootle_path=pootle_path, id=prev_id)
                break

    if edit_unit is None:
        if prev_unit is not None:
            # probably prev_unit was last unit in chain.
            if back:
                edit_unit = prev_unit
        else:
            # all methods failed, get first unit in queryset
            try:
                edit_unit = step_queryset.iterator().next()
            except StopIteration:
                pass

    return prev_unit, edit_unit, pager

def translate_end(request, translation_project):
    """render a message at end of review, translate or search action"""
    checks = 'matchnames' in request.GET
    if request.POST:
        # end of iteration
        if checks:
            message = _("No more matching strings to review.")
        else:
            message = _("No more matching strings to translate.")
    else:
        if checks:
            message = _("No matching strings to review.")
        else:
            message = _("No matching strings to translate.")

    if 'search' in request.GET and 'sfields' in request.GET:
        search_form = SearchForm(request.GET)
    else:
        search_form = SearchForm()

    context = {
        'endmessage': message,
        'translation_project': translation_project,
        'language': translation_project.language,
        'project': translation_project.project,
        'directory': translation_project.directory,
        'search_form': search_form,
        'checks': checks,
        }
    return render_to_response('store/translate_end.html', context, context_instance=RequestContext(request))


def translate_page(request, units_queryset, store=None):
    if not check_permission("view", request):
        raise PermissionDenied(_("You do not have rights to access this translation project."))

    cantranslate = check_permission("translate", request)
    cansuggest = check_permission("suggest", request)
    canreview = check_permission("review", request)
    translation_project = request.translation_project
    language = translation_project.language
    # shouldn't we globalize profile context
    profile = get_profile(request.user)

    step_queryset = None

    # Process search first
    search_form = None
    if 'search' in request.GET and 'sfields' in request.GET:
        search_form = SearchForm(request.GET)
        if search_form.is_valid():
            step_queryset = get_search_step_query(request.translation_project, search_form, units_queryset)
    else:
        search_form = SearchForm()

    # which units are we interested in?
    if step_queryset is None:
        step_queryset = get_step_query(request, units_queryset)

    prev_unit, edit_unit, pager = get_current_units(request, step_queryset, units_queryset)

    # time to process POST submission
    form = None
    if prev_unit is not None and ('submit' in request.POST or 'suggest' in request.POST):
        # check permissions
        if 'submit'  in request.POST and not cantranslate or \
           'suggest' in request.POST and not cansuggest:
            raise PermissionDenied

        form_class = unit_form_factory(language, len(prev_unit.source.strings))
        form = form_class(request.POST, instance=prev_unit)
        if form.is_valid():
            if cantranslate and 'submit' in request.POST:
                form.save()
                sub = Submission(translation_project=translation_project,
                                 submitter=get_profile(request.user))
                sub.save()
            elif cansuggest and 'suggest' in request.POST:
                #HACKISH: django 1.2 stupidly modifies instance on model form validation, reload unit from db
                prev_unit = Unit.objects.get(id=prev_unit.id)
                prev_unit.add_suggestion(form.cleaned_data['target_f'], get_profile(request.user))
                SuggestionStat.objects.get_or_create(translation_project=translation_project,
                                                           suggester=get_profile(request.user),
                                                           state='pending',
                                                           unit=prev_unit.id)
        else:
            # form failed, don't skip to next unit
            edit_unit = prev_unit

    if edit_unit is None:
        # no more units to step through, display end of translation message
        return translate_end(request, translation_project)

    # only create form for edit_unit if prev_unit was processed successfully
    if form is None or form.is_valid():
        form_class = unit_form_factory(language, len(edit_unit.source.strings))
        form = form_class(instance=edit_unit)

    if store is None:
        store = edit_unit.store
        pager_query = units_queryset
        preceding = (pager_query.filter(store=store, index__lt=edit_unit.index) | \
                     pager_query.filter(store__pootle_path__lt=store.pootle_path)).distinct().count()
        store_preceding = store.units.filter(index__lt=edit_unit.index).count()
    else:
        pager_query = store.units
        preceding = pager_query.filter(index__lt=edit_unit.index).count()
        store_preceding = preceding

    unit_rows = profile.get_unit_rows()

    # regardless of the query used to step through units, we will
    # display units in their original context, and display a pager for
    # the store not for the unit_step query
    if pager is None:
        page = preceding / unit_rows + 1
        pager = paginate(request, pager_query, items=unit_rows, page=page)

    # we always display the active unit in the middle of the page to
    # provide context for translators
    context_rows = (unit_rows - 1) / 2
    if store_preceding > context_rows:
        unit_position = store_preceding % unit_rows
        if unit_position < context_rows:
            # units too close to the top of the batch
            offset = unit_rows - (context_rows - unit_position)
            units_query = store.units[offset:]
            page = store_preceding / unit_rows
            units = paginate(request, units_query, items=unit_rows, page=page).object_list
        elif unit_position >= unit_rows - context_rows:
            # units too close to the bottom of the batch
            offset = context_rows - (unit_rows - unit_position - 1)
            units_query = store.units[offset:]
            page = store_preceding / unit_rows + 1
            units = paginate(request, units_query, items=unit_rows, page=page).object_list
        else:
            units = pager.object_list
    else:
        units = store.units[:unit_rows]

    # caluclate url querystring so state is retained on POST
    # we can't just use request URL cause unit and page GET vars cancel state
    GET_vars = []
    for key, values in request.GET.lists():
        if key not in ('page', 'unit'):
            for value in values:
                GET_vars.append('%s=%s' % (key, value))

    # links for quality check documentation
    checks = []
    for check in request.GET.getlist('matchnames'):
        link = '<a href="http://translate.sourceforge.net/wiki/toolkit/pofilter_tests#%s" target="_blank">%s</a>' % (check, check)
        checks.append(_('checking %s', link))

    # precalculate alternative source languages
    alt_src_langs = get_alt_src_langs(request, profile, translation_project)
    alt_src_codes = alt_src_langs.values_list('code', flat=True)

    context = {
        'unit_rows': unit_rows,
        'alt_src_langs': alt_src_langs,
        'alt_src_codes': alt_src_codes,
        'cantranslate': cantranslate,
        'cansuggest': cansuggest,
        'canreview': canreview,
        'form': form,
        'search_form': search_form,
        'edit_unit': edit_unit,
        'store': store,
        'pager': pager,
        'units': units,
        'language': language,
        'translation_project': translation_project,
        'project': translation_project.project,
        'profile': profile,
        'source_language': translation_project.project.source_language,
        'directory': store.parent,
        'GET_state': '&'.join(GET_vars),
        'checks': checks,
        'MT_BACKENDS': settings.MT_BACKENDS,
        'APERTIUM_API_KEY': getattr(settings, 'APERTIUM_API_KEY', None),
        }
    return render_to_response('store/translate.html', context, context_instance=RequestContext(request))

@never_cache
def translate(request, pootle_path):
    if pootle_path[0] != '/':
        pootle_path = '/' + pootle_path
    try:
        store = Store.objects.select_related('translation_project', 'parent').get(pootle_path=pootle_path)
    except Store.DoesNotExist:
        raise Http404
    request.translation_project = store.translation_project
    request.permissions = get_matching_permissions(get_profile(request.user), request.translation_project.directory)

    return translate_page(request, store.units, store=store)

def reject_suggestion(request, uid, suggid):
    unit = get_object_or_404(Unit, id=uid)
    directory = unit.store.parent
    translation_project = unit.store.translation_project

    response = {
        'udbid': unit.id,
        'sugid': suggid,
        }
    if request.POST.get('reject'):
        try:
            sugg = unit.suggestion_set.get(id=suggid)
        except ObjectDoesNotExist:
            sugg = None

        profile = get_profile(request.user)
        if not check_profile_permission(profile, 'review', directory) and \
               (not request.user.is_authenticated() or sugg and sugg.user != profile):
            raise PermissionDenied

        response['success'] = unit.reject_suggestion(suggid)

        if sugg is not None and response['success']:
            #FIXME: we need a totally different model for tracking stats, this is just lame
            suggstat, created = SuggestionStat.objects.get_or_create(translation_project=translation_project,
                                                            suggester=sugg.user,
                                                            state='pending',
                                                            unit=unit.id)
            suggstat.reviewer = get_profile(request.user)
            suggstat.state = 'rejected'
            suggstat.save()

    response = simplejson.dumps(response, indent=4)
    return HttpResponse(response, mimetype="application/json")

def accept_suggestion(request, uid, suggid):
    unit = get_object_or_404(Unit, id=uid)
    directory = unit.store.parent
    translation_project = unit.store.translation_project

    if not check_profile_permission(get_profile(request.user), 'review', directory):
        raise PermissionDenied

    response = {
        'udbid': unit.id,
        'sugid': suggid,
        }

    if request.POST.get('accept'):
        try:
            sugg = unit.suggestion_set.get(id=suggid)
        except ObjectDoesNotExist:
            sugg = None

        response['success'] = unit.accept_suggestion(suggid)
        response['newtargets'] = [highlight_whitespace(target) for target in unit.target.strings]
        response['newdiffs'] = {}
        for sugg in unit.get_suggestions():
            response['newdiffs'][sugg.id] = [highlight_diffs(unit.target.strings[i], target) \
                                             for i, target in enumerate(sugg.target.strings)]

        if sugg is not None and response['success']:
            #FIXME: we need a totally different model for tracking stats, this is just lame
            suggstat, created = SuggestionStat.objects.get_or_create(translation_project=translation_project,
                                                            suggester=sugg.user,
                                                            state='pending',
                                                            unit=unit.id)
            suggstat.reviewer = get_profile(request.user)
            suggstat.state = 'accepted'
            suggstat.save()

            sub = Submission(translation_project=translation_project,
                             submitter=get_profile(request.user),
                             from_suggestion=suggstat)
            sub.save()

    response = simplejson.dumps(response, indent=4)
    return HttpResponse(response, mimetype="application/json")


def reject_qualitycheck(request, uid, checkid):
    unit = get_object_or_404(Unit, id=uid)
    directory = unit.store.parent
    if not check_profile_permission(get_profile(request.user), 'review', directory):
        raise PermissionDenied

    response = {
        'udbid': unit.id,
        'checkid': checkid,
        }
    if request.POST.get('reject'):
        try:
            check = unit.qualitycheck_set.get(id=checkid)
            check.false_positive = True
            check.save()
            # update timestamp
            unit.save()
            response['success'] = True
        except ObjectDoesNotExist:
            check = None
            response['success'] = False

    response = simplejson.dumps(response, indent=4)
    return HttpResponse(response, mimetype="application/json")
