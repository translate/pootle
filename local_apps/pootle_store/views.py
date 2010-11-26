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
import tempfile
import shutil

from translate.storage.poxliff import PoXliffFile
from translate.lang import data

from django.conf import settings
from django.shortcuts import get_object_or_404
from django.http import HttpResponse, Http404
from django.shortcuts import render_to_response
from django.template import loader, RequestContext
from django.utils.translation import to_locale, ugettext as _
from django.utils.translation import ungettext
from django.utils.translation.trans_real import parse_accept_lang_header
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.core.cache import cache
from django.utils import simplejson
from django.views.decorators.cache import never_cache
from django.utils.encoding import iri_to_uri

from pootle_misc.baseurl import redirect
from pootle_app.models.permissions import get_matching_permissions, check_permission, check_profile_permission
from pootle_misc.util import paginate, ajax_required
from pootle_profile.models import get_profile
from pootle_translationproject.forms import SearchForm
from pootle_statistics.models import Submission
from pootle_app.models import Suggestion as SuggestionStat
from pootle_app.project_tree import ensure_target_dir_exists

from pootle_store.models import Store, Unit
from pootle_store.forms import unit_form_factory, highlight_whitespace
from pootle_store.templatetags.store_tags import fancy_highlight, find_altsrcs, get_sugg_list, highlight_diffs, pluralize_source, pluralize_target
from pootle_store.util import UNTRANSLATED, FUZZY, TRANSLATED, absolute_real_path
from pootle_store.filetypes import factory_classes, is_monolingual

def jsonify(json):
    if settings.DEBUG:
        indent = 4
    else:
        indent = None
    return simplejson.dumps(json, indent=indent)

def _common_context(request,  translation_project, permission_codes):
    """adds common context to request object and checks permissions"""
    request.translation_project = translation_project
    request.profile = get_profile(request.user)
    request.permissions = get_matching_permissions(request.profile,
                                                   translation_project.directory)
    if not permission_codes:
        # skip checking permissions
        return

    if isinstance(permission_codes, basestring):
        permission_codes = [permission_codes]
    for permission_code in permission_codes:
        if not check_permission(permission_code, request):
            raise PermissionDenied(_("Insufficient rights to this translation project."))


def get_store_context(permission_codes):
    def wrap_f(f):
        def decorated_f(request, pootle_path, *args, **kwargs):
            if pootle_path[0] != '/':
                pootle_path = '/' + pootle_path
            try:
                store = Store.objects.select_related('translation_project', 'parent').get(pootle_path=pootle_path)
            except Store.DoesNotExist:
                raise Http404
            _common_context(request, store.translation_project, permission_codes)
            request.store = store
            request.directory = store.parent
            return f(request, store, *args, **kwargs)
        return decorated_f
    return wrap_f

def get_unit_context(permission_codes):
    def wrap_f(f):
        def decorated_f(request, uid, *args, **kwargs):
            unit = get_object_or_404(Unit, id=uid)
            _common_context(request, unit.store.translation_project, permission_codes)
            request.unit = unit
            request.store = unit.store
            request.directory = unit.store.parent
            return f(request, unit, *args, **kwargs)
        return decorated_f
    return wrap_f

@get_store_context('view')
def export_as_xliff(request, store):
    """export given file to xliff for offline translation"""
    path, ext = os.path.splitext(store.real_path)
    export_path = os.path.join('POOTLE_EXPORT', path + os.path.extsep + 'xlf')
    abs_export_path = absolute_real_path(export_path)

    key = iri_to_uri("%s:export_as_xliff" % store.pootle_path)
    last_export = cache.get(key)
    if not (last_export and last_export == store.get_mtime() and os.path.isfile(abs_export_path)):
        ensure_target_dir_exists(abs_export_path)
        outputstore = store.convert(PoXliffFile)
        outputstore.switchfile(store.name, createifmissing=True)
        fd, tempstore = tempfile.mkstemp(prefix=store.name, suffix='.xlf')
        os.close(fd)
        outputstore.savefile(tempstore)
        shutil.move(tempstore, abs_export_path)
        cache.set(key, store.get_mtime(), settings.OBJECT_CACHE_TIMEOUT)
    return redirect('/export/' + export_path)

@get_store_context('view')
def export_as_type(request, store, filetype):
    """export given file to xliff for offline translation"""
    klass = factory_classes.get(filetype, None)
    if not klass or is_monolingual(klass) or store.pootle_path.endswith(filetype):
        raise ValueError

    path, ext = os.path.splitext(store.real_path)
    export_path = os.path.join('POOTLE_EXPORT', path + os.path.extsep + filetype)
    abs_export_path = absolute_real_path(export_path)

    key = iri_to_uri("%s:export_as_%s" % (store.pootle_path, filetype))
    last_export = cache.get(key)
    if not (last_export and last_export == store.get_mtime() and os.path.isfile(abs_export_path)):
        ensure_target_dir_exists(abs_export_path)
        outputstore = store.convert(klass)
        fd, tempstore = tempfile.mkstemp(prefix=store.name, suffix=os.path.extsep + filetype)
        os.close(fd)
        outputstore.savefile(tempstore)
        shutil.move(tempstore, abs_export_path)
        cache.set(key, store.get_mtime(), settings.OBJECT_CACHE_TIMEOUT)
    return redirect('/export/' + export_path)

@get_store_context('view')
def download(request, store):
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
    words = form.cleaned_data['search'].split()
    result = units_queryset.none()

    if 'source' in form.cleaned_data['sfields']:
        subresult = units_queryset
        for word in words:
            subresult = subresult.filter(source_f__icontains=word)
        result = result | subresult

    if 'target' in form.cleaned_data['sfields']:
        subresult = units_queryset
        for word in words:
            subresult = subresult.filter(target_f__icontains=word)
        result = result | subresult

    if 'notes' in form.cleaned_data['sfields']:
        translator_subresult = units_queryset
        developer_subresult = units_queryset
        for word in words:
            translator_subresult = translator_subresult.filter(translator_comment__icontains=word)
            developer_subresult = developer_subresult.filter(developer_comment__icontains=word)
        result = result | translator_subresult | developer_subresult

    if 'locations' in form.cleaned_data['sfields']:
        subresult = units_queryset
        for word in words:
            subresult = subresult.filter(locations__icontains=word)
        result = result | subresult

    return result

def get_search_step_query(translation_project, form, units_queryset):
    """Narrows down units query to units matching search string"""

    if translation_project.indexer is None:
        logging.debug(u"No indexer for %s, using database search", translation_project)
        return get_non_indexed_search_step_query(form, units_queryset)

    logging.debug(u"Found %s indexer for %s, using indexed search",
                  translation_project.indexer.INDEX_DIRECTORY_NAME, translation_project)

    word_querylist = []
    words = form.cleaned_data['search'].split()
    fields = form.cleaned_data['sfields']
    paths = units_queryset.order_by().values_list('store__pootle_path', flat=True).distinct()
    path_querylist = [('pofilename', pootle_path) for pootle_path in paths.iterator()]
    cache_key = "search:%s" % str(hash((repr(path_querylist), translation_project.get_mtime(), repr(words), repr(fields))))

    dbids = cache.get(cache_key)
    if dbids is None:
        searchparts = []
        # Split the search expression into single words. Otherwise xapian and
        # lucene would interprete the whole string as an "OR" combination of
        # words instead of the desired "AND".
        for word in words:
            # Generate a list for the query based on the selected fields
            word_querylist = [(field, word) for field in fields]
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

    if 'search' in request.GET and 'sfields' in request.GET:
        search_form = SearchForm(request.GET)
        if search_form.is_valid():
            units_queryset = get_search_step_query(request.translation_project, search_form, units_queryset)
    return units_queryset

def translate_page(request):
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
        profile = request.profile
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

        #FIXME: instead of using an arbitrary limit it would be best to page through mother query
        for unit in queryset[:64].iterator():
            if edit_unit is None and prev_unit is not None:
                edit_unit = unit
                break
            if unit.id == prev_id:
                prev_unit = unit
            elif unit.index > prev_index or back and unit.index < prev_index:
                logging.debug(u"submitting to a unit no longer part of step query, %s:%d", (pootle_path, prev_id))
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
                edit_unit = step_queryset[0:1][0]
            except IndexError:
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


    cantranslate = check_permission("translate", request)
    cansuggest = check_permission("suggest", request)
    canreview = check_permission("review", request)
    translation_project = request.translation_project
    language = translation_project.language
    profile = request.profile

    #step_queryset = None
    search_form = SearchForm()
    """
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
    '''

    step_queryset = get_step_query(request, units_queryset)

    prev_unit, edit_unit, pager = get_current_units(request, step_queryset, units_queryset)

    # time to process POST submission
    form = None
    if prev_unit is not None and ('submit' in request.POST or 'suggest' in request.POST):
        # check permissions
        if 'submit'  in request.POST and not cantranslate or \
           'suggest' in request.POST and not cansuggest:
            raise PermissionDenied

        if prev_unit.hasplural():
            snplurals = len(prev_unit.source.strings)
        else:
            snplurals = None
        form_class = unit_form_factory(language, snplurals)
        form = form_class(request.POST, instance=prev_unit)
        if form.is_valid():
            if cantranslate and 'submit' in request.POST:
                if form.instance._target_updated or form.instance._translator_comment_updated or \
                       form.instance._state_updated:
                    form.save()
                    sub = Submission(translation_project=translation_project,
                                     submitter=profile)
                    sub.save()

            elif cansuggest and 'suggest' in request.POST:
                if form.instance._target_updated:
                    #HACKISH: django 1.2 stupidly modifies instance on
                    # model form validation, reload unit from db
                    prev_unit = Unit.objects.get(id=prev_unit.id)
                    sugg = prev_unit.add_suggestion(form.cleaned_data['target_f'], profile)
                    if sugg:
                        SuggestionStat.objects.get_or_create(translation_project=translation_project,
                                                             suggester=profile,
                                                             state='pending', unit=prev_unit.id)
        else:
            # form failed, don't skip to next unit
            edit_unit = prev_unit

    if edit_unit is None:
        # no more units to step through, display end of translation message
        return translate_end(request, translation_project)

    # only create form for edit_unit if prev_unit was processed successfully
    if form is None or form.is_valid():
        if edit_unit.hasplural():
            snplurals = len(edit_unit.source.strings)
        else:
            snplurals = None
        form_class = unit_form_factory(language, snplurals)
        form = form_class(instance=edit_unit)

    if store is None:
        store = edit_unit.store
        pager_query = units_queryset
        preceding = (pager_query.filter(store=store, index__lt=edit_unit.index) | \
                     pager_query.filter(store__pootle_path__lt=store.pootle_path)).count()
        store_preceding = store.units.filter(index__lt=edit_unit.index).count()
    else:
        pager_query = store.units
        preceding = pager_query.filter(index__lt=edit_unit.index).count()
        store_preceding = preceding

    '''
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
    for check in request.GET.get('matchnames', '').split(','):
        if not check:
            continue
        safe_check = escape(check)
        link = '<a href="http://translate.sourceforge.net/wiki/toolkit/pofilter_tests#%s" target="_blank">%s</a>' % (safe_check, safe_check)
        checks.append(_('checking %s', link))

    # precalculate alternative source languages
    alt_src_langs = get_alt_src_langs(request, profile, translation_project)
    alt_src_codes = alt_src_langs.values_list('code', flat=True)
    """

    context = {
        #'unit_rows': unit_rows,
        #'alt_src_langs': alt_src_langs,
        #'alt_src_codes': alt_src_codes,
        'cantranslate': cantranslate,
        'cansuggest': cansuggest,
        'canreview': canreview,
        #'form': form,
        'search_form': search_form,
        'store': getattr(request, "store", None),
        #'edit_unit': edit_unit,
        #'pager': pager,
        #'units': units,
        'language': language,
        'translation_project': translation_project,
        #'project': translation_project.project,
        'profile': profile,
        'source_language': translation_project.project.source_language,
        'directory': getattr(request, "directory", None),
        #'GET_state': '&'.join(GET_vars),
        #'checks': checks,
        'MT_BACKENDS': settings.MT_BACKENDS,
        'AMAGAMA_URL': settings.AMAGAMA_URL,
        }
    return render_to_response('store/translate.html', context, context_instance=RequestContext(request))

@never_cache
@get_store_context('view')
def translate(request, store):
    return translate_page(request)

#
# Views used with XMLHttpRequest requests.
#

def _filter_queryset(qdict, qs, tp):
    """
    Filters the given C{qs} unit queryset by the criterion specified
    in the C{qdict} POST/GET parameters.

    @return: A filtered queryset.
    """
    filtered = qs
    if 'filter' in qdict and 'checks' not in qdict:
        filter_by = qdict['filter']
        if filter_by == "incomplete":
            filtered = qs.filter(state=FUZZY) | qs.filter(state=UNTRANSLATED)
        elif filter_by == "untranslated":
            filtered = qs.filter(state=UNTRANSLATED)
        elif filter_by == "fuzzy":
            filtered = qs.filter(state=FUZZY)
        elif filter_by == "suggestions":
            filtered = qs.exclude(suggestion=None)
        elif filter_by == "search":
            if 'search' in qdict and 'sfields' in qdict:
                search_form = SearchForm(qdict)
                if search_form.is_valid():
                    filtered = get_search_step_query(tp, search_form, qs)

    if 'checks' in qdict:
        checks = qdict['checks'].split(',')
        if checks:
            filtered = qs.filter(qualitycheck__false_positive=False,
                                 qualitycheck__name__in=checks)

    return filtered

def _filter_view_units(units_qs, current_page, per_page):
    """
    Returns C{per_page} units that are contained within page C{current_page}.
    """
    start_index = per_page * (current_page - 1)
    end_index = start_index + per_page
    filtered = units_qs[start_index:end_index]
    return _build_units_list(filtered)

def _filter_ctxt_units(units_qs, index, limit, gap=0):
    """
    Returns C{limit}*2 units that are before and after C{index}.
    """
    result = {}
    if index - gap > 0:
        before = units_qs.filter(index__lt=index)[gap:limit+gap]
        result['before'] = _build_units_list(before)
    else:
        result['before'] = []
    #FIXME: can we avoid this query if length is known?
    after = units_qs.filter(index__gt=index)[gap:limit+gap]
    result['after'] = _build_units_list(after)
    return result

def _get_prevnext_unit_ids(qs, unit):
    """
    Gets the previous and next unit ids of C{unit} based on index.

    @return: previous and next units. If previous or next is missing,
    None will be returned.
    """
    current_index = _get_index_in_qs(qs, unit)
    prev_index = qs.count()
    next_index = prev_index
    if current_index is not None:
        if current_index > 0:
            prev_index = current_index - 1
        next_index = current_index + 1
    try:
        prev = qs[prev_index].id
    except IndexError:
        prev = None
    try:
        next = qs[next_index].id
    except IndexError:
        next = None
    return prev, next

def _build_units_list(units):
    """
    Given a list/queryset of units, builds a list with the unit data
    contained in a dictionary ready to be returned as JSON.

    @return: A list with unit id, source, and target texts. In case of
    having plural forms, a title for the plural form is also provided.
    """
    return_units = []
    for unit in units.iterator():
        source_unit = []
        target_unit = []
        for i, source, title in pluralize_source(unit):
            unit_dict = {'text': fancy_highlight(source)}
            if title:
                unit_dict["title"] = title
            source_unit.append(unit_dict)
        for i, target, title in pluralize_target(unit):
            unit_dict = {'text': fancy_highlight(target)}
            if title:
                unit_dict["title"] = title
            target_unit.append(unit_dict)
        prev = None
        if return_units:
            return_units[-1]['next'] = unit.id
            prev = return_units[-1]['id']
        return_units.append({'id': unit.id,
                             'isfuzzy': unit.isfuzzy(),
                             'prev': prev,
                             'source': source_unit,
                             'target': target_unit})
    return return_units

def _build_pager_dict(pager):
    """
    Given a pager object C{pager}, retrieves all the information needed
    to build a pager.

    @return: A dictionary containing necessary pager information to build
    a pager.
    """
    return {"number": pager.number,
            "num_pages": pager.paginator.num_pages,
            "per_page": pager.paginator.per_page
           }

def _get_index_in_qs(qs, unit):
    """
    Given a queryset C{qs}, returns the position (index) of the unit C{unit}
    within that queryset.

    @return: Integer value representing the position of the unit C{unit}.
    """
    return qs.filter(index__lt=unit.index).count()

def get_view_units(request, units_queryset, limit=0):
    """
    @return: An object in JSON notation that contains the source and target
    texts for units that will be displayed before and after editing unit.

    If asked by using the 'meta' and 'pager' parameters, metadata and pager
    information will be calculated and returned too.
    """
    current_unit = None
    json = {}

    if not limit:
        limit = request.profile.get_unit_rows()

    step_queryset = get_step_query(request, units_queryset)

    # Return metadata it has been explicitely requested
    if request.GET.get('meta', False):
        tp = request.translation_project
        json["meta"] = {"source_lang": tp.project.source_language.code,
                        "source_dir": tp.project.source_language.get_direction(),
                        "target_lang": tp.language.code,
                        "target_dir": tp.language.get_direction()}

    # Maybe we are trying to load directly a specific unit, so we have
    # to calculate its page number
    uid = request.GET.get('uid', None)
    if uid:
        current_unit = step_queryset.get(id=uid)
        preceding = _get_index_in_qs(step_queryset, current_unit)
        page = preceding / limit + 1
    else:
        # Try to get a given page number, otherwise assume it's the first one
        page = int(request.GET.get('page', 1))

    pager = paginate(request, step_queryset, items=limit, page=page)

    json["units"] = _build_units_list(pager.object_list)

    # Return paging information if requested to do so
    if request.GET.get('pager', False):
        json["pager"] = _build_pager_dict(pager)
        if not current_unit:
            try:
                json["uid"] = json["units"][0]["id"]
            except IndexError:
                pass
        else:
            json["uid"] = current_unit.id

    response = jsonify(json)
    return HttpResponse(response, mimetype="application/json")


@ajax_required
@get_store_context('view')
def get_view_units_store(request, store, limit=0):
    """
    @return: An object in JSON notation that contains the source and target
    texts for units that will be displayed before and after unit C{uid}.
    """
    return get_view_units(request, store.units, limit=limit)

def _is_filtered(request):
    """checks if unit list is filtered"""
    return 'unitstates' in request.GET or 'matchnames' in request.GET or \
           ('search' in request.GET and 'sfields' in request.GET)

@ajax_required
@get_unit_context('view')
def get_more_context(request, unit):
    """
    @return: An object in JSON notation that contains the source and target
    texts for units that are in context of unit C{uid}.
    """
    store = request.store
    json = {}
    gap = int(request.GET.get('gap', 0))

    json["ctxt"] = _filter_ctxt_units(store.units, unit.index, 2, gap)
    rcode = 200
    response = jsonify(json)
    return HttpResponse(response, status=rcode, mimetype="application/json")

@ajax_required
@get_unit_context('view')
def get_edit_unit(request, unit):
    """
    Given a store path C{pootle_path} and unit id C{uid}, gathers all the
    necessary information to build the editing widget.

    @return: A templatised editing widget is returned within the C{editor}
    variable and paging information is also returned if the page number has
    changed.
    """

    json = {}

    translation_project = request.translation_project
    language = translation_project.language

    if unit.hasplural():
        snplurals = len(unit.source.strings)
    else:
        snplurals = None
    form_class = unit_form_factory(language, snplurals)
    form = form_class(instance=unit)
    store = unit.store
    directory = store.parent
    profile = request.profile
    alt_src_langs = get_alt_src_langs(request, profile, translation_project)
    project = translation_project.project
    template_vars = {'unit': unit,
                     'form': form,
                     'store': store,
                     'profile': profile,
                     'user': request.user,
                     'language': language,
                     'source_language': translation_project.project.source_language,
                     'cantranslate': check_profile_permission(profile, "translate", directory),
                     'cansuggest': check_profile_permission(profile, "suggest", directory),
                     'canreview': check_profile_permission(profile, "review", directory),
                     'altsrcs': find_altsrcs(unit, alt_src_langs, store=store, project=project),
                     'suggestions': get_sugg_list(unit)}

    t = loader.get_template('unit/edit.html')
    c = RequestContext(request, template_vars)
    json['editor'] = t.render(c)
    rcode = 200
    # Return context rows if filtering is applied
    if _is_filtered(request) or request.GET.get('filter', 'all') != 'all':
        json['ctxt'] = _filter_ctxt_units(store.units, unit.index, 2)
    response = jsonify(json)
    return HttpResponse(response, status=rcode, mimetype="application/json")


def get_failing_checks(request, pathobj):
    """
    Gets a list of failing checks for the current object.

    @return: JSON string representing action status and depending on success,
    returns an error message or a list containing the the name and number of
    failing checks.
    """
    json = {}
    checkopts = []
    # Borrowed from pootle_app.views.language.item_dict.getcheckdetails
    property_stats = pathobj.getcompletestats()
    quick_stats = pathobj.getquickstats()
    total = quick_stats['total']
    keys = property_stats.keys()
    keys.sort()
    for checkname in keys:
        checkcount = property_stats[checkname]
        if total and checkcount:
            stats = ungettext('%(checkname)s (%(checks)d)',
                              '%(checkname)s (%(checks)d)', checkcount,
                              {"checks": checkcount, "checkname": checkname})
            checkopt = {'name': checkname,
                        'text': stats}
            checkopts.append(checkopt)
            json["checks"] = checkopts
    response = jsonify(json)
    return HttpResponse(response, mimetype="application/json")


@ajax_required
@get_store_context('view')
def get_failing_checks_store(request, store):
    return get_failing_checks(request, store)

@ajax_required
@get_unit_context('')
def process_submit(request, unit, type):
    """
    Processes submissions and suggestions and stores them in the database.

    @return: An object in JSON notation that contains the previous
    and last units for the unit next to unit C{uid}.
    """
    json = {}
    cantranslate = check_permission("translate", request)
    cansuggest = check_permission("suggest", request)
    if type == 'submission' and not cantranslate or type == 'suggestion' and not cansuggest:
        raise PermissionDenied(_("You do not have rights to access translation mode."))

    translation_project = request.translation_project
    language = translation_project.language
    if unit.hasplural():
        snplurals = len(unit.source.strings)
    else:
        snplurals = None
    form_class = unit_form_factory(language, snplurals)
    form = form_class(request.POST, instance=unit)
    if form.is_valid():
        if type == 'submission':
            if form.instance._target_updated or \
               form.instance._translator_comment_updated or \
               form.instance._state_updated:
                form.save()
                sub = Submission(translation_project=translation_project,
                                 submitter=request.profile)
                sub.save()
        elif type == 'suggestion':
            if form.instance._target_updated:
                #HACKISH: django 1.2 stupidly modifies instance on
                # model form validation, reload unit from db
                unit = Unit.objects.get(id=unit.id)
                sugg = unit.add_suggestion(form.cleaned_data['target_f'], request.profile)
                if sugg:
                    SuggestionStat.objects.get_or_create(translation_project=translation_project,
                                                         suggester=request.profile,
                                                         state='pending', unit=unit.id)
        rcode = 200
    else:
        # Form failed
        #FIXME: we should display validation errors here
        rcode = 400
        json["msg"] = _("Failed to process submit.")
    response = jsonify(json)
    return HttpResponse(response, status=rcode, mimetype="application/json")


@ajax_required
@get_unit_context('')
def reject_suggestion(request, unit, suggid):
    json = {}
    translation_project = request.translation_project

    json["udbid"] = unit.id
    json["sugid"] = suggid
    if request.POST.get('reject'):
        try:
            sugg = unit.suggestion_set.get(id=suggid)
        except ObjectDoesNotExist:
            raise Http404
        if not check_permission('review', request) and \
                   (not request.user.is_authenticated() or sugg and sugg.user != request.profile):
            raise PermissionDenied(_("You do not have rights to access review mode."))

        success = unit.reject_suggestion(suggid)
        if sugg is not None and success:
            #FIXME: we need a totally different model for tracking stats, this is just lame
            suggstat, created = SuggestionStat.objects.get_or_create(translation_project=translation_project,
                                                                     suggester=sugg.user,
                                                                     state='pending',
                                                                     unit=unit.id)
            suggstat.reviewer = request.profile
            suggstat.state = 'rejected'
            suggstat.save()
    response = jsonify(json)
    return HttpResponse(response, mimetype="application/json")

@ajax_required
@get_unit_context('review')
def accept_suggestion(request, unit, suggid):
    json = {}
    translation_project = request.translation_project
    json["udbid"] = unit.id
    json["sugid"] = suggid
    if request.POST.get('accept'):
        try:
            sugg = unit.suggestion_set.get(id=suggid)
        except ObjectDoesNotExist:
            raise Http404

        success = unit.accept_suggestion(suggid)
        json['newtargets'] = [highlight_whitespace(target) for target in unit.target.strings]
        json['newdiffs'] = {}
        for sugg in unit.get_suggestions():
            json['newdiffs'][sugg.id] = [highlight_diffs(unit.target.strings[i], target) \
                                         for i, target in enumerate(sugg.target.strings)]

        if sugg is not None and success:
            #FIXME: we need a totally different model for tracking stats, this is just lame
            suggstat, created = SuggestionStat.objects.get_or_create(translation_project=translation_project,
                                                                     suggester=sugg.user,
                                                                     state='pending',
                                                                     unit=unit.id)
            suggstat.reviewer = request.profile
            suggstat.state = 'accepted'
            suggstat.save()

            sub = Submission(translation_project=translation_project,
                             submitter=request.profile,
                             from_suggestion=suggstat)
            sub.save()
    response = jsonify(json)
    return HttpResponse(response, mimetype="application/json")


@ajax_required
@get_unit_context('review')
def reject_qualitycheck(request, unit, checkid):
    json = {}
    json["udbid"] = unit.id
    json["checkid"] = checkid
    if request.POST.get('reject'):
        try:
            check = unit.qualitycheck_set.get(id=checkid)
            check.false_positive = True
            check.save()
            # update timestamp
            unit.save()
        except ObjectDoesNotExist:
            raise Http404

    response = jsonify(json)
    return HttpResponse(response, mimetype="application/json")
