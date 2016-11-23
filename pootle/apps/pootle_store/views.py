# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import calendar
import unicodedata
from collections import OrderedDict

from translate.lang import data

from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist, PermissionDenied
from django.http import Http404, QueryDict
from django.shortcuts import redirect
from django.template import loader
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache
from django.utils.translation import to_locale
from django.utils.translation.trans_real import parse_accept_lang_header
from django.views.decorators.http import require_http_methods

from pootle.core.delegate import review, search_backend
from pootle.core.exceptions import Http400
from pootle.core.http import JsonResponse, JsonResponseBadRequest
from pootle.core.utils import dateformat
from pootle.core.views import PootleJSON
from pootle.i18n.gettext import ugettext as _
from pootle.local.dates import timesince
from pootle_app.models.directory import Directory
from pootle_app.models.permissions import (check_permission,
                                           check_user_permission)
from pootle_comment.forms import UnsecuredCommentForm
from pootle_language.models import Language
from pootle_misc.util import ajax_required
from pootle_statistics.models import (Submission, SubmissionFields,
                                      SubmissionTypes)

from .decorators import get_unit_context
from .forms import UnitSearchForm, unit_comment_form_factory, unit_form_factory
from .models import Suggestion, Unit
from .templatetags.store_tags import pluralize_source, pluralize_target
from .unit.results import GroupedResults
from .unit.timeline import Timeline
from .util import find_altsrcs


def get_alt_src_langs(request, user, translation_project):
    language = translation_project.language
    project = translation_project.project
    source_language = project.source_language

    langs = user.alt_src_langs.exclude(
        id__in=(language.id, source_language.id)
    ).filter(translationproject__project=project)

    if not user.alt_src_langs.count():
        accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')

        for accept_lang, __ in parse_accept_lang_header(accept):
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
    return template.render(context=ctx, request=request)


@ajax_required
def get_units(request, **kwargs_):
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
def get_more_context(request, unit, **kwargs_):
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
def comment(request, unit, **kwargs_):
    """Dispatches the comment action according to the HTTP verb."""
    if request.method == 'DELETE':
        return delete_comment(request, unit)
    elif request.method == 'POST':
        return save_comment(request, unit)


def delete_comment(request, unit, **kwargs_):
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

        return JsonResponse({'comment': t.render(context=ctx,
                                                 request=request)})

    return JsonResponseBadRequest({'msg': _("Comment submission failed.")})


class PootleUnitJSON(PootleJSON):
    model = Unit
    pk_url_kwarg = "uid"

    @cached_property
    def permission_context(self):
        self.object = self.get_object()
        return Directory.objects.select_related("tp", "tp__project").get(
            pk=self.store.parent_id)

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
        return loader.get_template(self.template_name).render(context=context)

    def get_entries_group_data(self, context):
        result = []
        for entry_group in context['entries_group']:
            display_dt = entry_group['datetime']
            if display_dt is not None:
                display_dt = dateformat.format(display_dt)
                iso_dt = entry_group['datetime'].isoformat()
                relative_time = timesince(
                    calendar.timegm(entry_group['datetime'].timetuple()))
            else:
                iso_dt = None
                relative_time = None
            result.append({
                "display_datetime": display_dt,
                "iso_datetime": iso_dt,
                "relative_time": relative_time,
                "via_upload": entry_group.get('via_upload', False),
            })
        return result


CHARACTERS_NAMES = OrderedDict(
    (
        # Code  Display name
        (8204, 'ZWNJ'),
        (8205, 'ZWJ'),
        (8206, 'LRM'),
        (8207, 'RLM'),
        (8234, 'LRE'),
        (8235, 'RLE'),
        (8236, 'PDF'),
        (8237, 'LRO'),
        (8238, 'RLO'),
    )
)

CHARACTERS = u"".join([unichr(index) for index in CHARACTERS_NAMES.keys()])


class UnitEditJSON(PootleUnitJSON):

    @property
    def special_characters(self):
        if self.language.direction == "rtl":
            # Inject some extra special characters for RTL languages.
            language_specialchars = CHARACTERS
            # Do not repeat special chars.
            language_specialchars += u"".join(
                [c for c in self.language.specialchars if c not in CHARACTERS])
        else:
            language_specialchars = self.language.specialchars

        special_chars = []
        for specialchar in language_specialchars:
            code = ord(specialchar)
            special_chars.append({
                'display': CHARACTERS_NAMES.get(code, specialchar),
                'code': code,
                'hex_code': "U+" + hex(code)[2:].upper(),  # Like U+200C
                'name': unicodedata.name(specialchar, ''),
            })
        return special_chars

    def get_edit_template(self):
        if self.project.is_terminology or self.store.has_terminology:
            return loader.get_template('editor/units/term_edit.html')
        return loader.get_template('editor/units/edit.html')

    def render_edit_template(self, context):
        return self.get_edit_template().render(context=context,
                                               request=self.request)

    def get_source_nplurals(self):
        if self.object.hasplural():
            return len(self.object.source.strings)
        return None

    def get_target_nplurals(self):
        source_nplurals = self.get_source_nplurals()
        return self.language.nplurals if source_nplurals is not None else 1

    def get_unit_values(self):
        target_nplurals = self.get_target_nplurals()
        unit_values = [value for value in self.object.target_f.strings]
        if len(unit_values) < target_nplurals:
            return unit_values + ((target_nplurals - len(unit_values)) * [''])
        return unit_values

    def get_unit_edit_form(self):
        form_class = unit_form_factory(self.language,
                                       self.get_source_nplurals(),
                                       self.request)
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
            "store__filetype",
            "store__parent",
            "store__translation_project",
            "store__translation_project__project",
            "store__translation_project__project__source_language",
            "store__translation_project__language")

    def get_sources(self):
        sources = {
            unit.language_code: unit.target.strings
            for unit in self.get_alt_srcs()}
        sources[self.source_language.code] = self.object.source_f.strings
        return sources

    def get_context_data(self, *args, **kwargs):
        priority = (
            self.store.priority
            if 'virtualfolder' in settings.INSTALLED_APPS
            else None)
        suggestions = self.object.get_suggestions()
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
            'special_characters': self.special_characters,
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
            'altsrcs': {x.id: x.data for x in self.get_alt_srcs()},
            'unit_values': self.get_unit_values(),
            'target_nplurals': self.get_target_nplurals(),
            'has_plurals': self.object.hasplural(),
            'filetype': self.object.store.filetype.name,
            'suggestions': suggestions,
            'suggestions_dict': {x.id: dict(id=x.id, target=x.target.strings)
                                 for x in suggestions},
        }

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
@get_unit_context('translate')
def submit(request, unit, **kwargs_):
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
        suggestion = form.cleaned_data['suggestion']
        if suggestion:
            review.get(Suggestion)([suggestion], request.user).accept()
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
        json['newtargets'] = [target for target in form.instance.target.strings]

        return JsonResponse(json)

    return JsonResponseBadRequest({'msg': _("Failed to process submission.")})


@ajax_required
@get_unit_context('suggest')
def suggest(request, unit, **kwargs_):
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
        if form.cleaned_data.get("target_updated"):
            # TODO: Review if this hackish method is still necessary
            # HACKISH: django 1.2 stupidly modifies instance on model form
            # validation, reload unit from db
            unit = Unit.objects.get(id=unit.id)
            review.get(Suggestion)().add(
                unit,
                form.cleaned_data['target_f'],
                user=request.user,
                similarity=form.cleaned_data['similarity'],
                mt_similarity=form.cleaned_data['mt_similarity'])

            if not request.user.is_anonymous:
                json['user_score'] = request.user.public_score

        return JsonResponse(json)

    return JsonResponseBadRequest({'msg': _("Failed to process suggestion.")})


@ajax_required
@require_http_methods(['POST', 'DELETE'])
def manage_suggestion(request, uid, sugg_id, **kwargs_):
    """Dispatches the suggestion action according to the HTTP verb."""
    if request.method == 'DELETE':
        return reject_suggestion(request, uid, sugg_id)
    elif request.method == 'POST':
        return accept_suggestion(request, uid, sugg_id)


@get_unit_context()
def reject_suggestion(request, unit, suggid, **kwargs_):
    try:
        suggestion = unit.suggestion_set.get(id=suggid)
    except ObjectDoesNotExist:
        raise Http404

    # In order to be able to reject a suggestion, users have to either:
    # 1. Have `review` rights, or
    # 2. Be the author of the suggestion being rejected
    has_permission = (
        check_permission('review', request)
        or (not request.user.is_anonymous
            and request.user == suggestion.user))
    if not has_permission:
        raise PermissionDenied(
            _('Insufficient rights to access review mode.'))
    review.get(Suggestion)(
        [suggestion],
        request.user).reject(QueryDict(request.body).get("comment"))
    json = {
        'udbid': unit.id,
        'sugid': suggid,
        'user_score': request.user.public_score,
    }
    return JsonResponse(json)


@get_unit_context('review')
def accept_suggestion(request, unit, suggid, **kwargs_):
    try:
        suggestion = unit.suggestion_set.get(id=suggid)
    except ObjectDoesNotExist:
        raise Http404
    review.get(Suggestion)(
        [suggestion], request.user).accept(request.POST.get("comment"))
    json = {
        'udbid': unit.id,
        'sugid': suggid,
        'user_score': request.user.public_score,
        'newtargets': [target for target in unit.target.strings],
        'checks': _get_critical_checks_snippet(request, unit),
    }
    return JsonResponse(json)


@ajax_required
@get_unit_context('review')
def toggle_qualitycheck(request, unit, check_id, **kwargs_):
    try:
        unit.toggle_qualitycheck(check_id, 'mute' in request.POST, request.user)
    except ObjectDoesNotExist:
        raise Http404

    return JsonResponse({})
