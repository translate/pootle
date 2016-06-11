# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import copy

from translate.lang import data

from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404, QueryDict
from django.shortcuts import redirect
from django.template import RequestContext, loader
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache
from django.utils.translation import to_locale, ugettext as _
from django.utils.translation.trans_real import parse_accept_lang_header
from django.views.decorators.http import require_http_methods

from pootle.core.decorators import (get_path_obj, get_resource,
                                    permission_required)
from pootle.core.delegate import search_backend
from pootle.core.exceptions import Http400
from pootle.core.http import JsonResponse, JsonResponseBadRequest
from pootle.core.utils import dateformat
from pootle.core.views import PootleJSON
from pootle_app.models.directory import Directory
from pootle_app.models.permissions import (check_permission,
                                           check_user_permission)
from pootle_comment.forms import UnsecuredCommentForm
from pootle_misc.util import ajax_required
from pootle_statistics.models import (Submission, SubmissionFields,
                                      SubmissionTypes)

from .decorators import get_unit_context
from .forms import (
    highlight_whitespace, unit_comment_form_factory,
    unit_form_factory, UnitSearchForm)
from .models import Unit
from .templatetags.store_tags import (highlight_diffs, pluralize_source,
                                      pluralize_target)
from .unit.results import GroupedResults
from .unit.timeline import Timeline
from .util import find_altsrcs


#: Mapping of allowed sorting criteria.
#: Keys are supported query strings, values are the field + order that
#: will be used against the DB.
ALLOWED_SORTS = {
    'units': {
        'priority': '-priority',
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

    can_review = check_user_permission(request.user, 'review',
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
    search_form = UnitSearchForm(request.GET, user=request.user)

    if not search_form.is_valid():
        errors = search_form.errors.as_data()
        if "path" in errors:
            for error in errors["path"]:
                if error.code == "max_length":
                    raise Http400(_('Path too long.'))
                elif error.code == "required":
                    raise Http400(_('Arguments missing.'))
        raise Http404(forms.ValidationError(search_form.errors).messages)

    total, start, end, units_qs = search_backend.get(Unit)(
        request.user, **search_form.cleaned_data).search()
    return JsonResponse(
        {'start': start,
         'end': end,
         'total': total,
         'unitGroups': GroupedResults(units_qs).data})


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
    unit.commented_by = request.user
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
            'cantranslate': check_user_permission(user, 'translate',
                                                  directory),
            'cansuggest': check_user_permission(user, 'suggest', directory),
        }
        t = loader.get_template('editor/units/xhr_comment.html')
        c = RequestContext(request, ctx)

        return JsonResponse({'comment': t.render(c)})

    return JsonResponseBadRequest({'msg': _("Comment submission failed.")})


class PootleUnitJSON(PootleJSON):
    model = Unit
    pk_url_kwarg = "uid"

    @cached_property
    def permission_context(self):
        self.object = self.get_object()
        tp_prefix = "parent__" * (self.pootle_path.count("/") - 3)
        return Directory.objects.select_related(
            "%stranslationproject__project"
            % tp_prefix).get(pk=self.store.parent_id)

    @property
    def pootle_path(self):
        return self.store.pootle_path

    @cached_property
    def tp(self):
        return self.store.translation_project

    @cached_property
    def store(self):
        return self.object.store

    @cached_property
    def source_language(self):
        return self.project.source_language

    @cached_property
    def directory(self):
        return self.store.parent

    @lru_cache()
    def get_object(self):
        return super(PootleUnitJSON, self).get_object()


class UnitTimelineJSON(PootleUnitJSON):

    model = Unit
    pk_url_kwarg = "uid"

    template_name = 'editor/units/xhr_timeline.html'

    @property
    def language(self):
        return self.object.store.translation_project.language

    @cached_property
    def permission_context(self):
        self.object = self.get_object()
        return self.project.directory

    @property
    def project(self):
        return self.object.store.translation_project.project

    @property
    def timeline(self):
        return Timeline(self.object)

    def get_context_data(self, *args, **kwargs):
        return dict(
            entries_group=self.timeline.grouped_entries,
            language=self.language)

    def get_queryset(self):
        return Unit.objects.get_translatable(self.request.user).select_related(
            "store__translation_project__language",
            "store__translation_project__project__directory")

    def get_response_data(self, context):
        return {
            'uid': self.object.id,
            'entries_group': self.get_entries_group_data(context),
            'timeline': self.render_timeline(context)}

    def render_timeline(self, context):
        return loader.get_template(
            self.template_name).render(context).replace('\n', '')

    def get_entries_group_data(self, context):
        result = []
        for entry_group in context['entries_group']:
            display_dt = entry_group['datetime']
            if display_dt is not None:
                display_dt = dateformat.format(display_dt)
                iso_dt = entry_group['datetime'].isoformat()
            else:
                iso_dt = None
            result.append({
                "display_datetime": display_dt,
                "iso_datetime": iso_dt,
                "via_upload": entry_group.get('via_upload', False)})
        return result


class UnitEditJSON(PootleUnitJSON):

    def get_edit_template(self):
        if self.project.is_terminology or self.store.has_terminology:
            return loader.get_template('editor/units/term_edit.html')
        return loader.get_template('editor/units/edit.html')

    def render_edit_template(self, context):
        return self.get_edit_template().render(
            RequestContext(self.request, context))

    def get_unit_edit_form(self):
        snplurals = None
        if self.object.hasplural():
            snplurals = len(self.object.source.strings)
        form_class = unit_form_factory(self.language, snplurals, self.request)
        return form_class(instance=self.object, request=self.request)

    def get_unit_comment_form(self):
        comment_form_class = unit_comment_form_factory(self.language)
        return comment_form_class({}, instance=self.object, request=self.request)

    @lru_cache()
    def get_alt_srcs(self):
        return find_altsrcs(
            self.object,
            get_alt_src_langs(self.request, self.request.user, self.tp),
            store=self.store,
            project=self.project)

    def get_queryset(self):
        return Unit.objects.get_translatable(self.request.user).select_related(
            "store",
            "store__parent",
            "store__translation_project",
            "store__translation_project__project",
            "store__translation_project__project__source_language",
            "store__translation_project__language")

    def get_sources(self):
        sources = {
            unit.store.translation_project.language.code: unit.target_f.strings
            for unit in self.get_alt_srcs()}
        sources[self.source_language.code] = self.object.source_f.strings
        return sources

    def get_context_data(self, *args, **kwargs):
        priority = (
            self.object.priority if 'virtualfolder' in settings.INSTALLED_APPS
            else None
        )
        return {
            'unit': self.object,
            'form': self.get_unit_edit_form(),
            'comment_form': self.get_unit_comment_form(),
            'priority': priority,
            'store': self.store,
            'directory': self.directory,
            'user': self.request.user,
            'project': self.project,
            'language': self.language,
            'source_language': self.source_language,
            'cantranslate': check_user_permission(self.request.user,
                                                  "translate",
                                                  self.directory),
            'cantranslatexlang': check_user_permission(self.request.user,
                                                       "administrate",
                                                       self.project.directory),
            'cansuggest': check_user_permission(self.request.user,
                                                "suggest",
                                                self.directory),
            'canreview': check_user_permission(self.request.user,
                                               "review",
                                               self.directory),
            'has_admin_access': check_user_permission(self.request.user,
                                                      'administrate',
                                                      self.directory),
            'altsrcs': self.get_alt_srcs()}

    def get_response_data(self, context):
        return {
            'editor': self.render_edit_template(context),
            'tm_suggestions': self.object.get_tm_suggestions(),
            'is_obsolete': self.object.isobsolete(),
            'sources': self.get_sources()}


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
    old_unit = copy.copy(unit)

    if unit.hasplural():
        snplurals = len(unit.source.strings)
    else:
        snplurals = None

    # Store current time so that it is the same for all submissions
    current_time = timezone.now()

    form_class = unit_form_factory(language, snplurals, request)
    form = form_class(request.POST, instance=unit, request=request)

    if form.is_valid():
        suggestion = form.cleaned_data['suggestion']
        if suggestion:
            old_unit.accept_suggestion(suggestion,
                                       request.translation_project, request.user)
            if form.cleaned_data['comment']:
                kwargs = dict(
                    comment=form.cleaned_data['comment'],
                    user=request.user,
                )
                comment_form = UnsecuredCommentForm(suggestion, kwargs)
                if comment_form.is_valid():
                    comment_form.save()

        if form.updated_fields:
            for field, old_value, new_value in form.updated_fields:
                if field == SubmissionFields.TARGET and suggestion:
                    old_value = str(suggestion.target_f)
                sub = Submission(
                    creation_time=current_time,
                    translation_project=translation_project,
                    submitter=request.user,
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
                form.instance.submitted_by = request.user
                form.instance.submitted_on = current_time
                form.instance.reviewed_by = None
                form.instance.reviewed_on = None

            form.instance._log_user = request.user

            form.save()

            json['checks'] = _get_critical_checks_snippet(request, unit)

        json['user_score'] = request.user.public_score

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
                user=request.user,
                similarity=form.cleaned_data['similarity'],
                mt_similarity=form.cleaned_data['mt_similarity'],
            )

            json['user_score'] = request.user.public_score

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

    unit.reject_suggestion(sugg, request.translation_project, request.user)
    r_data = QueryDict(request.body)
    if "comment" in r_data and r_data["comment"]:
        kwargs = dict(
            comment=r_data["comment"],
            user=request.user,
        )
        comment_form = UnsecuredCommentForm(sugg, kwargs)
        if comment_form.is_valid():
            comment_form.save()

    json['user_score'] = request.user.public_score

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

    unit.accept_suggestion(suggestion, request.translation_project, request.user)
    if "comment" in request.POST and request.POST["comment"]:
        kwargs = dict(
            comment=request.POST["comment"],
            user=request.user,
        )
        comment_form = UnsecuredCommentForm(suggestion, kwargs)
        if comment_form.is_valid():
            comment_form.save()

    json['user_score'] = request.user.public_score
    json['newtargets'] = [highlight_whitespace(target)
                          for target in unit.target.strings]
    json['newdiffs'] = {}
    for sugg in unit.get_suggestions():
        json['newdiffs'][sugg.id] = [highlight_diffs(unit.target.strings[i],
                                                     target) for i, target in
                                     enumerate(sugg.target.strings)]

    json['checks'] = _get_critical_checks_snippet(request, unit)

    return JsonResponse(json)


@ajax_required
@get_unit_context('review')
def toggle_qualitycheck(request, unit, check_id):
    try:
        unit.toggle_qualitycheck(check_id, bool(request.POST.get('mute')),
                                 request.user)
    except ObjectDoesNotExist:
        raise Http404

    return JsonResponse({})
