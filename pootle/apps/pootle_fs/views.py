# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.urlresolvers import reverse

from pootle.core.views.admin import PootleAdminFormView
from pootle_project.models import Project

from .forms import ProjectFSAdminForm


class ProjectFSAdminView(PootleAdminFormView):
    template_name = 'admin/project_fs.html'
    form_class = ProjectFSAdminForm

    def get_context_data(self, **kwargs):
        context = super(ProjectFSAdminView, self).get_context_data(**kwargs)
        context["project"] = self.project
        return context

    @property
    def project(self):
        return Project.objects.get(code=self.kwargs.get("project_code"))

    def get_form_kwargs(self, **kwargs):
        kwargs = super(ProjectFSAdminView, self).get_form_kwargs(**kwargs)
        kwargs.update(dict(project=self.project))
        return kwargs

    def form_valid(self, form):
        form.save()
        return super(ProjectFSAdminView, self).form_valid(form)

    @property
    def success_url(self):
        return reverse(
            "pootle-admin-project-fs",
            kwargs=dict(project_code=self.project.code))
