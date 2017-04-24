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
from pootle.core.http import JsonResponse
from pootle.core.views import APIView
from pootle.core.views.decorators import (
    set_permissions, requires_permission_class)
from pootle.core.views.mixins import SuperuserRequiredMixin
from pootle_app.forms import ProjectForm
from pootle_app.models.directory import Directory
from pootle_app.models.permissions import (
    check_user_permission, get_pootle_permission, PermissionSet)
from pootle_language.models import Language
from pootle_project.models import PROJECT_CHECKERS, Project


__all__ = ('ProjectAdminView', 'ProjectAPIView')


class ProjectGenericAdminView(TemplateView):
    template_name = 'admin/projects.html'
    page_code = 'admin-projects'

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

        project_checker_choices = [
            (checker, checker)
            for checker
            in sorted(PROJECT_CHECKERS.keys())]

        return {
            'page': self.page_code,
            'form_choices': {
                'checkstyle': project_checker_choices,
                'filetypes': filetypes,
                'source_language': language_choices,
                'treestyle': Project.treestyle_choices,
                'defaults': {
                    'source_language': default_language,
                },
            },
        }


class ProjectAdminView(SuperuserRequiredMixin, ProjectGenericAdminView):
    pass


class ProjectAPIView(APIView):
    model = Project
    base_queryset = Project.objects.order_by('-id')
    add_form_class = ProjectForm
    edit_form_class = ProjectForm
    page_size = 10
    search_fields = ('code', 'fullname', 'disabled')
    m2m = ("filetypes",)

    @property
    def permission_context(self):
        return Directory.objects.root

    @set_permissions
    @requires_permission_class("add_project")
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_superuser:
            exclude_projects = [project.pk
                                for project in self.base_queryset.all()
                                if not check_user_permission(
                                    request.user,
                                    "administrate",
                                    project.directory
                                )]
            self.base_queryset = self.base_queryset.exclude(
                pk__in=exclude_projects)
        return super(ProjectAPIView, self).dispatch(request,
                                                    *args, **kwargs)

    def post(self, request, *args, **kwargs):
        try:
            request_dict = json.loads(request.body)
        except ValueError:
            return self.status_msg('Invalid JSON data', status=400)

        form = self.add_form_class(request_dict)

        if form.is_valid():
            new_object = form.save()
            permissionset = PermissionSet.objects.create(
                user=request.user,
                directory=new_object.directory
            )
            permissionset.positive_permissions.add(
                get_pootle_permission("administrate")
            )
            request.user.permissionset_set.add(permissionset)

            wrapper_qs = self.base_queryset.filter(pk=new_object.pk)
            return JsonResponse(
                self.qs_to_values(wrapper_qs, single_object=True)
            )

        return self.form_invalid(form)
