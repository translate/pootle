# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json

from django.core.exceptions import PermissionDenied
from django.views.generic import TemplateView

from pootle.core.delegate import formats
from pootle.core.views import APIView
from pootle.core.views.mixins import CanCreateProjectsRequiredMixin
from pootle.i18n.gettext import ugettext as _
from pootle_app.forms import ProjectForm
from pootle_app.models.permissions import (PermissionSet,
                                           check_user_permission,
                                           get_pootle_permission)
from pootle_config.utils import ObjectConfig
from pootle_fs.delegate import fs_plugins
from pootle_fs.presets import FS_PRESETS
from pootle_language.models import Language
from pootle_project.models import PROJECT_CHECKERS, Project


__all__ = ('ProjectAdminView', 'ProjectAPIView')


class ProjectAdminView(CanCreateProjectsRequiredMixin, TemplateView):
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

        project_checker_choices = [
            (checker, checker)
            for checker
            in sorted(PROJECT_CHECKERS.keys())]
        plugin_choices = sorted([(x, x) for x in fs_plugins.gather()])
        fs_presets = FS_PRESETS.values()
        return {
            'page': 'admin-projects',
            'form_choices': {
                'checkstyle': project_checker_choices,
                'filetypes': filetypes,
                'fs_plugin': plugin_choices,
                'fs_preset': fs_presets,
                'source_language': language_choices,
                'defaults': {
                    'source_language': default_language,
                },
            },
        }


class ProjectAPIView(CanCreateProjectsRequiredMixin, APIView):
    model = Project
    base_queryset = Project.objects.order_by('-id')
    add_form_class = ProjectForm
    edit_form_class = ProjectForm
    page_size = 10
    search_fields = ('code', 'fullname', 'disabled')
    m2m = ("filetypes", )
    config = (
        ("fs_plugin", "pootle_fs.fs_type"),
        ("fs_url", "pootle_fs.fs_url"),
        ("fs_mapping", "pootle_fs.translation_mappings"))

    def post(self, request, *args, **kwargs):
        """Creates a project.

        Users that are not superusers become administrators of the projects
        they create, so that they can manage them afterwards.
        """
        response = super(ProjectAPIView, self).post(request, *args, **kwargs)
        if response.status_code == 200 and not request.user.is_superuser:
            self.add_project_administrator(
                json.loads(response.content)[self.pk_field_name],
                request.user)
        return response

    def put(self, request, *args, **kwargs):
        """Updates a project.

        Only superusers and administrators of the given project can alter it.
        """
        project_pk = kwargs.get(self.pk_field_name)
        if project_pk is not None and not request.user.is_superuser:
            project = self.base_queryset.filter(pk=project_pk).first()
            can_administrate = (
                project is not None
                and check_user_permission(
                    request.user, 'administrate', project.directory))
            if not can_administrate:
                raise PermissionDenied(
                    _('You do not have rights to administer this project.'))
        return super(ProjectAPIView, self).put(request, *args, **kwargs)

    def delete(self, request, *args, **kwargs):
        """Deletes a project - only allowed for superusers."""
        if not request.user.is_superuser:
            raise PermissionDenied(
                _('You do not have rights to delete projects.'))
        return super(ProjectAPIView, self).delete(request, *args, **kwargs)

    def add_project_administrator(self, project_pk, user):
        """Gives `user` `administrate` rights on the given project."""
        project = self.base_queryset.get(pk=project_pk)
        permission_set = PermissionSet.objects.get_or_create(
            user=user, directory=project.directory)[0]
        permission_set.positive_permissions.add(
            get_pootle_permission('administrate'))

    def serialize_config(self, info, item):
        config = ObjectConfig(item)
        for k, v in self.config:
            if k == "fs_mapping":
                mapping = config.get(v) or {}
                info[k] = mapping.get("default")
            else:
                info[k] = config.get(v)
        info["template_name"] = (
            item.lang_mapper.get_upstream_code("templates"))
