# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib import messages
from django.http import Http404
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.safestring import mark_safe

from pootle.core.browser import make_project_item
from pootle.core.decorators import (
    get_object_or_404, get_path_obj, permission_required)
from pootle.core.exceptions import Http400
from pootle.core.views import PootleBrowseView, PootleTranslateView
from pootle.core.views.admin import PootleFormView
from pootle.core.views.decorators import requires_permission, set_permissions
from pootle.core.views.formtable import Formtable
from pootle.core.views.mixins import PootleJSONMixin
from pootle.i18n import formatter
from pootle.i18n.gettext import ugettext_lazy as _, ungettext_lazy
from pootle_misc.util import cmp_by_last_activity
from pootle_store.constants import STATES_MAP

from .apps import PootleLanguageConfig
from .forms import (
    LanguageSpecialCharsForm, LanguageSuggestionAdminForm,
    LanguageTeamAdminForm, LanguageTeamNewMemberSearchForm)
from .models import Language


class LanguageMixin(object):
    ns = "pootle.language"
    sw_version = PootleLanguageConfig.version
    model = Language
    browse_url_path = "pootle-language-browse"
    translate_url_path = "pootle-language-translate"
    template_extends = 'languages/base.html'

    @property
    def language(self):
        return self.object

    @property
    def permission_context(self):
        return self.get_object().directory

    @property
    def url_kwargs(self):
        return {"language_code": self.object.code}

    def get_object(self):
        return self.object

    @cached_property
    def object(self):
        lang = Language.get_canonical(self.kwargs["language_code"])
        if lang is None:
            raise Http404
        return lang

    def get(self, *args, **kwargs):
        self.object = self.get_object()
        if self.object.code != kwargs["language_code"]:
            return redirect(
                self.url_pattern_name,
                self.object.code,
                permanent=True)
        return super(LanguageMixin, self).get(*args, **kwargs)


class LanguageBrowseView(LanguageMixin, PootleBrowseView):
    url_pattern_name = "pootle-language-browse"
    view_name = "language"

    @cached_property
    def object_children(self):
        items = [make_project_item(tp)
                 for tp in self.object.get_children_for_user(self.request.user)]
        items = self.add_child_stats(items)
        items.sort(cmp_by_last_activity)
        return items

    @property
    def language(self):
        return {
            'code': self.object.code,
            'name': self.object.name}

    def get(self, *args, **kwargs):
        response = super(LanguageBrowseView, self).get(*args, **kwargs)
        response.set_cookie('pootle-language', self.object.code)
        return response


class LanguageTranslateView(LanguageMixin, PootleTranslateView):
    url_pattern_name = "pootle-language-translate"


@get_path_obj
@permission_required('administrate')
def language_characters_admin(request, language):
    form = LanguageSpecialCharsForm(request.POST
                                    if request.method == 'POST'
                                    else None,
                                    instance=language)
    if form.is_valid():
        form.save()
        return redirect('pootle-language-browse', language.code)

    ctx = {
        'page': 'admin-characters',

        'browse_url': reverse('pootle-language-browse', kwargs={
            'language_code': language.code,
        }),
        'translate_url': reverse('pootle-language-translate', kwargs={
            'language_code': language.code,
        }),

        'language': language,
        'directory': language.directory,
        'form': form,
    }

    return render(request, 'languages/admin/characters.html', ctx)


class SuggestionFormtable(Formtable):
    row_field = "suggestions"
    filters_template = "languages/admin/includes/suggestions_header.html"

    @property
    def messages(self):
        return self.kwargs.get("messages", [])


class SuggestionDisplay(object):

    def __init__(self, suggestion):
        self.__suggestion__ = suggestion

    @property
    def unit(self):
        return self.__suggestion__.unit.source_f

    @property
    def project(self):
        tp = self.__suggestion__.unit.store.translation_project
        return mark_safe(
            "<a href='%s'>%s</a>"
            % (tp.get_absolute_url(),
               tp.project.code))

    @property
    def unit_state(self):
        return STATES_MAP[self.__suggestion__.unit.state]

    @property
    def unit_link(self):
        return mark_safe(
            "<a href='%s'>#%s</a>"
            % (self.__suggestion__.unit.get_translate_url(),
               self.__suggestion__.unit.id))

    def __getattr__(self, k):
        try:
            return getattr(self.__suggestion__, k)
        except AttributeError:
            return self.__getattribute__(k)


class PootleLanguageAdminFormView(PootleFormView):

    @property
    def permission_context(self):
        return self.language.directory

    @set_permissions
    @requires_permission("administrate")
    def dispatch(self, request, *args, **kwargs):
        # get funky with the request 8/
        return super(
            PootleLanguageAdminFormView, self).dispatch(request, *args, **kwargs)

    @cached_property
    def language(self):
        return get_object_or_404(
            Language.objects.select_related("directory"),
            code=self.kwargs["language_code"])

    def get_form_kwargs(self):
        kwargs = super(PootleLanguageAdminFormView, self).get_form_kwargs()
        kwargs["language"] = self.language
        return kwargs

    @property
    def success_kwargs(self):
        return dict(language_code=self.language.code)


class LanguageSuggestionAdminView(PootleLanguageAdminFormView):
    template_name = 'languages/admin/language_team_suggestions.html'
    form_class = LanguageSuggestionAdminForm
    success_url_pattern = "pootle-language-admin-suggestions"
    formtable_columns = (
        _("Unit"),
        _("State"),
        _("Source"),
        _("Suggestion"),
        _("Suggested by"),
        _("Suggested at"),
        _("Project"))

    @property
    def default_form_kwargs(self):
        return dict(
            page_no=1,
            results_per_page=10)

    def add_success_message(self, form):
        count = (
            form.fields["suggestions"].queryset.count()
            if form.cleaned_data["select_all"]
            else len(form.cleaned_data["suggestions"]))
        reject_and_notify = (
            form.cleaned_data["actions"] == "reject"
            and form.cleaned_data["comment"])
        accept_and_notify = (
            form.cleaned_data["actions"] == "accept"
            and form.cleaned_data["comment"])
        if reject_and_notify:
            message = ungettext_lazy(
                "Rejected %s suggestion with comment. User will be notified",
                "Rejected %s suggestions with comment. Users will be notified",
                count, count)
        elif accept_and_notify:
            message = ungettext_lazy(
                "Accepted %s suggestion with comment. User will be notified",
                "Accepted %s suggestions with comment. Users will be notified",
                count, count)
        elif form.cleaned_data["actions"] == "reject":
            message = ungettext_lazy(
                "Rejected %s suggestion",
                "Rejected %s suggestions",
                count, count)
        else:
            message = ungettext_lazy(
                "Accepted %s suggestion",
                "Accepted %s suggestions",
                count, count)
        messages.success(self.request, message)

    def get_context_data(self, **kwargs):
        context = super(
            LanguageSuggestionAdminView, self).get_context_data(**kwargs)
        context["page"] = "admin-suggestions"
        context["language"] = self.language
        form = context["form"]
        form.is_valid()
        batch = form.batch()
        form.fields["suggestions"].choices = [
            (item.id, SuggestionDisplay(item))
            for item in
            batch.object_list]
        context["formtable"] = SuggestionFormtable(
            form,
            columns=self.formtable_columns,
            page=batch,
            messages=messages.get_messages(self.request))
        return context

    def get_form_kwargs(self):
        kwargs = super(LanguageSuggestionAdminView, self).get_form_kwargs()
        if not self.request.POST:
            kwargs["data"] = self.default_form_kwargs
        kwargs["user"] = self.request.user
        return kwargs


class LanguageTeamAdminFormView(PootleLanguageAdminFormView):
    form_class = LanguageTeamAdminForm
    template_name = "languages/admin/language_team.html"
    success_url_pattern = "pootle-language-admin-team"

    def get_context_data(self, **kwargs):
        context = super(LanguageTeamAdminFormView, self).get_context_data(**kwargs)
        form = context["form"]
        context["tps"] = self.language.translationproject_set.exclude(
            project__disabled=True)
        stats = self.language.data_tool.get_stats(
            include_children=False,
            user=self.request.user)
        keys = ("total", "critical", "incomplete", "translated", "fuzzy",
                "untranslated")
        for k in keys:
            if k in stats:
                stats[k + "_display"] = formatter.number(stats[k])
        context["stats"] = stats
        context["suggestions"] = form.language_team.suggestions.count()
        context["suggestions_display"] = formatter.number(
            context["suggestions"])
        context["language"] = self.language
        context["page"] = "admin-team"
        context["browse_url"] = reverse(
            "pootle-language-browse",
            kwargs=dict(language_code=self.language.code))
        context["translate_url"] = reverse(
            "pootle-language-translate",
            kwargs=dict(language_code=self.language.code))
        return context


class LanguageTeamAdminNewMembersJSON(PootleJSONMixin, PootleLanguageAdminFormView):
    form_class = LanguageTeamNewMemberSearchForm

    def get_context_data(self, **kwargs):
        context = super(
            LanguageTeamAdminNewMembersJSON, self).get_context_data(**kwargs)
        form = context["form"]
        return (
            dict(items=form.search())
            if form.is_valid()
            else dict(items=[]))

    def get_form_kwargs(self):
        kwargs = super(LanguageTeamAdminNewMembersJSON, self).get_form_kwargs()
        kwargs["data"] = self.request.POST
        return kwargs

    def form_valid(self, form):
        return self.render_to_response(
            self.get_context_data(form=form))

    def form_invalid(self, form):
        raise Http400(form.errors)
