# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.forms import ValidationError
from django.http import Http404
from django.utils.functional import cached_property

from pootle.core.delegate import scores
from pootle.core.url_helpers import split_pootle_path
from pootle.core.utils.stats import TOP_CONTRIBUTORS_CHUNK_SIZE
from pootle.core.views.base import PootleJSON
from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_project.models import Project, ProjectSet

from .forms import StatsForm


class TopContributorsJSON(PootleJSON):
    form_class = StatsForm

    @cached_property
    def request_kwargs(self):
        stats_form = self.get_form()
        if not stats_form.is_valid():
            raise Http404(
                ValidationError(stats_form.errors).messages)
        return stats_form.cleaned_data

    @cached_property
    def pootle_path(self):
        (language_code, project_code,
         dir_path, filename) = split_pootle_path(self.path)
        if language_code and project_code:
            return (
                "/%s/%s/"
                % (language_code, project_code))
        elif language_code:
            return "/%s/" % language_code
        elif project_code:
            return "/projects/%s/" % project_code

    @cached_property
    def object(self):
        return (
            self.pootle_path
            and Directory.objects.get(pootle_path=self.pootle_path)
            or Directory.objects.projects)

    def get_object(self):
        return self.object

    def get_form(self):
        return self.form_class(self.request.GET)

    @property
    def path(self):
        return self.request_kwargs.get("path")

    @property
    def offset(self):
        return self.request_kwargs.get("offset") or 0

    @property
    def limit(self):
        return TOP_CONTRIBUTORS_CHUNK_SIZE

    @cached_property
    def scores(self):
        return scores.get(
            self.score_context.__class__)(
                self.score_context)

    @property
    def score_context(self):
        (language_code, project_code,
         dir_path, filename) = split_pootle_path(self.path)
        if language_code and project_code:
            return self.object.translationproject
        elif language_code:
            return Language.objects.get(code=language_code)
        elif project_code:
            return Project.objects.get(code=project_code)
        return ProjectSet(
            Project.objects.for_user(self.request.user)
                           .select_related("directory"))

    def get_context_data(self, **kwargs_):

        def scores_to_json(score):
            score["user"] = score["user"].to_dict()
            return score
        top_scorers = self.scores.display(
            offset=self.offset,
            limit=self.limit,
            formatter=scores_to_json)
        return dict(
            items=list(top_scorers),
            has_more_items=(
                len(self.scores.top_scorers)
                > (self.offset + self.limit)))
