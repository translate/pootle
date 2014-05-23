#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010-2013 Zuza Software Foundation
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

import logging
import os
from itertools import groupby

from translate.filters.decorators import Category
from translate.lang import data
from translate.search.lshtein import LevenshteinComparer

from django.conf import settings
from django.contrib.auth.models import User
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.template import loader, RequestContext
from django.utils.translation import to_locale, ugettext as _
from django.utils.translation.trans_real import parse_accept_lang_header
from django.utils import timezone
from django.utils.encoding import iri_to_uri
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_POST

from taggit.models import Tag

from pootle.core.decorators import (get_path_obj, get_resource,
                                    permission_required)
from pootle.core.exceptions import Http400
from pootle.core.url_helpers import split_pootle_path
from pootle_app.models import Suggestion as SuggestionStat
from pootle_app.models.permissions import (check_permission,
                                           check_profile_permission)
from pootle_language.models import Language
from pootle_misc.checks import check_names
from pootle_misc.forms import make_search_form
from pootle_misc.util import ajax_required, jsonify, to_int
from pootle_profile.models import get_profile
from pootle_project.models import Project
from pootle_statistics.models import (Submission, SubmissionFields,
                                      SubmissionTypes)
from pootle_tagging.forms import TagForm
from pootle_tagging.models import Goal
from pootle_translationproject.models import TranslationProject

from .decorators import get_store_context, get_unit_context
from .fields import to_python
from .forms import (unit_comment_form_factory, unit_form_factory,
                    highlight_whitespace)
from .models import Store, TMUnit, Unit
from .signals import translation_submitted
from .templatetags.store_tags import (highlight_diffs, pluralize_source,
                                      pluralize_target)
from .util import (UNTRANSLATED, FUZZY, TRANSLATED, STATES_MAP,
                   absolute_real_path, find_altsrcs, get_sugg_list)


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
    if (not (last_export and last_export == store.get_mtime() and
        os.path.isfile(abs_export_path))):
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
    if (not klass or is_monolingual(klass) or
        store.pootle_path.endswith(filetype)):
        raise ValueError

    path, ext = os.path.splitext(store.real_path)
    export_path = os.path.join('POOTLE_EXPORT',
                               path + os.path.extsep + filetype)
    abs_export_path = absolute_real_path(export_path)

    key = iri_to_uri("%s:export_as_%s" % (store.pootle_path, filetype))
    last_export = cache.get(key)
    if (not (last_export and last_export == store.get_mtime() and
        os.path.isfile(abs_export_path))):
        from pootle_app.project_tree import ensure_target_dir_exists
        from pootle_misc import ptempfile as tempfile
        import shutil
        ensure_target_dir_exists(abs_export_path)
        outputstore = store.convert(klass)
        fd, tempstore = tempfile.mkstemp(prefix=store.name,
                                         suffix=os.path.extsep + filetype)
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

    langs = profile.alt_src_langs.exclude(
            id__in=(language.id, source_language.id)
        ).filter(translationproject__project=project)

    if not profile.alt_src_langs.count():
        from pootle_language.models import Language
        accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')

        for accept_lang, unused in parse_accept_lang_header(accept):
            if accept_lang == '*':
                continue

            simplified = data.simplify_to_common(accept_lang)
            normalized = to_locale(data.normalize_code(simplified))
            code = to_locale(accept_lang)
            if (normalized in
                    ('en', 'en_US', source_language.code, language.code) or
                code in ('en', 'en_US', source_language.code, language.code)):
                continue

            langs = Language.objects.filter(
                code__in=(normalized, code),
                translationproject__project=project,
            )
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
            translator_subresult = translator_subresult.filter(
                translator_comment__icontains=word,
            )
            developer_subresult = developer_subresult.filter(
                developer_comment__icontains=word,
            )
        result = result | translator_subresult | developer_subresult

    if 'locations' in form.cleaned_data['sfields']:
        subresult = units_queryset
        for word in words:
            subresult = subresult.filter(locations__icontains=word)
        result = result | subresult

    return result

def get_non_indexed_search_exact_query(form, units_queryset):
    phrase = form.cleaned_data['search']
    result = units_queryset.none()

    if 'source' in form.cleaned_data['sfields']:
        subresult = units_queryset.filter(source_f__contains=phrase)
        result = result | subresult

    if 'target' in form.cleaned_data['sfields']:
        subresult = units_queryset.filter(target_f__contains=phrase)
        result = result | subresult

    if 'notes' in form.cleaned_data['sfields']:
        translator_subresult = units_queryset
        developer_subresult = units_queryset
        translator_subresult = translator_subresult.filter(
            translator_comment__contains=phrase,
        )
        developer_subresult = developer_subresult.filter(
            developer_comment__contains=phrase,
        )
        result = result | translator_subresult | developer_subresult

    if 'locations' in form.cleaned_data['sfields']:
        subresult = units_queryset.filter(locations__contains=phrase)
        result = result | subresult

    return result

def get_search_step_query(request, form, units_queryset):
    """Narrows down units query to units matching search string."""

    if 'exact' in form.cleaned_data['soptions']:
        logging.debug(u"Using exact database search")
        return get_non_indexed_search_exact_query(form, units_queryset)

    path = request.GET.get('path', None)
    if path is not None:
        lang, proj, dir_path, filename = split_pootle_path(path)

        translation_projects = []
        # /<language_code>/<project_code>/
        if lang is not None and proj is not None:
            project = get_object_or_404(Project, code=proj)
            language = get_object_or_404(Language, code=lang)
            translation_projects = \
                    TranslationProject.objects.filter(project=project,
                                                      language=language)
        # /projects/<project_code>/
        elif lang is None and proj is not None:
            project = get_object_or_404(Project, code=proj)
            translation_projects = \
                    TranslationProject.objects.filter(project=project)
        # /<language_code>/
        elif lang is not None and proj is None:
            language = get_object_or_404(Language, code=lang)
            translation_projects = \
                    TranslationProject.objects.filter(language=language)
        # /
        elif lang is None and proj is None:
            translation_projects = TranslationProject.objects.all()

        has_indexer = True
        for translation_project in translation_projects:
            if translation_project.indexer is None:
                has_indexer = False

        if not has_indexer:
            logging.debug(u"No indexer for one or more translation project,"
                          u" using database search")
            return get_non_indexed_search_step_query(form, units_queryset)
        else:
            alldbids = []
            for translation_project in translation_projects:
                logging.debug(u"Found %s indexer for %s, using indexed search",
                              translation_project.indexer.INDEX_DIRECTORY_NAME,
                              translation_project)

                word_querylist = []
                words = form.cleaned_data['search']
                fields = form.cleaned_data['sfields']
                paths = units_queryset.order_by() \
                                      .values_list('store__pootle_path',
                                                   flat=True) \
                                      .distinct()
                path_querylist = [('pofilename', pootle_path)
                                  for pootle_path in paths.iterator()]
                cache_key = "search:%s" % str(hash((repr(path_querylist),
                                                    translation_project.get_mtime(),
                                                    repr(words),
                                                    repr(fields))))

                dbids = cache.get(cache_key)
                if dbids is None:
                    searchparts = []
                    word_querylist = [(field, words) for field in fields]
                    textquery = \
                            translation_project.indexer.make_query(word_querylist,
                                                                   False)
                    searchparts.append(textquery)

                    pathquery = \
                            translation_project.indexer.make_query(path_querylist,
                                                                   False)
                    searchparts.append(pathquery)
                    limitedquery = \
                            translation_project.indexer.make_query(searchparts,
                                                                   True)

                    result = translation_project.indexer.search(limitedquery,
                                                                ['dbid'])
                    dbids = [int(item['dbid'][0]) for item in result[:999]]
                    cache.set(cache_key, dbids, settings.OBJECT_CACHE_TIMEOUT)

                alldbids.extend(dbids)

            return units_queryset.filter(id__in=alldbids)


def get_step_query(request, units_queryset):
    """Narrows down unit query to units matching conditions in GET."""
    if 'filter' in request.GET:
        unit_filter = request.GET['filter']
        username = request.GET.get('user', None)

        profile = request.profile
        if username is not None:
            try:
                user = User.objects.get(username=username)
                profile = user.get_profile()
            except User.DoesNotExist:
                pass

        if unit_filter:
            match_queryset = units_queryset.none()

            if unit_filter == 'all':
                match_queryset = units_queryset
            elif unit_filter == 'translated':
                match_queryset = units_queryset.filter(state=TRANSLATED)
            elif unit_filter == 'untranslated':
                match_queryset = units_queryset.filter(state=UNTRANSLATED)
            elif unit_filter == 'fuzzy':
                match_queryset = units_queryset.filter(state=FUZZY)
            elif unit_filter == 'incomplete':
                match_queryset = units_queryset.filter(
                    Q(state=UNTRANSLATED) | Q(state=FUZZY),
                )
            elif unit_filter == 'suggestions':
                #FIXME: is None the most efficient query
                match_queryset = units_queryset.exclude(suggestion=None)
            elif unit_filter in ('my-suggestions', 'user-suggestions'):
                match_queryset = units_queryset.filter(
                        suggestion__user=profile,
                    ).distinct()
            elif unit_filter == 'user-suggestions-accepted':
                # FIXME: Oh, this is pretty lame, we need a completely
                # different way to model suggestions
                unit_ids = SuggestionStat.objects.filter(
                        suggester=profile,
                        state='accepted',
                    ).values_list('unit', flat=True)
                match_queryset = units_queryset.filter(
                        id__in=unit_ids,
                    ).distinct()
            elif unit_filter == 'user-suggestions-rejected':
                # FIXME: Oh, this is as lame as above
                unit_ids = SuggestionStat.objects.filter(
                        suggester=profile,
                        state='rejected',
                    ).values_list('unit', flat=True)
                match_queryset = units_queryset.filter(
                        id__in=unit_ids,
                    ).distinct()
            elif unit_filter in ('my-submissions', 'user-submissions'):
                match_queryset = units_queryset.filter(
                        submission__submitter=profile,
                    ).distinct()
            elif (unit_filter in ('my-submissions-overwritten',
                                  'user-submissions-overwritten')):
                match_queryset = units_queryset.filter(
                        submission__submitter=profile,
                    ).exclude(submitted_by=profile).distinct()
            elif unit_filter == 'checks' and 'checks' in request.GET:
                checks = request.GET['checks'].split(',')

                if checks:
                    match_queryset = units_queryset.filter(
                        qualitycheck__false_positive=False,
                        qualitycheck__name__in=checks
                    ).distinct()


            units_queryset = match_queryset

    if 'goal' in request.GET:
        try:
            goal = Goal.objects.get(slug=request.GET['goal'])
        except Goal.DoesNotExist:
            pass
        else:
            pootle_path = (request.GET.get('path', '') or
                           request.path.replace("/export-view/", "/", 1))
            goal_stores = goal.get_stores_for_path(pootle_path)
            units_queryset = units_queryset.filter(store__in=goal_stores)

    if 'search' in request.GET and 'sfields' in request.GET:
        # Accept `sfields` to be a comma-separated string of fields (#46)
        GET = request.GET.copy()
        sfields = GET['sfields']
        if isinstance(sfields, unicode) and u',' in sfields:
            GET.setlist('sfields', sfields.split(u','))

        # use the search form for validation only
        search_form = make_search_form(GET)

        if search_form.is_valid():
            units_queryset = get_search_step_query(request, search_form,
                                                   units_queryset)

    return units_queryset


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


def _prepare_unit(unit):
    """Constructs a dictionary with relevant `unit` data."""
    return {
        'id': unit.id,
        'url': unit.get_translate_url(),
        'isfuzzy': unit.isfuzzy(),
        'source': [source[1] for source in pluralize_source(unit)],
        'target': [target[1] for target in pluralize_target(unit)],
    }


def _path_units_with_meta(path, units):
    """Constructs a dictionary which contains a list of `units`
    corresponding to `path` as well as its metadata.
    """
    meta = None
    units_list = []

    for unit in iter(units):
        if meta is None:
            # XXX: Watch out for the query count
            store = unit.store
            tp = store.translation_project
            project = tp.project
            meta = {
                'source_lang': project.source_language.code,
                'source_dir': project.source_language.direction,
                'target_lang': tp.language.code,
                'target_dir': tp.language.direction,
                'project_code': project.code,
                'project_style': project.checkstyle,
            }

        units_list.append(_prepare_unit(unit))

    return {
        path: {
            'meta': meta,
            'units': units_list,
        },
    }


def _build_units_list(units, reverse=False):
    """Given a list/queryset of units, builds a list with the unit data
    contained in a dictionary ready to be returned as JSON.

    :return: A list with unit id, source, and target texts. In case of
             having plural forms, a title for the plural form is also provided.
    """
    return_units = []

    for unit in iter(units):
        return_units.append(_prepare_unit(unit))

    return return_units


@ajax_required
def get_units(request):
    """Gets source and target texts and its metadata.

    :return: A JSON-encoded string containing the source and target texts
        grouped by the store they belong to.

        The optional `count` GET parameter defines the chunk size to
        consider. The user's preference will be used by default.

        When the `initial` GET parameter is present, a sorted list of
        the result set ids will be returned too.
    """
    pootle_path = request.GET.get('path', None)
    if pootle_path is None:
        raise Http400(_('Arguments missing.'))

    request.profile = get_profile(request.user)
    limit = request.profile.get_unit_rows()

    units_qs = Unit.objects.get_for_path(pootle_path, request.profile)
    step_queryset = get_step_query(request, units_qs)

    is_initial_request = request.GET.get('initial', False)
    chunk_size = request.GET.get('count', limit)
    uids_param = filter(None, request.GET.get('uids', '').split(u','))
    uids = filter(None, map(to_int, uids_param))

    units = None
    unit_groups = []
    uid_list = []

    if is_initial_request:
        uid_list = list(step_queryset.values_list('id', flat=True))

        if len(uids) == 1:
            try:
                uid = uids[0]
                index = uid_list.index(uid)
                begin = max(index - chunk_size, 0)
                end = min(index + chunk_size + 1, len(uid_list))
                uids = uid_list[begin:end]
            except ValueError:
                raise Http404  # `uid` not found in `uid_list`
        else:
            count = 2 * chunk_size
            units = step_queryset[:count]

    if units is None and uids:
        units = step_queryset.filter(id__in=uids)

    units_by_path = groupby(units, lambda x: x.store.pootle_path)
    for pootle_path, units in units_by_path:
        unit_groups.append(_path_units_with_meta(pootle_path, units))

    response = {
        'unitGroups': unit_groups,
    }
    if uid_list:
        response['uIds'] = uid_list

    return HttpResponse(jsonify(response), mimetype="application/json")


def _is_filtered(request):
    """Checks if unit list is filtered."""
    return ('filter' in request.GET or 'checks' in request.GET or
            'user' in request.GET or
            ('search' in request.GET and 'sfields' in request.GET))


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
        SubmissionFields.COMMENT, SubmissionFields.NONE
    ])
    timeline = timeline.select_related("submitter__user",
                                       "translation_project__language")

    entries_group = []
    context = {
        'system': User.objects.get_system_user().get_profile()
    }

    if unit.creation_time:
        context['created'] = {
            'datetime': unit.creation_time,
        }

    for key, values in groupby(timeline, key=lambda x: x.creation_time):
        entry_group = {
            'datetime': key,
            'entries': [],
        }

        for item in values:
            # Only add submitter information for the whole entry group once
            entry_group.setdefault('submitter', item.submitter)

            context.setdefault('language', item.translation_project.language)

            entry = {
                'field': item.field,
                'field_name': SubmissionFields.NAMES_MAP[item.field],
            }

            if item.field == SubmissionFields.STATE:
                entry['old_value'] = STATES_MAP[int(to_python(item.old_value))]
                entry['new_value'] = STATES_MAP[int(to_python(item.new_value))]
            elif item.check:
                entry.update({
                    'check_name': item.check.name,
                    'check_display_name': check_names[item.check.name],
                    'checks_url': reverse('pootle-staticpages-display',
                                          args=['help/quality-checks']),
                    'action': {
                                SubmissionTypes.MUTE_CHECK: 'Muted',
                                SubmissionTypes.UNMUTE_CHECK: 'Unmuted'
                              }.get(item.type, '')
                })
            else:
                entry['new_value'] = to_python(item.new_value)

            entry_group['entries'].append(entry)

        entries_group.append(entry_group)

    # Let's reverse the chronological order
    entries_group.reverse()

    # May be better to show all translations?
    # Remove first timeline item if it's solely a change to the target
    #if (entries_group and len(entries_group[0]['entries']) == 1 and
    #    entries_group[0]['entries'][0]['field'] == SubmissionFields.TARGET):
    #    del entries_group[0]

    context['entries_group'] = entries_group

    if request.is_ajax():
        # The client will want to confirm that the response is relevant for
        # the unit on screen at the time of receiving this, so we add the uid.
        json = {'uid': unit.id}

        t = loader.get_template('editor/units/xhr_timeline.html')
        c = RequestContext(request, context)
        json['timeline'] = t.render(c).replace('\n', '')

        response = jsonify(json)
        return HttpResponse(response, mimetype="application/json")
    else:
        return render(request, "editor/units/timeline.html", context)


@ajax_required
@get_path_obj
@permission_required('view')
@get_resource
def get_qualitycheck_stats(request, path_obj, **kwargs):
    failing_checks = request.resource_obj.get_checks()['checks']
    response = jsonify(failing_checks)
    return HttpResponse(response, mimetype="application/json")


@ajax_required
@get_path_obj
@permission_required('view')
@get_resource
def get_overview_stats(request, path_obj, **kwargs):
    stats = request.resource_obj.get_stats()
    response = jsonify(stats)
    return HttpResponse(response, mimetype="application/json")


@require_POST
@ajax_required
@get_unit_context('translate')
def comment(request, unit):
    """Stores a new comment for the given ``unit``.

    :return: If the form validates, the cleaned comment is returned.
             An error message is returned otherwise.
    """
    # Update current unit instance's attributes
    unit.commented_by = request.profile
    unit.commented_on = timezone.now()

    language = request.translation_project.language
    form = unit_comment_form_factory(language)(request.POST, instance=unit,
                                               request=request)

    if form.is_valid():
        form.save()

        context = {
            'unit': unit,
            'language': language,
        }
        t = loader.get_template('editor/units/xhr_comment.html')
        c = RequestContext(request, context)

        json = {'comment': t.render(c)}
        rcode = 200
    else:
        json = {'msg': _("Comment submission failed.")}
        rcode = 400

    response = jsonify(json)

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
    form = form_class(instance=unit, request=request)
    comment_form_class = unit_comment_form_factory(language)
    comment_form = comment_form_class({}, instance=unit)

    store = unit.store
    directory = store.parent
    profile = request.profile
    alt_src_langs = get_alt_src_langs(request, profile, translation_project)
    project = translation_project.project

    suggestions = get_sugg_list(unit)
    template_vars = {
        'unit': unit,
        'form': form,
        'comment_form': comment_form,
        'store': store,
        'directory': directory,
        'profile': profile,
        'user': request.user,
        'project': project,
        'language': language,
        'source_language': translation_project.project.source_language,
        'cantranslate': check_profile_permission(profile, "translate",
                                                 directory),
        'cansuggest': check_profile_permission(profile, "suggest", directory),
        'canreview': check_profile_permission(profile, "review", directory),
        'is_admin': check_profile_permission(profile, 'administrate',
                                             directory),
        'altsrcs': find_altsrcs(unit, alt_src_langs, store=store,
                                project=project),
        'suggestions': suggestions,
    }

    if translation_project.project.is_terminology or store.is_terminology:
        t = loader.get_template('editor/units/term_edit.html')
    else:
        t = loader.get_template('editor/units/edit.html')
    c = RequestContext(request, template_vars)
    json['editor'] = t.render(c)

    rcode = 200

    # Return context rows if filtering is applied but
    # don't return any if the user has asked not to have it.
    current_filter = request.GET.get('filter', 'all')
    show_ctx = request.COOKIES.get('ctxShow', 'true')

    if ((_is_filtered(request) or current_filter not in ('all',)) and
        show_ctx == 'true'):
        # TODO: review if this first 'if' branch makes sense.
        if translation_project.project.is_terminology or store.is_terminology:
            json['ctx'] = _filter_ctx_units(store.units, unit, 0)
        else:
            ctx_qty = int(request.COOKIES.get('ctxQty', 1))
            json['ctx'] = _filter_ctx_units(store.units, unit, ctx_qty)

    response = jsonify(json)
    return HttpResponse(response, status=rcode, mimetype="application/json")


def _get_project_icon(project):
    path = "/".join(["", project.code, ".pootle", "icon.png"])
    if os.path.isfile(settings.PODIRECTORY + path):
        # XXX: we are abusing the export URL, need a better way to serve
        # static files
        return "/export" + path
    else:
        return ""

@ajax_required
@get_unit_context('view')
def get_tm_results(request, unit):
    """Gets a list of TM results for the current object.

    :return: JSON string with a list of TM results.
    """

    max_len = settings.LV_MAX_LENGTH
    min_similarity = settings.LV_MIN_SIMILARITY

    results = []

    # Shortcut Levenshtein comparer, since the distance, by definition, can't
    # be less than the difference in string length
    diff_len = unit.source_length * (100 - min_similarity)/100
    max_unit_len = unit.source_length + diff_len
    min_unit_len = unit.source_length - diff_len

    criteria = {
        'target_lang': unit.store.translation_project.language,
        'source_lang': unit.store.translation_project.project.source_language,
        'source_length__range': (min_unit_len, max_unit_len),
    }
    tmunits = TMUnit.objects.filter(**criteria).exclude(unit=unit)

    comparer = LevenshteinComparer(max_len)
    for tmunit in tmunits:
        quality = comparer.similarity(tmunit.source, unit.source,
                                      min_similarity)
        if quality >= min_similarity:
            project = tmunit.project
            profile = tmunit.submitted_by
            result = {
                'source': tmunit.source,
                'target': tmunit.target,
                'quality': quality,
                'project': {
                    'project': project.code,
                    'projectname': project.fullname,
                    'absolute_url': project.get_absolute_url(),
                    'icon': _get_project_icon(project),
                }
            }

            if profile is not None:
                submissions = Submission.objects.filter(
                                submitter=profile,
                                type=SubmissionTypes.NORMAL,
                                ).distinct().count()
                suggestions = SuggestionStat.objects.filter(
                                suggester=profile,
                                ).distinct().count()
                translations = submissions - suggestions  # XXX: is this correct?
                title = _("By %s on %s<br/><br/>%s translations<br/>%s suggestions" % (
                            profile.user.get_full_name(),
                            tmunit.submitted_on,
                            translations, suggestions))

                result['translator'] = {
                    'username': unicode(profile.user),
                    'title': title,
                    'absolute_url': profile.get_absolute_url(),
                    'gravatar': profile.gravatar_url(24),
                }

            results.append(result)

    return HttpResponse(jsonify(results), mimetype="application/json")


@require_POST
@ajax_required
@get_unit_context('translate')
def submit(request, unit):
    """Processes translation submissions and stores them in the database.

    :return: An object in JSON notation that contains the previous and last
             units for the unit next to unit ``uid``.
    """
    json = {}

    translation_project = request.translation_project
    language = translation_project.language

    if unit.hasplural():
        snplurals = len(unit.source.strings)
    else:
        snplurals = None

    # Store current time so that it is the same for all submissions
    current_time = timezone.now()

    # Update current unit instance's attributes
    unit.submitted_by = request.profile
    unit.submitted_on = current_time

    form_class = unit_form_factory(language, snplurals, request)
    form = form_class(request.POST, instance=unit, request=request)

    if form.is_valid():
        if form.updated_fields:
            for field, old_value, new_value in form.updated_fields:
                sub = Submission(
                        creation_time=current_time,
                        translation_project=translation_project,
                        submitter=request.profile,
                        unit=unit,
                        field=field,
                        type=SubmissionTypes.NORMAL,
                        old_value=old_value,
                        new_value=new_value,
                )
                sub.save()
            form.instance._log_user = request.profile
            form.save()
            translation_submitted.send(
                    sender=translation_project,
                    unit=form.instance,
                    profile=request.profile,
            )

            has_critical_checks = unit.qualitycheck_set.filter(
                category=Category.CRITICAL
            ).exists()

            if has_critical_checks:
                can_review = check_profile_permission(request.profile,
                                                      'review',
                                                      unit.store.parent)
                ctx = {
                    'canreview': can_review,
                    'unit': unit
                }
                template = loader.get_template('editor/units/xhr_checks.html')
                context = RequestContext(request, ctx)
                json['checks'] = template.render(context)

        rcode = 200
    else:
        # Form failed
        #FIXME: we should display validation errors here
        rcode = 400
        json["msg"] = _("Failed to process submission.")

    response = jsonify(json)
    return HttpResponse(response, status=rcode, mimetype="application/json")


@require_POST
@ajax_required
@get_unit_context('suggest')
def suggest(request, unit):
    """Processes translation suggestions and stores them in the database.

    :return: An object in JSON notation that contains the previous and last
             units for the unit next to unit ``uid``.
    """
    json = {}

    translation_project = request.translation_project
    language = translation_project.language

    if unit.hasplural():
        snplurals = len(unit.source.strings)
    else:
        snplurals = None

    form_class = unit_form_factory(language, snplurals, request)
    form = form_class(request.POST, instance=unit, request=request)

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
@get_unit_context('review')
def reject_suggestion(request, unit, suggid):
    if request.POST.get('reject'):
        try:
            sugg = unit.suggestion_set.get(id=suggid)
        except ObjectDoesNotExist:
            raise Http404

        unit.reject_suggestion(sugg, request.translation_project,
                               request.profile)

    json = {
        'udbid': unit.id,
        'sugid': suggid,
    }
    response = jsonify(json)
    return HttpResponse(response, mimetype="application/json")


@ajax_required
@get_unit_context('review')
def accept_suggestion(request, unit, suggid):
    json = {
        'udbid': unit.id,
        'sugid': suggid,
    }
    if request.POST.get('accept'):
        try:
            suggestion = unit.suggestion_set.get(id=suggid)
        except ObjectDoesNotExist:
            raise Http404

        unit.accept_suggestion(suggestion, request.translation_project,
                               request.profile)

        json['newtargets'] = [highlight_whitespace(target)
                              for target in unit.target.strings]
        json['newdiffs'] = {}
        for sugg in unit.get_suggestions():
            json['newdiffs'][sugg.id] = \
                    [highlight_diffs(unit.target.strings[i], target)
                     for i, target in enumerate(sugg.target.strings)]

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
                # No i18n, will not go to UI
                raise PermissionDenied("Users can only remove their own votes")
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
            # Why can't it just return the vote object?
            Vote.objects.record_vote(suggestion, request.user, +1)
            json["voteid"] = Vote.objects.get_for_user(suggestion,
                                                       request.user).id
        except ObjectDoesNotExist:
            raise Http404(_("The suggestion or vote is not valid any more."))
    response = jsonify(json)
    return HttpResponse(response, mimetype="application/json")


@ajax_required
@get_unit_context('review')
def toggle_qualitycheck(request, unit, check_id):
    json = {}
    json["udbid"] = unit.id
    json["checkid"] = check_id

    try:
        unit.toggle_qualitycheck(check_id,
            bool(request.POST.get('mute')), request.profile)
    except ObjectDoesNotExist:
        raise Http404

    response = jsonify(json)
    return HttpResponse(response, mimetype="application/json")


@require_POST
@ajax_required
def ajax_remove_tag_from_store(request, tag_slug, store_pk):
    if not check_permission('administrate', request):
        raise PermissionDenied(_("You do not have rights to remove tags."))

    store = get_object_or_404(Store, pk=store_pk)

    if tag_slug.startswith("goal-"):
        goal = get_object_or_404(Goal, slug=tag_slug)
        store.goals.remove(goal)
    else:
        tag = get_object_or_404(Tag, slug=tag_slug)
        store.tags.remove(tag)

    return HttpResponse(status=201)


def _add_tag(request, store, tag_like_object):
    if isinstance(tag_like_object, Tag):
        store.tags.add(tag_like_object)
    else:
        store.goals.add(tag_like_object)
    context = {
        'store_tags': store.tag_like_objects,
        'path_obj': store,
        'can_edit': check_permission('administrate', request),
    }
    response = render(request, "stores/xhr_tags_list.html", context)
    response.status_code = 201
    return response


@require_POST
@ajax_required
def ajax_add_tag_to_store(request, store_pk):
    """Return an HTML snippet with the failed form or blank if valid."""

    if not check_permission('administrate', request):
        raise PermissionDenied(_("You do not have rights to add tags."))

    store = get_object_or_404(Store, pk=store_pk)

    add_tag_form = TagForm(request.POST)

    if add_tag_form.is_valid():
        new_tag_like_object = add_tag_form.save()
        return _add_tag(request, store, new_tag_like_object)
    else:
        # If the form is invalid, perhaps it is because the tag already exists,
        # so check if the tag exists.
        try:
            criteria = {
                'name': add_tag_form.data['name'],
                'slug': add_tag_form.data['slug'],
            }
            if len(store.tags.filter(**criteria)) == 1:
                # If the tag is already applied to the store then avoid
                # reloading the page.
                return HttpResponse(status=204)
            elif len(store.goals.filter(**criteria)) == 1:
                # If the goal is already applied to the store then avoid
                # reloading the page.
                return HttpResponse(status=204)
            else:
                # Else add the tag (or goal) to the store.
                if criteria['name'].startswith("goal:"):
                    tag_like_object = Goal.objects.get(**criteria)
                else:
                    tag_like_object = Tag.objects.get(**criteria)
                return _add_tag(request, store, tag_like_object)
        except Exception:
            # If the form is invalid and the tag doesn't exist yet then display
            # the form with the error messages.
            context = {
                'add_tag_form': add_tag_form,
                'add_tag_action_url': reverse('pootle-xhr-tag-store',
                                              args=[store.pk])
            }
            return render(request, "core/xhr_add_tag_form.html", context)
