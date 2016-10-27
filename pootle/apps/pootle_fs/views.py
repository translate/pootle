# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.urls import reverse

from pootle.core.views.admin import PootleAdminFormView
from pootle_project.models import Project

from .forms import FS_CHOICES, LangMappingFormSet, ProjectFSAdminForm


class ProjectFSAdminView(PootleAdminFormView):
    template_name = 'admin/project_fs.html'
    form_class = ProjectFSAdminForm

    def get_context_data(self, **kwargs):
        context = super(ProjectFSAdminView, self).get_context_data(**kwargs)
        context["project"] = self.project
        context["lang_mapping_formset"] = self.get_lang_mapping_formset()
        context["fs_choices"] = FS_CHOICES
        return context

    def get_lang_mapping_formset(self):
        formset_data = {
            k: v for k, v
            in self.request.POST.items()
            if k.startswith("lang-mapping")}
        formset_kwargs = dict(project=self.project, prefix="lang-mapping")
        if formset_data:
            formset_kwargs["data"] = formset_data
        formset = LangMappingFormSet(**formset_kwargs)
        if formset_data and formset.is_valid():
            formset.save()
            del formset_kwargs["data"]
            formset = LangMappingFormSet(**formset_kwargs)
        return formset

    @property
    def project(self):
        return Project.objects.get(code=self.kwargs.get("project_code"))

    def get_form_kwargs(self, **kwargs):
        kwargs = super(ProjectFSAdminView, self).get_form_kwargs(**kwargs)
        kwargs.update(dict(project=self.project))
        kwargs["prefix"] = "fs-config"
        kwargs["data"] = {
            k: v for k, v
            in kwargs.get("data", {}).items()
            if k.startswith("fs-config")}
        if not kwargs["data"]:
            del kwargs["data"]
            if kwargs.get("files") is not None:
                del kwargs["files"]
        return kwargs

    def form_valid(self, form):
        form.save()
        return super(ProjectFSAdminView, self).form_valid(form)

    @property
    def success_url(self):
        return reverse(
            "pootle-admin-project-fs",
            kwargs=dict(project_code=self.project.code))
