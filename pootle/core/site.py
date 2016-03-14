#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.functional import cached_property
from django.utils.lru_cache import lru_cache

from pootle.i18n.gettext import language_dir
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject


class PootleSite(object):

    @cached_property
    def languages(self):
        languages = {
            lang["code"]: lang
            for lang
            in Language.objects.values("code", "pk", "nplurals")}
        for code, language in languages.items():
            language["direction"] = language_dir(code)
            language["projects"] = self.projects_for_language(language["pk"])
        return languages

    @cached_property
    def projects(self):
        projects = {
            proj["code"]: proj
            for proj
            in Project.objects.values(
                "code", "pk", "disabled", "source_language", "checkstyle")}
        for project in projects.values():
            project["source_direction"] = self.get_language(
                project["source_language"])["direction"]
            project["languages"] = self.languages_for_project(project["pk"])
        return projects

    @cached_property
    def active_languages(self):
        return set(
            TranslationProject.objects.values_list(
                "language_id", flat=True))

    @cached_property
    def active_projects(self):
        return set(
            Project.objects.values_list("id", flat=True))

    @lru_cache()
    def languages_for_project(self, project_id):
        return set(
            TranslationProject.objects.filter(
                project_id=project_id).values_list("language_id", flat=True))

    @lru_cache()
    def projects_for_language(self, language_id):
        return set(
            TranslationProject.objects.filter(
                language_id=language_id).values_list("project_id", flat=True))

    @property
    def disabled_projects(self):
        return [
            proj["pk"]
            for proj
            in self.projects.values()
            if proj["disabled"]]

    def get_language(self, language_id):
        for code, language in self.languages.items():
            if language["pk"] == language_id:
                return language

    def get_project(self, project_id):
        for code, project in self.projects.items():
            if project["pk"] == project_id:
                return project

pootle_site = PootleSite()
