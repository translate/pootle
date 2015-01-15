#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010-2013 Zuza Software Foundation
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

import logging
import os
from itertools import groupby

from translate.filters.decorators import Category
from translate.lang import data
from translate.search.lshtein import LevenshteinComparer

from django.conf import settings
from django.contrib.auth import get_user_model
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

from pootle.core.decorators import (get_path_obj, get_resource,
                                    permission_required)
from pootle.core.exceptions import Http400
from pootle.core.url_helpers import split_pootle_path
from pootle_app.models.permissions import (check_permission,
                                           check_user_permission)
from pootle_language.models import Language
from pootle_misc.checks import check_names
from pootle_misc.forms import make_search_form
from pootle_misc.util import ajax_required, jsonify, to_int
from pootle_project.models import Project
from pootle_statistics.models import (Submission, SubmissionFields,
                                      SubmissionTypes)
from pootle_translationproject.models import TranslationProject

from .decorators import get_store_context, get_unit_context
from .fields import to_python
from .forms import (unit_comment_form_factory, unit_form_factory,
                    highlight_whitespace)
from .models import Store, Suggestion, SuggestionStates, Unit
from .signals import translation_submitted
from .templatetags.store_tags import (highlight_diffs, pluralize_source,
                                      pluralize_target)
from .util import (UNTRANSLATED, FUZZY, TRANSLATED, STATES_MAP,
                   absolute_real_path, find_altsrcs, get_sugg_list)


User = get_user_model()


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

    return redirect(reverse('pootle-export', args=[export_path]))


@get_store_context('view')
def download(request, store):
    store.sync(update_translation=True)

    return redirect(reverse('pootle-export', args=[store.real_path]))


####################### Translate Page ##############################

def get_alt_src_langs(request, user, translation_project):
    if not user.is_authenticated():
        return Language.objects.none()

    language = translation_project.language
    project = translation_project.project
    source_language = project.source_language

    langs = user.alt_src_langs.exclude(
            id__in=(language.id, source_language.id)
        ).filter(translationproject__project=project)

    if not user.alt_src_langs.count():
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

        user = request.user
        if request.GET.get("user"):
            try:
                user = User.objects.get(username=request.GET["user"])
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
                match_queryset = units_queryset.filter(
                        suggestion__state=SuggestionStates.PENDING
                    ).distinct()
            elif unit_filter in ('my-suggestions', 'user-suggestions'):
                match_queryset = units_queryset.filter(
                        suggestion__state=SuggestionStates.PENDING,
                        suggestion__user=user,
                    ).distinct()
            elif unit_filter == 'user-suggestions-accepted':
                match_queryset = units_queryset.filter(
                        suggestion__state=SuggestionStates.ACCEPTED,
                        suggestion__user=user,
                    ).distinct()
            elif unit_filter == 'user-suggestions-rejected':
                match_queryset = units_queryset.filter(
                        suggestion__state=SuggestionStates.REJECTED,
                        suggestion__user=user,
                    ).distinct()
            elif unit_filter in ('my-submissions', 'user-submissions'):
                match_queryset = units_queryset.filter(
                        submission__submitter=user,
                        submission__type=SubmissionTypes.NORMAL,
                    ).distinct()
            elif (unit_filter in ('my-submissions-overwritten',
                                  'user-submissions-overwritten')):
                match_queryset = units_queryset.filter(
                        submission__submitter=user,
                    ).exclude(submitted_by=user).distinct()
            elif unit_filter == 'checks' and 'checks' in request.GET:
                checks = request.GET['checks'].split(',')

                if checks:
                    match_queryset = units_queryset.filter(
                        qualitycheck__false_positive=False,
                        qualitycheck__name__in=checks,
                    ).distinct()


            units_queryset = match_queryset

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

    units_qs = Unit.objects.get_for_path(pootle_path, request.user)
    step_queryset = get_step_query(request, units_qs)

    user = request.user
    if not user.is_authenticated():
        user = User.objects.get_nobody_user()

    is_initial_request = request.GET.get('initial', False)
    chunk_size = request.GET.get("count", user.unit_rows)
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

    return HttpResponse(jsonify(response), content_type="application/json")


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
    return HttpResponse(response, status=rcode, content_type="application/json")


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
        "system": User.objects.get_system_user()
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
            elif item.quality_check:
                check_name = item.quality_check.name
                entry.update({
                    'check_name': check_name,
                    'check_display_name': check_names[check_name],
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

    context['entries_group'] = entries_group

    if request.is_ajax():
        # The client will want to confirm that the response is relevant for
        # the unit on screen at the time of receiving this, so we add the uid.
        json = {'uid': unit.id}

        t = loader.get_template('editor/units/xhr_timeline.html')
        c = RequestContext(request, context)
        json['timeline'] = t.render(c).replace('\n', '')

        response = jsonify(json)
        return HttpResponse(response, content_type="application/json")
    else:
        return render(request, "editor/units/timeline.html", context)


@require_POST
@ajax_required
@get_unit_context('translate')
def comment(request, unit):
    """Stores a new comment for the given ``unit``.

    :return: If the form validates, the cleaned comment is returned.
             An error message is returned otherwise.
    """
    # Update current unit instance's attributes
    unit.commented_by = request.user
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

    return HttpResponse(response, status=rcode, content_type="application/json")


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
    user = request.user
    alt_src_langs = get_alt_src_langs(request, user, translation_project)
    project = translation_project.project

    suggestions = get_sugg_list(unit)
    template_vars = {
        'unit': unit,
        'form': form,
        'comment_form': comment_form,
        'store': store,
        'directory': directory,
        'project': project,
        'language': language,
        'source_language': translation_project.project.source_language,
        'cantranslate': check_user_permission(user, "translate", directory),
        'cansuggest': check_user_permission(user, "suggest", directory),
        'canreview': check_user_permission(user, "review", directory),
        'is_admin': check_user_permission(user, 'administrate', directory),
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
    return HttpResponse(response, status=rcode, content_type="application/json")


def _get_project_icon(project):
    path = "/".join(["", project.code, ".pootle", "icon.png"])
    if os.path.isfile(settings.PODIRECTORY + path):
        # XXX: we are abusing the export URL, need a better way to serve
        # static files
        return "/export" + path
    else:
        return ""


@ajax_required
@get_path_obj
@permission_required('view')
@get_resource
def get_qualitycheck_stats(request, *args, **kwargs):
    failing_checks = request.resource_obj.get_checks()['checks']
    response = jsonify(failing_checks)
    return HttpResponse(response, content_type="application/json")


@ajax_required
@get_path_obj
@permission_required('view')
@get_resource
def get_overview_stats(request, *args, **kwargs):
    stats = request.resource_obj.get_stats()
    response = jsonify(stats)
    return HttpResponse(response, content_type="application/json")


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
    user = request.user

    if unit.hasplural():
        snplurals = len(unit.source.strings)
    else:
        snplurals = None

    # Store current time so that it is the same for all submissions
    current_time = timezone.now()

    # Update current unit instance's attributes
    unit.submitted_by = request.user
    unit.submitted_on = current_time

    form_class = unit_form_factory(language, snplurals, request)
    form = form_class(request.POST, instance=unit, request=request)

    if form.is_valid():
        if form.updated_fields:
            for field, old_value, new_value in form.updated_fields:
                sub = Submission(
                        creation_time=current_time,
                        translation_project=translation_project,
                        submitter=request.user,
                        unit=unit,
                        field=field,
                        type=SubmissionTypes.NORMAL,
                        old_value=old_value,
                        new_value=new_value,
                )
                sub.save()

            form.instance._log_user = request.user

            form.save()
            translation_submitted.send(
                    sender=translation_project,
                    unit=form.instance,
                    user=request.user,
            )

            has_critical_checks = unit.qualitycheck_set.filter(
                category=Category.CRITICAL
            ).exists()

            if has_critical_checks:
                can_review = check_user_permission(user, 'review',
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
    return HttpResponse(response, status=rcode, content_type="application/json")


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
            unit.add_suggestion(form.cleaned_data['target_f'],
                                user=request.user)

        rcode = 200
    else:
        # Form failed
        #FIXME: we should display validation errors here
        rcode = 400
        json["msg"] = _("Failed to process suggestion.")

    response = jsonify(json)
    return HttpResponse(response, status=rcode, content_type="application/json")


@ajax_required
@get_unit_context('review')
def reject_suggestion(request, unit, suggid):
    if request.POST.get('reject'):
        try:
            sugg = unit.suggestion_set.get(id=suggid)
        except ObjectDoesNotExist:
            raise Http404

        unit.reject_suggestion(sugg, request.translation_project,
                               request.user)

    json = {
        'udbid': unit.id,
        'sugid': suggid,
    }
    response = jsonify(json)
    return HttpResponse(response, content_type="application/json")


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
                               request.user)

        json['newtargets'] = [highlight_whitespace(target)
                              for target in unit.target.strings]
        json['newdiffs'] = {}
        for sugg in unit.get_suggestions():
            json['newdiffs'][sugg.id] = \
                    [highlight_diffs(unit.target.strings[i], target)
                     for i, target in enumerate(sugg.target.strings)]

    response = jsonify(json)
    return HttpResponse(response, content_type="application/json")


@ajax_required
@get_unit_context('review')
def toggle_qualitycheck(request, unit, check_id):
    json = {}
    json["udbid"] = unit.id
    json["checkid"] = check_id

    try:
        unit.toggle_qualitycheck(check_id,
            bool(request.POST.get('mute')), request.user)
    except ObjectDoesNotExist:
        raise Http404

    response = jsonify(json)
    return HttpResponse(response, content_type="application/json")
