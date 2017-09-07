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
from django.core.exceptions import ObjectDoesNotExist
from django.http import Http404, QueryDict
from django.shortcuts import get_object_or_404, redirect
from django.template import loader
from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache
from django.utils.translation import to_locale
from django.utils.translation.trans_real import parse_accept_lang_header
from django.views.decorators.http import require_http_methods
from django.views.generic import FormView

from pootle.core.delegate import search_backend
from pootle.core.exceptions import Http400
from pootle.core.http import JsonResponse, JsonResponseBadRequest
from pootle.core.utils import dateformat
from pootle.core.views import PootleJSON
from pootle.core.views.decorators import requires_permission, set_permissions
from pootle.core.views.mixins import GatherContextMixin, PootleJSONMixin
from pootle.i18n.dates import timesince
from pootle.i18n.gettext import ugettext as _
from pootle_app.models.permissions import check_user_permission
from pootle_language.models import Language
from pootle_misc.util import ajax_required

from .decorators import get_unit_context
from .forms import (
    AddSuggestionForm, SubmitForm, SuggestionReviewForm, SuggestionSubmitForm,
    UnitSearchForm, unit_comment_form_factory, unit_form_factory)
from .models import Suggestion, Unit
from .templatetags.store_tags import pluralize_source, pluralize_target
from .unit.results import GroupedResults
from .unit.timeline import Timeline
from .util import find_altsrcs


def get_alt_src_langs(request, user, translation_project):
    if request.user.is_anonymous:
        return
    language = translation_project.language
    project = translation_project.project
    source_language = project.source_language
    langs = list(
        user.alt_src_langs.exclude(
            id__in=(language.id, source_language.id)
        ).filter(
            translationproject__project=project))
    if langs:
        return langs
    accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    for accept_lang, __ in parse_accept_lang_header(accept):
        if accept_lang == '*':
            continue
        normalized = to_locale(
            data.normalize_code(
                data.simplify_to_common(accept_lang)))
        code = to_locale(accept_lang)
        is_source_lang = any(
            langcode in ('en', 'en_US', source_language.code, language.code)
            for langcode in [code, normalized])
        if is_source_lang:
            continue

        langs = list(
            Language.objects.filter(
                code__in=(normalized, code),
                translationproject__project=project))
        if langs:
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
        'critical_checks': list(unit.get_critical_qualitychecks()),
        'warning_checks': list(unit.get_warning_qualitychecks()),
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
    unit.change.commented_by = None
    unit.change.commented_on = None

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
        return self.store.parent

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
            event_groups=self.timeline.grouped_events(),
            language=self.language)

    def get_queryset(self):
        return Unit.objects.get_translatable(self.request.user).select_related(
            "change",
            "store__translation_project__language",
            "store__translation_project__project__directory")

    def get_response_data(self, context):
        return {
            'uid': self.object.id,
            'event_groups': self.get_event_groups_data(context),
            'timeline': self.render_timeline(context)}

    def render_timeline(self, context):
        return loader.get_template(self.template_name).render(context=context)

    def get_event_groups_data(self, context):
        result = []
        for event_group in context['event_groups']:
            display_dt = event_group['datetime']
            if display_dt is not None:
                display_dt = dateformat.format(display_dt)
                iso_dt = event_group['datetime'].isoformat()
                relative_time = timesince(
                    calendar.timegm(event_group['datetime'].timetuple()),
                    self.request_lang)
            else:
                iso_dt = None
                relative_time = None
            result.append({
                "display_datetime": display_dt,
                "iso_datetime": iso_dt,
                "relative_time": relative_time,
                "via_upload": event_group.get('via_upload', False),
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
        if self.request.user.is_anonymous:
            return []
        return find_altsrcs(
            self.object,
            get_alt_src_langs(self.request, self.request.user, self.tp),
            store=self.store,
            project=self.project)

    def get_queryset(self):
        return Unit.objects.get_translatable(self.request.user).select_related(
            "change",
            "change__submitted_by",
            "store",
            "store__filetype",
            "store__parent",
            "store__translation_project",
            "store__translation_project__project",
            "store__translation_project__project__directory",
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
        latest_target_submission = self.object.get_latest_target_submission()
        accepted_suggestion = None
        if latest_target_submission is not None:
            accepted_suggestion = latest_target_submission.suggestion
        critical_checks = list(self.object.get_critical_qualitychecks())
        failing_checks = any(
            not check.false_positive
            for check
            in critical_checks)
        return {
            'unit': self.object,
            'accepted_suggestion': accepted_suggestion,
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
            "failing_checks": failing_checks,
            "critical_checks": critical_checks,
            "warning_checks": list(
                self.object.get_warning_qualitychecks()),
            "terms": self.object.get_terminology()}

    def get_response_data(self, context):
        return {
            'editor': self.render_edit_template(context),
            'tm_suggestions': self.object.get_tm_suggestions(),
            'is_obsolete': self.object.isobsolete(),
            'sources': self.get_sources()}


@get_unit_context('view')
def permalink_redirect(request, unit):
    return redirect(request.build_absolute_uri(unit.get_translate_url()))


class UnitSuggestionJSON(PootleJSONMixin, GatherContextMixin, FormView):

    action = "accept"
    form_class = SuggestionReviewForm
    http_method_names = ['post', 'delete']

    @property
    def permission_context(self):
        return self.get_object().unit.store.parent

    @set_permissions
    @requires_permission("view")
    def dispatch(self, request, *args, **kwargs):
        # get funky with the request 8/
        return super(UnitSuggestionJSON, self).dispatch(request, *args, **kwargs)

    @lru_cache()
    def get_object(self):
        return get_object_or_404(
            Suggestion.objects.select_related(
                "unit",
                "unit__store",
                "unit__store__parent",
                "unit__change",
                "state"),
            unit_id=self.request.resolver_match.kwargs["uid"],
            id=self.request.resolver_match.kwargs["sugg_id"])

    def get_form_kwargs(self, **kwargs):
        comment = (
            QueryDict(self.request.body).get("comment")
            if self.action == "reject"
            else self.request.POST.get("comment"))
        is_fuzzy = (
            QueryDict(self.request.body).get("is_fuzzy")
            if self.action == "reject"
            else self.request.POST.get("is_fuzzy"))
        return dict(
            target_object=self.get_object(),
            request_user=self.request.user,
            data=dict(
                is_fuzzy=is_fuzzy,
                comment=comment,
                action=self.action))

    def delete(self, request, *args, **kwargs):
        self.action = "reject"
        return self.post(request, *args, **kwargs)

    def get_context_data(self, *args, **kwargs):
        ctx = super(UnitSuggestionJSON, self).get_context_data(*args, **kwargs)
        form = ctx["form"]
        if form.is_valid():
            result = dict(
                udbid=form.target_object.unit.id,
                sugid=form.target_object.id,
                user_score=self.request.user.public_score)
            if form.cleaned_data["action"] == "accept":
                result.update(
                    dict(
                        newtargets=[
                            target
                            for target
                            in form.target_object.unit.target.strings],
                        checks=_get_critical_checks_snippet(
                            self.request,
                            form.target_object.unit)))
            return result

    def form_valid(self, form):
        form.save()
        return self.render_to_response(
            self.get_context_data(form=form))

    def form_invalid(self, form):
        if form.non_field_errors():
            raise Http404
        raise Http400(form.errors)


@ajax_required
@get_unit_context('review')
def toggle_qualitycheck(request, unit, check_id, **kwargs_):
    try:
        unit.toggle_qualitycheck(check_id, 'mute' in request.POST, request.user)
    except ObjectDoesNotExist:
        raise Http404

    return JsonResponse({})


class UnitSubmitJSON(UnitSuggestionJSON):

    @set_permissions
    @requires_permission("translate")
    def dispatch(self, request, *args, **kwargs):
        # get funky with the request 8/
        return super(UnitSuggestionJSON, self).dispatch(request, *args, **kwargs)

    @property
    def form_class(self):
        if self.get_suggestion():
            return SuggestionSubmitForm
        return SubmitForm

    @property
    def permission_context(self):
        return self.get_object().store.parent

    @lru_cache()
    def get_object(self):
        return get_object_or_404(
            Unit.objects.select_related(
                "store",
                "change",
                "store__parent",
                "store__translation_project",
                "store__filetype",
                "store__translation_project__language",
                "store__translation_project__project",
                "store__data",
                "store__translation_project__data"),
            id=self.request.resolver_match.kwargs["uid"])

    @lru_cache()
    def get_suggestion(self):
        if "suggestion" in self.request.POST:
            return get_object_or_404(
                Suggestion,
                unit_id=self.get_object().id,
                id=self.request.POST["suggestion"])

    def get_form_kwargs(self, **kwargs):
        kwargs = dict(
            unit=self.get_object(),
            request_user=self.request.user,
            data=self.request.POST)
        if self.get_suggestion():
            kwargs["target_object"] = self.get_suggestion()
        return kwargs

    def get_context_data(self, *args, **kwargs):
        ctx = super(UnitSuggestionJSON, self).get_context_data(*args, **kwargs)
        form = ctx["form"]
        if form.is_valid():
            form.unit.refresh_from_db()
            result = dict(
                checks=_get_critical_checks_snippet(self.request, form.unit),
                user_score=self.request.user.public_score,
                newtargets=[target for target in form.unit.target.strings],
                critical_checks_active=(
                    form.unit.get_active_critical_qualitychecks().exists()))
            return result


class UnitAddSuggestionJSON(PootleJSONMixin, GatherContextMixin, FormView):
    form_class = AddSuggestionForm
    http_method_names = ['post']

    @set_permissions
    @requires_permission("suggest")
    def dispatch(self, request, *args, **kwargs):
        # get funky with the request 8/
        return super(UnitAddSuggestionJSON, self).dispatch(request, *args, **kwargs)

    @property
    def permission_context(self):
        return self.get_object().store.parent

    @lru_cache()
    def get_object(self):
        return get_object_or_404(
            Unit.objects.select_related(
                "store",
                "store__parent",
                "store__translation_project",
                "store__filetype",
                "store__translation_project__language",
                "store__translation_project__project",
                "store__data",
                "store__translation_project__data"),
            id=self.request.resolver_match.kwargs["uid"])

    def get_form_kwargs(self, **kwargs):
        kwargs = dict(
            unit=self.get_object(),
            request_user=self.request.user,
            data=self.request.POST)
        return kwargs

    def get_context_data(self, *args, **kwargs):
        ctx = super(UnitAddSuggestionJSON, self).get_context_data(*args, **kwargs)
        form = ctx["form"]
        if form.is_valid():
            data = dict()
            if not self.request.user.is_anonymous:
                data['user_score'] = self.request.user.public_score
            return data

    def form_valid(self, form):
        form.save()
        return self.render_to_response(
            self.get_context_data(form=form))

    def form_invalid(self, form):
        if form.non_field_errors():
            raise Http404
        raise Http400(form.errors)
