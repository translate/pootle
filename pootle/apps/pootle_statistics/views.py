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
from pootle.core.views import PootleJSONMixin
from pootle_language.views import LanguageBrowseView
from pootle_misc.util import ajax_required
from pootle_project.views import ProjectBrowseView, ProjectsBrowseView
from pootle_translationproject.views import TPBrowseStoreView, TPBrowseView

from .forms import ContributorsForm


class ContributorsJSONMixin(PootleJSONMixin):
    @property
    def path(self):
        return self.kwargs["path"]

    def get_context_data(self, *args, **kwargs):
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


def create_stats_view_class(mixin_class, base_class):
    class new_class(mixin_class, base_class):
        pass
    return new_class


class BaseStatsJSON(View):
    form_class = None
    content_type = None
    mixin_class = None

    @never_cache
    @method_decorator(ajax_required)
    def dispatch(self, request, *args, **kwargs):
        form = self.get_form()
        if not form.is_valid():
            raise Http404(
                ValidationError(form.errors).messages)

        path = form.cleaned_data['path']
        language_code, project_code, dir_path, filename = \
            split_pootle_path(path)

        kwargs.update(
            dict(
                language_code=language_code,
                project_code=project_code,
                dir_path=dir_path,
                filename=filename,
                path=path,
            )
        )
        for field, value in form.cleaned_data.items():
            if field != 'path':
                kwargs.update({field: value})

        base_view_class = ProjectsBrowseView
        if language_code and project_code:
            if filename:
                base_view_class = TPBrowseStoreView
            else:
                base_view_class = TPBrowseView
        elif language_code:
            base_view_class = LanguageBrowseView
        elif project_code:
            base_view_class = ProjectBrowseView
        view_class = create_stats_view_class(self.mixin_class, base_view_class)

        return view_class.as_view()(request, *args, **kwargs)

    def get_form(self):
        return self.form_class(self.request.GET)


class TopContributorsJSON(BaseStatsJSON):
    form_class = ContributorsForm
    mixin_class = ContributorsJSONMixin
