#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010-2012 Zuza Software Foundation
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
from datetime import datetime

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, render_to_response
from django.template import loader, RequestContext
from django.utils.translation import to_locale, ugettext as _
from django.utils.translation.trans_real import parse_accept_lang_header
from django.utils import simplejson
from django.utils.encoding import iri_to_uri
from django.views.decorators.cache import never_cache

from translate.lang import data

from pootle_app.models import Suggestion as SuggestionStat
from pootle_app.models.permissions import (get_matching_permissions,
                                           check_permission,
                                           check_profile_permission)
from pootle_misc.baseurl import redirect
from pootle_misc.checks import get_quality_check_failures
from pootle_misc.forms import make_search_form
from pootle_misc.stats import get_raw_stats
from pootle_misc.url_manip import ensure_uri, previous_view_url
from pootle_misc.util import paginate, ajax_required, jsonify
from pootle_profile.models import get_profile
from pootle_statistics.models import (Submission, SubmissionFields,
                                      SubmissionTypes)
from pootle_store.models import Store, Unit
from pootle_store.forms import (unit_comment_form_factory, unit_form_factory,
                                highlight_whitespace)
from pootle_store.signals import translation_submitted
from pootle_store.templatetags.store_tags import (highlight_diffs,
                                                  pluralize_source,
                                                  pluralize_target)
from pootle_store.util import (UNTRANSLATED, FUZZY, TRANSLATED, STATES_MAP,
                               absolute_real_path, find_altsrcs, get_sugg_list)


def _common_context(request, translation_project, permission_codes):
    """Adds common context to request object and checks permissions."""
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
            unit = get_object_or_404(
                    Unit.objects.select_related("store__translation_project", "store__parent"),
                    id=uid,
            )
            _common_context(request, unit.store.translation_project, permission_codes)
            request.unit = unit
            request.store = unit.store
            request.directory = unit.store.parent
            return f(request, unit, *args, **kwargs)
        return decorated_f
    return wrap_f


@get_store_context('view')
def export_as_xliff(request, store):
    """Export given file to xliff for offline translation."""
    path = store.real_path
    if not path:
        # bug 2106
        project = request.translation_project.project
        if project.get_treestyle() == "gnu":
            path = "/".join(store.pootle_path.split(os.path.sep)[2:])
        else:
            parts = store.pootle_path.split(os.path.sep)[1:]
            path = "%s/%s/%s" % (parts[1], parts[0], "/".join(parts[2:]))

    path, ext = os.path.splitext(path)
    export_path = "/".join(['POOTLE_EXPORT', path + os.path.extsep + 'xlf'])
    abs_export_path = absolute_real_path(export_path)

    key = iri_to_uri("%s:export_as_xliff" % store.pootle_path)
    last_export = cache.get(key)
    if not (last_export and last_export == store.get_mtime() and os.path.isfile(abs_export_path)):
        from pootle_app.project_tree import ensure_target_dir_exists
        from translate.storage.poxliff import PoXliffFile
        from pootle_misc import ptempfile as tempfile
        import shutil
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
    """Export given file to xliff for offline translation."""
    from pootle_store.filetypes import factory_classes, is_monolingual
    klass = factory_classes.get(filetype, None)
    if not klass or is_monolingual(klass) or store.pootle_path.endswith(filetype):
        raise ValueError

    path, ext = os.path.splitext(store.real_path)
    export_path = os.path.join('POOTLE_EXPORT', path + os.path.extsep + filetype)
    abs_export_path = absolute_real_path(export_path)

    key = iri_to_uri("%s:export_as_%s" % (store.pootle_path, filetype))
    last_export = cache.get(key)
    if not (last_export and last_export == store.get_mtime() and os.path.isfile(abs_export_path)):
        from pootle_app.project_tree import ensure_target_dir_exists
        from pootle_misc import ptempfile as tempfile
        import shutil
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
    """Narrows down units query to units matching search string."""

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
    """Narrows down unit query to units matching conditions in GET and POST."""
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

    if 'checks' in request.GET:
        checks = request.GET['checks'].split(',')

        if checks:
            checks_queryset = units_queryset.filter(
                qualitycheck__false_positive=False,
                qualitycheck__name__in=checks
            )

            units_queryset = checks_queryset

    if 'matchnames' in request.GET:
        matchnames = request.GET['matchnames'].split(',')
        if matchnames:
            match_queryset = units_queryset.none()
            if 'hassuggestion' in matchnames:
                #FIXME: is None the most efficient query
                match_queryset = units_queryset.exclude(suggestion=None)
                matchnames.remove('hassuggestion')
            elif 'ownsuggestion' in matchnames:
                match_queryset = units_queryset.filter(suggestion__user=request.profile).distinct()
                matchnames.remove('ownsuggestion')

            units_queryset = match_queryset

    if 'search' in request.GET and 'sfields' in request.GET:
        # use the search form for validation only
        search_form = make_search_form(request.GET)
        if search_form.is_valid():
            units_queryset = get_search_step_query(request.translation_project, search_form, units_queryset)
    return units_queryset


def translate_page(request):
    cantranslate = check_permission("translate", request)
    cansuggest = check_permission("suggest", request)
    canreview = check_permission("review", request)

    translation_project = request.translation_project
    language = translation_project.language
    project = translation_project.project
    profile = request.profile

    store = getattr(request, "store", None)
    is_terminology = project.is_terminology or store and store.is_terminology
    search_form = make_search_form(request=request, terminology=is_terminology)

    previous_overview_url = previous_view_url(request, ['overview'])

    context = {
        'cantranslate': cantranslate,
        'cansuggest': cansuggest,
        'canreview': canreview,
        'search_form': search_form,
        'store': store,
        'store_id': store and store.id,
        'language': language,
        'project': project,
        'translation_project': translation_project,
        'profile': profile,
        'source_language': translation_project.project.source_language,
        'directory': getattr(request, "directory", None),
        'previous_overview_url': previous_overview_url,
        'MT_BACKENDS': settings.MT_BACKENDS,
        'LOOKUP_BACKENDS': settings.LOOKUP_BACKENDS,
        'AMAGAMA_URL': settings.AMAGAMA_URL,
        }

    return render_to_response('store/translate.html', context,
                              context_instance=RequestContext(request))


@get_store_context('view')
def translate(request, store):
    return translate_page(request)

#
# Views used with XMLHttpRequest requests.
#

def _filter_ctx_units(units_qs, unit, how_many, gap=0):
    """Returns ``how_many``*2 units that are before and after ``index``."""
    result = {'before': [], 'after': []}

    if how_many and unit.index - gap > 0:
        before = units_qs.filter(store=unit.store_id, index__lt=unit.index) \
                         .order_by('-index')[gap:how_many+gap]
        result['before'] = _build_units_list(before, reverse=True)
        result['before'].reverse()

    #FIXME: can we avoid this query if length is known?
    if how_many:
        after = units_qs.filter(store=unit.store_id,
                                index__gt=unit.index)[gap:how_many+gap]
        result['after'] = _build_units_list(after)

    return result

def _build_units_list(units, reverse=False):
    """Given a list/queryset of units, builds a list with the unit data
    contained in a dictionary ready to be returned as JSON.

    :return: A list with unit id, source, and target texts. In case of
             having plural forms, a title for the plural form is also provided.
    """
    return_units = []
    for unit in iter(units):
        source_unit = []
        target_unit = []
        for i, source, title in pluralize_source(unit):
            unit_dict = {'text': source}
            if title:
                unit_dict["title"] = title
            source_unit.append(unit_dict)
        for i, target, title in pluralize_target(unit):
            unit_dict = {'text': target}
            if title:
                unit_dict["title"] = title
            target_unit.append(unit_dict)
        prev = None
        next = None
        if return_units:
            if reverse:
                return_units[-1]['prev'] = unit.id
                next = return_units[-1]['id']
            else:
                return_units[-1]['next'] = unit.id
                prev = return_units[-1]['id']
        return_units.append({'id': unit.id,
                             'isfuzzy': unit.isfuzzy(),
                             'prev': prev,
                             'next': next,
                             'source': source_unit,
                             'target': target_unit})
    return return_units


def _build_pager_dict(pager):
    """Given a pager object ``pager``, retrieves all the information needed
    to build a pager.

    :return: A dictionary containing necessary pager information to build
             a pager.
    """
    return {"number": pager.number,
            "num_pages": pager.paginator.num_pages,
            "per_page": pager.paginator.per_page
           }


def _get_index_in_qs(qs, unit, store=False):
    """Given a queryset ``qs``, returns the position (index) of the unit
    ``unit`` within that queryset. ``store`` specifies if the queryset is
    limited to a single store.

    :return: Value representing the position of the unit ``unit``.
    :rtype: int
    """
    if store:
        return qs.filter(index__lt=unit.index).count()
    else:
        store = unit.store
        return (qs.filter(store=store, index__lt=unit.index) | \
                qs.filter(store__pootle_path__lt=store.pootle_path)).count()


def get_view_units(request, units_queryset, store, limit=0):
    """Gets source and target texts excluding the editing unit.

    :return: An object in JSON notation that contains the source and target
             texts for units that will be displayed before and after editing
             unit.

             If asked by using the ``meta`` and ``pager`` parameters,
             metadata and pager information will be calculated and returned
             too.
    """
    current_unit = None
    json = {}

    try:
        limit = int(limit)
    except ValueError:
        limit = None

    if not limit:
        limit = request.profile.get_unit_rows()

    step_queryset = get_step_query(request, units_queryset)

    # Return metadata it has been explicitely requested
    if request.GET.get('meta', False):
        tp = request.translation_project
        json["meta"] = {"source_lang": tp.project.source_language.code,
                        "source_dir": tp.project.source_language.get_direction(),
                        "target_lang": tp.language.code,
                        "target_dir": tp.language.get_direction(),
                        "project_style": tp.project.checkstyle}

    # Maybe we are trying to load directly a specific unit, so we have
    # to calculate its page number
    uid = request.GET.get('uid', None)
    if uid:
        current_unit = units_queryset.get(id=uid)
        preceding = _get_index_in_qs(step_queryset, current_unit, store)
        page = preceding / limit + 1
    else:
        page = None

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
    """Gets source and target texts excluding the editing widget (store-level).

    :return: An object in JSON notation that contains the source and target
             texts for units that will be displayed before and after
             unit ``uid``.
    """
    return get_view_units(request, store.units, store=True, limit=limit)


def _is_filtered(request):
    """Checks if unit list is filtered."""
    return ('unitstates' in request.GET or 'matchnames' in request.GET or
            'checks' in request.GET or ('search' in request.GET and
            'sfields' in request.GET))


@ajax_required
@get_unit_context('view')
def get_more_context(request, unit):
    """Retrieves more context units.

    :return: An object in JSON notation that contains the source and target
             texts for units that are in the context of unit ``uid``.
    """
    store = request.store
    json = {}
    gap = int(request.GET.get('gap', 0))
    qty = int(request.GET.get('qty', 1))

    json["ctx"] = _filter_ctx_units(store.units, unit, qty, gap)
    rcode = 200
    response = jsonify(json)
    return HttpResponse(response, status=rcode, mimetype="application/json")


@never_cache
@get_unit_context('view')
def timeline(request, unit):
    """Returns a JSON-encoded string including the changes to the unit
    rendered in HTML.
    """
    timeline = Submission.objects.filter(unit=unit, field__in=[
        SubmissionFields.TARGET, SubmissionFields.STATE,
        SubmissionFields.COMMENT
    ])
    timeline = timeline.select_related("submitter__user",
                                       "translation_project__language")

    context = {}
    entries_group = []

    import locale
    from itertools import groupby
    from pootle_store.fields import to_python

    for key, values in groupby(timeline, key=lambda x: x.creation_time):
        entry_group = {
            'datetime': key,
            'datetime_str': key.strftime(locale.nl_langinfo(locale.D_T_FMT)),
            'entries': [],
        }

        for item in values:
            # Only add submitter information for the whole entry group once
            if 'submitter' not in entry_group:
                entry_group['submitter'] = item.submitter

            if 'language' not in context:
                context['language'] = item.translation_project.language

            entry = {
                'field': item.field,
                'field_name': SubmissionFields.NAMES_MAP[item.field],
            }

            if item.field == SubmissionFields.STATE:
                entry['old_value'] = STATES_MAP[int(to_python(item.old_value))]
                entry['new_value'] = STATES_MAP[int(to_python(item.new_value))]
            else:
                entry['new_value'] = to_python(item.new_value)

            entry_group['entries'].append(entry)

        entries_group.append(entry_group)

    # Let's reverse the chronological order
    entries_group.reverse()
    context['entries_group'] = entries_group

    if request.is_ajax():
        # The client will want to confirm that the response is relevant for
        # the unit on screen at the time of receiving this, so we add the uid.
        json = {'uid': unit.id}

        t = loader.get_template('unit/xhr-timeline.html')
        c = RequestContext(request, context)
        json['timeline'] = t.render(c)

        response = simplejson.dumps(json)
        return HttpResponse(response, mimetype="application/json")
    else:
        return render_to_response('unit/timeline.html', context,
                                  context_instance=RequestContext(request))


@ajax_required
@get_unit_context('translate')
def comment(request, unit):
    """Stores a new comment for the given ``unit``.

    :return: If the form validates, the cleaned comment is returned.
             An error message is returned otherwise.
    """
    # Update current unit instance's attributes
    unit.commented_by = request.profile
    unit.commented_on = datetime.utcnow()

    language = request.translation_project.language
    form = unit_comment_form_factory(language)(request.POST, instance=unit,
                                               request=request)

    if form.is_valid():
        form.save()

        context = {
            'comment': unit.translator_comment,
            'language': language,
            'submitter': request.profile,
        }
        t = loader.get_template('unit/xhr-comment.html')
        c = RequestContext(request, context)

        json = {'comment': t.render(c)}
        rcode = 200
    else:
        json = {'msg':  _("Comment submission failed.")}
        rcode = 400

    response = simplejson.dumps(json)

    return HttpResponse(response, status=rcode, mimetype="application/json")


@never_cache
@ajax_required
@get_unit_context('view')
def get_edit_unit(request, unit):
    """Given a store path ``pootle_path`` and unit id ``uid``, gathers all the
    necessary information to build the editing widget.

    :return: A templatised editing widget is returned within the ``editor``
             variable and paging information is also returned if the page
             number has changed.
    """
    json = {}

    translation_project = request.translation_project
    language = translation_project.language

    if unit.hasplural():
        snplurals = len(unit.source.strings)
    else:
        snplurals = None

    form_class = unit_form_factory(language, snplurals, request)
    form = form_class(instance=unit)
    comment_form_class = unit_comment_form_factory(language)
    comment_form = comment_form_class({}, instance=unit)

    store = unit.store
    directory = store.parent
    profile = request.profile
    alt_src_langs = get_alt_src_langs(request, profile, translation_project)
    project = translation_project.project
    report_target = ensure_uri(project.report_target)

    suggestions = get_sugg_list(unit)
    template_vars = {
        'unit': unit,
        'form': form,
        'comment_form': comment_form,
        'store': store,
        'directory': directory,
        'profile': profile,
        'user': request.user,
        'language': language,
        'source_language': translation_project.project.source_language,
        'cantranslate': check_profile_permission(profile, "translate",
                                                 directory),
        'cansuggest': check_profile_permission(profile, "suggest", directory),
        'canreview': check_profile_permission(profile, "review", directory),
        'altsrcs': find_altsrcs(unit, alt_src_langs, store=store,
                                project=project),
        'report_target': report_target,
        'suggestions': suggestions,
    }

    if translation_project.project.is_terminology or store.is_terminology:
        t = loader.get_template('unit/term_edit.html')
    else:
        t = loader.get_template('unit/edit.html')
    c = RequestContext(request, template_vars)
    json['editor'] = t.render(c)

    rcode = 200

    # Return context rows if filtering is applied but
    # don't return any if the user has asked not to have it
    current_filter = request.GET.get('filter', 'all')
    show_ctx = request.COOKIES.get('ctxShow', 'true')

    if ((_is_filtered(request) or current_filter not in ('all',)) and
        show_ctx == 'true'):
        # TODO: review if this first 'if' branch makes sense
        if translation_project.project.is_terminology or store.is_terminology:
            json['ctx'] = _filter_ctx_units(store.units, unit, 0)
        else:
            ctx_qty = int(request.COOKIES.get('ctxQty', 1))
            json['ctx'] = _filter_ctx_units(store.units, unit, ctx_qty)
    response = jsonify(json)
    return HttpResponse(response, status=rcode, mimetype="application/json")


def get_failing_checks(request, pathobj):
    """Gets a list of failing checks for the current object.

    :return: JSON string with a list of failing check categories which
             include the actual checks that are failing.
    """
    stats = get_raw_stats(pathobj)
    failures = get_quality_check_failures(pathobj, stats, include_url=False)

    response = jsonify(failures)

    return HttpResponse(response, mimetype="application/json")


@ajax_required
@get_store_context('view')
def get_failing_checks_store(request, store):
    return get_failing_checks(request, store)


@ajax_required
@get_unit_context('')
def submit(request, unit):
    """Processes translation submissions and stores them in the database.

    :return: An object in JSON notation that contains the previous and last
             units for the unit next to unit ``uid``.
    """
    json = {}

    cantranslate = check_permission("translate", request)
    if not cantranslate:
        raise PermissionDenied(_("You do not have rights to access "
                                 "translation mode."))

    translation_project = request.translation_project
    language = translation_project.language

    if unit.hasplural():
        snplurals = len(unit.source.strings)
    else:
        snplurals = None

    # Update current unit instance's attributes
    unit.submitted_by = request.profile
    unit.submitted_on = datetime.utcnow()

    form_class = unit_form_factory(language, snplurals, request)
    form = form_class(request.POST, instance=unit)

    if form.is_valid():
        if form.updated_fields:
            # Store creation time so that it is the same for all submissions
            creation_time=datetime.utcnow()
            for field, old_value, new_value in form.updated_fields:
                sub = Submission(
                        creation_time=creation_time,
                        translation_project=translation_project,
                        submitter=request.profile,
                        unit=unit,
                        field=field,
                        type=SubmissionTypes.NORMAL,
                        old_value=old_value,
                        new_value=new_value,
                )
                sub.save()

            form.save()
            translation_submitted.send(
                    sender=translation_project,
                    unit=form.instance,
                    profile=request.profile,
            )

        rcode = 200
    else:
        # Form failed
        #FIXME: we should display validation errors here
        rcode = 400
        json["msg"] = _("Failed to process submission.")
    response = jsonify(json)
    return HttpResponse(response, status=rcode, mimetype="application/json")


@ajax_required
@get_unit_context('')
def suggest(request, unit):
    """Processes translation suggestions and stores them in the database.

    :return: An object in JSON notation that contains the previous and last
             units for the unit next to unit ``uid``.
    """
    json = {}

    cansuggest = check_permission("suggest", request)
    if not cansuggest:
        raise PermissionDenied(_("You do not have rights to access "
                                 "translation mode."))

    translation_project = request.translation_project
    language = translation_project.language

    if unit.hasplural():
        snplurals = len(unit.source.strings)
    else:
        snplurals = None

    form_class = unit_form_factory(language, snplurals, request)
    form = form_class(request.POST, instance=unit)

    if form.is_valid():
        if form.instance._target_updated:
            # TODO: Review if this hackish method is still necessary
            #HACKISH: django 1.2 stupidly modifies instance on
            # model form validation, reload unit from db
            unit = Unit.objects.get(id=unit.id)
            sugg = unit.add_suggestion(form.cleaned_data['target_f'],
                                       request.profile)
            if sugg:
                SuggestionStat.objects.get_or_create(
                    translation_project=translation_project,
                    suggester=request.profile, state='pending', unit=unit.id
                )
        rcode = 200
    else:
        # Form failed
        #FIXME: we should display validation errors here
        rcode = 400
        json["msg"] = _("Failed to process suggestion.")
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
        if sugg is not None and success and request.profile != sugg.user:
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
            suggestion = unit.suggestion_set.get(id=suggid)
        except ObjectDoesNotExist:
            raise Http404

        old_target = unit.target
        success = unit.accept_suggestion(suggid)
        json['newtargets'] = [highlight_whitespace(target) for target in unit.target.strings]
        json['newdiffs'] = {}
        for sugg in unit.get_suggestions():
            json['newdiffs'][sugg.id] = [highlight_diffs(unit.target.strings[i], target) \
                                         for i, target in enumerate(sugg.target.strings)]

        if suggestion is not None and success:
            if suggestion.user:
                translation_submitted.send(sender=translation_project, unit=unit, profile=suggestion.user)
            #FIXME: we need a totally different model for tracking stats, this is just lame
            if suggestion.user != request.profile:
                suggstat, created = SuggestionStat.objects.get_or_create(translation_project=translation_project,
                                                                     suggester=suggestion.user,
                                                                     state='pending',
                                                                     unit=unit.id)
                suggstat.reviewer = request.profile
                suggstat.state = 'accepted'
                suggstat.save()
            else:
                suggstat = None

            # For now assume the target changed
            # TODO: check all fields for changes
            creation_time=datetime.utcnow()
            sub = Submission(
                    creation_time=creation_time,
                    translation_project=translation_project,
                    submitter=suggestion.user,
                    from_suggestion=suggstat,
                    unit=unit,
                    field=SubmissionFields.TARGET,
                    type=SubmissionTypes.SUGG_ACCEPT,
                    old_value=old_target,
                    new_value=unit.target,
            )
            sub.save()
    response = jsonify(json)
    return HttpResponse(response, mimetype="application/json")

@ajax_required
def clear_vote(request, voteid):
    json = {}
    json["voteid"] = voteid
    if request.POST.get('clear'):
        try:
            from voting.models import Vote
            vote = Vote.objects.get(pk=voteid)
            if vote.user != request.user:
                raise PermissionDenied("Users can only remove their own votes") # no i18n, will not go to UI
            vote.delete()
        except ObjectDoesNotExist:
            raise Http404
    response = jsonify(json)
    return HttpResponse(response, mimetype="application/json")


@ajax_required
@get_unit_context('')
def vote_up(request, unit, suggid):
    json = {}
    json["suggid"] = suggid
    if request.POST.get('up'):
        try:
            suggestion = unit.suggestion_set.get(id=suggid)
            from voting.models import Vote
            Vote.objects.record_vote(suggestion, request.user, +1) # why can't it just return the vote object?
            json["voteid"] = Vote.objects.get_for_user(suggestion, request.user).id
        except ObjectDoesNotExist:
            raise Http404(_("The suggestion or vote is not valid any more."))
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
