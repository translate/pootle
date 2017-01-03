# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import REDIRECT_FIELD_NAME
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.translation import get_language
from django.views.generic import TemplateView

from pootle.core.decorators import persistent_property
from pootle.core.delegate import revision, scores
from pootle.i18n.override import get_lang_from_http_header
from pootle_language.models import Language
from pootle_project.models import Project, ProjectSet


COOKIE_NAME = 'pootle-language'


class WelcomeView(TemplateView):
    ns = "pootle.web.welcome"
    template_name = "welcome.html"

    @property
    def revision(self):
        return revision.get(self.project_set.directory.__class__)(
            self.project_set.directory).get(key="stats")

    @property
    def cache_key(self):
        return (
            "%s.%s.%s"
            % (self.request.user.username,
               self.revision,
               self.request_lang))

    @cached_property
    def project_set(self):
        user_projects = Project.accessible_by_user(self.request.user)
        user_projects = (
            Project.objects.for_user(self.request.user)
                           .filter(code__in=user_projects))
        return ProjectSet(user_projects)

    @property
    def request_lang(self):
        return get_language()

    @persistent_property
    def score_data(self):
        return scores.get(ProjectSet)(
            self.project_set).display(language=self.request_lang)

    def get_context_data(self, **kwargs):
        context = super(WelcomeView, self).get_context_data(**kwargs)
        context.update(dict(score_data=self.score_data))
        return context


def view(request):
    if not request.user.is_authenticated:
        ctx = {
            'next': request.GET.get(REDIRECT_FIELD_NAME, ''),
        }
        return WelcomeView.as_view()(request, ctx)

    lang = request.COOKIES.get(COOKIE_NAME, None)

    if lang is None:
        supported = Language.live.cached_dict(
            show_all=request.user.is_superuser
        )
        lang = get_lang_from_http_header(request, supported)

    if lang is not None and lang not in ('projects', ''):
        url = reverse('pootle-language-browse', args=[lang])
    else:
        url = reverse('pootle-projects-browse')

    # Preserve query strings
    args = request.GET.urlencode()
    qs = '?%s' % args if args else ''
    redirect_url = '%s%s' % (url, qs)

    return redirect(redirect_url)


class AboutView(TemplateView):
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        from translate.__version__ import sver as toolkit_version
        from pootle import __version__

        return {
            'pootle_version': __version__,
            'toolkit_version': toolkit_version,
        }
