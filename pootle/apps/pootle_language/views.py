# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import redirect, render
from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from pootle.core.browser import make_project_item
from pootle.core.decorators import get_path_obj, permission_required
from pootle.core.views import (
    PootleBrowseView, PootleTranslateView, PootleExportView)
from pootle.i18n.gettext import tr_lang
from pootle_app.views.admin.permissions import admin_permissions

from .forms import LanguageSpecialCharsForm
from .models import Language


class LanguageMixin(object):
    model = Language
    browse_url_path = "pootle-language-browse"
    export_url_path = "pootle-language-export"
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

    @property
    def stats(self):
        return self.object.get_stats_for_user(self.request.user)

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


class LanguageExportView(LanguageMixin, PootleExportView):
    url_pattern_name = "pootle-language-export"
    source_language = "en"


@get_path_obj
@permission_required('administrate')
def language_admin(request, language):
    ctx = {
        'page': 'admin-permissions',

        'browse_url': reverse('pootle-language-browse', kwargs={
            'language_code': language.code,
        }),
        'translate_url': reverse('pootle-language-translate', kwargs={
            'language_code': language.code,
        }),

        'language': language,
        'directory': language.directory,
    }
    return admin_permissions(request, language.directory,
                             'languages/admin/permissions.html', ctx)


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
