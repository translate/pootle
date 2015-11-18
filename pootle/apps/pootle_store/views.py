#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from itertools import groupby

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.core.urlresolvers import reverse
from django.db.models import Max, Q
from django.http import Http404
from django.shortcuts import redirect
from django.template import loader, RequestContext
from django.utils.safestring import mark_safe
from django.utils.translation import to_locale, ugettext as _
from django.utils.translation.trans_real import parse_accept_lang_header
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods

from translate.lang import data

from pootle.core.dateparse import parse_datetime
from pootle.core.decorators import (get_path_obj, get_resource,
                                    permission_required)
from pootle.core.exceptions import Http400
from pootle.core.http import JsonResponse, JsonResponseBadRequest
from pootle_app.models.directory import Directory
from pootle_app.models.permissions import check_permission, check_user_permission
from pootle_misc.checks import get_category_id, check_names
from pootle_misc.forms import make_search_form
from pootle_misc.util import ajax_required, to_int, get_date_interval
from pootle_statistics.models import (Submission, SubmissionFields,
                                      SubmissionTypes)

from .decorators import get_unit_context
from .fields import to_python
from .forms import (unit_comment_form_factory, unit_form_factory,
                    highlight_whitespace)
from .models import Unit, SuggestionStates
from .templatetags.store_tags import (highlight_diffs, pluralize_source,
                                      pluralize_target)
from .util import (UNTRANSLATED, FUZZY, TRANSLATED, STATES_MAP,
                   find_altsrcs)


#: Mapping of allowed sorting criteria.
#: Keys are supported query strings, values are the field + order that
#: will be used against the DB.
ALLOWED_SORTS = {
    'units': {
        'priority': 'priority',
        'oldest': 'submitted_on',
        'newest': '-submitted_on',
    },
    'suggestions': {
        'oldest': 'suggestion__creation_time',
        'newest': '-suggestion__creation_time',
    },
    'submissions': {
        'oldest': 'submission__creation_time',
        'newest': '-submission__creation_time',
    },
}


#: List of fields from `ALLOWED_SORTS` that can be sorted by simply using
#: `order_by(field)`
SIMPLY_SORTED = ['units']


def get_alt_src_langs(request, user, translation_project):
    language = translation_project.language
    project = translation_project.project
    source_language = project.source_language

    langs = user.alt_src_langs.exclude(
            id__in=(language.id, source_language.id)
        ).filter(translationproject__project=project)

    if not user.alt_src_langs.count():
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


def get_search_query(form, units_queryset):
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


def get_search_exact_query(form, units_queryset):
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


def get_search_step_query(form, units_queryset):
    """Narrows down units query to units matching search string."""
    if 'exact' in form.cleaned_data['soptions']:
        return get_search_exact_query(form, units_queryset)

    return get_search_query(form, units_queryset)


def get_step_query(request, units_queryset):
    """Narrows down unit query to units matching conditions in GET."""
    if 'filter' in request.GET:
        unit_filter = request.GET['filter']
        username = request.GET.get('user', None)
        modified_since = request.GET.get('modified-since', None)
        month = request.GET.get('month', None)
        sort_by_param = request.GET.get('sort', None)
        sort_on = 'units'

        user = request.profile
        if username is not None:
            User = get_user_model()
            try:
                user = User.objects.get(username=username)
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
                sort_on = 'suggestions'
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
                        submission__type__in=SubmissionTypes.EDIT_TYPES,
                    ).distinct()
                sort_on = 'submissions'
            elif (unit_filter in ('my-submissions-overwritten',
                                  'user-submissions-overwritten')):
                match_queryset = units_queryset.filter(
                        submission__submitter=user,
                        submission__type__in=SubmissionTypes.EDIT_TYPES,
                    ).exclude(submitted_by=user).distinct()
            elif unit_filter == 'checks':
                if 'checks' in request.GET:
                    checks = request.GET['checks'].split(',')

                    if checks:
                        match_queryset = units_queryset.filter(
                            qualitycheck__false_positive=False,
                            qualitycheck__name__in=checks,
                        ).distinct()
                elif 'category' in request.GET:
                    category_name = request.GET['category']
                    try:
                        category = get_category_id(category_name)
                    except KeyError:
                        raise Http404

                    match_queryset = units_queryset.filter(
                        qualitycheck__false_positive=False,
                        qualitycheck__category=category,
                    ).distinct()

            if modified_since is not None:
                datetime_obj = parse_datetime(modified_since)
                if datetime_obj is not None:
                    match_queryset = match_queryset.filter(
                        submitted_on__gt=datetime_obj,
                    ).distinct()

            if month is not None:
                [start, end] = get_date_interval(month)
                match_queryset = match_queryset.filter(
                    submitted_on__gte=start,
                    submitted_on__lte=end,
                ).distinct()

            sort_by = ALLOWED_SORTS[sort_on].get(sort_by_param, None)
            if sort_by is not None:
                if sort_on in SIMPLY_SORTED:
                    if sort_by == 'priority':
                        # TODO: Replace the following extra() with Coalesce
                        # https://docs.djangoproject.com/en/1.8/ref/models/database-functions/#coalesce
                        # once we drop support for Django<1.8.x:
                        # .annotate(
                        #     sort_by_field=Coalesce(
                        #         Max("vfolders__priority"),
                        #         Value(1)
                        #     )
                        # ).order_by("-sort_by_field")
                        match_queryset = match_queryset.extra(select={'sort_by_field': """
                            SELECT COALESCE(MAX(virtualfolder_virtualfolder.priority), 1)
                            FROM virtualfolder_virtualfolder
                            INNER JOIN virtualfolder_virtualfolder_units
                            ON virtualfolder_virtualfolder.id = virtualfolder_virtualfolder_units.virtualfolder_id
                            WHERE virtualfolder_virtualfolder_units.unit_id = pootle_store_unit.id
                        """}).extra(order_by=['-sort_by_field'])
                    else:
                        match_queryset = match_queryset.order_by(sort_by)
                else:
                    # Omit leading `-` sign
                    if sort_by[0] == '-':
                        max_field = sort_by[1:]
                        sort_order = '-sort_by_field'
                    else:
                        max_field = sort_by
                        sort_order = 'sort_by_field'

                    # It's necessary to use `Max()` here because we can't
                    # use `distinct()` and `order_by()` at the same time
                    # (unless PostreSQL is used and `distinct(field_name)`)
                    match_queryset = match_queryset \
                        .annotate(sort_by_field=Max(max_field)) \
                        .order_by(sort_order)

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
            units_queryset = get_search_step_query(search_form, units_queryset)

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

    # FIXME: can we avoid this query if length is known?
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


def _get_critical_checks_snippet(request, unit):
    """Retrieves the critical checks snippet.

    :param request: an `HttpRequest` object
    :param unit: a `Unit` instance for which critical checks need to be
        rendered.
    :return: rendered HTML snippet with the failing checks, or `None` if
        there are no critical failing checks.
    """
    if not unit.has_critical_checks():
        return None

    can_review = check_user_permission(request.profile, 'review',
                                       unit.store.parent)
    ctx = {
        'canreview': can_review,
        'unit': unit,
    }
    template = loader.get_template('editor/units/xhr_checks.html')
    return template.render(RequestContext(request, ctx))


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

    User = get_user_model()
    request.profile = User.get(request.user)
    limit = request.profile.get_unit_rows()
    vfolder = None

    if 'virtualfolder' in settings.INSTALLED_APPS:
        from virtualfolder.helpers import extract_vfolder_from_path

        vfolder, pootle_path = extract_vfolder_from_path(pootle_path)

    units_qs = Unit.objects.get_for_path(pootle_path, request.profile)

    if vfolder is not None:
        units_qs = units_qs.filter(vfolders=vfolder)

    units_qs = units_qs.select_related(
        'store__translation_project__project',
        'store__translation_project__language',
    )
    step_queryset = get_step_query(request, units_qs)

    is_initial_request = request.GET.get('initial', False)
    chunk_size = request.GET.get('count', limit)
    uids_param = filter(None, request.GET.get('uids', '').split(u','))
    uids = filter(None, map(to_int, uids_param))

    units = []
    unit_groups = []
    uid_list = []

    if is_initial_request:
        sort_by_field = None
        if len(step_queryset.query.order_by) == 1:
            sort_by_field = step_queryset.query.order_by[0]

        sort_on = None
        for key, item in ALLOWED_SORTS.items():
            if sort_by_field in item.values():
                sort_on = key
                break

        if sort_by_field is None or sort_on == 'units':
            # Since `extra()` has been used before, it's necessary to explicitly
            # request the `store__pootle_path` field. This is a subtetly in
            # Django's ORM.
            uid_list = [u['id'] for u in step_queryset.values('id',
                                                              'store__pootle_path')]
        else:
            # Not using `values_list()` here because it doesn't know about all
            # existing relations when `extra()` has been used before in the
            # queryset. This affects annotated names such as those ending in
            # `__max`, where Django thinks we're trying to lookup a field on a
            # relationship field. That's why `sort_by_field` alias for `__max`
            # is used here. This alias must be queried in
            # `values('sort_by_field', 'id')` with `id` otherwise
            # Django looks for `sort_by_field` field in the initial table.
            # https://code.djangoproject.com/ticket/19434
            uid_list = [u['id'] for u in step_queryset.values('id',
                                                              'sort_by_field',
                                                              'store__pootle_path')]

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
            uids = uid_list[:count]

    if not units and uids:
        units = step_queryset.filter(id__in=uids)

    units_by_path = groupby(units, lambda x: x.store.pootle_path)
    for pootle_path, units in units_by_path:
        unit_groups.append(_path_units_with_meta(pootle_path, units))

    response = {
        'unitGroups': unit_groups,
    }
    if uid_list:
        response['uIds'] = uid_list

    return JsonResponse(response)


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
    return JsonResponse(json)


@never_cache
@get_unit_context('view')
def timeline(request, unit):
    """Returns a JSON-encoded string including the changes to the unit
    rendered in HTML.
    """
    timeline = Submission.objects.filter(
        unit=unit,
    ).filter(
        Q(field__in=[
            SubmissionFields.TARGET, SubmissionFields.STATE,
            SubmissionFields.COMMENT, SubmissionFields.NONE
        ]) |
        Q(type__in=SubmissionTypes.SUGGESTION_TYPES)
    ).exclude(
        field=SubmissionFields.COMMENT,
        creation_time=unit.commented_on
    ).order_by("id")
    timeline = timeline.select_related("submitter__user",
                                       "translation_project__language")

    User = get_user_model()
    entries_group = []
    context = {}

    # Group by submitter id and creation_time because
    # different submissions can have same creation time
    for key, values in \
        groupby(timeline,
                key=lambda x: "%d\001%s" % (x.submitter.id, x.creation_time)):

        entry_group = {
            'entries': [],
        }

        for item in values:
            # Only add creation_time information for the whole entry group once
            entry_group['datetime'] = item.creation_time

            # Only add submitter information for the whole entry group once
            entry_group.setdefault('submitter', item.submitter)

            context.setdefault('language', item.translation_project.language)

            entry = {
                'field': item.field,
                'field_name': SubmissionFields.NAMES_MAP.get(item.field, None),
                'type': item.type,
            }

            if item.field == SubmissionFields.STATE:
                entry['old_value'] = STATES_MAP[int(to_python(item.old_value))]
                entry['new_value'] = STATES_MAP[int(to_python(item.new_value))]
            elif item.suggestion:
                entry.update({
                    'suggestion_text': item.suggestion.target,
                    'suggestion_description': mark_safe(item.get_suggestion_description()),
                })
            elif item.quality_check:
                check_name = item.quality_check.name
                entry.update({
                    'check_name': check_name,
                    'check_display_name': check_names[check_name],
                    'checks_url': u''.join([
                        reverse('pootle-checks-descriptions'), '#', check_name,
                    ]),
                })
            else:
                entry['new_value'] = to_python(item.new_value)

            entry_group['entries'].append(entry)

        entries_group.append(entry_group)

    if (len(entries_group) > 0 and
        entries_group[0]['datetime'] == unit.creation_time):
        entries_group[0]['created'] = True
    else:
        created = {
            'created': True,
            'submitter': User.objects.get_system_user(),
        }

        if unit.creation_time:
            created['datetime'] = unit.creation_time
        entries_group[:0] = [created]

    # Let's reverse the chronological order
    entries_group.reverse()

    context['entries_group'] = entries_group

    # The client will want to confirm that the response is relevant for
    # the unit on screen at the time of receiving this, so we add the uid.
    json = {'uid': unit.id}

    t = loader.get_template('editor/units/xhr_timeline.html')
    c = RequestContext(request, context)
    json['timeline'] = t.render(c).replace('\n', '')

    return JsonResponse(json)


@ajax_required
@require_http_methods(['POST', 'DELETE'])
@get_unit_context('translate')
def comment(request, unit):
    """Dispatches the comment action according to the HTTP verb."""
    if request.method == 'DELETE':
        return delete_comment(request, unit)
    elif request.method == 'POST':
        return save_comment(request, unit)


def delete_comment(request, unit):
    """Deletes a comment by blanking its contents and records a new
    submission.
    """
    unit.commented_by = None
    unit.commented_on = None

    language = request.translation_project.language
    comment_form_class = unit_comment_form_factory(language)
    form = comment_form_class({}, instance=unit, request=request)

    if form.is_valid():
        form.save()
        return JsonResponse({})

    return JsonResponseBadRequest({'msg': _("Failed to remove comment.")})


def save_comment(request, unit):
    """Stores a new comment for the given ``unit``.

    :return: If the form validates, the cleaned comment is returned.
             An error message is returned otherwise.
    """
    # Update current unit instance's attributes
    unit.commented_by = request.profile
    unit.commented_on = timezone.now().replace(microsecond=0)

    language = request.translation_project.language
    form = unit_comment_form_factory(language)(request.POST, instance=unit,
                                               request=request)

    if form.is_valid():
        form.save()

        user = request.user
        directory = unit.store.parent

        ctx = {
            'unit': unit,
            'language': language,
            'cantranslate': check_user_permission(user, 'translate', directory),
            'cansuggest': check_user_permission(user, 'suggest', directory),
        }
        t = loader.get_template('editor/units/xhr_comment.html')
        c = RequestContext(request, ctx)

        return JsonResponse({'comment': t.render(c)})

    return JsonResponseBadRequest({'msg': _("Comment submission failed.")})


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
    comment_form = comment_form_class({}, instance=unit, request=request)

    store = unit.store
    directory = store.parent
    user = request.profile
    project = translation_project.project

    alt_src_langs = get_alt_src_langs(request, user, translation_project)
    altsrcs = find_altsrcs(unit, alt_src_langs, store=store, project=project)
    source_language = translation_project.project.source_language
    sources = {
        unit.store.translation_project.language.code: unit.target_f.strings
        for unit in altsrcs
    }
    sources[source_language.code] = unit.source_f.strings

    priority = None

    if 'virtualfolder' in settings.INSTALLED_APPS:
        vfolder_pk = request.GET.get('vfolder', '')

        if vfolder_pk:
            from virtualfolder.models import VirtualFolder

            try:
                # If we are translating a virtual folder, then display its
                # priority.
                # Note that the passed virtual folder pk might be invalid.
                priority = VirtualFolder.objects.get(pk=vfolder_pk).priority
            except VirtualFolder.DoesNotExist:
                pass

        if priority is None:
            # Retrieve the unit top priority, if any. This can happen if we are
            # not in a virtual folder or if the passed virtual folder pk is
            # invalid.
            priority = unit.vfolders.aggregate(
                priority=Max('priority')
            )['priority']

    template_vars = {
        'unit': unit,
        'form': form,
        'comment_form': comment_form,
        'priority': priority,
        'store': store,
        'directory': directory,
        'profile': user,
        'user': request.user,
        'project': project,
        'language': language,
        'source_language': source_language,
        'cantranslate': check_user_permission(user, "translate", directory),
        'cansuggest': check_user_permission(user, "suggest", directory),
        'canreview': check_user_permission(user, "review", directory),
        'is_admin': check_user_permission(user, 'administrate', directory),
        'altsrcs': altsrcs,
    }

    if translation_project.project.is_terminology or store.is_terminology:
        t = loader.get_template('editor/units/term_edit.html')
    else:
        t = loader.get_template('editor/units/edit.html')
    c = RequestContext(request, template_vars)

    json.update({
        'editor': t.render(c),
        'tm_suggestions': unit.get_tm_suggestions(),
        'is_obsolete': unit.isobsolete(),
        'sources': sources,
    })

    return JsonResponse(json)


@get_unit_context('view')
def permalink_redirect(request, unit):
    return redirect(request.build_absolute_uri(unit.get_translate_url()))


@ajax_required
@get_path_obj
@permission_required('view')
@get_resource
def get_qualitycheck_stats(request, *args, **kwargs):
    failing_checks = request.resource_obj.get_checks()
    return JsonResponse(failing_checks if failing_checks is not None else {})


@ajax_required
@get_path_obj
@permission_required('view')
@get_resource
def get_stats(request, *args, **kwargs):
    stats = request.resource_obj.get_stats()

    if (isinstance(request.resource_obj, Directory) and
        'virtualfolder' in settings.INSTALLED_APPS):
        stats['vfolders'] = {}

        for vfolder_treeitem in request.resource_obj.vf_treeitems.iterator():
            if request.user.is_superuser or vfolder_treeitem.is_visible:
                stats['vfolders'][vfolder_treeitem.code] = \
                    vfolder_treeitem.get_stats(include_children=False)

    return JsonResponse(stats)


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
                        store=unit.store,
                        field=field,
                        type=SubmissionTypes.NORMAL,
                        old_value=old_value,
                        new_value=new_value,
                        similarity=form.cleaned_data['similarity'],
                        mt_similarity=form.cleaned_data['mt_similarity'],
                )
                sub.save()

            # Update current unit instance's attributes
            # important to set these attributes after saving Submission
            # because we need to access the unit's state before it was saved
            if SubmissionFields.TARGET in (f[0] for f in form.updated_fields):
                form.instance.submitted_by = request.profile
                form.instance.submitted_on = current_time
                form.instance.reviewed_by = None
                form.instance.reviewed_on = None

            form.instance._log_user = request.profile

            form.save()

            json['checks'] = _get_critical_checks_snippet(request, unit)

        json['user_score'] = request.profile.public_score

        return JsonResponse(json)

    return JsonResponseBadRequest({'msg': _("Failed to process submission.")})


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
            # HACKISH: django 1.2 stupidly modifies instance on model form
            # validation, reload unit from db
            unit = Unit.objects.get(id=unit.id)
            unit.add_suggestion(
                form.cleaned_data['target_f'],
                user=request.profile,
                similarity=form.cleaned_data['similarity'],
                mt_similarity=form.cleaned_data['mt_similarity'],
            )

            json['user_score'] = request.profile.public_score

        return JsonResponse(json)

    return JsonResponseBadRequest({'msg': _("Failed to process suggestion.")})


@ajax_required
@require_http_methods(['POST', 'DELETE'])
def manage_suggestion(request, uid, sugg_id):
    """Dispatches the suggestion action according to the HTTP verb."""
    if request.method == 'DELETE':
        return reject_suggestion(request, uid, sugg_id)
    elif request.method == 'POST':
        return accept_suggestion(request, uid, sugg_id)


@get_unit_context()
def reject_suggestion(request, unit, suggid):
    json = {
        'udbid': unit.id,
        'sugid': suggid,
    }

    try:
        sugg = unit.suggestion_set.get(id=suggid)
    except ObjectDoesNotExist:
        raise Http404

    # In order to be able to reject a suggestion, users have to either:
    # 1. Have `review` rights, or
    # 2. Be the author of the suggestion being rejected
    if (not check_permission('review', request) and
        (request.user.is_anonymous() or request.user != sugg.user)):
        raise PermissionDenied(_('Insufficient rights to access review mode.'))

    unit.reject_suggestion(sugg, request.translation_project,
                           request.profile)

    json['user_score'] = request.profile.public_score

    return JsonResponse(json)


@get_unit_context('review')
def accept_suggestion(request, unit, suggid):
    json = {
        'udbid': unit.id,
        'sugid': suggid,
    }

    try:
        suggestion = unit.suggestion_set.get(id=suggid)
    except ObjectDoesNotExist:
        raise Http404

    unit.accept_suggestion(suggestion, request.translation_project,
                           request.profile)

    json['user_score'] = request.profile.public_score
    json['newtargets'] = [highlight_whitespace(target)
                          for target in unit.target.strings]
    json['newdiffs'] = {}
    for sugg in unit.get_suggestions():
        json['newdiffs'][sugg.id] = \
                [highlight_diffs(unit.target.strings[i], target)
                 for i, target in enumerate(sugg.target.strings)]

    json['checks'] = _get_critical_checks_snippet(request, unit)

    return JsonResponse(json)


@ajax_required
@get_unit_context('review')
def toggle_qualitycheck(request, unit, check_id):
    try:
        unit.toggle_qualitycheck(check_id, bool(request.POST.get('mute')),
                                 request.profile)
    except ObjectDoesNotExist:
        raise Http404

    return JsonResponse({})
