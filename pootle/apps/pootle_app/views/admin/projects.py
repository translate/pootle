# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json

from django.views.generic import TemplateView

from pootle.core.delegate import formats
from pootle.core.views import APIView, SuperuserRequiredMixin
from pootle_app.forms import ProjectAddForm, ProjectEditForm
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject


__all__ = ('ProjectAdminView', 'ProjectAPIView')


class ProjectAdminView(SuperuserRequiredMixin, TemplateView):
    template_name = 'admin/projects.html'

    def get_context_data(self, **kwargs):
        languages = Language.objects.exclude(code='templates')
        language_choices = [(lang.id, unicode(lang)) for lang in languages]
        try:
            english = Language.objects.get(code='en')
            default_language = english.id
        except Language.DoesNotExist:
            default_language = languages[0].id

        filetypes = []
        for info in formats.get().values():
            filetypes.append(
                [info["pk"], info["display_title"]])

        pk = self.kwargs.get("id")
        if pk:
            instance = Project.objects.get(pk=pk)
            template_choices = instance.translationproject_set.values_list(
                "id", "language__fullname")
        else:
            template_choices = Language.objects.values_list("id", "fullname")

        template_choices = [
            (choice[0], unicode(choice[1])) for choice in template_choices]

        return {
            'page': 'admin-projects',
            'form_choices': {
                'checkstyle': Project.checker_choices,
                'filetypes': filetypes,
                'source_language': language_choices,
                'template_tp': template_choices,
                'template_lang': language_choices,
                'treestyle': Project.treestyle_choices,
                'defaults': {
                    'source_language': default_language,
                },
            },
        }


class ProjectAPIView(SuperuserRequiredMixin, APIView):
    model = Project
    base_queryset = Project.objects.order_by('-id')
    add_form_class = ProjectAddForm
    edit_form_class = ProjectEditForm
    page_size = 10
    search_fields = ('code', 'fullname', 'disabled')
    m2m = ("filetypes", )

    def serialize_qs(self, *args, **kwargs):
        deserial = json.loads(
            super(ProjectAPIView, self).serialize_qs(*args, **kwargs))
        project_pks = None
        tp_fields = ("pk", "project_id", "language__fullname")
        tps = {}

        if "models" in deserial:
            project_pks = [
                proj["id"] for proj
                in deserial["models"]]
        elif "id" in deserial:
            project_pks = [deserial["id"]]

        if project_pks:
            tp_qs = TranslationProject.objects.filter(project_id__in=project_pks)
            for tp, proj, language in tp_qs.values_list(*tp_fields):
                if proj not in tps:
                    tps[proj] = []
                tps[proj].append(dict(value=str(tp), label=language))

        if "models" in deserial:
            for project in deserial["models"]:
                project["template_tp"] = project["template_tp"] or ""
                project["tps"] = tps.get(project["id"], [])
        elif "id" in deserial:
            deserial["template_tp"] = deserial["template_tp"] or ""
            deserial["tps"] = tps.get(deserial["id"], [])
        return json.dumps(deserial)
