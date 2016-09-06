# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model
from django.forms import ValidationError
from django.http import Http404
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.generic import View

from pootle.core.url_helpers import split_pootle_path
from pootle.core.utils.stats import (TOP_CONTRIBUTORS_CHUNK_SIZE,
                                     get_top_scorers_data)
from pootle.core.views.mixins import PootleJSONMixin
from pootle_language.views import LanguageBrowseView
from pootle_misc.util import ajax_required
from pootle_project.views import ProjectBrowseView, ProjectsBrowseView
from pootle_translationproject.views import TPBrowseStoreView, TPBrowseView

from .forms import StatsForm


class ContributorsJSONMixin(PootleJSONMixin):
    @property
    def path(self):
        return self.kwargs["path"]

    def get_context_data(self, **kwargs_):
        User = get_user_model()

        language_code, project_code = split_pootle_path(self.pootle_path)[:2]
        offset = self.kwargs.get("offset", 0)

        top_scorers = User.top_scorers(
            project=project_code,
            language=language_code,
            limit=TOP_CONTRIBUTORS_CHUNK_SIZE + 1,
            offset=offset,
        )

        return get_top_scorers_data(
            top_scorers,
            TOP_CONTRIBUTORS_CHUNK_SIZE
        )


class TPContributorsJSON(ContributorsJSONMixin, TPBrowseView):
    pass


class TPStoreContributorsJSON(ContributorsJSONMixin, TPBrowseStoreView):
    pass


class LanguageContributorsJSON(ContributorsJSONMixin, LanguageBrowseView):
    pass


class ProjectContributorsJSON(ContributorsJSONMixin, ProjectBrowseView):
    pass


class ProjectsContributorsJSON(ContributorsJSONMixin, ProjectsBrowseView):
    pass


class TopContributorsJSON(View):
    form_class = StatsForm
    content_type = None

    @never_cache
    @method_decorator(ajax_required)
    def dispatch(self, request, *args, **kwargs):
        stats_form = self.get_form()
        if not stats_form.is_valid():
            raise Http404(
                ValidationError(stats_form.errors).messages)

        offset = stats_form.cleaned_data['offset'] or 0
        path = stats_form.cleaned_data['path']
        language_code, project_code, dir_path, filename = \
            split_pootle_path(path)

        kwargs.update(
            dict(
                language_code=language_code,
                project_code=project_code,
                dir_path=dir_path,
                filename=filename,
                offset=offset,
                path=path,
            )
        )
        view_class = ProjectsContributorsJSON
        if language_code and project_code:
            if filename:
                view_class = TPStoreContributorsJSON
            else:
                view_class = TPContributorsJSON
        elif language_code:
            view_class = LanguageContributorsJSON
        elif project_code:
            view_class = ProjectContributorsJSON

        return view_class.as_view()(request, *args, **kwargs)

    def get_form(self):
        return self.form_class(self.request.GET)
