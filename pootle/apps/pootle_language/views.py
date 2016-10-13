# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from pootle.core.browser import make_project_item
from pootle.core.decorators import get_path_obj, permission_required
from pootle.core.views import PootleBrowseView, PootleTranslateView
from pootle.core.views.admin import PootleLanguageAdminFormView
from pootle.core.views.mixins import PootleJSONMixin
from pootle.i18n.gettext import tr_lang

from .forms import (
    LanguageSpecialCharsForm, LanguageTeamAdminForm,
    LanguageTeamNewMemberSearchForm)
from .models import Language


class LanguageMixin(object):
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

    @lru_cache()
    def get_object(self):
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
    table_id = "language"
    table_fields = [
        'name', 'progress', 'total', 'need-translation',
        'suggestions', 'critical', 'last-updated', 'activity']

    @cached_property
    def items(self):
        return [
            make_project_item(tp)
            for tp in self.object.get_children_for_user(self.request.user)
        ]

    @property
    def language(self):
        return {
            'code': self.object.code,
            'name': tr_lang(self.object.fullname)}

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


class LanguageTeamBaseAdminView(PootleLanguageAdminFormView):

    @property
    def language(self):
        return get_object_or_404(Language, code=self.kwargs["language_code"])

    def get_form_kwargs(self):
        kwargs = super(LanguageTeamBaseAdminView, self).get_form_kwargs()
        kwargs["language"] = self.language
        return kwargs


class LanguageTeamAdminFormView(LanguageTeamBaseAdminView):
    form_class = LanguageTeamAdminForm
    template_name = "languages/admin/language_team.html"

    def form_valid(self, form):
        form.save()
        return super(LanguageTeamAdminFormView, self).form_valid(form)

    def get_context_data(self, **kwargs):
        context = super(LanguageTeamAdminFormView, self).get_context_data(**kwargs)
        form = context["form"]
        context["tps"] = self.language.translationproject_set.exclude(
            project__disabled=True)
        context["stats"] = self.language.data_tool.get_stats(
            include_children=False,
            user=self.request.user)
        context["suggestions"] = form.language_team.suggestions
        context["language"] = self.language
        context["page"] = "admin-team"
        context["browse_url"] = reverse(
            "pootle-language-browse",
            kwargs=dict(language_code=self.language.code))
        context["translate_url"] = reverse(
            "pootle-language-translate",
            kwargs=dict(language_code=self.language.code))
        return context

    @property
    def success_url(self):
        return reverse(
            "pootle-language-admin-team",
            kwargs=dict(language_code=self.language.code))


class LanguageTeamAdminNewMembersJSON(PootleJSONMixin, LanguageTeamBaseAdminView):
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
        kwargs["data"] = self.request.GET
        return kwargs
