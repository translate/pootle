#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.utils.functional import cached_property

from pootle.i18n.gettext import language_dir
from pootle_language.models import Language
from pootle_project.models import Project


class PootleSite(object):

    @cached_property
    def languages(self):
        languages = {
            lang["code"]: lang
            for lang
            in Language.objects.values("code", "pk", "nplurals")}
        for code, language in languages.items():
            language["direction"] = language_dir(code)
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
        return projects

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
